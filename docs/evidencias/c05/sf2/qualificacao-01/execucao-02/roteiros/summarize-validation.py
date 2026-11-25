from collections import Counter
from pathlib import Path
import sys

from script.classification_comparison.setfit_sf2.contracts.core import PLAN, PROTOCOL, REVIEW, read, read_lines
from script.classification_comparison.setfit_sf2.training.package import write_json

validation = Path(sys.argv[1]) / "evaluation-02/validation"
destination = Path(sys.argv[2])
grid = read(validation / "grid.json")
policies = grid["policies"]
others = [policy for policy in policies if all(value for name, value in policy["gates"].items()
                                                if name != "wrong_expected_review")]
failure_counts = Counter(policy["metrics"]["wrong_expected_review"]["numerator"] for policy in policies)
other_gate_failure_counts = Counter(policy["metrics"]["wrong_expected_review"]["numerator"] for policy in others)
minimum = min(failure_counts)
min_wrong = [policy["metrics"] for policy in policies if policy["metrics"]["wrong_expected_review"]["numerator"] == minimum]
maxima = {word: max(PROTOCOL["review_policy"][word + "_grid"]) for word in ("tau", "delta")}
strict = next(policy for policy in policies if all(policy["policy"][field] == maxima for field in ("category", "priority")))
keys = ("wrong_expected_review", "nonurgent_on_urgent", "automatic_coverage", "correct_coverage",
        "applied_accuracy", "raw_urgent", "applied_urgent", "review_by_case")
public = {row["id"]: row for row in read_lines(PLAN / "dados/validation.jsonl")}
frames = read_lines(validation / "run/predictions.jsonl")
anomalies = []
for original in frames:
    row = public[original["id"]]
    for field in row["missing_fields"]:
        applied = original["applied"].get(field)
        if not applied:
            continue
        gold = row["gold"][field]
        review_miss = gold == REVIEW
        demotion = field == "priority" and gold == "urgent" and applied != "urgent"
        if review_miss or demotion:
            observed = original["fields"][field]
            vector = observed["vector"]
            scores = dict(zip(vector["classes"], vector["scores"], strict=True))
            anomalies.append({
                "id": original["id"], "missing_fields": row["missing_fields"], "field": field,
                "reason": "expected_review_completed" if review_miss else "urgent_demotion", "gold": gold,
                "received": original["received"], "raw": observed["raw"], "applied": applied, "scores": scores,
                "top_score": scores[observed["raw"]], "margin": observed["margin"], "capture_cut": observed["cut"],
            })
write_json(destination, {
    "capture_errors": anomalies, "policies": len(policies), "eligible": sum(p["eligible"] for p in policies),
    "wrong_review_completion_distribution": failure_counts,
    "wrong_review_completion_distribution_other_gates": other_gate_failure_counts,
    "passing_all_other_gates": len(others),
    "minimum_wrong_review": minimum,
    "min_auto_coverage_given_minimum_wrong_review": min(m["automatic_coverage"]["numerator"] for m in min_wrong),
    "max_auto_coverage_given_minimum_wrong_review": max(m["automatic_coverage"]["numerator"] for m in min_wrong),
    "max_correct_coverage_given_all_other_gates": max(p["metrics"]["correct_coverage"]["numerator"] for p in others),
    "highest_cuts": {"policy": strict["policy"], "metrics": {key: strict["metrics"][key] for key in keys},
                     "gates": strict["gates"]},
    "argmax_baseline": {key: grid["baseline_argmax"][key] for key in keys},
})
