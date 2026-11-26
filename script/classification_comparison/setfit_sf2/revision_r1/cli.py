"""Inicializador de replay SF2-R1. Até a atestação, usa só a biblioteca padrão."""
import argparse
import gzip
import hashlib
import importlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
import time
import types

ROOT = Path(__file__).absolute().parents[4]
SF = "script/classification_comparison/setfit_sf2"
PLAN = "docs/planejamento/classificacao-comparativa/sf2"
QUAL = "docs/evidencias/c05/sf2/qualificacao-01"
PACK = QUAL + "/execucao-02/pacote"
EVAL = QUAL + "/execucao-02/avaliacao"
VAL = EVAL + "/validation"
AMENDMENT = PLAN + "/sf2-r1-protocolo.json"
SCHEMA = PLAN + "/sf2-r1.schema.json"
INVENTORY = SF + "/revision_r1/sources.json"
DESTINATION = SF + "/.cache/revisao-01"
PARENT_FILES = {
    "protocol": PLAN + "/protocolo.json", "schema": PLAN + "/contratos/sf2.schema.json",
    "validation": PLAN + "/dados/validation.jsonl", "public_manifest": PLAN + "/dados/manifest-public.json",
    "final_seal": PLAN + "/dados/final-seal.json", "catalog": "script/f08/jev/catalog.json",
    "package_manifest": PACK + "/manifest.json", "training_freeze": QUAL + "/training-freeze.json",
    "capture": VAL + "/capture.json", "capture_policy": EVAL + "/capture-policy.json", "seal": VAL + "/run/seal.json",
    "predictions": VAL + "/run/predictions.jsonl", "controls": VAL + "/run/controls.jsonl",
    "journal": VAL + "/run/timings.jsonl", "scores04": VAL + "/scores.json", "scores03": EVAL + "/scores-sf2-03.json",
    "parent_selection": VAL + "/selection.json", "parent_report": VAL + "/report.json",
    "parent_grid_gzip": VAL + "/grid.json.gz", "parent_grid_original": VAL + "/grid-original.json",
    "parent_config": EVAL + "/config.json", "pre_validation": EVAL + "/pre-validation.json",
    "capture_argv": EVAL + "/capture-argv.json", "adapter_index": EVAL + "/adapter.json",
    "training_code": QUAL + "/training-code.json", "training_arguments": QUAL + "/arguments.json",
    "capture_costs": EVAL + "/costs.json", "capture_versions": EVAL + "/versions.json",
}
CAPTURE_MODULES = [f"evaluation/{name}.py" for name in ("audit", "metrics", "runner", "selection", "workflow", "__main__")]
CAPTURE_MODULES += [f"contracts/{name}.py" for name in ("ipc", "core", "artifacts", "data")]
CAPTURE_PATHS = {name: SF + "/" + name for name in CAPTURE_MODULES}
CAPTURE_PATHS.update({role: PARENT_FILES[key] for role, key in {
    "schema": "schema", "protocol": "protocol", "argv": "capture_argv", "policy": "capture_policy",
    "catalog": "catalog", "contract_catalog": "catalog", "package": "package_manifest",
    "validation": "validation", "adapter": "adapter_index",
}.items()})
PILOT = "script/classification_comparison/setfit_pilot"
TRAINING_SOURCES = {
    "script/classification_comparison/requirements.txt", PILOT + "/provision.py", PILOT + "/requirements.txt",
    SF + "/adapter/decide.py", SF + "/contracts/__init__.py",
    *(SF + "/" + name for name in CAPTURE_MODULES if name.startswith("contracts/")),
    *(SF + "/training/" + filename for filename in (
        "__main__.py", "environment.py", "fit.py", "package.py", "scores.py", "supervise.py", "requirements.txt")),
}
ADAPTER_MEMBERS = TRAINING_SOURCES | {SF + "/adapter/__main__.py"}
# Somente estes módulos podem ser importados, mesmo se houver um homônimo ou .pyc no checkout.
MODULES = [name for name in CAPTURE_MODULES if name not in ("evaluation/__main__.py", "evaluation/workflow.py")]
MODULES += ["evaluation/__init__.py", "contracts/__init__.py", "revision_r1/engine.py"]
SOURCES = (ADAPTER_MEMBERS | {SF + "/" + name for name in (*CAPTURE_MODULES, *MODULES, "revision_r1/cli.py")}
           | {SCHEMA, PARENT_FILES["catalog"], PARENT_FILES["schema"], PARENT_FILES["protocol"]})
EXTRA_TRAINING = {
    "annotations": PLAN + "/dados/annotations-public.jsonl", "train": PLAN + "/dados/train.jsonl",
    "rubric": PLAN.rsplit("/", 1)[0] + "/rubrica-comum.md", "model_lock": PILOT + "/model-lock.json",
    "requirements": PILOT + "/requirements.txt",
    **{role: "docs/evidencias/c05/sf2/dados-publicos-01/" + name for role, name in (
        ("review_receipt", "review-receipt.json"), ("token_lengths", "token-lengths.json"))},
}
COMPONENTS = ("base_encoder", "encoder", "head", "tokenizer", "training_evidence")


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    root, rel = Path(root), Path(relative)
    check(root.is_absolute() and root == root.resolve() and not rel.is_absolute()
          and ".." not in rel.parts and str(rel) == relative and "\\" not in relative,
          "raiz ou caminho não canônico")
    path = root / rel
    check(path.resolve() == path, f"caminho redirecionado: {relative}")
    return path


def verified(root, name, digest):
    raw = safe_path(root, name).read_bytes()
    check(sha(raw) == digest, f"SHA-256 divergente: {name}")
    return raw


def verify_sources(root, expected_digest):
    inventory = json.loads(verified(root, INVENTORY, expected_digest))
    check(set(inventory) == SOURCES, "conjunto de fontes R1 divergente")
    source_bytes = {name: verified(root, name, digest) for name, digest in inventory.items()}
    return inventory, source_bytes


def attest(root, history, amendment_sha, inventory_sha):
    inventory, source_bytes = verify_sources(root, inventory_sha)
    amendment = json.loads(verified(root, AMENDMENT, amendment_sha))
    check((amendment["id"], amendment["version"], amendment["status"]) ==
          ("C05-SF2-R1", "1.0.0", "approved_offline_extension"), "emenda incorreta")
    files = amendment["parent"]["files"]
    check({role: info["path"] for role, info in files.items()} == PARENT_FILES, "caminhos públicos divergentes")
    paths = {role: safe_path(root, path) for role, path in PARENT_FILES.items()}
    raw = {role: verified(root, info["path"], info["sha256"]) for role, info in files.items()}
    capture, pre = (json.loads(raw[k]) for k in ("capture", "pre_validation"))
    check(pre["preflight_status"] == "passed" and pre["capture_expected"] == capture
          and pre["evaluation_config_sha256"] == sha(raw["parent_config"])
          and pre["package_sha256"] == sha(raw["package_manifest"]), "pré-voo/configuração divergente")
    check(set(capture) == set(CAPTURE_PATHS), "inventário histórico de captura divergente")
    for role, path in CAPTURE_PATHS.items():
        verified(history, path, capture[role])
        if role != "evaluation/selection.py":
            verified(root, path, capture[role])
    adapter, training = (json.loads(raw[k])["files"] for k in ("adapter_index", "training_code"))
    check(set(adapter) == ADAPTER_MEMBERS and set(training) == TRAINING_SOURCES
          and all(adapter[k] == v for k, v in training.items()) and pre["adapter_member_count"] == len(adapter),
          "membros de treino/adaptador divergentes")
    for path, digest in adapter.items():
        verified(history, path, digest)
        check(inventory[path] == digest, "adaptador atual diverge da captura")
    freeze = json.loads(raw["training_freeze"])
    training_paths = {**EXTRA_TRAINING, **{k: PARENT_FILES[k] for k in (
        "catalog", "protocol", "public_manifest", "validation", "training_code")},
        "arguments": PARENT_FILES["training_arguments"], "contracts": PARENT_FILES["schema"]}
    check(set(training_paths) == set(freeze["files"]) and freeze["final_seal_sha256"] == sha(raw["final_seal"]),
          "freeze de treino divergente")
    for role, name in training_paths.items():
        verified(root, name, freeze["files"][role])
    model = json.loads(raw["package_manifest"])
    component_hashes = {}
    model_files = model["files"]
    for field in ("category", "priority"):
        descriptor = verified(root, f"{PACK}/{field}/manifest.json", model["model_sha256"][field])
        component_hashes[field + ".manifest"] = sha(descriptor)
        check(json.loads(descriptor) == model["models"][field] and set(model["models"][field]) == set(COMPONENTS),
              "descritor público de especialista divergente")
        for part in COMPONENTS:
            role = field + "." + part
            index = verified(root, f"{PACK}/{field}/{part}.json", model["models"][field][part])
            component_hashes[role] = sha(index)
            component_hashes.update({role + "/" + name: digest for name, digest in json.loads(index)["files"].items()})
    check(model["training_freeze_sha256"] == sha(raw["training_freeze"]) and
          model["arguments_sha256"] == sha(raw["training_arguments"]) and model_files == {
              **component_hashes, "training_freeze": sha(raw["training_freeze"]), "arguments": sha(raw["training_arguments"])}
          and pre["package_member_count"] == len(model_files), "índices públicos do pacote divergentes")
    seal = json.loads(raw["seal"])
    run_files = {"predictions.jsonl": "predictions", "controls.jsonl": "controls", "timings.jsonl": "journal"}
    check(set(seal["files"]) == {*run_files, "stderr.log"} and seal["failure"] is None, "selo incompleto")
    for name, role in run_files.items():
        check(seal["files"][name] == sha(raw[role]), "arquivo do selo divergente: " + name)
    verified(root, VAL + "/run/stderr.log", seal["files"]["stderr.log"])
    archived = gzip.decompress(raw["parent_grid_gzip"])
    grid_hash = amendment["parent"]["original_grid_sha256"]
    check(json.loads(raw["parent_grid_original"]) == {"size_bytes": len(archived), "sha256": sha(archived)}
          and sha(archived) == grid_hash, "grade descomprimida divergente")
    provenance = dict(amendment_sha256=amendment_sha, inventory_sha256=inventory_sha, current_sources=inventory,
                      historical_capture=capture, historical_adapter=adapter, parent_files=files,
                      sealed_files=seal["files"], public_package_members=model_files,
                      weights_verified_in_replay=False)
    return amendment, paths, archived, provenance, source_bytes


class VerifiedModules(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Usa exclusivamente os bytes Python atestados, sem consultar caches do checkout."""
    namespace = "_sf2_verified"
    def __init__(self, root, sources):
        self.modules = {}
        for name in MODULES:
            path = SF + "/" + name
            module = name.removesuffix(".py").removesuffix("/__init__").replace("/", ".")
            self.modules[self.namespace + "." + module] = (str(root/path), sources[path], name.endswith("/__init__.py"))

    def find_spec(self, fullname, path, target=None):
        if fullname in self.modules:
            filename, _, package = self.modules[fullname]
            return importlib.util.spec_from_loader(fullname, self, origin=filename, is_package=package)
        if fullname.startswith(self.namespace + "."):
            raise ImportError("módulo SF2 fora do inventário: " + fullname)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        filename, source, _ = self.modules[module.__name__]
        module.__file__ = filename
        exec(compile(source, filename, "exec"), module.__dict__)


def engine_from(root, sources):
    finder = VerifiedModules(root, sources)
    for name in (finder.namespace, finder.namespace + ".revision_r1"):
        check(name not in sys.modules, "inicializador exige um processo novo")
        pkg = types.ModuleType(name)
        pkg.__path__ = []
        sys.modules[name] = pkg
    sys.meta_path.insert(0, finder)
    return importlib.import_module(finder.namespace + ".revision_r1.engine")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", required=True, type=Path)
    parser.add_argument("--amendment-sha256", required=True)
    parser.add_argument("--inventory-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        check(sys.flags.isolated and sys.dont_write_bytecode, "use o Python com -I -B")
        destination = safe_path(ROOT, DESTINATION)
        check(not destination.exists(), "destino R1 já existe")
        amendment, paths, archive, origin, sources = attest(
            ROOT, args.historical_root, args.amendment_sha256, args.inventory_sha256)
        engine = engine_from(ROOT, sources)
        policies = engine.extension_policies(amendment, sources[SCHEMA])
        data = engine.audit_capture(amendment, paths)
        original = engine.confirm_original(data, archive, amendment["parent"])
        engine.check_union(original, policies)
        # A criação exclusiva reserva a única rodada antes de avaliar qualquer corte novo.
        destination.mkdir(parents=True, exist_ok=False)
        started = time.perf_counter()
        report = engine.compare(data, original, policies)
        report.update(extension_compute_seconds=time.perf_counter()-started, provenance=origin,
                      quotas=amendment["validation_quotas"], gates=amendment["gates"],
                      selection_order=amendment["extension"]["selection_order"])
        pending = destination/"result.pending"
        with pending.open("xb") as stream:
            stream.write(engine.encoded(report))
        (destination/"result.json").hardlink_to(pending)
        pending.unlink()
        print(f"{report['status']} | {destination}/result.json")
        return 0 if report["selected"] else 1
    except Exception as exc:
        print(f"SF2-R1 inválida: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
