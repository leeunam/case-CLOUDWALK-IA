"""Transporte Feita fictício do aceite E01. Usado exclusivamente em teste."""

import logging

if __package__:
    from .agent_flow import json_bytes
    from .e01_backend import FEITA_PATH, MODEL
    from .e01_contracts import read_json_object
    from .e01_knowledge import HANDOFF_TEXT, RESOLUTION_QUESTION, RESOLVE_TEXT
else:
    from agent_flow import json_bytes
    from e01_backend import FEITA_PATH, MODEL
    from e01_contracts import read_json_object
    from e01_knowledge import HANDOFF_TEXT, RESOLUTION_QUESTION, RESOLVE_TEXT


def fixture_post(path, headers, raw, *, deadline):
    if path != FEITA_PATH or headers.get("Authorization") != "Bearer offline-test-fixture":
        raise ValueError("invalid_offline_fixture_transport")
    document = read_json_object(raw)
    context = read_json_object(document["messages"][-1]["content"])
    candidates = context["knowledge"]
    history = context["history"]
    latest = history[-1]
    text = latest["text"].casefold()
    response_id = "offline-fixture-" + latest["id"]
    logging.info("e01 fixture HTTP POST message_id=%s provider_response_id=%s", latest["id"], response_id)

    decision = {"message_ids": [latest["id"]], "source_refs": []}
    source_id = None
    if text == "sim, resolveu.":
        decision.update(action="resolve", text=RESOLVE_TEXT)
    elif "estorno" in text or "falar com uma pessoa" in text or text == "ainda não tenho certeza.":
        reason = "sensitive_operation" if "estorno" in text else (
            "human_requested" if "falar com uma pessoa" in text else "no_guidance"
        )
        rule = next(rule for rule in candidates["handoff_rules"] if rule["reason"] == reason)
        decision.update(action="handoff", rule_id=rule["id"], text=HANDOFF_TEXT)
        source_id = rule["source_id"]
    else:
        intent = {
            "onde consulto o comprovante de pix?": "consultar-comprovante-pix",
            "onde consulto o status do repasse?": "consultar-status-repasse",
            "a tela da minha maquininha está estranha.": "consultar-visor-terminal",
        }[text]
        procedure = next(row for row in candidates["procedures"] if row["intent_id"] == intent)
        source_id = procedure["source_id"]
        if procedure["requires"]:
            condition_id = procedure["requires"][0]
            condition = next(row for row in candidates["conditions"] if row["id"] == condition_id)
            decision.update(action="reply", kind="clarify", procedure_id=procedure["id"], text=condition["question"])
        else:
            response = " ".join([*procedure["steps"], RESOLUTION_QUESTION])
            decision.update(action="reply", kind="procedure", procedure_id=procedure["id"], text=response)

    if source_id:
        source = next(row for row in candidates["sources"] if row["id"] == source_id)
        decision["source_refs"] = [{"id": source["id"], "version": source["version"]}]
    return 200, json_bytes({
        "id": response_id,
        "model": MODEL,
        "choices": [{"finish_reason": "stop", "message": {"content": json_bytes({"decision": decision}).decode()}}],
        "usage": {"prompt_tokens": 100, "prompt_tokens_details": {"cached_tokens": 20},
                  "completion_tokens": 25, "total_tokens": 125},
    })
