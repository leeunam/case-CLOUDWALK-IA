"""Auditoria independente da saída: nunca repara predição parcial."""
import json

from .core import (CATALOG, FIELDS, PROTOCOL, REVIEW, VERSION, channel,
                   decimal, require, structure)


def project(record, catalog=CATALOG):
    item = {"contract_version": VERSION, **{k: record[k] for k in ("id", "text", "received")},
            "catalog": catalog, "missing_fields": channel(record["received"], catalog)[0]}
    if "missing_fields" in record:
        require(set(record["missing_fields"]) == set(item["missing_fields"]), "missing_fields diverge do canal")
    validate_input(item)
    return item


def validate_input(item):
    structure("input", item)
    missing, invalid, valid = channel(item["received"], item["catalog"])
    require(set(missing) == set(item["missing_fields"]), "missing_fields diverge do canal")
    known_catalog = item["catalog"]["version"] == CATALOG["version"] and all(
        all(CATALOG[field].get(code) == description for code, description in item["catalog"][field].items())
        for field in FIELDS)
    return missing, invalid, valid, known_catalog


def validate_vector(vector, class_order):
    structure("scoreVector", vector)
    require(vector["classes"] == class_order and len(vector["scores"]) == len(class_order),
            "classes, ordem ou quantidade de scores inesperadas")
    scores = [decimal(x) for x in vector["scores"]]
    tolerance = decimal(PROTOCOL["review_policy"]["sum_scores_absolute_tolerance"])
    require(abs(sum(scores) - 1) <= tolerance, "soma de scores inválida")
    # sorted é estável. Em empate, o primeiro índice em classes_ continua sendo o vencedor bruto.
    order = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
    return class_order[order[0]], scores[order[0]], scores[order[0]] - scores[order[1]]


def _assess(raw, top, margin, cut, catalog):
    if raw == REVIEW:
        return "review", "raw_review"
    if raw not in catalog:
        return "review", "inactive_label"
    if top < decimal(cut["tau"]):
        return "review", "below_tau"
    if margin <= decimal(cut["delta"]):
        return "review", "low_margin"
    return "accept", "accepted"


def _require_blank(field, cut=None):
    require(all(field[k] is None for k in ("vector", "raw", "margin")) and field["cut"] == cut,
            "score, margem, rótulo ou corte sem observação")


def validate_decision(item, decision, policy, class_order, identities, *, interruption=None):
    """identities vem de bytes verificados. interruption vem do supervisor/tokenizador."""
    missing, invalid, valid, catalog_ok = validate_input(item)
    structure("policy", policy)
    structure("classes", class_order)
    structure("decision", decision)
    require(interruption in (None, "error", "timeout", "too_long"), "falha externa inválida")
    require(set(identities) == {"package_sha256", "model_sha256", "policy_sha256"} and
            all(decision[k] == v for k, v in identities.items()), "identidade de execução divergente")
    require(decision["id"] == item["id"], "canal/ID alterado")
    # Em Python True == 1. Para preservar um controle inválido inclusive no tipo, compare JSON estrito.
    require(json.dumps(decision["received"], sort_keys=True) == json.dumps(item["received"], sort_keys=True),
            "tipo do campo recebido alterado")
    blocked = bool(invalid) or not catalog_ok
    accepted = {}
    error = False
    for key in FIELDS:
        field = decision["fields"][key]
        call = decision["calls"][key]
        if key in valid and catalog_ok:
            expected = ("provided", "provided")
        elif not catalog_ok:
            expected = ("invalid", "invalid_catalog")
        elif key in invalid:
            expected = ("invalid", "invalid_input")
        elif blocked:
            expected = ("not_requested", "not_requested")
        else:
            expected = None
        if expected:
            _require_blank(field)
            require(call == 0 and (field["decision"], field["reason"]) == expected,
                    "campo fornecido, inválido ou bloqueado recebeu decisão/chamada indevida")
        elif interruption == "too_long":
            require(call == 0 and field["decision"] == "review" and field["reason"] == "too_long",
                    "texto longo deve ficar em revisão sem inferência")
            _require_blank(field, policy[key])
        elif field["decision"] == "error":
            require(field["reason"] in ("error", "timeout", "invalid_score"), "motivo de erro inválido")
            require(call == 1 or
                    (not call and interruption == field["reason"]), "chamada ou interrupção incompatível")
            _require_blank(field, policy[key])
            error = True
        else:
            require(call == 1 and field["cut"] == policy[key] and field["vector"] is not None,
                    "observação ou corte ausente")
            raw, top, margin = validate_vector(field["vector"], class_order[key])
            require(field["raw"] == raw and field["margin"] is not None and
                    abs(decimal(field["margin"]) - margin) <= decimal("1e-15"), "argmax ou margem divergente")
            expected = _assess(raw, top, margin, policy[key], item["catalog"][key])
            require((field["decision"], field["reason"]) == expected, "regra de revisão divergente")
            if expected[0] == "accept":
                accepted[key] = raw
    if interruption in ("error", "timeout"):
        require(error and not blocked and missing, "interrupção sem erro registrado")
    if interruption == "too_long":
        require(missing and not blocked, "controle completo/inválido indevidamente tokenizado")
    outcome = ("error" if error else "review" if blocked or set(accepted) != set(missing) else "complete")
    require(decision["outcome"] == outcome, "resultado do caso inconsistente")
    require(decision["applied"] == (accepted if outcome == "complete" else {}), "aplicação parcial ou indevida")


def validate_scores(bundle, records, *, dataset_sha256, package_sha256, model_sha256, class_order):
    structure("scorePackage", bundle)
    for key, expected in (("dataset_sha256", dataset_sha256), ("package_sha256", package_sha256),
                          ("model_sha256", model_sha256), ("class_order", class_order)):
        require(bundle[key] == expected, "pacote de scores diverge do manifesto: " + key)
    rows = bundle["rows"]
    required = {r["id"]: r for r in records}
    require(len(rows) == len(required) == len(records) and {r["id"] for r in rows} == set(required),
            "IDs de scores ausentes/duplicados")
    for row in rows:
        record = required[row["id"]]
        require(record["partition"] == bundle["partition"], "partição de scores incorreta")
        item = project(record)
        require(set(record["missing_fields"]) == set(item["missing_fields"]), "máscara declarada inconsistente")
        observed = row["heads"].keys()
        errors = row["errors"].keys()
        require(not observed & errors and observed | errors == set(item["missing_fields"]), "cobertura de scores")
        for field, vector in row["heads"].items():
            validate_vector(vector, class_order[field])
