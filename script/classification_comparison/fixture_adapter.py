"""Adaptador de referência JSONL, sem acesso ao dataset ou a seus rótulos."""
import json
import os
import platform
import sys
from pathlib import Path

base = Path(__file__).resolve().parents[2]
fixtures = base / "docs/planejamento/classificacao-comparativa/contratos/fixtures"
identity = json.loads(os.environ["CLASSIFICATION_IDENTITY"])
if identity["mode"] != "fixture":
    sys.exit("O adaptador de demonstração exige modo fixture.")
run_id = os.environ["CLASSIFICATION_RUN_ID"]
with (fixtures / "observations.jsonl").open(encoding="utf-8", newline="\n") as lines:
    controls = {obs["id"]: obs for obs in map(json.loads, lines)}

# Primeiro carregar tudo, depois sinalizar prontidão atomicamente.
ready = Path(os.environ["CLASSIFICATION_READY_FILE"])
temp = ready.with_suffix(".tmp")
temp.write_text(json.dumps(dict(runtime=platform.python_version(), hardware=platform.machine())), encoding="utf-8")
temp.replace(ready)

for line in sys.stdin.buffer:
    item = json.loads(line.decode("utf-8"))
    fields = item["missing"]
    if item["id"] in controls:
        obs = controls[item["id"]].copy()
    else:
        # Controles determinísticos de domínio, sem aprendizado ou consulta ao gabarito.
        choices = {}
        text = item["text"].casefold()
        for field in fields:
            raw = None
            if field == "priority" and "agora" in text:
                raw = "urgent"
            elif field == "category" and "pix" in text:
                raw = "pix"
            choices[field] = (dict(status="predicted", reason=None, raw=raw) if raw else
                              dict(status="abstained", reason="explicit", raw="informacao_insuficiente"))
        obs = dict(contract_version="1.0.0", id=item["id"], attempt=1, choices=choices,
                   returned_model=identity["requested_model"], weights_revision=None, requests=1,
                   questions=len(fields))
    obs.update(identity=identity, run_id=run_id, temperature_state="unknown", elapsed_ms=None,
               load_ms=None, inference_ms=None)
    obs["request_usage"] = [dict(input_tokens=None, output_tokens=None, observed_api_usd=None,
                                 estimated_api_usd=None, tariff=None) for _ in range(obs["requests"])]
    print(json.dumps(obs, ensure_ascii=False), flush=True)
