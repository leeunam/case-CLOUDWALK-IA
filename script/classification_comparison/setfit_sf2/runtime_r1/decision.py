"""Derivação e auditoria sobre os bytes exatos da observação por item."""
from jsonschema import Draft202012Validator

from ..adapter.decide import assess
from ..contracts import ipc
from ..contracts.core import FIELDS, decode, require
from .context import check_context, check_originals, digest, encoded, same_json, schema

VERSION = "sf2-final-r1/1.0"


def _observed(item, raw_frame, context):
    checked = check_context(context)
    check_originals(("input", "policy", "classes", "decision", "scoreVector"))
    require(type(item) is dict and same_json(item, decode(encoded(item))), "entrada fora da projeção JSON")
    missing, invalid, provided, known = ipc.validate_input(item)
    require(item["missing_fields"] == missing, "máscara fora da ordem da projeção")
    require(type(raw_frame) is bytes and raw_frame.endswith(b"\n") and raw_frame.count(b"\n") == 1
            and b"\r" not in raw_frame, "esperada uma linha de coleta UTF-8 com LF")
    try:
        raw = decode(raw_frame.decode("utf-8"))
    except RecursionError as exc:
        raise ValueError("JSON do frame excede a profundidade suportada") from exc
    identities = {"model_sha256": checked["model_sha256"], "package_sha256": checked["package_sha256"],
                  "policy_sha256": checked["capture_policy_sha256"]}
    ipc.validate_decision(item, raw, checked["capture_policy"], checked["class_order"], identities)
    require(same_json(item["received"], raw["received"]), "canal alterado")
    require(all(type(raw["calls"][f]) is int for f in FIELDS), "contagem de chamadas não inteira")
    return raw, checked, (missing, invalid, provided, known)


def _header(raw, raw_frame, context):
    return {"contract_version": VERSION, "id": raw["id"], "raw_sha256": digest(raw_frame),
            "capture_policy_sha256": context["capture_policy_sha256"],
            "selected_policy_sha256": context["selected_policy_sha256"], "package_sha256": raw["package_sha256"],
            "model_sha256": raw["model_sha256"], "received": raw["received"], "calls": raw["calls"]}


def _structure(decision):
    encoded(decision)  # jsonschema também recebe decisões em memória. Rejeita ciclos e não finitos.
    error = next(Draft202012Validator(schema()).iter_errors(decision), None)
    if error:
        raise ValueError(f"decisão R1 fora do schema em {list(error.absolute_path)!r}: {error.validator}")


def derive(item: dict, raw_frame: bytes, context: dict) -> dict:
    raw, checked, (missing, invalid, _, known) = _observed(item, raw_frame, context)
    fields, accepted = {}, {}
    for key in FIELDS:
        field = raw["fields"][key].copy()
        if raw["calls"][key]:
            field["cut"] = checked["selected_policy"][key]
            if field["vector"] is not None:
                assessment = assess(field["vector"], checked["class_order"][key], field["cut"], item["catalog"][key])
                # A margem publicada é a observada e auditada, inclusive a precisão da serialização.
                field.update(decision=assessment["decision"], reason=assessment["reason"])
                if field["decision"] == "accept":
                    accepted[key] = field["raw"]
        fields[key] = field
    if any(field["decision"] == "error" for field in fields.values()):
        outcome = "error"
    elif not known or invalid or set(accepted) != set(missing):
        outcome = "review"
    else:
        outcome = "complete"
    decision = dict(_header(raw, raw_frame, checked), fields=fields, outcome=outcome,
                    applied=accepted if outcome == "complete" else {})
    _structure(decision)
    return decision


def verify(item: dict, raw_frame: bytes, decision: dict, context: dict) -> None:
    raw, checked, (missing, invalid, provided, known) = _observed(item, raw_frame, context)
    _structure(decision)
    for key, value in _header(raw, raw_frame, checked).items():
        require(same_json(decision[key], value), "identidade ou observação divergente: " + key)
    accepted = {}
    has_error = False
    for key in FIELDS:
        observed = raw["fields"][key]
        field = decision["fields"][key]
        for name in ("vector", "raw", "margin"):
            require(same_json(field[name], observed[name]), f"observação divergente: {key}.{name}")
        cut = None
        if not known:
            expected = ("invalid", "invalid_catalog")
        elif key in provided:
            expected = ("provided", "provided")
        elif key in invalid:
            expected = ("invalid", "invalid_input")
        elif invalid:
            expected = ("not_requested", "not_requested")
        else:
            cut = checked["selected_policy"][key]
            if observed["vector"] is None:
                expected = ("error", observed["reason"])
                has_error = True
            else:
                label, score, margin = ipc.validate_vector(observed["vector"], checked["class_order"][key])
                expected = ipc._assess(label, score, margin, cut, item["catalog"][key])
                if expected[0] == "accept":
                    accepted[key] = label
        require((field["decision"], field["reason"]) == expected and same_json(field["cut"], cut),
                "decisão, motivo ou corte R1 divergente: " + key)
    complete = known and not invalid and set(accepted) == set(missing)
    outcome = "error" if has_error else "complete" if complete else "review"
    require(decision["outcome"] == outcome and same_json(decision["applied"], accepted if complete else {}),
            "resultado ou aplicação atômica divergente")
