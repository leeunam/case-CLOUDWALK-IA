from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

from script.classification_comparison.setfit_sf2.contracts.artifacts import validate_report
from script.classification_comparison.setfit_sf2.contracts.core import (
    FIELDS, PROTOCOL, read, read_lines, require, sha256, verify_files,
)
from script.classification_comparison.setfit_sf2.evaluation.metrics import quality_gates
from script.classification_comparison.setfit_sf2.training.package import write_json

cache = Path(sys.argv[1]) / "evaluation-02"
validation = cache / "validation"
cfg = read(cache / "config.json")
pre = read(cache / "pre-validation.json")
require(read(validation / "capture.json") == pre["capture_expected"], "capture alterado")
report = read(validation / "report.json")
validate_report(report)
run = validation / "run"
seal = read(run / "seal.json")
verify_files(seal["files"], {name: run / name for name in seal["files"]})
require(report["status"] in {"eligible", "failed"} and seal["failure"] is None, "coleta incompleta")
quota = PROTOCOL["data"]["validation"]
require(report["counts"]["observed"] == quota["total"], "narrativas incompletas")
predictions = read_lines(run / "predictions.jsonl")
timings = read_lines(run / "timings.jsonl")
controls = read_lines(run / "controls.jsonl")
require(len(predictions) == quota["total"] and len(timings) == len(predictions) + len(controls),
        "contagens dos frames/timings divergem")
require(all(r["valid"] for r in timings), "tentativa sem frame válido")
selection = read(validation / "selection.json")
scores = read(validation / "scores.json")
extracted = read(cache / "scores-sf2-03.json")
require(scores == extracted, "objetos do extrator 03 e da coleta 04 divergem")
grid = read(validation / "grid.json")
require(len(grid["policies"]) == selection["policy_count"] == PROTOCOL["review_policy"]["joint_policy_count"],
        "grade incompleta")
require(selection["eligible_count"] == sum(item["eligible"] for item in grid["policies"]), "contagem elegível divergente")
for role, path in {
    "capture_policy": cfg["capture_policy"], "scores": validation / "scores.json", "grid": validation / "grid.json",
    "predictions": run / "predictions.jsonl", "timings": run / "timings.jsonl",
}.items():
    require(selection[role + "_sha256"] == sha256(path), f"seleção usa bytes diferentes: {role}")
gates = quality_gates(report["metrics"], "validation")
passes = Counter()
for policy in grid["policies"]:
    passes.update(name for name, passed in policy["gates"].items() if passed)
summary = {
    "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": report["status"], "reason": report["reason"], "narratives": len(predictions), "controls": len(controls),
    "journal_count": len(timings), "package_sha256": pre["package_sha256"], "report_sha256": sha256(validation/"report.json"),
    "original_frames_sha256": sha256(run/"predictions.jsonl"), "run_seal_sha256": sha256(run/"seal.json"),
    "sf2_03_scores_sha256": sha256(cache/"scores-sf2-03.json"), "sf2_04_scores_sha256": sha256(validation/"scores.json"),
    "equal_score_objects": True, "scores_by_target": {field: sum(field in r["heads"] for r in scores["rows"]) for field in FIELDS},
    "errors_by_target": {field: sum(field in r["errors"] for r in scores["rows"]) for field in FIELDS},
    "controls_observed": [{"id": row["id"], "outcome": row["outcome"], "calls": row["calls"],
                           "applied": row["applied"]} for row in controls],
    "observed_latency_ms": report["latency_ms"], "resources": report["resources"],
    "gate_results_reported_policy": gates, "policies_passed_by_gate": {k: passes[k] for k in gates},
    "selection": selection, "selected_policy": grid["selected"],
}
write_json(cache / "validation-audit.json", summary)
print(report["status"])
