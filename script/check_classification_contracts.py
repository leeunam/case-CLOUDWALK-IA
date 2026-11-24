"""Validate CLASS-001 contracts and their static fixtures offline (no evaluator)."""
import argparse
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from math import fsum, isclose, isfinite
from pathlib import Path
import sys
from urllib.parse import urldefrag, urljoin

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from classification_comparison.metrics import apply_final_populations, canonical_summary

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/planejamento/classificacao-comparativa"
CONTRACTS = PLAN / "contratos"
FIXTURES = CONTRACTS / "fixtures"
FIELDS = ("category", "priority")
KINDS = {"inputs": "input", "observations": "observation", "decisions": "decision"}
ABSTENTION = "informacao_insuficiente"
LEGACY = "warm-1.0"
OBSERVED = "observed-total-1.1"
R2 = "observed-total-r2"
LUNA = "observed-total-luna-1.0"
LUNA_R4 = "observed-total-luna-r4"
LUNA_PROFILES = (LUNA, LUNA_R4)
DEDICATED = (R2, *LUNA_PROFILES)
LUNA_FIXTURE_PROVIDER = "simulador-c05-luna"
R2_FIXTURE_PROVIDER = "simulador-c05-r2"
R2_OFFLINE_APPROVAL_DATE = "2026-11-24"
WARM_GATE = "warm_total_latency_p95_ms_max"
OBSERVED_GATE = "observed_total_latency_p95_ms_max"
TIMEOUT_DELIVERY_MS = 250


@dataclass(frozen=True)
class ReportProfile:
    name: str
    quality_version: str
    report_version: str
    ipc_version: str
    latency_gate: str
    protocol_file: str
    protocol_sha256: str
    golden_file: str
    lock_file: str
    lock_sha256: str

    @property
    def is_luna(self):
        return self.name in LUNA_PROFILES

    @property
    def protocol_path(self):
        return PLAN / self.protocol_file

    @property
    def golden_path(self):
        return CONTRACTS / self.golden_file

    def protocol_source(self):
        return dict(version=self.quality_version, path=self.protocol_path.relative_to(ROOT).as_posix(),
                    sha256=self.protocol_sha256)


PROFILES = {
    LEGACY: ReportProfile(LEGACY, "1.0.0", "1.1.0", "1.1.0", WARM_GATE,
                          "protocolo-comparacao.json", "eb9bdbb786037bac864f3155ff6dfbb45feb83dfdb99958f463b6896a614dced",
                          "fixtures/report.json", "script/classification_comparison/sources.lock.json",
                          "b13426334322158f2b94961f47f9eb531a96d7e3a369b68ac9c1f704d28ca3a4"),
    OBSERVED: ReportProfile(OBSERVED, "1.1.0", "1.2.0", "1.1.0", OBSERVED_GATE,
                            "protocolo-comparacao-1.1.json", "061a91a0c9b1b054ca2c9579077453d77ac765f24d725667fb97b5749db1aed7",
                            "relatorio-1.2/report.json", "docs/planejamento/classificacao-comparativa/contratos/relatorio-1.2/sources.lock.json",
                            "8640c343dd182f0e683f82525ed2f48616e4620503c12172e6dc6a70faf0bb22"),
    R2: ReportProfile(R2, "1.2.0", "1.3.0", "1.1.0", OBSERVED_GATE,
                      "r2/protocol.json", "4e89f10dcb15b4a9593532aa52d05917b68df4771972d570dd646a7ce11163d1",
                      "relatorio-1.3/report.json", "docs/planejamento/classificacao-comparativa/contratos/relatorio-1.3/sources.lock.json",
                      "f91f9325870cde169eba795195052908035af2c179de610a0a432f1eaa344df1"),
    LUNA: ReportProfile(LUNA, "1.3.0", "1.4.0", "1.1.0", OBSERVED_GATE,
                        "luna/protocol.json", "a9fe9fc8fd55420986ca9a1e63ed09d9be8b88d55cd3373235f471d5e50b288b",
                        "relatorio-1.4/report.json", "docs/planejamento/classificacao-comparativa/contratos/relatorio-1.4/sources.lock.json",
                        "7a826e8217be8f5a0ca00b3d51d596dd724b620efcf7ac932744fc02bc18ae1b"),
    LUNA_R4: ReportProfile(LUNA_R4, "1.4.0", "1.5.0", "1.1.0", OBSERVED_GATE,
                           "r4/protocol.json", "85590d95926acc76c05e50bae420180f869ff1084856f4c1fcf11542175df8fd",
                           "relatorio-1.5/report.json", "docs/planejamento/classificacao-comparativa/contratos/relatorio-1.5/sources.lock.json",
                           "ea1531d622ea21c0db68f71b576acea59cef829d765ed16a76a36312b25584be"),
}


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


def get_profile(name=LEGACY):
    require(name in PROFILES, "unknown_profile", name)
    return PROFILES[name]


def profile_for_report(report):
    require(isinstance(report, dict) and isinstance(report.get("sources"), dict),
            "profile_protocol", "report.sources")
    for profile in PROFILES.values():
        if report.get("contract_version") == profile.report_version:
            require(report.get("sources", {}).get("protocol") == profile.protocol_source(),
                    "profile_protocol", profile.name)
            return profile
    raise ContractError("unknown_report_version", report.get("contract_version"))


def references(node):
    if isinstance(node, dict):
        if "$ref" in node:
            yield node["$ref"]
        for value in node.values():
            yield from references(value)
    elif isinstance(node, list):
        for value in node:
            yield from references(value)


def validators(profile_name=LEGACY):
    profile = get_profile(profile_name)
    lock = read(source_path({"path": profile.lock_file, "sha256": profile.lock_sha256}))
    schemas = {}
    for path, sha in lock.items():
        pinned = source_path({"path": path, "sha256": sha})
        if path.endswith(".schema.json"):
            schemas[pinned] = read(pinned)
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
    selected = {path.name.split(".")[0]: schema for path, schema in schemas.items()
                if path.parent == CONTRACTS}
    if profile.latency_gate == OBSERVED_GATE:
        selected["report"] = schemas[profile.golden_path.with_name("report.schema.json")]
    return {k: Draft202012Validator(v, registry=registry, format_checker=FormatChecker())
            for k, v in selected.items()}


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
    injected = case_id in report["injected_controls"]["ids"]
    require(obs["origin"] == ("injected_control" if injected else "candidate"), "observation_origin", case_id)
    identity = report["injected_controls"]["identity"] if injected else report["identity"]
    require(obs["identity"] == identity and obs["run_id"] == report["run_id"],
            "observation_identity", case_id)
    choices = obs["choices"]
    require(set(choices) == set(missing), "requested_fields", case_id)
    for field, choice in choices.items():
        verify_choice(choice, catalog[field], case_id)
    if injected:
        # Structure has already ruled out inference, scores, usage and model identity.
        return
    if report.get("contract_version") in {PROFILES[name].report_version for name in DEDICATED}:
        require(obs["requests"] <= 1, "r2_request_limit", case_id)
        require(all(choice.get("score") is None for choice in choices.values()), "r2_score", case_id)
    pins = (("expected_returned_model", "returned_model"), ("expected_weights_revision", "weights_revision"))
    expected = [(identity[pin], obs[actual]) for pin, actual in pins if identity.get(pin) is not None]
    mismatch = any(actual is not None and actual != pin for pin, actual in expected)
    unknown = any(actual is None for _, actual in expected)
    for choice in choices.values():
        require((choice["reason"] == "version_mismatch") == mismatch, "model_version", case_id)
        require(not unknown or choice["status"] == "error", "model_version", case_id)
    if "version_error_raw" in obs:
        require(any(c["reason"] == "version_mismatch" for c in choices.values()), "model_version", case_id)
    has_response = any(choice["status"] != "error" for choice in choices.values())
    require(not has_response or obs["requests"] > 0, "request_count", case_id)
    require(obs["requests"] > 0 or obs["questions"] == 0, "question_count", case_id)
    answered = sum(choice["status"] != "error" for choice in choices.values())
    require(answered <= obs["questions"] <= len(missing), "question_count", case_id)
    require(obs["requests"] == len(obs["request_usage"]), "request_usage_count", case_id)
    for usage in obs["request_usage"]:
        require(usage["estimated_api_usd"] is None or usage["tariff"] is not None, "estimate_tariff", case_id)
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


def verify_usage(report, observations):
    observations = [obs for obs in observations if obs["origin"] == "candidate"]
    requests = [row for obs in observations for row in obs["request_usage"]]
    counts = {"attempts": len(observations), "requests": len(requests),
              "questions": sum(obs["questions"] for obs in observations)}
    for name, total in report["usage"].items():
        state, value, n, expected = (total[k] for k in ("state", "value", "samples", "expected_samples"))
        if name in counts:
            require(n == expected == len(observations), "usage_sample", name)
            require(state == "measured" and value == counts[name], "usage_state", name)
            continue
        known = [row[name] for row in requests if row[name] is not None]
        require(expected == len(requests) and n == len(known), "usage_sample", name)
        if not known:
            require(state in ("unavailable", "unmeasured") and value is None, "usage_state", name)
        else:
            expected_state = "measured" if n == expected else "partial"
            require(state == expected_state and value is not None, "usage_state", name)
            if name.endswith("_tokens"):
                require(isinstance(value, int) and value == sum(known), "usage_total", name)
            else:
                require(isclose(value, fsum(known)), "usage_total", name)


def slice_population(dimension, group, completed, dataset, decisions):
    """Count units at risk; never compute a quality numerator or candidate score."""
    cases = targets = classifiable = applied = 0
    for case_id in completed:
        case = dataset[case_id]
        fields = case["missing"]
        if dimension == "by_field":
            if group not in fields:
                continue
            fields = [group]
        elif dimension == "by_mask" and group != "+".join(fields):
            continue
        elif dimension == "by_stratum" and group != case["stratum"]:
            continue
        cases += 1
        targets += len(fields)
        classifiable += ABSTENTION not in case["expected"].values()
        applied += sum(decisions[case_id]["fields"][f]["applied"] is not None for f in fields)
    return cases, targets, classifiable, applied


def verify_population(metric, population, code, label):
    denominator = metric["denominator"]
    if denominator is None:
        return
    if metric["state"] == "partial":
        require(denominator <= population, code, label)
    else:
        require(denominator == population, code, label)


def verify_metrics(report, protocol, fully_observed, dataset, decisions, latency_gate=WARM_GATE):
    states = []
    passed = []
    counts = protocol["exact_test_denominators"]
    final_test = report.get("split") == "final_test"
    fixed_populations = fully_observed or final_test
    latency_cases = protocol["execution"]["full_test_cases_per_candidate"] if final_test else len(report["completed_ids"])
    urgent_cases = counts["urgent_priority_omitted_cases"]
    gate_populations = {latency_gate: latency_cases,
                        "automatic_coverage_on_fully_classifiable_cases_min": counts["fully_classifiable_cases"],
                        "raw_urgent_recognition_min": urgent_cases,
                        "automatic_completion_on_expected_review_cases": counts["expected_review_cases"],
                        "automatic_non_urgent_applied_when_expected_urgent": urgent_cases}
    for name, metric in report["gates"].items():
        if name.startswith("applied_") and name.endswith("_accuracy"):
            field = name.removeprefix("applied_").removesuffix("_accuracy")
            require(metric == report["by_field"][field]["applied_accuracy"], "applied_accuracy_mismatch", field)
            limit = protocol["gates"]["applied_accuracy_per_field_min"]
        else:
            limit = protocol["gates"][name]
        if name == latency_gate:
            operation = "percentile"
        elif name.endswith(("_min", "_ratio", "_accuracy")):
            operation = "ratio"
        else:
            operation = "count"
        verify_metric(metric, operation, name)
        if fixed_populations and name in gate_populations:
            verify_population(metric, gate_populations[name], "gate_denominator", name)
        states.append(metric["state"])
        if metric["state"] == "measured":
            if operation == "ratio":
                passed.append(metric["value"] >= limit)
            else:
                passed.append(metric["value"] <= limit)
    for dimension in ("by_field", "by_mask", "by_stratum"):
        for group, summary in report[dimension].items():
            cases, targets, classifiable, applied = slice_population(
                dimension, group, report["completed_ids"], dataset, decisions)
            populations = {"applied_accuracy": applied, "review": cases,
                           "automatic_coverage": classifiable, "correct_completion_coverage": classifiable}
            for name, metric in summary.items():
                label = f"{dimension}.{group}.{name}"
                verify_metric(metric, "ratio", label)
                population = populations.get(name, targets)
                denominator = metric["denominator"]
                if fully_observed:
                    verify_population(metric, population, "slice_denominator", label)
                if not (population == 0 and metric["state"] == "unmeasured" and denominator == 0):
                    states.append(metric["state"])
    for name, metric in report["urgent_outcomes"].items():
        verify_metric(metric, "ratio", name)
        if fixed_populations:
            verify_population(metric, urgent_cases, "urgent_denominator", name)
        states.append(metric["state"])
    verify_metric(report["latency_p50_ms"], "percentile", "latency_p50_ms")
    if fixed_populations:
        verify_population(report["latency_p50_ms"], latency_cases, "latency_denominator", "latency_p50_ms")
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
    profile = profile_for_report(report)
    frozen_protocol = read(source_path(profile.protocol_source()))
    require(protocol == frozen_protocol, "profile_protocol", profile.name)
    expected = {
        "dataset": protocol["source_dataset"], "catalog": protocol["source_catalog"], "rubric": protocol["rubric"],
        "protocol": profile.protocol_source(),
        "split": {"version": split["version"], "path": str((PLAN / protocol["data_split_file"]).relative_to(ROOT)),
                  "sha256": protocol["data_split_sha256"]},
    }
    if profile.name in DEDICATED:
        candidate = read(source_path(round_sources(protocol)["candidate"]))
        identity = candidate["identity"]
        if report["identity"]["mode"] == "fixture":
            identity = dict(identity, mode="fixture", provider=LUNA_FIXTURE_PROVIDER if profile.is_luna else R2_FIXTURE_PROVIDER)
        require(report["identity"] == identity, "r2_identity", report["run_id"])
        expected.update(prompt=candidate["prompt"], policy=candidate["policy"])
    for name, entry in report["sources"].items():
        source_path(entry)
        require(all(entry[k] == v for k, v in expected.get(name, {}).items()), "source_version", name)
    require(report["identity"]["policy_version"] == report["sources"]["policy"]["version"],
            "policy_version", report["run_id"])


def verify_injected_controls(report, indexed, protocol):
    inventory = report["injected_controls"]
    approved = protocol["control_policy"]
    policy = read(source_path(approved))
    require(policy["identity"]["policy_version"] == approved["version"], "control_policy_identity", approved["path"])
    ids = [i for i in report["control_ids"] if i in policy["controls"]]
    require(inventory["ids"] == ids and inventory["count"] == len(ids), "injected_inventory", report["run_id"])
    observed_ids = [i for i, obs in indexed["observations"].items() if obs["origin"] == "injected_control"]
    require(observed_ids == ids, "observation_origin", report["run_id"])
    if not ids:
        return
    source = inventory["policy"]
    require(source["path"] == approved["path"], "control_policy_path", source["path"])
    require(source["sha256"] == approved["sha256"], "artifact_hash", source["path"])
    require(inventory["identity"] == policy["identity"] and source["version"] == approved["version"],
            "control_policy_identity", report["run_id"])
    for i in ids:
        spec = policy["controls"][i]
        item = indexed["inputs"][i]
        obs = indexed["observations"][i]
        require(item["text"] == spec["text"] and item["received"] == spec["received"], "control_policy_input", i)
        # A null or absent score both describe absence of a score in the wire format.
        choices = {f: {k: v for k, v in ch.items() if k != "score"} for f, ch in obs["choices"].items()}
        require(choices == spec["choices"], "control_policy_choices", i)


def verify_partial_application(report, observations, decisions):
    # One case per incomplete attempt, including controls of either origin.
    incomplete = [obs for obs in observations.values()
                  if any(choice["status"] != "predicted" for choice in obs["choices"].values())]
    violations = sum(any(decisions[obs["id"]]["fields"][field]["applied"] is not None
                         for field in obs["choices"]) for obs in incomplete)
    if incomplete:
        expected = dict(state="measured", numerator=violations, denominator=len(incomplete), value=violations)
    else:
        expected = dict(state="unmeasured", numerator=None, denominator=0, value=None)
    require(report["gates"]["partial_application_after_abstention_or_error"] == expected,
            "partial_application_gate", report["run_id"])


def has_required_controls(report, decisions):
    reasons = {decisions[i]["reason"] for i in report["control_ids"]}
    mixed = any(decisions[i]["outcome"] == "review" and
                any(f["status"] == "predicted" for f in decisions[i]["fields"].values())
                for i in report["injected_controls"]["ids"])
    return {"channel_complete", "invalid_input"} <= reasons and mixed


def verify_observed_latency(report, observations, population):
    """Reconstruct the two nearest ranks from completed cases, independent of C02."""
    durations = []
    if report["identity"]["mode"] == "real":
        completed = set(report["completed_ids"])
        timeout_ms = report["environment"]["timeout_ms"]
        for case_id, obs in observations.items():
            elapsed = obs["elapsed_ms"]
            if obs["origin"] != "candidate" or elapsed is None:
                continue
            require(isfinite(elapsed) and elapsed >= 0, "observed_duration", case_id)
            if elapsed > timeout_ms:
                has_timeout = any(choice["status"] == "error" and choice.get("reason") == "timeout"
                                  for choice in obs["choices"].values())
                require(has_timeout and elapsed <= timeout_ms + TIMEOUT_DELIVERY_MS, "observed_deadline", case_id)
            if case_id in completed:
                durations.append(elapsed)
    durations.sort()
    count = len(durations)
    for percent, metric in ((50, report["latency_p50_ms"]), (95, report["gates"][OBSERVED_GATE])):
        expected = dict(state="unmeasured", numerator=None, denominator=population, value=None)
        if count:
            rank = (percent * count + 99) // 100
            expected.update(state="measured" if count == population else "partial",
                            denominator=count, value=durations[rank - 1])
        require(metric == expected, "observed_latency", f"{report['run_id']} p{percent}")
    return count


def has_complete_evidence(report, observations, decisions, latency_samples):
    completed = report["completed_ids"]
    return (report["identity"]["mode"] == "real" and report["split"] == "final_test"
            and completed == report["planned_ids"] and has_required_controls(report, decisions)
            and latency_samples == len(completed)
            and any(c["status"] != "error" for i in completed for c in observations[i]["choices"].values()))


def round_sources(protocol):
    return protocol["luna"] if "luna" in protocol else protocol["r2"]


def verify_r2_scope(report, protocol, split, inputs, catalog, dataset):
    stage = report["split"]
    planned, completed, controls = (report[k] for k in ("planned_ids", "completed_ids", "control_ids"))
    r2 = round_sources(protocol)
    final_ids = [case for mask in ("category", "priority", "category+priority") for case in split["final_test"][mask]]
    wanted = {"development": r2["development_ids"], "final_test": final_ids, "control": []}
    require(planned == wanted[stage] and completed == planned[:len(completed)], "r2_stage_order", stage)
    approved_controls = read_records(source_path(r2["control_inputs"]))
    prefix = Path(report["artifacts"]["inputs"]["path"]).name == "verified_inputs.jsonl"
    if stage == "development" or (stage == "final_test" and completed != planned):
        allowed = []
    elif stage == "final_test" and prefix:
        allowed = approved_controls[:len(controls)]
    else:
        allowed = approved_controls
    require(stage != "control" or report["identity"]["mode"] == "fixture", "r2_stage_order", stage)
    require(controls == [item["id"] for item in allowed] and [inputs[i] for i in controls] == allowed,
            "r2_control_inputs", stage)
    for case_id in completed:
        item, case = inputs[case_id], dataset[case_id]
        expected = {**{k: case[k] for k in ("id", "text", "received", "missing")},
                    "brand": "marca-sintetica", "catalog": catalog,
                    "contract_version": protocol["ipc_contract_version"]}
        require(json.dumps(item, sort_keys=True) == json.dumps(expected, sort_keys=True), "dataset_projection", case_id)


def verify_run(bundle, validation, protocol, split, catalog, dataset):
    report = bundle["report"]
    structure(validation, "report", report)
    require(report["contract_version"] == protocol["contract_version"], "protocol_contract_version", report["run_id"])
    verify_sources(report, protocol, split)
    profile = profile_for_report(report)
    inventory = report["artifacts"]
    require(len({a["path"] for a in inventory.values()}) == len(inventory), "duplicate_artifact", report["run_id"])
    indexed = {}
    paths = {kind: source_path(entry) for kind, entry in inventory.items()}
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
    if profile.name in DEDICATED:
        verify_r2_scope(report, protocol, split, indexed["inputs"], catalog, dataset)
    observations = indexed["observations"]
    require(list(observations) == [i for i in order if i in observations], "stream_ids", "observations")
    verify_injected_controls(report, indexed, protocol)
    for i in order:
        item = indexed["inputs"][i]
        if i in completed:
            require(all(item[k] == dataset[i][k] for k in ("received", "missing", "text")) and
                    item["catalog"] == catalog, "dataset_projection", i)
        verify_case(item, observations.get(i), indexed["decisions"][i], report, catalog)
    if profile.latency_gate == OBSERVED_GATE:
        population = protocol["execution"]["full_test_cases_per_candidate"] if split_name == "final_test" else len(completed)
        latency_samples = verify_observed_latency(report, observations, population)
    else:
        latency_samples = sum(observations[i]["temperature_state"] == "warm" and observations[i]["elapsed_ms"] is not None
                              for i in completed)
    if split_name == "final_test":
        urgent_ids = split["summary"]["final_test"]["urgent_priority_omitted_ids"]
        urgent_seen = len(set(completed).intersection(urgent_ids))
        for name, metric in report["urgent_outcomes"].items():
            if metric["state"] in ("measured", "partial"):
                require(metric["denominator"] <= urgent_seen, "urgent_denominator", name)
        latencies = (report["latency_p50_ms"], report["gates"][profile.latency_gate])
        for metric in latencies:
            if metric["state"] in ("measured", "partial"):
                require(metric["denominator"] <= latency_samples, "latency_denominator", report["run_id"])
    full = has_complete_evidence(report, observations, indexed["decisions"], latency_samples)
    if profile.name in DEDICATED and Path(inventory["inputs"]["path"]).name == "verified_inputs.jsonl":
        full = False
    verify_partial_application(report, observations, indexed["decisions"])
    verify_usage(report, list(observations.values()))
    if profile.name in DEDICATED:
        derived = canonical_summary(dataset, bundle["inputs"], bundle["observations"], bundle["decisions"],
                                    catalog, completed, fixture=report["identity"]["mode"] == "fixture",
                                    latency_gate=profile.latency_gate, observed_latency=True,
                                    fields=FIELDS, abstention=ABSTENTION, normalize_input=normalize_input)
        apply_final_populations(derived, report, protocol, profile.latency_gate)
        for name, expected in derived.items():
            require(report[name] == expected, "r2_metrics", name)
    verify_metrics(report, protocol, full, dataset, indexed["decisions"], profile.latency_gate)
    for kind, path in paths.items():
        # Compare JSON types too: Python considers False == 0 and True == 1.
        require(json.dumps(bundle[kind], sort_keys=True) == json.dumps(read_records(path), sort_keys=True),
                "artifact_records", kind)


def read_records(path):
    with path.open(encoding="utf-8", newline="\n") as lines:
        return [json.loads(line, object_pairs_hook=unique_properties, parse_constant=reject_constant,
                           parse_float=finite_float) for line in lines]


def load_bundle(validation, report_path=FIXTURES / "report.json"):
    report = read(report_path)
    structure(validation, "report", report)
    bundle = {"report": report}
    for kind, entry in report["artifacts"].items():
        bundle[kind] = read_records(source_path(entry))
    return bundle


def mutate(bundle, mutation):
    # Paths address JSON properties or row indexes. Extend/replace is sufficient
    # for the counterexamples, whose declared expected rejection is mandatory.
    node = bundle
    for part in mutation["path"][:-1]:
        node = node[part]
    node[mutation["path"][-1]] = mutation["value"]


def verify_r2_package(protocol, split, data):
    r2 = protocol["r2"]
    approval = protocol["approval"]
    require(protocol["created_on"] == split["created_on"] == approval["approved_on"]
            == split["approved_on"] == R2_OFFLINE_APPROVAL_DATE
            and approval["evidence"] == split["approval_evidence"]
            and approval["paid_execution_authorized"] is False
            and protocol["execution"]["paid_execution_authorized"] is False,
            "r2_offline_approval", "aprovação da abordagem offline")
    source = protocol["source_dataset"]
    require(split["source_dataset_version"] == source["version"] == data["version"]
            and split["source_dataset_sha256"] == source["sha256"], "r2_split_source", "dataset composto")
    model_fields = ["text", "brand", "catalog", "missing", "received"]
    require(split["model_visible_fields"] == model_fields
            and split["ipc_projection_fields"] == ["id", *model_fields, "contract_version"]
            and {"id", "contract_version", "expected", "rationale", "stratum"} <= set(split["model_hidden_fields"]),
            "r2_split_projection", "contexto Qwen e projeção IPC")
    historical_split = read(source_path(r2["historical_split"]))
    historical_data = read(source_path(r2["historical_dataset"]))
    final = read(source_path(r2["final_cases"]))["cases"]
    freeze = read(source_path(r2["freeze"]))
    authorship = read(source_path(r2["authorship"]))
    labels = read(source_path(r2["label_review"]))
    similarity = read(source_path(r2["similarity_review"]))
    provenance = protocol["provenance"]["final"]
    summary = split["summary"]["final_test"]
    require(freeze["human_case_approvals"] == provenance["human_direct_cases"] == summary["human_direct_cases"] == 0
            and provenance["agent_delegated_cases"] == summary["agent_delegated_cases"] == len(final)
            and labels["human_approval"] is False, "r2_label_provenance", "referência exploratória final")
    final_sha = r2["final_cases"]["sha256"]
    require(freeze["status"] == "approved_frozen_offline" and freeze["dataset_sha256"] == final_sha
            and freeze["authorship_sha256"] == r2["authorship"]["sha256"]
            and authorship["dataset_sha256"] == labels["dataset_sha256"] == final_sha
            and similarity["sources"]["r2_final"]["file_sha256"] == final_sha
            and freeze["candidate_sha256"] == r2["candidate"]["sha256"], "r2_freeze", "fontes")
    for name, key in (("labels", "label_review"), ("similarity", "similarity_review")):
        require(freeze["reviews"][name] == dict(r2[key], verdict="pass", open_findings=0), "r2_freeze", name)
    require(labels["spec_verdict"] == labels["quality_verdict"] == "pass" and not labels["open_disputes"]
            and labels["authorship_sha256"] == r2["authorship"]["sha256"]
            and similarity["sources"]["historical"]["file_sha256"] == r2["historical_dataset"]["sha256"]
            and similarity["summary"]["verdict_counts"] == {"manter": 36}
            and not similarity["summary"]["replacement_ids"], "r2_freeze", "pareceres")
    dev_ids = {i for ids in historical_split["development"].values() for i in ids}
    development = [case for case in historical_data["cases"] if case["id"] in dev_ids]
    require(split["development"] == historical_split["development"] and len(development) == 24
            and json.dumps(data["cases"], ensure_ascii=False) == json.dumps(development + final, ensure_ascii=False),
            "r2_membership", "pacote composto")
    expected_masks = {"category": (1, 12, 2), "priority": (13, 24, 2), "category+priority": (25, 36, 3)}
    require(len(final) == 36 and [c["id"] for c in final] == [f"r2-{i:03d}" for i in range(1, 37)],
            "r2_membership", "ordem final")
    for mask, (first, last, reviews) in expected_masks.items():
        rows = [case for case in final if "+".join(case["missing"]) == mask]
        ids = [case["id"] for case in rows]
        require(ids == split["final_test"][mask] == [f"r2-{i:03d}" for i in range(first, last + 1)]
                and sum(ABSTENTION in case["expected"].values() for case in rows) == reviews,
                "r2_quota", mask)
    dual = [c["expected"] for c in final[24:] if ABSTENTION in c["expected"].values()]
    dual_priorities = [c["priority"] for c in dual]
    urgent_ids = [c["id"] for c in final if c["expected"].get("priority") == "urgent"]
    require(all(c["category"] == ABSTENTION for c in dual) and dual_priorities.count(ABSTENTION) == 1
            and dual_priorities.count("urgent") == 1 and len(urgent_ids) == 6
            and sum(c["expected"].get("priority") == "urgent" for c in final[12:24]) == 3
            and split["summary"]["final_test"]["urgent_priority_omitted_ids"] == urgent_ids,
            "r2_quota", "insuficientes e urgentes")
    require(len(labels["cases"]) == 36
            and {c["id"]: c["reviewed_expected"] for c in labels["cases"]} == {c["id"]: c["expected"] for c in final},
            "r2_freeze", "alvos revisados")


def verify_luna_package(profile, protocol, split, data):
    sources = protocol["luna"]
    binding = read(source_path(sources["freeze"]))
    historical = read(source_path(binding["historical_protocol"]))
    require(binding["historical_protocol"]["sha256"] == PROFILES[R2].protocol_sha256,
            "luna_origin", "protocolo R2")
    verify_r2_package(historical, split, data)
    shared = set(historical) - {"version", "contract_version", "approval", "task", "r2"}
    require(all(protocol[k] == historical[k] for k in shared)
            and all(sources[k] == historical["r2"][k] for k in
                    ("final_cases", "development_ids", "development_gate", "control_inputs")),
            "luna_criteria", "projeção ou critérios divergentes da R2")
    freeze = read(source_path(binding["candidate_freeze"]))
    candidate = read(source_path(sources["candidate"]))
    if profile.name == LUNA_R4:
        verify_luna_r4_freeze(protocol, binding, historical, freeze, candidate)
        return
    require(binding["candidate"] == sources["candidate"] == freeze["candidate"]
            and binding["operational"] == sources["operational"] == freeze["operational"]
            and binding["historical_data_freeze"] == historical["r2"]["freeze"] == freeze["historical_data_freeze"]
            and binding["final_cases"] == sources["final_cases"]
            and freeze["final_case_sha256"] == binding["final_cases"]["sha256"]
            and candidate["rubric"] == historical["rubric"]
            and protocol["approval"]["decision"] == "D"
            and protocol["approval"]["source"] == binding["offline_approval"]
            and binding["paid_execution_authorized"] is protocol["approval"]["paid_execution_authorized"] is False
            and binding["new_final_human_case_approvals"] == freeze["new_final_human_case_approvals"] == 0,
            "luna_freeze", "aprovação offline e origens")
    for path, pin in freeze["runtime_and_semantic_sources_sha256"].items():
        source_path({"path": path, "sha256": pin})


def verify_luna_r4_freeze(protocol, binding, historical, freeze, candidate):
    sources = protocol["luna"]
    approval = read(source_path(binding["offline_approval"]))
    previous = read(source_path(binding["previous_luna_protocol"]))
    previous_candidate = read(source_path(previous["luna"]["candidate"]))
    require(binding["previous_luna_protocol"]["sha256"] == PROFILES[LUNA].protocol_sha256
            and sources["operational"] == binding["operational"] == previous["luna"]["operational"]
            and binding["historical_data_freeze"] == historical["r2"]["freeze"]
            and binding["final_cases"] == sources["final_cases"]
            and approval["task"] == protocol["task"] == binding["task"] == "C05-R4"
            and protocol["approval"]["source"] == binding["offline_approval"]
            and approval["paid_execution_authorized"] is binding["paid_execution_authorized"]
            is protocol["approval"]["paid_execution_authorized"] is False
            and binding["new_final_human_case_approvals"] == 0,
            "luna_freeze", "aprovação offline e origens R4")
    require(binding["candidate"] == sources["candidate"] == freeze["candidate"]
            and approval["candidate_sha256"] == sources["candidate"]["sha256"]
            and freeze["candidate_commit"] == approval["candidate_commit"]
            and candidate["identity"] == previous_candidate["identity"]
            and candidate["policy"] == previous_candidate["policy"]
            and candidate["rubric"] == previous_candidate["rubric"] == historical["rubric"]
            and candidate["prompt"]["version"] == "1.2.0"
            and candidate["prompt"]["sha256"] != previous_candidate["prompt"]["sha256"],
            "luna_freeze", "instrução R4 congelada e runtime R3")
    for path, pin in freeze["sources_sha256"].items():
        source_path({"path": path, "sha256": pin})


def profile_context(profile_name=LEGACY):
    profile = get_profile(profile_name)
    validation = validators(profile_name)
    protocol = read(source_path(profile.protocol_source()))
    split_path = (PLAN / protocol["data_split_file"]).relative_to(ROOT).as_posix()
    split = read(source_path({"path": split_path, "sha256": protocol["data_split_sha256"]}))
    catalog = read(source_path(protocol["source_catalog"]))
    data = read(source_path(protocol["source_dataset"]))
    if profile_name == R2:
        verify_r2_package(protocol, split, data)
    if profile.is_luna:
        verify_luna_package(profile, protocol, split, data)
    dataset = {row["id"]: row for row in data["cases"]}
    return validation, protocol, split, catalog, dataset


def verify_report(path, profile_name=None):
    profile = profile_for_report(read(path))
    require(profile_name is None or profile_name == profile.name, "profile_mismatch", profile.name)
    args = profile_context(profile.name)
    bundle = load_bundle(args[0], path)
    verify_run(bundle, *args)
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, help="perfil aprovado dos exemplos ou do relatório")
    parser.add_argument("--report", type=Path, help="validar relatório salvo com suas próprias fontes")
    options = parser.parse_args()
    if options.report:
        profile = verify_report(options.report, options.profile)
        print(f"OK: {profile.name} · {options.report}")
        return
    profile = get_profile(options.profile or LEGACY)
    args = profile_context(profile.name)
    validation = args[0]
    bundle = load_bundle(validation, profile.golden_path)
    verify_run(bundle, *args)
    negatives = read(profile.golden_path.with_name("negative.json"))
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
