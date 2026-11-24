"""Seleção, projeção e vínculo canônicos das duas etapas R2."""
from dataclasses import dataclass
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
C02 = HERE.parent
C05 = C02 / "c05"
sys.path[:0] = [str(C05), str(C02)]

from budget import BudgetError, cap_usd
from common import c01, encode, injected_inventory, preflight, project
from journal import inventory
from settings import EXECUTOR_FILES, Settings, digest, read_pinned

PROFILE = c01.get_profile(c01.R2)
SCOPE = "c05-qwen-r2"
STAGES = ("development", "final")
VERSIONS = {"profile": PROFILE.name, "protocol_version": PROFILE.quality_version,
            "report_version": PROFILE.report_version, "ipc_contract_version": PROFILE.ipc_version}
EXECUTION_FILES = (*EXECUTOR_FILES, *(HERE / name for name in ("execute.py", "plan.py", "gate.py", "seal.py")))


@dataclass(frozen=True)
class Round:
    profile: c01.ReportProfile
    scope: str
    prefix: str
    fixture_provider: str
    entrypoint: Path
    settings_class: type
    execution_files: tuple
    check_account: object = None
    adapter: type = None
    live_gateway: object = None
    stop_on_error: bool = False

    @property
    def versions(self):
        profile = self.profile
        return dict(profile=profile.name, protocol_version=profile.quality_version,
                    report_version=profile.report_version, ipc_contract_version=profile.ipc_version)


R2 = Round(PROFILE, SCOPE, "r2-", c01.R2_FIXTURE_PROVIDER, HERE / "execute.py", Settings, EXECUTION_FILES)


def canonical_digest(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def gate_reference(path):
    path = path.resolve()
    if not path.is_relative_to(c01.ROOT) or not path.is_file():
        raise BudgetError("prova de development exige arquivo dentro do checkout")
    return inventory(path)


class Plan:
    def __init__(self, stage, mode, run_id, config, *, round_spec=R2):
        self.round = round_spec
        profile = round_spec.profile
        if stage not in STAGES or mode not in {"real", "fixture"}:
            raise BudgetError("etapa ou modo inválido")
        self.stage, self.mode, self.config = stage, mode, config
        self.settings = round_spec.settings_class.load(config, mode, expected_scope=round_spec.scope)
        self.validation, self.protocol, self.split, self.catalog, self.cases, golden = preflight(profile.name)
        self.sources = c01.round_sources(self.protocol)
        candidate = c01.read(c01.source_path(self.sources["candidate"]))
        if candidate["contract_version"] != profile.ipc_version:
            raise BudgetError("IPC da candidata diverge do perfil")
        self.identity = candidate["identity"]
        if mode == "fixture":
            self.identity = dict(self.identity, mode=mode, provider=round_spec.fixture_provider)

        reference = self.protocol["control_policy"]
        self.control_policy = c01.read(c01.source_path(reference))
        if stage == "development":
            split_name, ids, controls, request_limit = "development", self.sources["development_ids"], [], 6
        else:
            split_name = "final_test"
            ids = [i for mask in ("category", "priority", "category+priority") for i in self.split[split_name][mask]]
            controls, request_limit = golden["inputs"], 44
        control_ids = [i["id"] for i in controls]
        self.injections = injected_inventory([i for i in control_ids if i in self.control_policy["controls"]],
                                             reference, self.control_policy)
        self.inputs = [project(self.cases[i], self.catalog, ipc_version=profile.ipc_version) for i in ids] + controls
        self.candidates = {}
        for item in self.inputs:
            c01.structure(self.validation, "input", item)
            missing, invalid, _ = c01.normalize_input(item, self.catalog)
            if missing and not invalid and item["catalog"] == self.catalog and item["id"] not in self.injections["ids"]:
                self.candidates[item["id"]] = item
        expected = (6, 0, 0, 6) if stage == "development" else (36, 13, 1, 44)
        if (len(ids), len(controls), self.injections["count"], len(self.candidates)) != expected:
            raise BudgetError("dimensões da etapa divergem do protocolo congelado")

        self.input_bytes = "".join(encode(item) + "\n" for item in self.inputs).encode("utf-8")
        revision = subprocess.check_output(["rtk", "git", "rev-parse", "HEAD"], cwd=c01.ROOT, text=True).strip()
        baseline = golden["report"]
        self.report = dict(baseline, identity=self.identity, split=split_name, planned_ids=ids, completed_ids=ids,
                           control_ids=control_ids, injected_controls=self.injections, run_id=run_id,
                           git_revision=revision, eligibility="inconclusive",
                           environment=dict(baseline["environment"], runtime=platform.python_version(),
                                            hardware=platform.machine(), peak_memory_bytes=None))
        c01.structure(self.validation, "report", self.report)
        c01.verify_sources(self.report, self.protocol, self.split)
        self.binding = dict(round_spec.versions, scope=round_spec.scope, stage=stage, git_revision=revision, identity=self.identity,
                            sources=self.report["sources"], candidate=self.sources["candidate"], data_freeze=self.sources["freeze"],
                            final_cases=self.sources["final_cases"], config_sha256=self.settings.sha256,
                            control_policy=reference, inputs_sha256=digest(self.input_bytes), selected_ids=ids,
                            control_ids=control_ids, candidate_ids=list(self.candidates),
                            concurrency=1, attempts=1, max_requests=request_limit,
                            reservation_usd=None if self.settings.reservation is None else str(self.settings.reservation),
                            executor_sha256={file.relative_to(c01.ROOT).as_posix(): c01.digest(file)
                                             for file in round_spec.execution_files})
        if "operational" in self.sources:
            self.binding.update(operational=self.sources["operational"],
                                source_lock={"path": profile.lock_file, "sha256": profile.lock_sha256})

    def bound_account(self, account, cap, gate=None):
        if account is None or not account.id or cap is None or account.scope != self.mode:
            raise BudgetError("informe caminho, identidade, modo e teto da conta")
        cap = cap_usd(cap)
        if self.round.check_account is not None:
            self.round.check_account(account)
        if self.mode == "real" and cap != cap_usd("10"):
            raise BudgetError("execução real exige o teto global de US$ 10")
        return dict(self.binding, development_gate=gate, account={"path": str(account.path), "id": account.id,
                                                                  "scope": account.scope, "cap_usd": str(cap)})

    def manifest_id(self, account):
        return self.round.prefix + canonical_digest(dict(account_id=account.id, stage=self.stage,
            candidate_sha256=self.sources["candidate"]["sha256"], final_cases_sha256=self.sources["final_cases"]["sha256"]))

    def authorize(self, path, account, cap, confirmed, gate=None):
        if not confirmed or path is None:
            raise BudgetError("execução exige --confirm-execution e manifesto habilitado")
        if self.stage == "final" and gate is None:
            raise BudgetError("etapa final exige --development-gate")
        self.settings.verify_execution()
        binding = self.bound_account(account, cap, gate)
        manifest, pin = read_pinned(path)
        manifest_id = self.manifest_id(account)
        if (not isinstance(manifest, dict) or set(manifest) != {"enabled", "manifest_id", "binding"}
                or manifest["enabled"] is not True or manifest["manifest_id"] != manifest_id
                or canonical_digest(manifest["binding"]) != canonical_digest(binding)):
            raise BudgetError(f"manifesto {self.round.prefix[:-1].upper()} desabilitado ou divergente da etapa, conta, código, fontes ou prova")
        return manifest_id, pin, canonical_digest(binding), binding
