from datetime import datetime, timezone
from pathlib import Path
import sys

from script.classification_comparison.setfit_sf2.contracts.core import (
    FIELDS, LABELS, PROTOCOL, ROOT, VERSION, read, require, sha256,
)
from script.classification_comparison.setfit_sf2.evaluation.workflow import WORKER_ENTRY, capture_receipt, public_setup
from script.classification_comparison.setfit_sf2.training.package import read_verified_package, write_json

cache = Path(sys.argv[1])
training = cache / "training-02"
output = cache / "evaluation-02"
status = read(training / "status.json")
evidence = read(training / "evidence.json")
preflight = read(cache / "attempt-02/preflight.json")
environment = read(cache / "environment.json")
recipe = PROTOCOL["training"]
require(status["status"] == "complete" and status["exit_code"] == 0, "supervisor não completou o treino")
require(0 < status["training_seconds"] <= recipe["aggregate_training_limit_seconds"], "prazo de aprendizado inválido")
package_hash = status["package_sha256"]
package = training / "package"
manifest, files = read_verified_package(package, package_hash)
require(evidence["package_sha256"] == package_hash, "evidência de treino não corresponde ao pacote")
require(evidence["training_freeze_sha256"] == manifest["training_freeze_sha256"] == preflight["training_freeze_sha256"],
        "treino não corresponde ao congelamento")
require(evidence["versions"] == manifest["versions"] == environment["versions"], "versões divergentes")
specialists = evidence["specialists"]
require(set(specialists) == set(FIELDS), "inventário de especialistas divergente")
for field in FIELDS:
    learned = specialists[field]
    require(learned["status"] == "trained" and set(learned["classes"]) == set(LABELS[field]),
            f"classes ou aprendizado ausente: {field}")
    require(learned["classes"] == manifest["class_order"][field], f"ordem de classes inválida: {field}")
    require(learned["encoder_parameter_sha256_before"] != learned["encoder_parameter_sha256_after"],
            f"peso monitorado não mudou: {field}")
    require(all(learned["head_parameters"][key] == value for key, value in recipe["head"].items() if key != "class"),
            f"parâmetros da cabeça divergentes: {field}")
    require(read(files[field + ".base_encoder/snapshot.json"]) == environment["snapshot"]
            and read(files[field + ".training_evidence/run.json"]) == learned,
            f"evidência de proveniência divergente: {field}")
    require(learned["head_iterations"] and
            all(0 < n < recipe["head"]["max_iter"] for n in learned["head_iterations"]),
            f"convergência da cabeça sem evidência: {field}")
    require(learned["pair_rows"] == 2 * recipe["num_iterations"] * PROTOCOL["data"]["train"]["total"]
            and learned["optimizer_steps"] > 0 and learned["training_seconds"] > 0,
            f"ajuste incompleto: {field}")
    require(learned["applied_encoder_arguments"] == {k: recipe[k] for k in learned["applied_encoder_arguments"]},
            f"receita aplicada divergente: {field}")
require(specialists["category"]["encoder_parameter_sha256_before"] ==
        specialists["priority"]["encoder_parameter_sha256_before"], "pesos iniciais divergentes")
reload_checks = evidence["reload_checks"]
require(len(reload_checks) == 6 and all(sum(item["field"] == field for item in reload_checks) == 3 for field in FIELDS)
        and all(item["max_abs_score_diff"] <= recipe["reload_score_absolute_tolerance"] for item in reload_checks),
        "recibo de reload incompleto")
adapter = read(cache / "training-code.json")
adapter["files"][WORKER_ENTRY] = sha256(ROOT / WORKER_ENTRY)
minimum = {k: min(PROTOCOL["review_policy"][k + "_grid"]) for k in ("tau", "delta")}
policy = {"contract_version": VERSION, **{field: minimum for field in FIELDS}}
output.mkdir()
capture_policy = output / "capture-policy.json"
versions = output / "versions.json"
adapter_path = output / "adapter.json"
costs = output / "costs.json"
capture_argv = output / "capture-argv.json"
final_argv = output / "final-argv.json"
cfg_path = output / "config.json"
validation = output / "validation"
worker = [sys.executable, "-B", "-m", "script.classification_comparison.setfit_sf2.adapter",
          "--package", str(package), "--package-sha256", package_hash, "--policy"]
write_json(capture_policy, policy)
write_json(versions, manifest["versions"])
write_json(adapter_path, adapter)
write_json(costs, {"download_ms": 0, "training_ms": status["training_seconds"] * 1000, "classifier_api_calls": 0})
write_json(capture_argv, worker + [str(capture_policy)])
write_json(final_argv, worker + [str(validation / "policy.json")])
cfg = {"training_files": read(cache / "training-files.json"), "model_files": {key: str(path) for key, path in files.items()},
       "model_manifest": str(package / "manifest.json"), "versions": str(versions), "adapter": str(adapter_path),
       "capture_policy": str(capture_policy), "capture_command": str(capture_argv), "final_command": str(final_argv),
       "costs": str(costs), "startup_seconds": 60}
write_json(cfg_path, cfg)
public_setup(cfg_path)
capture = capture_receipt(cfg, capture_policy)
require(capture["package"] == package_hash and capture["adapter"] == sha256(adapter_path), "captura não autentica o pacote")
write_json(output / "pre-validation.json", {
    "preflight_status": "passed", "checked_at_utc": datetime.now(timezone.utc).isoformat(), "cwd": str(ROOT),
    "package_sha256": package_hash, "package_member_count": len(files), "adapter_member_count": len(adapter["files"]),
    "evidence_sha256": sha256(training / "evidence.json"), "supervised_status_sha256": sha256(training / "status.json"),
    "reload_observations": len(reload_checks), "startup_seconds": cfg["startup_seconds"],
    "evaluation_config_sha256": sha256(cfg_path), "capture_expected": capture,
    "evaluation_argv": [sys.executable, "-B", "-m", "script.classification_comparison.setfit_sf2.evaluation",
                        "validate", str(cfg_path), str(validation)],
})
print(package_hash)
