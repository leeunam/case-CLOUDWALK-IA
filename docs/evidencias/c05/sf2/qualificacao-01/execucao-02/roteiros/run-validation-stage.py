from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from time import monotonic

from script.classification_comparison.setfit_sf2.contracts.core import read, require, sha256
from script.classification_comparison.setfit_sf2.training.package import json_bytes, write_json

root = Path(sys.argv[1])
stage = sys.argv[2]
evaluation = root / "evaluation-02"
stage_config = read(evaluation / "config.json")
pre = read(evaluation / "pre-validation.json")
env = read(root / "attempt-02/preflight.json")["environment_allowlist"]
require(str(Path.cwd()) == pre["cwd"], "cwd fora do pré-voo")
require(sha256(evaluation / "config.json") == pre["evaluation_config_sha256"], "configuração alterada")
validation = evaluation / "validation"
interpreter = pre["evaluation_argv"][0]
run = validation / "run"
if stage == "validate":
    require(not validation.exists(), "coleta já iniciada")
    argv = pre["evaluation_argv"]
elif stage == "scores":
    report = read(validation / "report.json")
    seal = read(run / "seal.json")
    manifest = Path(stage_config["model_manifest"])
    require(report["status"] in {"failed", "eligible"} and seal["failure"] is None, "coleta incompleta ou interrompida")
    require(sha256(manifest) == pre["package_sha256"], "pacote não corresponde ao verificado")
    argv = [interpreter, "-B", "-m", "script.classification_comparison.setfit_sf2.training", "scores",
            "--package", str(manifest.parent), "--package-sha256", pre["package_sha256"],
            "--validation", stage_config["training_files"]["validation"], "--policy", stage_config["capture_policy"],
            "--predictions", str(run / "predictions.jsonl"), "--predictions-sha256", seal["files"]["predictions.jsonl"],
            "--output", str(evaluation / "scores-sf2-03.json")]
elif stage == "freeze":
    audit = read(evaluation / "validation-audit.json")
    require(audit["status"] == "eligible" and audit["equal_score_objects"], "validação sem elegibilidade auditada")
    require(sha256(validation / "report.json") == audit["report_sha256"], "relatório não corresponde à auditoria")
    require(not (evaluation / "release").exists(), "liberação já iniciada")
    argv = [*pre["evaluation_argv"][:4], "freeze", str(evaluation / "config.json"), str(validation),
            str(evaluation / "release")]
else:
    raise ValueError("etapa fora da passagem A")
receipt = evaluation / f"{stage}-launch.json"
started = datetime.now(timezone.utc).isoformat()
with receipt.open("xb") as target:
    target.write(json_bytes({"argv": argv, "cwd": str(Path.cwd()), "started_at_utc": started}))
stdout_path = evaluation / f"{stage}.stdout.log"
stderr_path = evaluation / f"{stage}.stderr.log"
before = monotonic()
with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
    run_status = subprocess.run(argv, env=env, stdout=stdout, stderr=stderr, check=False)
write_json(evaluation / f"{stage}-status.json", {
    "exit_code": run_status.returncode, "started_at_utc": started,
    "finished_at_utc": datetime.now(timezone.utc).isoformat(), "operator_elapsed_seconds": monotonic() - before,
    "stdout_sha256": sha256(stdout_path), "stderr_sha256": sha256(stderr_path),
})
print(stdout_path.read_text(), end="")
print(stderr_path.read_text(), end="", file=sys.stderr)
sys.exit(run_status.returncode)
