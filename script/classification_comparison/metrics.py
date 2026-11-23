"""Unidades do protocolo C01. Controles entram em integridade e usage apenas."""
from collections import Counter
from math import ceil, fsum

from common import c01


def metric(num, den, count=False):
    if not den:
        return dict(state="unmeasured", numerator=None, denominator=0, value=None)
    return dict(state="measured", numerator=num, denominator=den, value=num if count else num / den)


def slice_metrics(rows, field=None):
    n = Counter()
    for case, obs, decision in rows:
        expected = case["expected"]
        complete = decision["outcome"] == "complete"
        classifiable = c01.ABSTENTION not in expected.values()
        n["cases"] += 1
        n["review"] += not complete
        n["classifiable"] += classifiable
        n["automatic_coverage"] += classifiable and complete
        n["correct_completion_coverage"] += classifiable and complete and all(
            decision["fields"][f]["applied"] == code for f, code in expected.items())
        for f in ([field] if field else case["missing"]):
            code = expected[f]
            choice = obs["choices"][f]
            status = choice["status"]
            applied = decision["fields"][f]["applied"]
            abstain = code == c01.ABSTENTION
            n["targets"] += 1
            n["applied"] += applied is not None
            n["applied_accuracy"] += applied == code
            n["raw_accuracy"] += ((status == "predicted" and choice["raw"] == code) or
                                  (status == "abstained" and abstain))
            n["correct_abstention"] += status == "abstained" and abstain
            n["undue_abstention"] += status == "abstained" and not abstain
            n["invalid_output"] += status == "invalid"
            n["operational_error"] += status == "error"
            n["unapplied_choices"] += status == "predicted" and applied is None
    populations = dict(raw_accuracy="targets", applied_accuracy="applied", correct_abstention="targets",
                       undue_abstention="targets", invalid_output="targets", operational_error="targets",
                       unapplied_choices="targets", review="cases", automatic_coverage="classifiable",
                       correct_completion_coverage="classifiable")
    return {key: metric(n[key], n[pop]) for key, pop in populations.items()}


def usage(observations):
    observations = [o for o in observations if o["origin"] == "candidate"]
    n = len(observations)
    requests = [u for o in observations for u in o["request_usage"]]
    totals = dict(attempts=n, requests=len(requests), questions=sum(o["questions"] for o in observations))
    result = {k: dict(state="measured", value=v, samples=n, expected_samples=n) for k, v in totals.items()}
    for key in ("input_tokens", "output_tokens", "observed_api_usd", "estimated_api_usd"):
        values = [u[key] for u in requests if u[key] is not None]
        state = "unmeasured" if not values else "measured" if len(values) == len(requests) else "partial"
        total = sum(values) if key.endswith("tokens") else fsum(values)
        result[key] = dict(state=state, value=total if values else None, samples=len(values),
                           expected_samples=len(requests))
    return result


def percentile(values, population, p):
    if not values:
        return dict(state="unmeasured", value=None, numerator=None, denominator=population)
    return dict(state="measured" if len(values) == population else "partial",
                value=sorted(values)[ceil(p * len(values)) - 1], numerator=None, denominator=len(values))


def summarize(cases, inputs, observations, decisions, catalog, completed, fixture=True):
    by_id = {o["id"]: o for o in observations}
    verdicts = {d["id"]: d for d in decisions}
    rows = [(cases[i], by_id[i], verdicts[i]) for i in completed]
    by_field = {f: slice_metrics([r for r in rows if f in r[0]["missing"]], f) for f in c01.FIELDS}
    by_mask = {m: slice_metrics([r for r in rows if "+".join(r[0]["missing"]) == m])
               for m in ("category", "priority", "category+priority")}
    by_stratum = {s: slice_metrics([r for r in rows if r[0]["stratum"] == s])
                  for s in ("rotina", "urgente", "ambiguo")}
    urgent = [r for r in rows if r[0]["expected"].get("priority") == "urgent"]
    counters = Counter()
    for _, obs, decision in urgent:
        choice = obs["choices"]["priority"]
        applied = decision["fields"]["priority"]["applied"]
        counters["raw"] += choice["status"] == "predicted" and choice["raw"] == "urgent"
        counters["applied_urgent"] += applied == "urgent"
        counters["applied_lower"] += applied is not None and applied != "urgent"
        counters["review"] += decision["outcome"] == "review"
        for key, status in (("abstained", "abstained"), ("invalid", "invalid"), ("operational_error", "error")):
            counters[key] += choice["status"] == status
    outcomes = {k: metric(counters[k], len(urgent)) for k in
                ("applied_urgent", "applied_lower", "review", "abstained", "invalid", "operational_error")}
    integrity = Counter()
    for item in inputs:
        i = item["id"]
        _, invalid, valid = c01.normalize_input(item, catalog)
        d = verdicts[i]
        integrity["provided"] += len(valid)
        integrity["preserved"] += sum(d["fields"][f]["applied"] == v for f, v in valid.items())
        if i not in cases and (invalid or not item["missing"] or item["catalog"] != catalog):
            integrity["blocked"] += 1
            integrity["calls"] += by_id.get(i, {}).get("requests", 0)
        if i in by_id and any(c["status"] != "predicted" for c in by_id[i]["choices"].values()):
            integrity["incomplete"] += 1
            integrity["partial"] += any(d["fields"][f]["applied"] is not None for f in item["missing"])

    expected_review = [r for r in rows if c01.ABSTENTION in r[0]["expected"].values()]
    durations = [o["elapsed_ms"] for _, o, _ in rows if not fixture and
                 o["temperature_state"] == "warm" and o["elapsed_ms"] is not None]
    gates = dict(channel_field_preservation_ratio=metric(integrity["preserved"], integrity["provided"]),
                 complete_or_invalid_controls_model_calls=metric(integrity["calls"], integrity["blocked"], count=True),
                 partial_application_after_abstention_or_error=metric(integrity["partial"], integrity["incomplete"], count=True),
                 automatic_completion_on_expected_review_cases=metric(sum(d["outcome"] == "complete" for _, _, d in expected_review),
                                                                     len(expected_review), count=True),
                 automatic_non_urgent_applied_when_expected_urgent=metric(counters["applied_lower"], len(urgent), count=True),
                 automatic_coverage_on_fully_classifiable_cases_min=slice_metrics(rows)["automatic_coverage"],
                 raw_urgent_recognition_min=metric(counters["raw"], len(urgent)),
                 warm_total_latency_p95_ms_max=percentile(durations, len(rows), .95))
    for f in c01.FIELDS:
        gates[f"applied_{f}_accuracy"] = by_field[f]["applied_accuracy"]
    return dict(by_field=by_field, by_mask=by_mask, by_stratum=by_stratum, urgent_outcomes=outcomes,
                latency_p50_ms=percentile(durations, len(rows), .5), usage=usage(observations), gates=gates)


def eligibility(report, protocol, observations, decisions):
    """Conclusão exclusiva do teste real com evidência completa e controles."""
    if (report["identity"]["mode"] != "real" or report["split"] != "final_test" or
            report["completed_ids"] != report["planned_ids"] or
            len(report["completed_ids"]) != protocol["execution"]["full_test_cases_per_candidate"]):
        return "inconclusive"
    if not c01.has_required_controls(report, {d["id"]: d for d in decisions}):
        return "inconclusive"
    if not any(c["status"] != "error" for o in observations if o["id"] in report["completed_ids"]
               for c in o["choices"].values()):
        return "inconclusive"
    required = [*report["gates"].values(), *report["urgent_outcomes"].values(), report["latency_p50_ms"]]
    if any(m["state"] != "measured" for m in required):
        return "inconclusive"
    for name, m in report["gates"].items():
        if name.endswith("_accuracy"):
            threshold = protocol["gates"]["applied_accuracy_per_field_min"]
        else:
            threshold = protocol["gates"][name]
        minimum = name.endswith(("_accuracy", "_ratio", "_min"))
        if (minimum and m["value"] < threshold) or (not minimum and m["value"] > threshold):
            return "fail"
    return "pass"
