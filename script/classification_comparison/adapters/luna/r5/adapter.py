"""Coordena uma única classificação Luna R5 pelo IPC de evidência."""
from functools import lru_cache
from pathlib import Path
import time

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from adapters.qwen.adapter import IPC_MARGIN_SECONDS, PUBLIC_TARIFF, Blocked, metadata, parse_object, rates, usage_from
from common import c01, encode

from .evidence import CRITERIA, POLICY_SHA256, POLICY_VERSION, QUOTE_LIMIT, build_audit, input_sha256, project_choices

HERE = Path(__file__).resolve().parent
MODEL = "openai/gpt-5.6-luna"
MAX_COMPLETION_TOKENS = 384
REASONING_EFFORT = "none"
ADAPTER_VERSION = "2.0.0"
PROFILE_VERSION = "1.0.0"
IPC_VERSION = "1.1.0"
PROVIDERS = {"real": "feita", "fixture": "simulador-c05-luna-r5"}
FIELD_KEYS = ("code", "criterion", "quote")


def identity_for(mode):
    return {"mode": mode, "provider": PROVIDERS[mode], "requested_model": MODEL, "expected_returned_model": MODEL,
            "adapter_version": ADAPTER_VERSION, "policy_version": POLICY_VERSION}


def request_body(item, received, instructions):
    fields = item["missing"]
    shape = {"type": "object", "required": fields, "additionalProperties": False, "properties": {
        field: {"type": "object", "required": list(FIELD_KEYS), "additionalProperties": False, "properties": {
            "code": {"type": "string", "enum": [*item["catalog"][field], c01.ABSTENTION]},
            "criterion": {"type": "string", "enum": list(CRITERIA[field])},
            "quote": {"type": "string", "maxLength": QUOTE_LIMIT},
        }} for field in fields
    }}
    context = {key: item[key] for key in ("text", "brand", "catalog", "missing")}
    context["received"] = received
    payload = {
        "model": MODEL, "reasoning_effort": REASONING_EFFORT,
        "max_completion_tokens": MAX_COMPLETION_TOKENS, "stream": False,
        "messages": [{"role": "system", "content": instructions}, {"role": "user", "content": encode(context)}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "classificacao_com_evidencia", "strict": True, "schema": shape,
        }},
    }
    return encode(payload).encode("utf-8")


@lru_cache(maxsize=1)
def local_validators():
    # Só esquemas IPC e o esquema R5 entram no registro local.
    schemas = {name: c01.read(c01.CONTRACTS / f"{name}.schema.json")
               for name in ("common", "input", "observation")}
    schemas["envelope"] = c01.read(HERE / "evidence-envelope.schema.json")
    registry = Registry()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return {name: Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
            for name, schema in schemas.items() if name != "common"}


def validate_envelope(envelope):
    """Valida o envelope R5 e o schema IPC 1.1.0 nele referenciado."""
    c01.structure(local_validators(), "envelope", envelope)


def verify_observation(item, observation, run_id):
    mode = observation["identity"].get("mode")
    if (mode not in PROVIDERS or observation["identity"] != identity_for(mode)
            or observation["contract_version"] != IPC_VERSION or observation["requests"] > 1
            or observation["questions"] != observation["requests"] * len(item["missing"])):
        raise ValueError("observação incompatível com a candidata Luna R5")
    c01.verify_observation(observation, item["missing"],
                           {"run_id": run_id, "identity": identity_for(mode), "injected_controls": {"ids": []}},
                           item["catalog"])


def replay_envelope(item, envelope, *, policy_sha256=None):
    """Compara auditoria e escolhas com o replay local e devolve a auditoria recalculada."""
    c01.structure(local_validators(), "input", item)
    fields, invalid, _ = c01.normalize_input(item, item["catalog"])
    if not fields or invalid:
        raise ValueError("entrada inapta recebida no replay Luna R5")
    validate_envelope(envelope)
    observation, audit = envelope["observation"], envelope["audit"]
    if observation["id"] != item["id"]:
        raise ValueError("identificador incompatível com a entrada Luna R5")
    verify_observation(item, observation, observation["run_id"])
    error_reasons = {choice["reason"] for choice in observation["choices"].values() if choice["status"] == "error"}
    if error_reasons and (len(error_reasons) != 1 or any(choice["status"] != "error"
                                                        for choice in observation["choices"].values())):
        raise ValueError("erro técnico deve abranger todos os campos solicitados")
    failure, = error_reasons or {None}
    if policy_sha256 is not None and policy_sha256 != POLICY_SHA256:
        raise ValueError("hash da política congelada diverge dos bytes da Luna R5")
    rebuilt = build_audit(item, audit["raw_content"], audit["finish_reason"], refusal=audit["refusal"],
                          error=failure)
    if audit != rebuilt or observation["choices"] != project_choices(rebuilt):
        raise ValueError("evidência Luna R5 incompatível com o replay")
    return rebuilt


def completion_metadata(response):
    candidates = response.get("choices")
    first, = candidates if isinstance(candidates, list) and len(candidates) == 1 else (None,)
    first = first if isinstance(first, dict) else {}
    message = first.get("message")
    message = message if isinstance(message, dict) else {}
    content = message.get("content")
    return (content if isinstance(content, str) else None,
            metadata(first.get("finish_reason")), metadata(message.get("refusal")))


class R5Adapter:
    def __init__(self, identity, run_id, instructions, transport, budget=None, timeout_ms=5000, *,
                 clock=time.monotonic):
        mode = identity.get("mode")
        if mode not in PROVIDERS or identity != identity_for(mode):
            raise ValueError("identidade incompatível com a candidata Luna R5")
        if mode == "real" and budget is None:
            raise ValueError("candidata Luna R5 real exige orçamento")
        if timeout_ms <= IPC_MARGIN_SECONDS * 1000:
            raise ValueError("prazo Luna R5 deve incluir margem do IPC")
        self.identity = identity_for(mode)
        self.run_id = run_id
        self.instructions = instructions
        self.transport = transport
        self.budget = budget
        self.timeout_ms = timeout_ms
        self.clock = clock
        self._closed = False
        local_validators()

    def _validate_budget(self):
        budget = self.budget
        if budget is None:
            if self.identity["mode"] == "real":
                raise ValueError("candidata Luna R5 real exige orçamento")
            return
        if not budget or not all(callable(getattr(budget, name, None)) for name in ("reserve", "observe")):
            raise ValueError("orçamento Luna R5 exige reserva e registro de uso")
        if not all(hasattr(budget, name) for name in ("max_tokens", "cost_unit", "tariff")):
            raise ValueError("orçamento Luna R5 sem os atributos exigidos pelo adaptador")
        if type(budget.max_tokens) is not int or budget.max_tokens != MAX_COMPLETION_TOKENS:
            raise ValueError("orçamento Luna R5 exige limite solicitado de 384 tokens")
        if budget.cost_unit not in (None, "USD"):
            raise ValueError("orçamento Luna R5 exige custo em USD ou unidade indisponível")
        rates(budget.tariff)

    def close(self):
        if not self._closed:
            self._closed = True
            close = getattr(self.transport, "close", None)
            if close is not None:
                close()

    def classify(self, item):
        if self._closed:
            raise ConnectionError("sessão Luna R5 encerrada")
        try:
            deadline = self.clock() + self.timeout_ms / 1000 - IPC_MARGIN_SECONDS
            self._validate_budget()
            c01.structure(local_validators(), "input", item)
            fields, invalid, received = c01.normalize_input(item, item["catalog"])
            if not fields or invalid:
                raise ValueError("entrada inapta recebida no IPC")
            # Valida a representação UTF-8 canônica antes de reservar ou despachar.
            input_sha256(item)
            envelope = self._classify(item, received, deadline)
            if any(choice["status"] in ("invalid", "error") for choice in envelope["observation"]["choices"].values()):
                self.close()
            return envelope
        except BaseException:
            self.close()
            raise

    def _classify(self, item, received, deadline):
        sent = False
        response = {}
        failure = None

        def dispatched():
            nonlocal sent
            if sent:
                raise ConnectionError("segundo despacho Luna R5")
            sent = True

        try:
            body = request_body(item, received, self.instructions)
            if self.clock() >= deadline:
                raise TimeoutError
            if self.budget is not None:
                self.budget.reserve(item["id"], len(body))
            if self.clock() >= deadline:
                raise TimeoutError
            status, raw = self.transport(body, deadline, dispatched)
            if not sent:
                raise ConnectionError("resposta Luna R5 sem despacho")
            response = parse_object(raw) or {}
            if status != 200:
                failure = "transport"
        except TimeoutError:
            failure = "timeout"
        except (OSError, EOFError):
            failure = "transport"
        except Blocked:
            failure = "adapter_error"

        usage = []
        if sent:
            if self.budget is None:
                metered = usage_from(response, PUBLIC_TARIFF, None)
                metered.update(estimated_api_usd=None, tariff=None)
            else:
                metered = usage_from(response, self.budget.tariff, self.budget.cost_unit)
                self.budget.observe(metered)
            usage.append(metered)

        returned = metadata(response.get("model"))
        raw_content, finish_reason, refusal = completion_metadata(response)
        if self.clock() >= deadline:
            failure = "timeout"
        if returned is not None and returned != MODEL:
            failure = "version_mismatch"
        elif returned is None and failure is None:
            failure = "adapter_error"

        observation = {
            "contract_version": IPC_VERSION, "id": item["id"], "run_id": self.run_id, "attempt": 1,
            "origin": "candidate", "identity": self.identity.copy(), "returned_model": returned,
            "weights_revision": metadata(response.get("weights_revision")), "temperature_state": "unknown",
            "elapsed_ms": None, "load_ms": None, "inference_ms": None, "requests": int(sent),
            "questions": len(item["missing"]) if sent else 0, "request_usage": usage,
        }

        def envelope_with(error):
            audit = build_audit(item, raw_content, finish_reason, refusal=refusal, error=error)
            checked = dict(observation, choices=project_choices(audit))
            envelope = {"profile_version": PROFILE_VERSION, "observation": checked, "audit": audit}
            validate_envelope(envelope)
            verify_observation(item, checked, self.run_id)
            return envelope

        envelope = envelope_with(failure)
        if failure not in ("timeout", "version_mismatch") and self.clock() >= deadline:
            return envelope_with("timeout")
        return envelope
