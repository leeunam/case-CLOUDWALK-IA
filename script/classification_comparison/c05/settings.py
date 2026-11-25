"""Vincula o plano canônico da C02 à configuração financeira da C05."""
import json
import platform
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
C02 = HERE.parent
QWEN = C02 / "adapters" / "qwen"
sys.path[:0] = [str(C02), str(QWEN)]

from adapters.qwen.adapter import MODEL, VERSION
from budget import Account, BudgetError, cap_usd, reference, usd
from common import c01, decode, encode, injected_inventory, preflight, project

SCOPE = "c05-qwen-final"
ADAPTER_VERSION = "1.1.0"
PROFILE = c01.get_profile(c01.OBSERVED)
MAX_TOKENS = 128
REASONING = {"enabled": False}
MIN_INPUT_CEILING = 1_024_000
MIN_OUTPUT_CEILING = 131_072
PRICE_NAMES = ("input", "output", "cache_read", "cache_write")
REQUEST_LIMIT = 44
USD_PER_CREDIT = Decimal("0.01")
VERSIONS = {"profile": PROFILE.name, "protocol_version": PROFILE.quality_version,
            "report_version": PROFILE.report_version, "ipc_contract_version": PROFILE.ipc_version}
EXECUTOR_FILES = (
    HERE / "execute.py", HERE / "settings.py", HERE / "budget.py", HERE / "final_adapter.py",
    QWEN / "adapter.py", QWEN / "pilot.py", QWEN / "transport.py", QWEN / "fixture.py",
    C02 / "run.py", C02 / "common.py", C02 / "journal.py", C02 / "metrics.py",
    C02.parent / "check_classification_contracts.py",
)


def digest(content):
    return sha256(content).hexdigest()


def read_pinned(path):
    content = path.read_bytes()
    return decode(content), digest(content)


@dataclass
class Settings:
    data: dict
    sha256: str
    reservation: Decimal

    request_keys = {"max_tokens", "reasoning"}
    extra_keys = set()
    real_minimum = (MIN_INPUT_CEILING, MIN_OUTPUT_CEILING)

    @classmethod
    def valid_request(cls, data):
        return (type(data["max_tokens"]) is int and data["max_tokens"] == MAX_TOKENS
                and isinstance(data["reasoning"], dict) and set(data["reasoning"]) == {"enabled"}
                and data["reasoning"]["enabled"] is False)

    @classmethod
    def load(cls, path, mode, *, expected_scope=SCOPE):
        return cls.from_pinned(*read_pinned(path), mode, expected_scope)

    @classmethod
    def from_pinned(cls, data, pin, mode, expected_scope):
        expected = {"scope", "mode", *cls.request_keys, *cls.extra_keys, "billable_input_token_ceiling",
                    "billable_output_token_ceiling", "billable_limits_reference", "billable_limits_confirmed",
                    "tariff_verified", "tariff", "usage_cost_unit", "usage_cost_reference", "usage_credits"}
        if (not isinstance(data, dict) or set(data) != expected or data["scope"] != expected_scope or data["mode"] != mode
                or not cls.valid_request(data)):
            raise BudgetError("configuração de requisição ou escopo incompatível com a C05")
        in_min, out_min = cls.real_minimum if mode == "real" else (1, MAX_TOKENS)
        input_limit = data["billable_input_token_ceiling"]
        output_limit = data["billable_output_token_ceiling"]
        if (type(input_limit) is not int or input_limit < in_min
                or type(output_limit) is not int or output_limit < out_min):
            raise BudgetError("limites faturáveis inválidos ou abaixo dos limites conservadores")
        reference(data["billable_limits_reference"])
        tariff = data["tariff"]
        if not isinstance(tariff, dict) or set(tariff) != {"unit", "source", "date", *PRICE_NAMES}:
            raise BudgetError("tarifa requer unidade, data, fonte e quatro valores")
        try:
            date.fromisoformat(tariff["date"])
        except (TypeError, ValueError):
            raise BudgetError("data de tarifa inválida") from None
        reference(tariff["source"])
        if tariff["unit"] != "USD/Mtoken":
            raise BudgetError("tarifa deve usar USD/Mtoken")
        price = {name: usd(tariff[name]) for name in PRICE_NAMES}
        if price["input"] <= 0 or price["output"] <= 0:
            raise BudgetError("tarifa de entrada e saída deve ser positiva")
        for name in ("billable_limits_confirmed", "tariff_verified"):
            if type(data[name]) is not bool:
                raise BudgetError(f"{name} deve ser booleano")
        if data["usage_cost_unit"] not in (None, "USD"):
            raise BudgetError("unidade de usage.cost deve ser USD ou desconhecida")
        if data["usage_cost_unit"] == "USD":
            reference(data["usage_cost_reference"])
        elif data["usage_cost_reference"] is not None:
            raise BudgetError("referência de custo exige unidade USD declarada")
        credits = data["usage_credits"]
        if credits is not None:
            if (not isinstance(credits, dict) or set(credits) != {"confirmed", "reference", "usd_per_credit"}
                    or type(credits["confirmed"]) is not bool or usd(credits["usd_per_credit"]) != USD_PER_CREDIT):
                raise BudgetError("conversão de créditos exige referência, confirmação e US$ 0,01 por crédito")
            reference(credits["reference"])
        with localcontext() as ctx:
            ctx.prec = 64
            worst = (input_limit * (price["input"] + price["cache_read"] + price["cache_write"])
                     + output_limit * price["output"]) / 1_000_000
        return cls(data, pin, usd(worst))

    def verify_execution(self):
        if self.data["billable_limits_confirmed"] is not True or self.data["tariff_verified"] is not True:
            raise BudgetError("confirmação de tarifa e limites faturáveis pendente")


class Plan:
    def __init__(self, mode, run_id, config_path):
        self.settings = Settings.load(config_path, mode)
        self.validation, self.protocol, self.split, self.catalog, self.cases, example = preflight(PROFILE.name)
        historic = c01.read(QWEN / "real.json")
        if (historic["identity"]["requested_model"] != MODEL or historic["contract_version"] != VERSION
                or VERSION != PROFILE.ipc_version):
            raise BudgetError("adaptador Qwen ou IPC incompatível")
        self.identity = dict(historic["identity"], mode=mode, adapter_version=ADAPTER_VERSION)
        if mode == "fixture":
            self.identity["provider"] = "simulador-c05"
        historic_plan = c01.read(HERE / "plano-qwen-final" / "plan.json")
        for key in ("prompt", "policy"):
            if historic[key] != historic_plan["sources"][key]:
                raise BudgetError("prompt ou política divergente do plano congelado")
        sources = dict(example["report"]["sources"], prompt=historic["prompt"], policy=historic["policy"])
        ids = [case for group in self.split["final_test"].values() for case in group]
        controls = example["inputs"]
        reference = self.protocol["control_policy"]
        self.control_policy = c01.read(c01.source_path(reference))
        self.injections = injected_inventory(
            [item["id"] for item in controls if item["id"] in self.control_policy["controls"]],
            reference, self.control_policy)
        self.inputs = [project(self.cases[case], self.catalog, ipc_version=PROFILE.ipc_version) for case in ids] + controls
        self.candidates = {}
        for item in self.inputs:
            c01.structure(self.validation, "input", item)
            missing, invalid, _ = c01.normalize_input(item, self.catalog)
            if (missing and not invalid and item["catalog"] == self.catalog
                    and item["id"] not in self.injections["ids"]):
                self.candidates[item["id"]] = item
        if (len(ids), len(controls), len(self.candidates)) != (36, 13, REQUEST_LIMIT):
            raise BudgetError("dimensões divergentes do plano final congelado")
        if (ids != historic_plan["selected_ids"]
                or [item["id"] for item in controls] != historic_plan["control_ids"]):
            raise BudgetError("IDs ou ordem divergentes do plano final congelado")
        self.input_bytes = "".join(encode(item) + "\n" for item in self.inputs).encode("utf-8")
        if digest(self.input_bytes) != historic_plan["input"]["sha256"]:
            raise BudgetError("entradas divergentes da projeção final congelada")
        revision = subprocess.check_output(["rtk", "git", "rev-parse", "HEAD"], cwd=c01.ROOT, text=True).strip()
        self.report = dict(example["report"], identity=self.identity, sources=sources, split="final_test",
                           planned_ids=ids, completed_ids=ids, injected_controls=self.injections,
                           run_id=run_id, git_revision=revision, eligibility="inconclusive",
                           environment=dict(example["report"]["environment"], runtime=platform.python_version(),
                                            hardware=platform.machine(), peak_memory_bytes=None))
        c01.structure(self.validation, "report", self.report)
        c01.verify_sources(self.report, self.protocol, self.split)
        self.binding = dict(VERSIONS, scope=SCOPE, git_revision=revision, identity=self.identity,
                            config_sha256=self.settings.sha256, sources=sources, control_policy=reference,
                            inputs_sha256=digest(self.input_bytes), final_ids=ids,
                            control_ids=self.report["control_ids"], candidate_ids=list(self.candidates),
                            concurrency=1, attempts=1, max_requests=REQUEST_LIMIT,
                            reservation_usd=str(self.settings.reservation),
                            executor_sha256={str(file.relative_to(c01.ROOT)): c01.digest(file)
                                             for file in EXECUTOR_FILES})

    def bound_account(self, account, cap):
        if account is None or cap is None or not account.id:
            raise BudgetError("execução exige caminho, identidade da conta e teto global")
        return dict(self.binding, account={"path": str(account.path), "id": account.id,
                                           "scope": account.scope, "cap_usd": str(cap_usd(cap))})

    def authorize(self, path, account, cap, confirmed):
        if not confirmed or path is None:
            raise BudgetError("execução exige --confirm-execution e manifesto habilitado")
        self.settings.verify_execution()
        actual, pin = read_pinned(path)
        binding = self.bound_account(account, cap)
        if (not isinstance(actual, dict) or set(actual) != {"enabled", "manifest_id", "binding"}
                or actual["enabled"] is not True or
                json.dumps(actual["binding"], sort_keys=True) != json.dumps(binding, sort_keys=True)):
            raise BudgetError("manifesto desabilitado ou divergente do plano, da configuração ou da conta")
        manifest_id = reference(actual["manifest_id"])
        return manifest_id, pin, digest(json.dumps(binding, sort_keys=True).encode("utf-8"))


def account_from_args(parser):
    parser.add_argument("--account", type=Path, help="caminho explícito do arquivo SQLite")
    parser.add_argument("--account-id", help="identidade retornada na inicialização")
    parser.add_argument("--cap-usd", type=cap_usd, help="teto global vinculado ao manifesto")


def resolve_account(args, scope):
    options = (args.account, args.account_id, args.cap_usd)
    if not any(option is not None for option in options):
        return None
    if any(option is None for option in options):
        raise BudgetError("informe caminho, identidade e teto global juntos")
    return Account(args.account, args.account_id, scope)
