"""Reconfere a origem pública histórica, a execução atual e a paridade da decisão fixa."""
import gzip
from pathlib import Path
from types import CodeType
import sys
from tempfile import TemporaryDirectory

from ..contracts import core, ipc
from ..evaluation.metrics import metrics
from ..evaluation.runner import controls
from ..revision_r1 import cli as replay
from ..training.environment import check_pins
from . import bootstrap as b
from .package import verified_package
from .storage import canonical, digest, encoded, read, require

PACKAGE = b.PACKAGE
HISTORICAL_COMMIT = "4eb86a3282f94f32119042a0f6aa075e9f72960a"
OFFLINE = "99cf2f33e1803838e33813d5c4ff46971181ce4e"
PUBLIC = {"final_protocol": b.FINAL_PROTOCOL, "offline_protocol": replay.AMENDMENT,
          "preflight": b.REV + "/preflight.json", "capture": replay.PARENT_FILES["capture"],
          "policy": replay.PARENT_FILES["capture_policy"], "selected": b.REV + "/selected-policy.json",
          "package_manifest": replay.PARENT_FILES["package_manifest"], "final_seal": replay.PARENT_FILES["final_seal"]}


def command(root, commit, release, run):
    argv = [str(b.PYTHON), "-I", "-B", "-S", str(root / b.SF / "qualification_r1/cli.py"), "_worker",
            "--commit", commit, "--release", str(release), "--run", str(run), "--package", str(PACKAGE),
            "--package-sha256", "224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872",
            "--policy", str(root / PUBLIC["policy"])]
    return dict(argv=argv, cwd=str(root), environment=b.ENVIRONMENT)


def configuration(root, commit, release, run):
    return dict(accepted_checkout=str(root), accepted_commit=commit, historical_checkout=str(b.HISTORY),
                offline_checkout=str(b.REPLAY), package=str(PACKAGE), python=str(b.PYTHON), public_paths=PUBLIC,
                command=command(root, commit, release, run), release=str(release), run=str(run))


def validate_bindings():
    from . import execution, runner
    require(runner.project is ipc.project and execution.project is ipc.project and execution.CATALOG is core.CATALOG
            and execution._supervise is runner._supervise, "alias em memória do caminho de execução substituído")


def validate_state(snapshot, data, runtime):
    validate_bindings()
    require(core.ROOT == snapshot and encoded(core.PROTOCOL) == encoded(core.decode(data["protocol"]))
            and encoded(core.CATALOG) == encoded(core.decode(data["catalog"]))
            and core.LABELS == {f: core.PROTOCOL["labels"][f] for f in core.FIELDS}
            and core.validator("decision").schema == {
                **core.decode(data["schema"]), "$ref": "#/$defs/decision"}, "contratos em memória divergentes")
    for name, module in tuple(sys.modules.items()):
        if name.startswith("script.") and getattr(module, "__file__", None):
            require(Path(module.__file__).is_relative_to(snapshot), "import local fora do snapshot: " + name)
    for name in ("load_context", "derive", "verify"):
        func = getattr(runtime, name)
        module = sys.modules.get(getattr(func, "__module__", ""))
        require(module and func.__module__.startswith(runtime.__name__) and getattr(func, "__name__", None) == name
                and func.__globals__ is vars(module), "runtime substituído em memória")
        filename = Path(func.__code__.co_filename)
        require(filename == Path(module.__file__) and filename.is_relative_to(snapshot), "runtime fora do snapshot")
        declared = compile(read(filename), str(filename), "exec")
        implementations = [c for c in declared.co_consts if isinstance(c, CodeType) and c.co_name == name]
        require(implementations == [func.__code__], "implementação do runtime substituída em memória")


def parity(data, report, context, runtime):
    rows = [core.decode(line) for line in data["validation"].splitlines()]
    groups = [(rows, data["predictions"]), (controls(), data["controls"])]
    cases, calls = [], 0
    for index, (batch, frames) in enumerate(groups):
        for row, raw in zip(batch, frames.splitlines(keepends=True), strict=True):
            item = ipc.project(row, core.CATALOG)
            decision = runtime.derive(item, raw, context)
            runtime.verify(item, raw, decision, context)
            if index == 0:
                cases.append(decision)
            elif row["id"] in ("sf2-control-complete", "sf2-control-invalid"):
                calls += sum(decision["calls"].values())
    matches = [entry for entry in report["policies"] if entry["policy"] == report["selected"]]
    m = metrics(rows, cases, calls)
    require(len(cases) == 90 and len(matches) == 1 and matches[0]["eligible"] and
            encoded(m) == encoded(matches[0]["metrics"]), "métricas divergem do replay escolhido")
    return dict(cases=len(cases), controls=len(controls()), metrics_sha256=digest(encoded(m)),
                first_id=cases[0]["id"], first_raw_sha256=cases[0]["raw_sha256"])


def attest_history(replay_root, capture_root, amendment_sha, inventory_sha):
    """O auditor histórico só recebe cópias regulares de papéis públicos abertos sem seguir links."""
    replay_names = {replay.INVENTORY, replay.AMENDMENT, *replay.SOURCES, *replay.PARENT_FILES.values(),
                    *replay.EXTRA_TRAINING.values(), replay.VAL + "/run/stderr.log"}
    for field in ("category", "priority"):
        for component in ("manifest", *replay.COMPONENTS):
            replay_names.add(f"{replay.PACK}/{field}/{component}.json")
    capture_names = {*replay.CAPTURE_PATHS.values(), *replay.ADAPTER_MEMBERS}
    with TemporaryDirectory(dir="/tmp", prefix="sf2-history-") as temporary:
        base = Path(temporary)
        for root, copy, names in ((replay_root, base / "replay", replay_names),
                                  (capture_root, base / "capture", capture_names)):
            for name in sorted(names):
                raw = read(root / name)
                path = copy / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        return replay.attest(base / "replay", base / "capture", amendment_sha, inventory_sha)


def inspect_public(root, commit, snapshot, sources, config, dependencies=None):
    release, run = (Path(config[k]) for k in ("release", "run"))
    projected = root / b.SF / ".cache/qualificacao-r1-01"
    require(all(path.parent == projected for path in (release, run)), "diretório fora da área projetada")
    canonical(release)
    canonical(run)
    require(release != run and not release.is_relative_to(run) and not run.is_relative_to(release)
            and config == configuration(root, commit, release, run), "configuração ou comando desviado")
    spec = core.decode(read(snapshot / b.FINAL_PROTOCOL, b.PLAN_SHA))
    anchors = spec["anchors_sha256"]
    pre = core.decode(read(snapshot / PUBLIC["preflight"], anchors["offline_preflight"]))
    b.checkout(b.HISTORY, HISTORICAL_COMMIT)
    require(pre["historical_commit"] == HISTORICAL_COMMIT and pre["accepted_commit"] == OFFLINE,
            "commits históricos divergentes")
    origin = pre["provenance"]
    for name, sha in origin["current_sources"].items():
        require(digest(b.committed(b.REPLAY, OFFLINE, name)) == sha, "fonte histórica do replay divergente")
    # Aqui as dependências auditadas são as da revisão offline original. O runner atual tem outro inventário.
    amendment, data, _, provenance, _ = attest_history(
        b.REPLAY, b.HISTORY, anchors["amendment_offline"], origin["inventory_sha256"])
    require(provenance == origin and len(data) == 29 and len(amendment["parent"]["files"]) == 28
            and len(origin["historical_capture"]) == 19 and len(origin["historical_adapter"]) == 17,
            "proveniência histórica divergente")
    for role, info in amendment["parent"]["files"].items():
        require(read(snapshot / info["path"], info["sha256"]) == data[role], "papel público divergente: " + role)
    for name, expected in origin["historical_adapter"].items():
        require(sources[name] == expected, "membro efetivo do worker divergente: " + name)
    validation = Path(core.decode(data["pre_validation"])["evaluation_argv"][-1])
    require(validation == b.HISTORY / b.SF / ".cache/qualificacao-01/evaluation-02/validation"
            and read(validation / "capture.json") == data["capture"], "captura histórica efetiva divergente")
    exe = core.decode(read(snapshot / (b.REV + "/execution.json"), anchors["offline_execution"]))
    archived = gzip.decompress(read(snapshot / (b.REV + "/result.json.gz"), anchors["offline_result_gzip"]))
    require(digest(archived) == exe["original_result_sha256"], "resultado R1 divergente")
    read(snapshot / (b.REV + "/revisoes/revisao-final.md"), anchors["offline_global_review"])
    report = core.decode(archived)
    policy = read(snapshot / PUBLIC["selected"], spec["candidate"]["selected"]["policy_sha256"])
    require(report["provenance"] == origin and report["status"] == "eligible_validation_only"
            and report["selected"] == core.decode(policy) and report["counts"] ==
            {"original": 225, "original_eligible": 0, "additional": 45, "eligible": 9, "union": 270}
            and core.decode(data["parent_report"])["status"] == "failed", "seleção histórica divergente")
    from .. import runtime_r1 as runtime
    validate_state(snapshot, data, runtime)
    context = runtime.load_context(data["capture_policy"], policy, data["package_manifest"])
    versions = check_pins()
    with verified_package(PACKAGE, data["package_manifest"], spec["candidate"]["package_sha256"]) as (_, manifest):
        require(manifest["versions"] == versions and manifest["class_order"] == spec["candidate"]["class_order"]
                and manifest["model_sha256"] == spec["candidate"]["model_sha256"]
                and manifest["files"] == origin["public_package_members"], "pacote, classes ou pins divergentes")
    require(dependencies, "dependências do processo sem atestação")
    checked_parity = parity(data, report, context, runtime)
    protocol_seal = read(snapshot / PUBLIC["final_seal"], anchors["public_final_seal"])
    freeze = dict(accepted_commit=commit, offline_commit=OFFLINE, capture_commit=HISTORICAL_COMMIT,
                  current_sources=sources, historical=origin, selection=report["selected"],
                  selection_counts=report["counts"], parity=checked_parity, final_seal_sha256=digest(protocol_seal),
                  package_sha256=context["package_sha256"], package_members=manifest["files"],
                  class_order=manifest["class_order"], model_sha256=manifest["model_sha256"], versions=versions, dependencies=dependencies,
                  python_executable=b.interpreter(), historical_capture_costs=core.decode(data["capture_costs"]))
    return freeze, context, core.decode(protocol_seal)

