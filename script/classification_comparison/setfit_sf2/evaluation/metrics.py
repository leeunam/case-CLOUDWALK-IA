"""Contagens por caso e alvo omitido. Os controles são auditados separadamente."""
from collections import Counter
from math import ceil, sqrt
from statistics import NormalDist

from ..contracts.core import FIELDS, LABELS, PROTOCOL, REVIEW, require

Z95 = NormalDist().inv_cdf(0.975)


def ratio(n, d):
    bounds = None
    if d:
        p = n / d
        scale = 1 + Z95**2 / d
        center = (p + Z95**2 / (2*d)) / scale
        radius = Z95 * sqrt(p*(1-p)/d + Z95**2/(4*d*d)) / scale
        bounds = [max(0, center-radius), min(1, center+radius)]
    return {"numerator": n, "denominator": d, "wilson95": bounds}


def percentiles(durations):
    if not durations:
        return None
    ordered = sorted(durations)
    n = len(ordered)
    return {"n": n, "p50": ordered[ceil(.50*n)-1], "p95": ordered[ceil(.95*n)-1],
            "maximum": ordered[-1]}


def metrics(records, decisions, control_calls):
    require(len(records) == len(decisions), "quantidade de decisões divergente")
    totals = Counter()
    accurate, applied, abstain = Counter(), Counter(), Counter()
    matrix = {f: {g: dict.fromkeys([*LABELS[f], "error"], 0) for g in LABELS[f]} for f in FIELDS}
    for row, result in zip(records, decisions, strict=True):
        require(result["id"] == row["id"], "ordem/ID das decisões divergente")
        targets, gold = row["missing_fields"], row["gold"]
        completed = result["outcome"] == "complete"
        clear = all(gold[f] != REVIEW for f in targets)
        totals["clear"] += clear
        totals["auto"] += completed and clear
        totals["correct"] += completed and clear and all(result["applied"].get(f) == gold[f] for f in targets)
        totals["wrong_review"] += completed and not clear
        totals["reviewed"] += not completed
        totals["partial"] += bool(result["applied"]) and not completed
        for f in FIELDS:
            if f not in targets:
                totals["provided"] += 1
                totals["preserved"] += row["received"][f] == result["received"].get(f)
                continue
            field = result["fields"][f]
            raw = field["raw"] or "error"
            matrix[f][gold[f]][raw] += 1
            abstain[f] += field["decision"] != "accept"
            if f in result["applied"]:
                applied[f] += 1
                accurate[f] += result["applied"][f] == gold[f]
            if f == "priority" and gold[f] == "urgent":
                totals["urgent"] += 1
                totals["raw_urgent"] += raw == "urgent"
                totals["applied_urgent"] += result["applied"].get(f) == "urgent"
                totals["nonurgent"] += f in result["applied"] and result["applied"][f] != "urgent"

    by_class, review_by_field = {}, {}
    for f in FIELDS:
        by_class[f] = {}
        for label, counts in matrix[f].items():
            tp, support = counts[label], sum(counts.values())
            predicted = sum(r[label] for r in matrix[f].values())
            by_class[f][label] = dict(precision=ratio(tp, predicted), recall=ratio(tp, support),
                                      f1=2*tp/(support+predicted) if support+predicted else None, support=support)
        review_by_field[f] = ratio(abstain[f], sum(s["support"] for s in by_class[f].values()))
    return dict(preservation=ratio(totals["preserved"], totals["provided"]), control_calls=control_calls,
                partial_applications=totals["partial"], wrong_expected_review=ratio(totals["wrong_review"], len(records)-totals["clear"]),
                nonurgent_on_urgent=totals["nonurgent"], applied_accuracy={f: ratio(accurate[f], applied[f]) for f in FIELDS},
                automatic_coverage=ratio(totals["auto"], totals["clear"]), correct_coverage=ratio(totals["correct"], totals["clear"]),
                raw_urgent=ratio(totals["raw_urgent"], totals["urgent"]),
                applied_urgent=ratio(totals["applied_urgent"], totals["urgent"]),
                review_by_case=ratio(totals["reviewed"], len(records)), review_by_field=review_by_field,
                confusion=matrix, by_class=by_class)


def quality_gates(m, partition):
    q, limits = PROTOCOL["data"][partition], PROTOCOL["gates"]
    def meets(r, limit):
        return r["denominator"] > 0 and r["numerator"] / r["denominator"] >= limit

    return {
        "preservation": meets(m["preservation"], limits["channel_field_preservation_ratio"]),
        "control_calls": m["control_calls"] == 0,
        "partial_applications": m["partial_applications"] == 0,
        "wrong_expected_review": m["wrong_expected_review"]["denominator"] == q["expected_review_cases"]
                                 and m["wrong_expected_review"]["numerator"] == 0,
        "nonurgent_on_urgent": m["nonurgent_on_urgent"] == 0,
        **{f + "_accuracy": meets(m["applied_accuracy"][f], limits["applied_accuracy_per_field_min"]) for f in FIELDS},
        "automatic_coverage": m["automatic_coverage"]["denominator"] == q["classifiable_cases"]
                              and m["automatic_coverage"]["numerator"] >= q["min_auto_completions"],
        "raw_urgent": m["raw_urgent"]["denominator"] == q["urgent_target_cases"]
                      and m["raw_urgent"]["numerator"] >= q["min_raw_urgent_choices"],
    }
