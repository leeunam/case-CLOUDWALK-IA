"""Validate CLASS-001 contracts and their static fixtures offline (no evaluator)."""
from copy import deepcopy
from hashlib import sha256
import json
from math import isclose, isfinite
from pathlib import Path
import sys
from urllib.parse import urldefrag, urljoin

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/planejamento/classificacao-comparativa"
CONTRACTS = PLAN / "contratos"
FIXTURES = CONTRACTS / "fixtures"
FIELDS = ("category", "priority")
KINDS = {"inputs": "input", "observations": "observation", "decisions": "decision"}
ABSTENTION = "informacao_insuficiente"


class ContractError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(f"{code}: {detail}")


def require(condition, code, detail):
    if not condition:
        raise ContractError(code, detail)


def finite_float(value):
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"non-finite number: {value}")
    return number


def read(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_properties,
                      parse_constant=reject_constant, parse_float=finite_float)


def reject_constant(value):
    raise ValueError(f"non-JSON number: {value}")


def unique_properties(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_property", key)
        result[key] = value
    return result


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def references(node):
    if isinstance(node, dict):
        if "$ref" in node:
            yield node["$ref"]
        for value in node.values():
            yield from references(value)
    elif isinstance(node, list):
        for value in node:
            yield from references(value)


def validators():
    schemas = {p.name.split(".")[0]: read(p) for p in CONTRACTS.glob("*.schema.json")}
    registry = Registry()  # No resource retriever; all URIs are local identifiers.
    ids = set()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        uri = schema["$id"]
        require(uri not in ids, "duplicate_schema_id", uri)
        ids.add(uri)
        registry = registry.with_resource(uri, Resource.from_contents(schema))
    for schema in schemas.values():
        resolver = registry.resolver(schema["$id"])
        for reference in references(schema):
            uri, _ = urldefrag(urljoin(schema["$id"], reference))
            require(uri in ids, "unknown_schema", reference)
            resolver.lookup(reference)
    return {k: Draft202012Validator(v, registry=registry, format_checker=FormatChecker())
            for k, v in schemas.items()}


def structure(validation, kind, document):
    error = next(validation[kind].iter_errors(document), None)
    if error:
        path = "/".join(map(str, error.absolute_path))
        raise ContractError(f"schema/{kind}/{path}/{error.validator}", error.message)


def normalize_input(item, catalog):
    received = item["received"]
    missing = []
    invalid = []
    valid = {}
    for field in FIELDS:
        value = received.get(field)
        if value is None or isinstance(value, str) and not value.strip():
            missing.append(field)
        elif isinstance(value, str) and value in catalog[field]:
            valid[field] = value
        else:
            invalid.append(field)
    require(item["missing"] == missing, "missing_mask", item["id"])
    return missing, invalid, valid


def verify_choice(choice, codes, case_id):
    raw, status, reason = (choice[k] for k in ("raw", "status", "reason"))
    in_catalog = isinstance(raw, str) and raw in codes
    if status == "predicted":
        require(in_catalog, "predicted_code", case_id)
    elif status == "abstained" and reason == "explicit":
        require(raw == ABSTENTION, "abstention_code", case_id)
    elif status == "invalid":
        require(not in_catalog and raw != ABSTENTION, "invalid_code", case_id)
        require(reason != "missing_output" or raw is None, "missing_output", case_id)


def verify_observation(obs, missing, report, catalog):
    case_id = obs["id"]
    require(obs["identity"] == report["identity"] and obs["run_id"] == report["run_id"],
            "observation_identity", case_id)
    choices = obs["choices"]
    require(set(choices) == set(missing), "requested_fields", case_id)
    for field, choice in choices.items():
        verify_choice(choice, catalog[field], case_id)
    identity = obs["identity"]
    pins = (("expected_returned_model", "returned_model"), ("expected_weights_revision", "weights_revision"))
    mismatch = any(identity.get(pin) is not None and obs[actual] != identity[pin] for pin, actual in pins)
    if mismatch:
        require(all(c["status"] == "error" for c in choices.values()), "model_version", case_id)
    if "version_error_raw" in obs:
        require(any(c["reason"] == "version_mismatch" for c in choices.values()), "model_version", case_id)
    has_response = any(choice["status"] != "error" for choice in choices.values())
    require(not has_response or obs["requests"] > 0, "request_count", case_id)
    require(obs["requests"] > 0 or obs["questions"] == 0, "question_count", case_id)
    answered = sum(choice["status"] != "error" for choice in choices.values())
    require(answered <= obs["questions"] <= len(missing), "question_count", case_id)
    require(obs["estimated_api_usd"] is None or obs["tariff"] is not None, "estimate_tariff", case_id)
    if obs["inference_ms"] is not None and obs["elapsed_ms"] is not None:
        require(obs["inference_ms"] <= obs["elapsed_ms"], "inference_duration", case_id)


def verify_case(item, obs, decision, report, catalog):
    case_id = item["id"]
    missing, invalid, valid = normalize_input(item, catalog)
    compatible = item["catalog"] == catalog
    needs_attempt = compatible and not invalid and bool(missing)
    require(bool(obs) == needs_attempt and decision["attempts"] == int(needs_attempt), "attempt_count", case_id)
    require(decision["run_id"] == report["run_id"], "decision_identity", case_id)
    choices = {}
    if obs:
        verify_observation(obs, missing, report, catalog)
        choices = obs["choices"]
    if not compatible:
        reason = "incompatible_catalog"
    elif invalid:
        reason = "invalid_input"
    elif not missing:
        reason = "channel_complete"
    elif all(c["status"] == "predicted" for c in choices.values()):
        reason = "all_predicted"
    else:
        reason = "incomplete_prediction"
    complete = reason in ("all_predicted", "channel_complete")
    require(decision["reason"] == reason and (decision["outcome"] == "complete") == complete,
            "case_outcome", case_id)
    for field in FIELDS:
        applied = valid.get(field)
        if field in valid:
            status = "provided"
        elif field in invalid:
            status = "invalid"
        elif field in choices:
            status = choices[field]["status"]
            if complete:
                applied = choices[field]["raw"]
        else:
            status = "not_requested"
        result = decision["fields"][field]
        require(result["status"] == status, "field_status", f"{case_id}.{field}")
        require(result["applied"] == applied, "applied_value", f"{case_id}.{field}")


def verify_metric(metric, operation, name):
    value, num, den = (metric[k] for k in ("value", "numerator", "denominator"))
    if metric["state"] in ("unavailable", "unmeasured"):
        return
    require(den > 0 and isfinite(value), "metric_sample", name)
    if operation == "percentile":
        require(num is None, "percentile_numerator", name)
    elif operation == "count":
        require(num is not None and value == num, "metric_count", name)
    else:
        require(num is not None and num <= den and isclose(value, num / den), "metric_ratio", name)


def verify_usage(report, attempts):
    for name, total in report["usage"].items():
        state, value, n, expected = (total[k] for k in ("state", "value", "samples", "expected_samples"))
        require(expected == attempts and n <= expected, "usage_sample", name)
        if state in ("unmeasured", "unavailable"):
            consistent = n == 0 and value is None
        else:
            consistent = value is not None and n > 0 and (n == expected) == (state == "measured")
            if name not in ("observed_api_usd", "estimated_api_usd"):
                consistent = consistent and isinstance(value, int)
        require(consistent, "usage_state", name)


def verify_metrics(report, protocol, fully_observed):
    states = []
    passed = []
    for name, metric in report["gates"].items():
        if name.startswith("applied_") and name.endswith("_accuracy"):
            limit = protocol["gates"]["applied_accuracy_per_field_min"]
        else:
            limit = protocol["gates"][name]
        if name == "warm_total_latency_p95_ms_max":
            operation = "percentile"
        elif name.endswith(("_min", "_ratio", "_accuracy")):
            operation = "ratio"
        else:
            operation = "count"
        verify_metric(metric, operation, name)
        states.append(metric["state"])
        if metric["state"] == "measured":
            if operation == "ratio":
                passed.append(metric["value"] >= limit)
            else:
                passed.append(metric["value"] <= limit)
    for dimension in ("by_field", "by_mask", "by_stratum"):
        for group, summary in report[dimension].items():
            for name, metric in summary.items():
                verify_metric(metric, "ratio", f"{dimension}.{group}.{name}")
                if metric["state"] != "unmeasured" or metric["denominator"] != 0:
                    states.append(metric["state"])
    for name, metric in report["urgent_outcomes"].items():
        verify_metric(metric, "ratio", name)
        states.append(metric["state"])
    verify_metric(report["latency_p50_ms"], "percentile", "latency_p50_ms")
    states.append(report["latency_p50_ms"]["state"])
    # Gates require denominators. Descriptive slices can legitimately be empty
    # (e.g. applied accuracy in a stratum with no accepted predictions).
    measured_gates = all(m["state"] == "measured" for m in report["gates"].values())
    missing_evidence = any(s != "measured" for s in states)
    eligible_to_decide = fully_observed and measured_gates and not missing_evidence
    expected = "inconclusive"
    if eligible_to_decide:
        expected = "pass" if all(passed) else "fail"
    require(report["eligibility"] == expected, "eligibility", report["run_id"])


def source_path(entry):
    path = (ROOT / entry["path"]).resolve()
    require(not Path(entry["path"]).is_absolute() and path.is_relative_to(ROOT), "artifact_path", entry["path"])
    require(path.is_file() and digest(path) == entry["sha256"], "artifact_hash", entry["path"])
    return path


def verify_sources(report, protocol, split):
    expected = {
        "dataset": protocol["source_dataset"], "catalog": protocol["source_catalog"], "rubric": protocol["rubric"],
        "protocol": {"version": protocol["version"], "path": str((PLAN / "protocolo-comparacao.json").relative_to(ROOT))},
        "split": {"version": split["version"], "path": str((PLAN / protocol["data_split_file"]).relative_to(ROOT)),
                  "sha256": protocol["data_split_sha256"]},
    }
    for name, entry in report["sources"].items():
        source_path(entry)
        require(all(entry[k] == v for k, v in expected.get(name, {}).items()), "source_version", name)
    require(report["identity"]["policy_version"] == report["sources"]["policy"]["version"],
            "policy_version", report["run_id"])


def verify_run(bundle, validation, protocol, split, catalog, dataset):
    report = bundle["report"]
    structure(validation, "report", report)
    verify_sources(report, protocol, split)
    inventory = report["artifacts"]
    require(len({a["path"] for a in inventory.values()}) == len(inventory), "duplicate_artifact", report["run_id"])
    indexed = {}
    for entry in inventory.values():
        source_path(entry)
    for kind, schema_name in KINDS.items():
        records = bundle[kind]
        for row in records:
            structure(validation, schema_name, row)
        indexed[kind] = {row["id"]: row for row in records}
        require(len(indexed[kind]) == len(records), "duplicate_id", kind)
    completed, planned, controls = (report[k] for k in ("completed_ids", "planned_ids", "control_ids"))
    require(not set(controls).intersection(planned), "overlapping_controls", report["run_id"])
    require([i for i in planned if i in completed] == completed, "completed_order", report["run_id"])
    split_name = report["split"]
    if split_name == "control":
        require(planned == [], "split_ids", split_name)
    else:
        split_ids = {i for group in split[split_name].values() for i in group}
        require(set(planned) <= split_ids, "split_ids", split_name)
        if split_name == "final_test":
            require(set(planned) == split_ids, "split_ids", split_name)
    require(not set(controls).intersection(dataset), "dataset_as_control", report["run_id"])
    order = completed + controls
    for kind in ("inputs", "decisions"):
        require(list(indexed[kind]) == order, "stream_ids", kind)
    observations = indexed["observations"]
    require(list(observations) == [i for i in order if i in observations], "stream_ids", "observations")
    for i in order:
        item = indexed["inputs"][i]
        if i in completed:
            require(all(item[k] == dataset[i][k] for k in ("received", "missing", "text")) and
                    item["catalog"] == catalog, "dataset_projection", i)
        verify_case(item, observations.get(i), indexed["decisions"][i], report, catalog)
    reasons = {indexed["decisions"][i]["reason"] for i in controls}
    partial_control = any(indexed["decisions"][i]["outcome"] == "review" and
                          any(f["status"] == "predicted" for f in indexed["decisions"][i]["fields"].values())
                          for i in controls)
    full = (report["identity"]["mode"] == "real" and split_name == "final_test" and completed == planned
            and {"channel_complete", "invalid_input"} <= reasons and partial_control
            and all(observations[i]["temperature_state"] == "warm" and observations[i]["elapsed_ms"] is not None
                    for i in completed)
            and any(c["status"] != "error" for i in completed for c in observations[i]["choices"].values()))
    if full:
        den = protocol["exact_test_denominators"]
        denominators = {"warm_total_latency_p95_ms_max": len(completed),
                        "automatic_coverage_on_fully_classifiable_cases_min": den["fully_classifiable_cases"],
                        "raw_urgent_recognition_min": den["urgent_priority_omitted_cases"],
                        "automatic_completion_on_expected_review_cases": den["expected_review_cases"],
                        "automatic_non_urgent_applied_when_expected_urgent": den["urgent_priority_omitted_cases"]}
        for name, expected in denominators.items():
            metric = report["gates"][name]
            require(metric["state"] != "measured" or metric["denominator"] == expected, "gate_denominator", name)
    verify_usage(report, len(observations))
    verify_metrics(report, protocol, full)


def load_bundle(validation):
    report = read(FIXTURES / "report.json")
    structure(validation, "report", report)
    bundle = {"report": report}
    for kind, entry in report["artifacts"].items():
        path = source_path(entry)
        bundle[kind] = [json.loads(line, object_pairs_hook=unique_properties, parse_constant=reject_constant, parse_float=finite_float)
                        for line in path.read_text(encoding="utf-8").splitlines()]
    return bundle


def mutate(bundle, mutation):
    # Paths address JSON properties or row indexes. Extend/replace is sufficient
    # for the counterexamples, whose declared expected rejection is mandatory.
    node = bundle
    for part in mutation["path"][:-1]:
        node = node[part]
    node[mutation["path"][-1]] = mutation["value"]


def main():
    validation = validators()
    protocol = read(PLAN / "protocolo-comparacao.json")
    split = read(PLAN / protocol["data_split_file"])
    catalog = read(ROOT / protocol["source_catalog"]["path"])
    dataset = {r["id"]: r for r in read(ROOT / protocol["source_dataset"]["path"])["cases"]}
    args = validation, protocol, split, catalog, dataset
    bundle = load_bundle(validation)
    verify_run(bundle, *args)
    negatives = read(FIXTURES / "negative.json")
    require(len({c["id"] for c in negatives}) == len(negatives), "duplicate_negative_id", "negative.json")
    for case in negatives:
        candidate = deepcopy(bundle)
        for mutation in case["changes"]:
            mutate(candidate, mutation)
        try:
            verify_run(candidate, *args)
        except ContractError as error:
            require(error.code == case["expected_error"], "unexpected_rejection", f"{case['id']}: {error}")
        else:
            raise ContractError("negative_accepted", case["id"])
    print(f"OK: {len(validation)} schemas; {len(bundle['inputs'])} inputs, "
          f"{len(bundle['observations'])} observations, {len(bundle['decisions'])} decisions; "
          f"1 fixture report; {len(negatives)} expected rejections. No model calls.")


if __name__ == "__main__":
    try:
        main()
    except (ContractError, ValueError, OSError) as exc:
        sys.exit(str(exc))
