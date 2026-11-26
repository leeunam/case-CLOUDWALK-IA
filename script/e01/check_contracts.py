"""Verifica os contratos E01 com exemplos independentes do runtime do piloto."""

import base64
import binascii
import hashlib
import hmac
import json
import uuid
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "docs/contratos"
E01 = CONTRACTS / "e01"
FIXTURES = E01 / "fixtures"
BRANDS = {
    "aurora": "11111111-1111-4111-8111-111111111111",
    "horizonte": "22222222-2222-4222-8222-222222222222",
}


def read(path):
    return json.loads(path.read_bytes())


def require(predicate, code):
    if not predicate:
        raise ValueError(code)


def index(rows):
    result = {row["id"]: row for row in rows}
    require(len(result) == len(rows), "duplicate_id")
    return result


def validate_catalog(ontology, brand, slug):
    subjects = index(ontology["subjects"])
    intents = index(ontology["intents"])
    conditions = index(ontology["conditions"])
    for intent in intents.values():
        require(intent["subject_id"] in subjects, "subject_ref")
    require(brand["brand_id"] == BRANDS[slug] and brand["slug"] == slug, "brand_origin")
    require(brand["ontology_version"] == ontology["version"], "ontology_version")
    sources = index(brand["sources"])
    procedures = index(brand["procedures"])
    rules = index(brand["handoff_rules"])
    for identifier in (*sources, *procedures, *rules):
        require(identifier.startswith(slug + "."), "foreign_brand_id")
    for row in [*procedures.values(), *rules.values()]:
        require(row["source_id"] in sources, "source_ref")
    for row in procedures.values():
        require(row["intent_id"] in intents, "intent_ref")
        require(set(row["requires"]) <= conditions.keys(), "condition_ref")


def confirmed(history, question, answers, *, suffix=False):
    if len(history) < 2:
        return False
    previous, current = history[-2:]
    if previous["author"]["type"] != "ai" or current["author"]["type"] != "customer":
        return False
    previous_text = previous["text"]
    asked = previous_text.endswith(question) if suffix else previous_text == question
    answer = current["text"].strip().casefold().rstrip(".!")
    return asked and answer in answers


def validate_decision(request, ontology, brand, decision, candidates):
    require(request["brand_id"] == brand["brand_id"], "brand_origin")
    history = request["payload"]["history"]
    messages = index(history)
    customers = [row["id"] for row in history if row["author"]["type"] == "customer"]
    require(set(decision["message_ids"]) <= messages.keys(), "message_origin")
    require(customers and customers[-1] in decision["message_ids"], "latest_customer")
    if decision["action"] == "resolve":
        require(confirmed(history, "O procedimento resolveu o problema?", {"sim, resolveu", "o problema foi resolvido"}, suffix=True), "resolution_evidence")
        require(decision["text"] == "Certo, vou encerrar este atendimento.", "resolve_text")
        return
    if decision["action"] == "reply":
        identifier = decision["procedure_id"]
        collection = "procedures"
    else:
        identifier = decision["rule_id"]
        collection = "handoff_rules"
    require(identifier in candidates, "candidate_origin")
    item = index(brand[collection]).get(identifier)
    require(item is not None, "candidate_origin")
    source = index(brand["sources"])[item["source_id"]]
    require(decision["source_refs"] == [{"id": source["id"], "version": source["version"]}], "source_origin")
    if collection == "handoff_rules":
        require(decision["text"] == "Vou encaminhar seu atendimento para a equipe.", "handoff_text")
        return
    conditions = index(ontology["conditions"])
    missing = [
        conditions[condition]["question"] for condition in item["requires"]
        if not confirmed(history, conditions[condition]["question"], {"sim", "sim, confirmo"})
    ]
    if decision["kind"] == "clarify":
        require(bool(missing), "condition_evidence")
        require(decision["text"] == missing[0], "reply_text")
    else:
        require(not missing, "condition_evidence")
        expected = " ".join([*item["steps"], "O procedimento resolveu o problema?"])
        require(decision["text"] == expected, "reply_text")


def schema_check(schema, value, fragment=None):
    entry = schema if fragment is None else {
        "$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/" + fragment
    }
    Draft202012Validator(entry, format_checker=FormatChecker()).validate(value)


def validate_exchange(doc, schemas, request_bytes):
    request = doc["request"]
    schema_check(schemas["public"], request, "AgentTurnRequested")
    schema_check(schemas["knowledge"], doc["ontology"], "ontology")
    for slug in BRANDS:
        schema_check(schemas["knowledge"], doc[slug], "brand")
        validate_catalog(doc["ontology"], doc[slug], slug)
    decision = doc["decision"]
    schema_check(schemas["decision"], decision)
    validate_decision(request, doc["ontology"], doc["aurora"], decision, doc["candidates"])

    exchange = doc["ledger"]
    for name, body in exchange.items():
        schema_check(schemas["ledger"], body, name)
    require(exchange["claim"]["request_sha256"] == hashlib.sha256(request_bytes).hexdigest(), "request_digest")
    complete = exchange["complete_result"]
    for response in (complete, exchange["complete_failed"]):
        usage = response["usage"]
        require(usage["cached_input_tokens"] <= usage["input_tokens"], "cache_range")
    require(complete["source_refs"] == decision["source_refs"], "audit_sources")
    require(complete["knowledge_version"] == doc["aurora"]["version"], "audit_version")
    try:
        raw = base64.b64decode(complete["result_b64"], validate=True)
    except binascii.Error as error:
        raise ValueError("result_encoding") from error
    require(len(raw) <= 65536 and base64.b64encode(raw).decode() == complete["result_b64"], "result_encoding")
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == complete["result_sha256"], "result_digest")
    result = json.loads(raw)
    schema_check(schemas["public"], result, "AgentResult")
    shared = ("case_id", "brand_id", "correlation_id", "turn_id", "assignment_generation", "occurred_at")
    require(all(result[key] == request[key] for key in shared), "result_origin")
    request_id = request["event_id"]
    expected = uuid.uuid5(uuid.NAMESPACE_URL, "cloudwalk:e01-luna-v1:" + request_id)
    require(result["event_id"] == str(expected) and result["payload"]["request_event_id"] == request_id, "result_origin")
    require(exchange["saved"]["result_b64"] == complete["result_b64"], "saved_bytes")
    require(exchange["saved"]["result_sha256"] == digest == exchange["published"]["result_sha256"], "published_digest")


def replace(document, path, value):
    keys = path.strip("/").split("/")
    current = document
    for key in keys[:-1]:
        current = current[int(key) if isinstance(current, list) else key]
    current[int(keys[-1]) if isinstance(current, list) else keys[-1]] = value


def main():
    schemas = {name: read(E01 / (name + ".schema.json")) for name in ("knowledge", "decision", "ledger")}
    schemas["public"] = read(CONTRACTS / "schemas/v1.json")
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    request_bytes = (FIXTURES / "request.json").read_bytes()
    doc = {name: read(FIXTURES / (name + ".json")) for name in ("ontology", *BRANDS, "request", "decision", "ledger")}
    doc["candidates"] = ["aurora.visor", "aurora.humano"]
    validate_exchange(doc, schemas, request_bytes)
    vector = read(FIXTURES / "signature.json")
    signed = "\n".join(vector[key] for key in ("timestamp", "nonce", "method", "path", "body_utf8")).encode()
    require(hmac.digest(vector["fixture_key"].encode(), signed, "sha256").hex() == vector["signature"], "signature")
    require(json.loads(vector["body_utf8"]) == doc["ledger"]["claim"], "signed_claim")
    alternatives = read(FIXTURES / "decisions-other.json")
    for example in alternatives:
        decision = example["decision"]
        schema_check(schemas["decision"], decision)
        request = deepcopy(doc["request"])
        request["payload"]["history"] = example["history"]
        schema_check(schemas["public"], request, "AgentTurnRequested")
        validate_decision(request, doc["ontology"], doc["aurora"], decision, doc["candidates"])
    rejected = read(FIXTURES / "negative.json")
    for case in rejected:
        changed = deepcopy(doc)
        replace(changed, case["path"], case["value"])
        try:
            validate_exchange(changed, schemas, request_bytes)
        except ValidationError:
            reason = "schema"
        except ValueError as error:
            reason = str(error)
        else:
            reason = "accepted"
        if reason != case["expected"]:
            raise SystemExit(f"{case['name']}: esperado {case['expected']}, obtido {reason}")
    print(f"3 schemas E01 e contrato público válidos; 1 troca completa, {len(alternatives)} decisões adicionais "
          f"e {len(rejected)} rejeições verificadas.")


if __name__ == "__main__":
    main()
