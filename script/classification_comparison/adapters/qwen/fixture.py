"""Gateway simulado. Regras pequenas para exercitar o protocolo em qualquer relato."""
import json

INSUFFICIENT = "informacao_insuficiente"


def completion(model, content, **metadata):
    return json.dumps({"model": model, "choices": [{"message": {"content": content}}], **metadata}).encode()


def fake_gateway(body, deadline, dispatched):
    request = json.loads(body)
    item = json.loads(request["messages"][1]["content"])
    text = item["text"].casefold()
    categories = [code for code, cues in (
        ("pix", ("pix",)), ("payouts", ("repasse", "liquidação")), ("terminal", ("terminal", "maquininha"))
    ) if any(cue in text for cue in cues)]
    category = categories[0] if len(categories) == 1 else INSUFFICIENT
    priority = INSUFFICIENT
    if ("sem alternativa" in text or "não existe alternativa" in text
            or "agora" in text and ("retirando saldo" in text or "perda" in text)):
        priority = "urgent"
    elif "um dos caixas" in text:
        priority = "intermediate"
    elif any(cue in text for cue in ("onde ", "como ", "treinamento")):
        priority = "basic"
    schema = request["response_format"]["json_schema"]["schema"]
    candidates = {"category": category, "priority": priority}
    answer = {field: candidates[field] if candidates[field] in schema["properties"][field]["enum"] else INSUFFICIENT
              for field in schema["required"]}
    dispatched()
    return 200, completion(request["model"], json.dumps(answer))
