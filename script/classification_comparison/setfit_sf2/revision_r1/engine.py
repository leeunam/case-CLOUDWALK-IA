"""Auditoria da captura e comparação exclusiva em validação."""
import hashlib
from itertools import product

from jsonschema import Draft202012Validator

from ..contracts.artifacts import validate_report
from ..contracts.core import FIELDS, PROTOCOL, VERSION, decode, read, read_lines, require, sha256, structure
from ..contracts.data import _validate_masked, validate_isolation, validate_record
from ..contracts.ipc import validate_scores
from ..evaluation.audit import originals
from ..evaluation.metrics import metrics
from ..evaluation.runner import encoded
from ..evaluation.selection import evaluate_policies, prepare_replay, rank_key, scored_rows, select


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def extension_policies(amendment, schema_bytes):
    rule = PROTOCOL["review_policy"]
    spec = amendment["extension"]
    require(spec == dict(namespace="sf2-r1-offline/1.0", category_tau=[.95], category_delta=rule["delta_grid"],
                         priority_tau=rule["tau_grid"], priority_delta=rule["delta_grid"], new_policy_count=45,
                         combined_policy_count=270, max_execution_rounds=1, selection_order=rule["selection_order"],
                         allowed_scope="offline_replay_only"), "cortes ou critérios fora da autorização")
    schema = decode(schema_bytes)
    validator = Draft202012Validator(schema)
    policies = []
    for tau, delta, priority_tau, priority_delta in product(spec["category_tau"], spec["category_delta"],
                                                            spec["priority_tau"], spec["priority_delta"]):
        policy = dict(contract_version=spec["namespace"], category=dict(tau=tau, delta=delta),
                      priority=dict(tau=priority_tau, delta=priority_delta))
        require(validator.is_valid(policy), "candidata incompatível com o subcontrato R1")
        policies.append(policy)
    return policies


def audit_capture(amendment, paths):
    quota = amendment["validation_quotas"]
    require(quota == PROTOCOL["data"]["validation"] and amendment["gates"] == PROTOCOL["gates"],
            "quotas/gates divergem da SF2")
    records = read_lines(paths["validation"])
    require(len(records) == quota["total"] == 90, "validação incompleta")
    for row in records:
        validate_record(row)
    validate_isolation({"validation": records})
    _validate_masked(records, quota)

    policy, model = read(paths["capture_policy"]), read(paths["package_manifest"])
    structure("policy", policy)
    structure("modelManifest", model)
    minimum = {key: min(PROTOCOL["review_policy"][key + "_grid"]) for key in ("tau", "delta")}
    require(all(policy[f] == minimum for f in FIELDS), "corte histórico não corresponde à coleta")
    ids = dict(package_sha256=sha256(paths["package_manifest"]), model_sha256=model["model_sha256"],
               policy_sha256=sha256(paths["capture_policy"]))
    seal, decisions, durations, calls = originals(paths["seal"].parent, records, policy, model, ids)
    require(seal["failure"] is None and len(decisions) == len(durations) == 90 and calls == 0,
            "coleta incompleta ou chamadas em controle bloqueado")
    public, freeze = read(paths["public_manifest"]), read(paths["training_freeze"])
    for kind, value in (("publicManifest", public), ("trainingFreeze", freeze), ("finalSeal", read(paths["final_seal"]))):
        structure(kind, value)
    data_sha = sha256(paths["validation"])
    require(public["stage"] == "accepted" and public["counts"]["validation"] == len(records)
            and all(freeze["files"][k] == v["sha256"] for k, v in public["files"].items())
            and public["files"]["validation"]["sha256"] == data_sha, "validação pública fora do freeze")
    versions = read(paths["capture_versions"])
    require(all(versions.get(k) == v for k, v in model["versions"].items()), "versões da captura divergentes")
    scores = dict(contract_version=VERSION, partition="validation", dataset_sha256=data_sha,
                  package_sha256=ids["package_sha256"], model_sha256=model["model_sha256"],
                  class_order=model["class_order"], rows=scored_rows(records, decisions))
    validate_scores(scores, records, dataset_sha256=data_sha, package_sha256=ids["package_sha256"],
                    model_sha256=model["model_sha256"], class_order=model["class_order"])
    require(scores == read(paths["scores03"]) == read(paths["scores04"]), "scores 03/04 ou vetores dos frames divergem")
    parent = amendment["parent"]
    selection = read(paths["parent_selection"])
    require(selection == dict(policy_count=225, eligible_count=0, capture_policy_sha256=ids["policy_sha256"],
                              selected_policy_sha256=None, scores_sha256=sha256(paths["scores04"]),
                              predictions_sha256=sha256(paths["predictions"]), grid_sha256=parent["original_grid_sha256"],
                              timings_sha256=sha256(paths["journal"]), latency_source="observed_capture_policy_external_total"),
            "recibo original divergente")
    report = read(paths["parent_report"])
    validate_report(report)
    require(report["status"] == "failed" and report["policy_sha256"] == ids["policy_sha256"]
            and report["score_package_sha256"] == selection["scores_sha256"]
            and report["predictions_sha256"] == selection["predictions_sha256"]
            and report["metrics"] == metrics(records, decisions, calls), "relatório histórico diverge dos frames")
    return records, scores, calls


def confirm_original(data, archived_bytes, parent):
    result = select(*data)
    require(parent["original_grid_policy_count"] == len(result["policies"]) == 225
            and parent["original_grid_eligible_count"] == sum(row["eligible"] for row in result["policies"]) == 0
            and result["selected"] is None, "estado histórico da seleção divergente")
    require(result == decode(archived_bytes) and digest(result) == parent["original_grid_sha256"]
            and encoded(result) == archived_bytes, "225 políticas ou baseline divergem da grade arquivada")
    return result


def check_union(original, policies):
    all_policies = [row["policy"] for row in original["policies"]] + policies
    keys = {tuple(p[f][k] for f in FIELDS for k in ("tau", "delta")) for p in all_policies}
    require(len(original["policies"]) == 225 and len(policies) == 45 and len(keys) == 270,
            "união de cortes incompleta ou duplicada")


def compare(data, original, policies):
    check_union(original, policies)
    extra = evaluate_policies(prepare_replay(*data), policies)
    union = original["policies"] + extra
    eligible = [row for row in union if row["eligible"]]
    selected = min(eligible, key=rank_key, default=None)
    return dict(contract_version="sf2-r1-offline/1.0", scope="validation_offline_replay",
                status="eligible_validation_only" if selected else "negative",
                selected=selected["policy"] if selected else None,
                counts=dict(original=225, original_eligible=0, additional=45, union=270, eligible=len(eligible)),
                original_grid_sha256=digest(original), additional_grid_sha256=digest(extra), union_sha256=digest(union),
                original_parity=dict(policies=225, baseline=True, identical_bytes=True),
                capture_audit=dict(valid_cases=len(data[0]), valid_controls=5, valid_attempts=len(data[0])+5,
                                   scores03_scores04_match_frames=True, failure=None),
                baseline_argmax=original["baseline_argmax"],
                policies=[{**row, "failed_gates": [k for k, ok in row["gates"].items() if not ok]} for row in union],
                scope_limits=dict(final_release=False, c06_c07_released=False, model_adopted=False,
                                  post_validation_amendment=True, inference_latency_measured=False),
                new_consumption=dict(training_runs=0, inferences=0, api_calls=0, final_exposures=0))
