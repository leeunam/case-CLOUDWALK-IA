"""Replay dos scores auditados. A grade não invoca nem cronometra o modelo."""
from itertools import product

from ..contracts.core import CATALOG, FIELDS, PROTOCOL, REVIEW, VERSION, decimal, require
from ..contracts.ipc import validate_vector
from .metrics import metrics, quality_gates


def scored_rows(records, decisions):
    rows = []
    for row, decision in zip(records, decisions, strict=True):
        require(row["id"] == decision["id"], "score de outro ID")
        heads, errors = {}, {}
        for f in row["missing_fields"]:
            field = decision["fields"][f]
            if field["vector"] is None:
                errors[f] = field["reason"]
            else:
                heads[f] = field["vector"]
        rows.append(dict(id=row["id"], heads=heads, errors=errors))
    return rows


def rank_key(candidate):
    m = candidate["metrics"]
    correct = m["correct_coverage"]["numerator"]
    auto = m["automatic_coverage"]["numerator"]
    wrong = auto - correct + m["wrong_expected_review"]["numerator"]
    cuts = candidate["policy"]
    return (-correct, -m["applied_urgent"]["numerator"], wrong, -auto,
            *(cuts[f][k] for f in FIELDS for k in ("tau", "delta")))


def select(records, bundle, control_calls):
    require(bundle["partition"] == "validation", "a grade aceita somente validação")
    # validate_scores e a auditoria das decisões de origem antecedem esta função.
    indexed = {r["id"]: r for r in bundle["rows"]}
    cases = []
    for r in records:
        heads = {f: validate_vector(v, bundle["class_order"][f]) for f, v in indexed[r["id"]]["heads"].items()}
        cases.append((r, heads, indexed[r["id"]]["errors"]))

    def replay(policy):
        results = []
        for row, heads, errors in cases:
            accepted, fields = {}, {}
            for f in row["missing_fields"]:
                if f in errors:
                    fields[f] = {"decision": "error", "raw": None}
                    continue
                raw, top, margin = heads[f]
                accept = raw != REVIEW and raw in CATALOG[f]
                if policy:
                    cut = policy[f]
                    accept = accept and top >= decimal(cut["tau"]) and margin > decimal(cut["delta"])
                if accept:
                    accepted[f] = raw
                fields[f] = {"raw": raw, "decision": "accept" if accept else "review"}
            complete = len(accepted) == len(row["missing_fields"])
            results.append(dict(id=row["id"], received=row["received"], fields=fields,
                                outcome="complete" if complete else "error" if errors else "review",
                                applied=accepted if complete else {}))
        return metrics(records, results, control_calls)

    rule = PROTOCOL["review_policy"]
    cuts = [dict(tau=t, delta=d) for t, d in product(rule["tau_grid"], rule["delta_grid"])]
    grid = []
    for category, priority in product(cuts, repeat=2):
        policy = dict(contract_version=VERSION, category=category, priority=priority)
        totals = replay(policy)
        gates = quality_gates(totals, "validation")
        grid.append(dict(policy=policy, metrics=totals, gates=gates, eligible=all(gates.values())))
    winner = min((p for p in grid if p["eligible"]), key=rank_key, default=None)
    return dict(baseline_argmax=replay(None), policies=grid, selected=winner["policy"] if winner else None)
