"""Candidato Qwen/Feita para o protocolo JSONL 1.1.0 da C02."""
import argparse
import math
import os
import platform
import sys
import time
from pathlib import Path

from fixture import fake_gateway
from pilot import Blocked, Budget, PUBLIC_TARIFF, authorized_cap, money, rates
from transport import FeitaTransport

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import c01, decode, encode

MODEL = "qwen/qwen3.8-27b"
VERSION = "1.1.0"
IPC_MARGIN_SECONDS = 0.05


def metadata(value):
    return value if isinstance(value, str) and value.strip() else None


def integer(value):
    return value if type(value) is int and value >= 0 else None


def choices_for(fields, status, reason, raw=None):
    return {field: choice(status, raw, reason) for field in fields}


def choice(status, raw, reason=None):
    return {"status": status, "raw": raw, "reason": reason, "score": None}


def parse_object(data):
    if not isinstance(data, (str, bytes)):
        return None
    try:
        parsed = decode(data)
    except (ValueError, RecursionError):
        return None
    return parsed if isinstance(parsed, dict) else None


def numeric_cost(amount):
    if amount is None:
        return None
    result = float(amount)
    return result if math.isfinite(result) else None


def usage_from(response, tariff, cost_unit):
    data = response.get("usage")
    data = data if isinstance(data, dict) else {}
    input_tokens = integer(data.get("prompt_tokens"))
    output_tokens = integer(data.get("completion_tokens"))
    observed = money(data.get("cost")) if cost_unit == "USD" else None
    # O exemplo público de credits não confirma o débito nem a unidade de cost.
    estimate = reference = None
    if input_tokens is not None and output_tokens is not None:
        price = rates(tariff)
        total = (input_tokens * price["input"] + output_tokens * price["output"]) / 1_000_000
        rate = f"USD/Mtoken: entrada {price['input']}, saída {price['output']} (sem ajuste de cache)"
        estimate = numeric_cost(total)
        if estimate is not None:
            reference = {"source": tariff["source"], "date": tariff["date"], "rate": rate}
    return {"input_tokens": input_tokens, "output_tokens": output_tokens,
            "observed_api_usd": numeric_cost(observed),
            "estimated_api_usd": estimate, "tariff": reference}


def request_body(item, received, instructions, max_tokens):
    fields = item["missing"]
    shape = {"type": "object", "required": fields, "additionalProperties": False, "properties": {
        field: {"type": "string", "enum": [*item["catalog"][field], c01.ABSTENTION]} for field in fields
    }}
    context = {key: item[key] for key in ("text", "brand", "catalog", "missing")}
    context["received"] = received
    return encode({
        "model": MODEL, "stream": False, "temperature": 0, "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": instructions}, {"role": "user", "content": encode(context)}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "classificacao", "strict": True, "schema": shape,
        }},
    }).encode("utf-8")


def interpretation(response, fields, catalog):
    candidates = response.get("choices")
    first, = candidates if isinstance(candidates, list) and len(candidates) == 1 else (None,)
    message = first.get("message") if isinstance(first, dict) else None
    if not isinstance(message, dict):
        if isinstance(first, dict) and first.get("finish_reason") == "content_filter":
            return choices_for(fields, "abstained", "policy")
        return choices_for(fields, "invalid", "missing_output")
    content = message.get("content")
    result = parse_object(content)
    if metadata(message.get("refusal")) or first.get("finish_reason") == "content_filter":
        return {field: choice("abstained", (result or {}).get(field), "policy") for field in fields}
    if content is None:
        return choices_for(fields, "invalid", "missing_output")
    if result is None:
        return choices_for(fields, "invalid", "invalid_output")
    if result.keys() - set(fields) or first.get("finish_reason") == "length":
        # A evidência é o objeto inválido inteiro, inclusive propriedades extras.
        return choices_for(fields, "invalid", "invalid_output", result)
    evidence = {}
    for field in fields:
        raw = result.get(field)
        if field not in result:
            evidence[field] = choice("invalid", None, "missing_output")
        elif raw == c01.ABSTENTION:
            evidence[field] = choice("abstained", raw, "explicit")
        elif isinstance(raw, str) and raw in catalog[field]:
            evidence[field] = choice("predicted", raw)
        else:
            evidence[field] = choice("invalid", raw, "invalid_output")
    return evidence


class Adapter:
    def __init__(self, identity, run_id, instructions, transport=fake_gateway, budget=None, timeout_ms=5000):
        self.identity = identity
        self.run_id = run_id
        self.instructions = instructions
        self.transport = transport
        self.budget = budget
        self.timeout_ms = timeout_ms
        self.validation = c01.validators()

    def classify(self, item):
        started = time.monotonic()
        deadline = started + self.timeout_ms / 1000 - IPC_MARGIN_SECONDS
        c01.structure(self.validation, "input", item)
        fields, invalid, received = c01.normalize_input(item, item["catalog"])
        if not fields or invalid:
            raise ValueError("entrada inapta recebida no IPC")
        response = {}
        sent = False

        def dispatched():
            nonlocal sent
            sent = True

        obs = {"contract_version": VERSION, "id": item["id"], "run_id": self.run_id, "attempt": 1,
               "origin": "candidate", "identity": self.identity, "returned_model": None, "weights_revision": None,
               "temperature_state": "unknown",
               "elapsed_ms": None, "load_ms": None, "inference_ms": None}

        try:
            body = request_body(item, received, self.instructions, self.budget.max_tokens if self.budget else 128)
            if time.monotonic() >= deadline:
                raise TimeoutError
            if self.budget:
                self.budget.reserve(item["id"], len(body))
            status, data = self.transport(body, deadline, dispatched)
            parsed = parse_object(data)
            response = parsed or {}
            if time.monotonic() >= deadline:
                raise TimeoutError
            if status != 200:
                detail = "rate_limit (HTTP 429)" if status == 429 else f"HTTP {status}"
                print(f"Feita {item['id']}: {detail}", file=sys.stderr)
                evidence = choices_for(fields, "error", "transport")
            elif parsed is None:
                evidence = choices_for(fields, "invalid", "invalid_output")
            else:
                evidence = interpretation(response, fields, item["catalog"])
            if time.monotonic() >= deadline:
                raise TimeoutError
        except TimeoutError:
            evidence = choices_for(fields, "error", "timeout")
        except (OSError, EOFError):
            print(f"Feita {item['id']}: falha de transporte", file=sys.stderr)
            evidence = choices_for(fields, "error", "transport")
        except Blocked as error:
            print(f"Feita {item['id']}: {error}", file=sys.stderr)
            evidence = choices_for(fields, "error", "adapter_error")

        usage = []
        if sent:
            usage = [usage_from(response, self.budget.tariff if self.budget else PUBLIC_TARIFF,
                                self.budget.cost_unit if self.budget else None)]
            if self.budget:
                self.budget.observe(usage[0])
        obs.update(choices=evidence, requests=int(sent), questions=len(fields) if sent else 0, request_usage=usage,
                   returned_model=metadata(response.get("model")), weights_revision=metadata(response.get("weights_revision")))
        pins = (("expected_returned_model", "returned_model"), ("expected_weights_revision", "weights_revision"))
        pinned = [(self.identity[pin], obs[key]) for pin, key in pins if self.identity.get(pin) is not None]
        mismatch = any(actual is not None and actual != expected for expected, actual in pinned)
        missing_provenance = any(actual is None for _, actual in pinned)
        if mismatch:
            obs["choices"] = choices_for(fields, "error", "version_mismatch")
        elif missing_provenance:
            obs["choices"] = {field: value if value["status"] == "error" else choice("error", None, "adapter_error")
                              for field, value in evidence.items()}
        c01.structure(self.validation, "observation", obs)
        c01.verify_observation(obs, fields, {"run_id": self.run_id, "identity": self.identity,
                                            "injected_controls": {"ids": []}}, item["catalog"])
        return obs


def pilot_budget(args, scope, identity, has_credential):
    path = args.pilot
    if path is None or not args.pilot_sha256 or c01.digest(path) != args.pilot_sha256:
        raise Blocked("configuração de piloto sem hash correspondente")
    authorization = args.authorization
    if authorization is None or not args.authorization_sha256 or c01.digest(authorization) != args.authorization_sha256:
        raise Blocked("manifesto de autorização sem hash correspondente")
    protocol_path = c01.PLAN / "protocolo-comparacao.json"
    cap = authorized_cap(c01.read(authorization), scope=scope, identity=identity,
                         protocol_sha256=c01.digest(protocol_path), pilot_sha256=args.pilot_sha256)
    protocol = c01.read(protocol_path)
    settings = c01.read(path)
    split = c01.read(c01.PLAN / "divisao-dados.json")
    development = [case for cases in split["development"].values() for case in cases]
    policy = c01.read(c01.source_path(protocol["control_policy"]))
    controls = []
    with (c01.FIXTURES / "inputs.jsonl").open("rb") as stream:
        for line in stream:
            item = decode(line)
            if item["id"] not in policy["controls"] and item["catalog"]["version"] == "1.0.0":
                fields, invalid, _ = c01.normalize_input(item, item["catalog"])
                if fields and not invalid:
                    controls.append(item["id"])
    return Budget(settings, cap, development, controls, has_credential)


def atomic(path, payload):
    target = Path(path)
    temp = target.with_suffix(".tmp")
    temp.write_text(encode(payload), encoding="utf-8")
    temp.replace(target)


def main(*, synthetic_transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path)
    parser.add_argument("--pilot-sha256")
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--authorization-sha256")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    scope = "synthetic" if synthetic_transport is not None else "live"

    def has_credential():
        return scope == "synthetic" or bool(os.environ.get("FEITA_API_KEY", "").strip())

    try:
        if args.preflight:
            identity = c01.read(HERE / "real.json")["identity"]
            budget = pilot_budget(args, scope, identity, has_credential)
            print(encode({"state": "ready", "pilot_requests": len(budget.allowed),
                          "reservation_usd": str(len(budget.allowed) * budget.per_request)}))
            return
        identity = decode(os.environ["CLASSIFICATION_IDENTITY"])
        if identity["requested_model"] != MODEL or os.environ["CLASSIFICATION_CONTRACT_VERSION"] != VERSION:
            raise Blocked("identidade ou versão IPC incompatível")
        budget = pilot_budget(args, scope, identity, has_credential) if identity["mode"] == "real" else None
        if identity["mode"] not in ("real", "fixture") or (not budget and (args.pilot or args.authorization or synthetic_transport is not None)):
            raise Blocked("modo incompatível com a configuração")
        timeout = int(os.environ["CLASSIFICATION_TIMEOUT_MS"])
        if timeout != 5000:
            raise Blocked("prazo da C02 deve ser de 5 s")
        instructions = "\n\n".join(Path(os.environ[key]).read_text(encoding="utf-8")
                                     for key in ("CLASSIFICATION_PROMPT", "CLASSIFICATION_RUBRIC"))
        gateway = fake_gateway
        if budget:
            gateway = synthetic_transport if synthetic_transport is not None else FeitaTransport()
        adapter = Adapter(identity, os.environ["CLASSIFICATION_RUN_ID"], instructions, gateway, budget, timeout)
        atomic(os.environ["CLASSIFICATION_READY_FILE"], {"runtime": platform.python_version(),
                                                         "hardware": platform.machine()})
        for line in sys.stdin.buffer:
            print(encode(adapter.classify(decode(line))), flush=True)
        if os.environ.get("CLASSIFICATION_FINAL_FILE"):
            atomic(os.environ["CLASSIFICATION_FINAL_FILE"], {"peak_memory_bytes": None})
    except Blocked as error:
        parser.exit(2, f"C03 bloqueada: {error}\n")
    except (OSError, ValueError, KeyError, TypeError):
        parser.exit(2, "C03 falhou ao validar a configuração ou a mensagem IPC.\n")


if __name__ == "__main__":
    main()
