"""Boundary shared by the evaluator and fixture process."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import check_classification_contracts as c01


def decode(line):
    return json.loads(line, object_pairs_hook=c01.unique_properties,
                      parse_constant=c01.reject_constant, parse_float=c01.finite_float)


def encode(obj):
    return json.dumps(obj, ensure_ascii=False, allow_nan=False)


def project(case, catalog):
    return {**{key: case[key] for key in ("id", "text", "received", "missing")},
            "brand": "marca-sintetica", "catalog": catalog, "contract_version": "1.0.0"}


def preflight():
    # The protocol is the trust root. It pins the catalog, data, split and rubric.
    lock = c01.read(HERE / "sources.lock.json")
    for path, sha in lock.items():
        c01.source_path({"path": path, "sha256": sha})
    validators = c01.validators()
    example = c01.load_bundle(validators)
    sources = example["report"]["sources"]
    protocol, split, catalog, dataset = [c01.read(c01.source_path(sources[key]))
                                         for key in ("protocol", "split", "catalog", "dataset")]
    cases = dataset["cases"]
    indexed = {case["id"]: case for case in cases}
    if len(indexed) != len(cases) or dataset["version"] != sources["dataset"]["version"]:
        raise ValueError("dataset incompatível")
    membership = []
    for partition in ("development", "final_test"):
        for mask, ids in split[partition].items():
            for case_id in ids:
                case = indexed[case_id]
                envelope = project(case, catalog)
                c01.structure(validators, "input", envelope)
                missing, invalid, _ = c01.normalize_input(envelope, catalog)
                expected = case["expected"]
                if (invalid or "+".join(missing) != mask or set(expected) != set(missing) or
                        any(v != c01.ABSTENTION and v not in catalog[f] for f, v in expected.items())):
                    raise ValueError(f"máscara ou rótulo inválido em {case_id}")
                membership.append(case_id)
    if sorted(membership) != sorted(indexed):
        raise ValueError("partição inconsistente")
    c01.verify_run(example, validators, protocol, split, catalog, indexed)
    return validators, protocol, split, catalog, indexed, example


def decide(item, observation, catalog, run_id):
    missing, invalid, provided = c01.normalize_input(item, catalog)
    choices = observation["choices"] if observation else {}
    if item["catalog"] != catalog:
        reason = "incompatible_catalog"
    elif invalid:
        reason = "invalid_input"
    elif not missing:
        reason = "channel_complete"
    elif all(choices[f]["status"] == "predicted" for f in missing):
        reason = "all_predicted"
    else:
        reason = "incomplete_prediction"

    fields = {}
    for field in c01.FIELDS:
        choice = choices.get(field, {})
        status = choice.get("status", "not_requested")
        if field in provided:
            status = "provided"
        elif field in invalid:
            status = "invalid"
        applied = choice.get("raw") if reason == "all_predicted" and field in missing else provided.get(field)
        fields[field] = {"status": status, "applied": applied}
    return {"contract_version": item["contract_version"], "run_id": run_id, "id": item["id"],
            "attempts": int(observation is not None), "fields": fields, "reason": reason,
            "outcome": "complete" if reason in ("all_predicted", "channel_complete") else "review"}
