"""Ordem operacional: coleta -> seleção -> freeze público -> exposição -> auditoria."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from ..contracts.artifacts import validate_manifest, validate_report
from ..contracts.core import CATALOG, FIELDS, PLAN, PROTOCOL, ROOT, SCHEMA_PATH, VERSION, decode, read, read_lines, require, sha256, structure, verify_files
from .audit import derive
from .runner import check_command, encoded, save, supervise

WORKER_ENTRY = "script/classification_comparison/setfit_sf2/adapter/__main__.py"


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def approved_catalog(cfg):
    source = PROTOCOL["sources"]["catalog"]
    raw = Path(cfg["training_files"]["catalog"]).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == source["sha256"] == sha256(ROOT/source["path"]),
            "catálogo ativo diverge dos bytes aprovados")
    catalog = decode(raw)
    require(catalog == CATALOG, "catálogo dos contratos em memória diverge do aprovado")
    return catalog


def adapter_digest(path, training_code):
    """Confere o índice com o inventário efetivo de 03 e os bytes do entrypoint."""
    raw = Path(path).read_bytes()
    index = decode(raw)
    structure("componentIndex", index)
    frozen = read(training_code)
    structure("componentIndex", frozen)
    for name in index["files"]:
        member = PurePosixPath(name)
        require(member.parts and not member.is_absolute() and ".." not in member.parts
                and member.as_posix() == name and "\\" not in name
                and (ROOT / name).resolve().is_relative_to(ROOT), "caminho inválido no índice do adaptador")
    require(index["files"].keys() == (frozen["files"].keys() | {WORKER_ENTRY}),
            "inventário incompleto ou divergente do adaptador")
    for name, expected in index["files"].items():
        require(sha256(ROOT/name) == expected, "SHA-256 divergente no membro do adaptador: " + name)
    # Importar o helper de inventário somente após conferir os módulos que ele carrega.
    from ..training.fit import code_manifest

    # code_manifest recalcula os digests, inclusive de requisitos e módulos de contrato.
    actual = code_manifest()["files"]
    require(actual == {name: digest for name, digest in index["files"].items() if name != WORKER_ENTRY},
            "inventário incompleto ou divergente do adaptador")
    return hashlib.sha256(raw).hexdigest()


def public_setup(config):
    cfg = read(config)
    expected = {"training_files", "model_files", "model_manifest", "adapter", "versions", "capture_policy",
                "capture_command", "final_command", "costs", "startup_seconds"}
    require(set(cfg) == expected, "configuração pública divergente")
    model_files, train_files = cfg["model_files"], cfg["training_files"]
    training = read(model_files["training_freeze"])
    validate_manifest("trainingFreeze", training, train_files)
    model = read(cfg["model_manifest"])
    validate_manifest("modelManifest", model, model_files)
    require(model["training_freeze_sha256"] == sha256(model_files["training_freeze"]), "base de treino divergente")
    versions = read(cfg["versions"])
    require(all(versions.get(k) == v for k, v in model["versions"].items()), "versões do modelo divergentes")
    check_command(read(cfg["capture_command"]))
    require(type(cfg["startup_seconds"]) in (int, float) and cfg["startup_seconds"] > 0, "startup_seconds inválido")
    return cfg, model


def load_policy(cfg, model, path):
    policy = read(path)
    structure("policy", policy)
    ids = dict(package_sha256=sha256(cfg["model_manifest"]), model_sha256=model["model_sha256"], policy_sha256=sha256(path))
    return policy, ids


def products(cfg, model, data, dest, policy_path):
    policy, ids = load_policy(cfg, model, policy_path)
    scores, grid, report = derive(read_lines(data), sha256(data), dest/"run", policy, model, ids, read(cfg["costs"]),
                                  catalog=approved_catalog(cfg))
    complete = len(scores["rows"]) == PROTOCOL["data"][report["partition"]]["total"]
    results = {"scores.json" if complete else "partial-scores.json": scores}
    if grid is not None:
        results["grid.json"] = grid
        if grid["selected"] is not None:
            results["policy.json"] = grid["selected"]
            report["policy_sha256"] = digest(grid["selected"])
    report["score_package_sha256"] = digest(scores)
    validate_report(report)
    results["report.json"] = report
    if grid is not None:
        results["selection.json"] = dict(
            policy_count=len(grid["policies"]), eligible_count=sum(row["eligible"] for row in grid["policies"]),
            capture_policy_sha256=ids["policy_sha256"], selected_policy_sha256=digest(grid["selected"]) if grid["selected"] else None,
            scores_sha256=digest(scores), predictions_sha256=report["predictions_sha256"], grid_sha256=digest(grid),
            timings_sha256=sha256(dest/"run/timings.jsonl"), latency_source="observed_capture_policy_external_total")
    return results


def store_products(dest, docs):
    for name, doc in docs.items():
        save(dest/name, doc)


def validate(config, dest):
    cfg, model = public_setup(config)
    spec = cfg["capture_policy"]
    policy, ids = load_policy(cfg, model, spec)
    data = cfg["training_files"]["validation"]
    dest.mkdir()
    save(dest/"capture.json", capture_receipt(cfg, spec))
    supervise(read_lines(data), read(cfg["capture_command"]), policy, model, ids, dest/"run", cfg["startup_seconds"],
              catalog=approved_catalog(cfg))
    docs = products(cfg, model, data, dest, spec)
    store_products(dest, docs)
    return docs["report.json"]["status"]


def sources():
    here = Path(__file__).parent
    return {**{f"evaluation/{n}": here/n for n in ("audit.py", "metrics.py", "runner.py", "selection.py", "workflow.py", "__main__.py")},
            **{f"contracts/{n}": here.parent/"contracts"/n for n in ("ipc.py", "core.py", "artifacts.py", "data.py")},
            "schema": SCHEMA_PATH, "protocol": PLAN/"protocolo.json"}


def capture_receipt(cfg, spec):
    approved_catalog(cfg)
    policy = read(spec)
    minimum = {k: min(PROTOCOL["review_policy"][k+"_grid"]) for k in ("tau", "delta")}
    require(all(policy[f] == minimum for f in FIELDS), "política de coleta não predeterminada")
    files = dict(policy=spec, argv=cfg["capture_command"], package=cfg["model_manifest"],
                 catalog=cfg["training_files"]["catalog"], contract_catalog=ROOT/PROTOCOL["sources"]["catalog"]["path"],
                 validation=cfg["training_files"]["validation"], **sources())
    return {**{k: sha256(p) for k,p in files.items()},
            "adapter": adapter_digest(cfg["adapter"], cfg["training_files"]["training_code"])}


def freeze_files(cfg, validation, release):
    return dict(training_freeze=cfg["model_files"]["training_freeze"], model_manifest=cfg["model_manifest"],
                adapter=cfg["adapter"], policy=validation/"policy.json", validation_scores=validation/"scores.json",
                validation_report=validation/"report.json", validation_predictions=validation/"run/predictions.jsonl",
                final_seal=cfg["training_files"]["final_seal"], command=release/"command.json", versions=cfg["versions"],
                train=cfg["training_files"]["train"], validation=cfg["training_files"]["validation"])


def checked_development(config, validation, release):
    cfg, model = public_setup(config)
    paths = freeze_files(cfg, validation, release)
    require(capture_receipt(cfg, cfg["capture_policy"]) == read(validation/"capture.json"), "coleta diverge do pré-voo")
    docs = products(cfg, model, paths["validation"], validation, cfg["capture_policy"])
    require(docs["report.json"]["status"] == "eligible", "validação inelegível; final fechado")
    verify_files({k: digest(v) for k, v in docs.items()}, {k: validation/k for k in docs})
    return cfg, model, paths


def command_receipt(cfg, validation):
    files = {**sources(), "capture": validation/"capture.json", "capture_policy": cfg["capture_policy"],
             "capture_command": cfg["capture_command"], "originals": validation/"run/predictions.jsonl",
             "observed_timings": validation/"run/timings.jsonl", "controls": validation/"run/controls.jsonl",
             "capture_seal": validation/"run/seal.json", "scores": validation/"scores.json", "grid": validation/"grid.json",
             "selection_receipt": validation/"selection.json",
             "selected_policy": validation/"policy.json", "validation_report": validation/"report.json"}
    return dict(argv=check_command(read(cfg["final_command"])), files={k: sha256(p) for k,p in files.items()})


def release_files(config, cfg, validation, release):
    return dict(config=config, capture_policy=cfg["capture_policy"], capture_command=cfg["capture_command"],
                costs=cfg["costs"], validation_seal=validation/"run/seal.json", grid=validation/"grid.json",
                freeze=release/"freeze.json")


def freeze(config, validation, release):
    require(not (validation/"final-exposure.json").exists(), "validação já usada para expor o final")
    cfg, model, paths = checked_development(config, validation, release)
    release.mkdir()
    save(paths["command"], command_receipt(cfg, validation))
    final_hash = read(paths["final_seal"])["files"]["final"]["sha256"]
    doc = dict(contract_version=VERSION, files={**{k: sha256(p) for k, p in paths.items()}, "final": final_hash},
               class_order=model["class_order"], model_sha256=model["model_sha256"], validation_eligible=True)
    validate_manifest("freeze", doc, paths)
    save(release/"freeze.json", doc)
    files = release_files(config, cfg, validation, release)
    save(release/"release.json", {k: sha256(p) for k,p in files.items()})
    return sha256(release/"release.json")


def check_release(config, validation, release, expected):
    require(sha256(release/"release.json") == expected, "recibo de freeze diferente do aprovado")
    cfg = read(config)
    verify_files(read(release/"release.json"), release_files(config, cfg, validation, release))
    cfg, model, paths = checked_development(config, validation, release)
    validate_manifest("freeze", read(release/"freeze.json"), paths)
    require(read(paths["command"]) == command_receipt(cfg, validation), "comando/proveniência de seleção divergente")
    return cfg, model, paths


def final_files(paths, private_inventory):
    private = read(private_inventory)
    require(set(private) == {"final", "annotations", "review_receipt", "token_lengths"}, "inventário reservado divergente")
    validate_manifest("finalSeal", read(paths["final_seal"]), private)
    return private


def execute(config, validation, release, expected, private_inventory, dest):
    cfg, model, paths = check_release(config, validation, release, expected)
    policy, ids = load_policy(cfg, model, paths["policy"])
    argv = check_command(read(paths["command"])["argv"])
    exposure = dict(release_sha256=expected, destination=str(dest.resolve()), inventory=str(private_inventory.resolve()),
                    opened_at=datetime.now(timezone.utc).isoformat())
    require(not dest.exists(), "diretório final já existe")
    # Também impede uma nova tentativa com outra liberação da mesma coleta.
    save(validation/"final-exposure.json", exposure)
    save(release/"exposure.json", exposure)
    dest.mkdir()
    try:
        private = final_files(paths, private_inventory)
        seal = supervise(read_lines(private["final"]), argv, policy, model, ids, dest/"run", cfg["startup_seconds"],
                         catalog=approved_catalog(cfg))
    except (ValueError, OSError, KeyError) as exc:
        save(dest/"interruption.json", dict(reason=str(exc), exposure=exposure))
        raise
    save(dest/"execution.json", dict(exposure=exposure, predictions_seal_sha256=sha256(dest/"run/seal.json"),
                                    interrupted=seal["failure"] is not None))
    return sha256(dest/"execution.json")


def audit(config, validation, release, expected, private_inventory, dest, execution_sha256):
    cfg, model, paths = check_release(config, validation, release, expected)
    exposure = read(release/"exposure.json")
    require(read(validation/"final-exposure.json") == exposure, "exposição diverge da validação")
    require(datetime.fromisoformat(exposure["opened_at"]).tzinfo is not None and
            exposure == dict(release_sha256=expected, destination=str(dest.resolve()), inventory=str(private_inventory.resolve()),
                             opened_at=exposure["opened_at"]),
            "exposição final incompatível com a execução")
    require(sha256(dest/"execution.json") == execution_sha256, "recibo de execução diferente do selado")
    receipt = read(dest/"execution.json")
    require(receipt["exposure"] == exposure and receipt["predictions_seal_sha256"] == sha256(dest/"run/seal.json"),
            "previsões não seladas para esta execução")
    private = final_files(paths, private_inventory)
    docs = products(cfg, model, private["final"], dest, paths["policy"])
    for name, value in docs.items():
        path = dest/name
        if path.exists():
            require(sha256(path) == digest(value), "auditoria diverge do artefato " + name)
        else:
            save(path, value)
    return docs["report.json"]["status"]
