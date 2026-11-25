"""Completa os campos ausentes com aplicação atômica da política SF2."""

import logging
from time import perf_counter_ns

from ..contracts.core import ContractError, FIELDS, REVIEW, VERSION, decimal, structure
from ..contracts.ipc import validate_input, validate_vector
from ..training.environment import RECIPE

LOG = logging.getLogger(__name__)


def observe(package, field, text):
    try:
        vector = package.score(field, text)
    except TimeoutError:
        LOG.warning("Prazo excedido pelo especialista %s", field)
        return None, "timeout"
    except Exception as error:
        LOG.warning("Falha no especialista %s (%s)", field, type(error).__name__)
        return None, "error"
    try:
        validate_vector(vector, package.class_order[field])
    except ContractError:
        LOG.warning("Vetor inválido do especialista %s", field)
        return None, "invalid_score"
    return vector, None


def result(decision, reason, *, cut=None, vector=None, raw=None, margin=None):
    return {
        "decision": decision, "reason": reason, "cut": cut,
        "vector": vector, "raw": raw, "margin": margin,
    }


def assess(vector, classes, cut, catalog):
    raw, top, margin = validate_vector(vector, classes)
    if raw == REVIEW:
        decision, reason = "review", "raw_review"
    elif raw not in catalog:
        decision, reason = "review", "inactive_label"
    elif top < decimal(cut["tau"]):
        decision, reason = "review", "below_tau"
    elif margin <= decimal(cut["delta"]):
        decision, reason = "review", "low_margin"
    else:
        decision, reason = "accept", "accepted"
    return result(decision, reason, cut=cut, vector=vector, raw=raw, margin=float(margin))


def decide(item, package, policy, policy_sha256, *, started=None):
    if started is None:
        started = perf_counter_ns()
    missing, invalid, provided, catalog_ok = validate_input(item)
    blocked = bool(invalid) or not catalog_ok
    text = item["text"]
    too_long = (not blocked and bool(missing) and
                package.token_length(text, missing) > RECIPE["max_sequence_length"])
    calls = dict.fromkeys(FIELDS, 0)
    fields, accepted = {}, {}
    for field in FIELDS:
        if not catalog_ok:
            fields[field] = result("invalid", "invalid_catalog")
        elif field in provided:
            fields[field] = result("provided", "provided")
        elif field in invalid:
            fields[field] = result("invalid", "invalid_input")
        elif blocked:
            fields[field] = result("not_requested", "not_requested")
        elif too_long:
            fields[field] = result("review", "too_long", cut=policy[field])
        else:
            calls[field] = 1
            vector, error = observe(package, field, text)
            if error:
                fields[field] = result("error", error, cut=policy[field])
            else:
                fields[field] = assess(vector, package.class_order[field], policy[field], item["catalog"][field])
                if fields[field]["decision"] == "accept":
                    accepted[field] = fields[field]["raw"]

    if any(value["decision"] == "error" for value in fields.values()):
        outcome = "error"
    elif blocked or len(accepted) != len(missing):
        outcome = "review"
    else:
        outcome = "complete"

    decision = {
        "contract_version": VERSION,
        "id": item["id"],
        "outcome": outcome,
        "received": item["received"],
        "applied": accepted if outcome == "complete" else {},
        "fields": fields,
        "calls": calls,
        "package_sha256": package.digest,
        "model_sha256": package.model_sha256,
        "policy_sha256": policy_sha256,
        "elapsed_ms": 0,
    }
    structure("decision", decision)
    decision["elapsed_ms"] = (perf_counter_ns() - started) / 1_000_000
    return decision
