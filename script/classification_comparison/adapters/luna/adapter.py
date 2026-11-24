"""Candidata Luna fixa com IPC 1.1.0 e a política semântica da C05-R2."""
from adapters.qwen.adapter import Adapter, encode, structured_request
from adapters.qwen.pilot import rates

MODEL = "openai/gpt-5.6-luna"
MAX_COMPLETION_TOKENS = 128
REASONING_EFFORT = "none"
ADAPTER_VERSION = "1.0.0"
POLICY_VERSION = "1.1.0"
PROVIDERS = {"real": "feita", "fixture": "simulador-c05-luna"}


def request_body(item, received, instructions, _max_tokens, _reasoning):
    return encode({
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "stream": False,
        **structured_request(item, received, instructions),
    }).encode("utf-8")


class LunaAdapter(Adapter):
    def __init__(self, identity, run_id, instructions, transport, budget=None, timeout_ms=5000):
        mode = identity.get("mode")
        provider = PROVIDERS.get(mode)
        pins = {"mode": mode, "provider": provider, "requested_model": MODEL, "expected_returned_model": MODEL,
                "adapter_version": ADAPTER_VERSION, "policy_version": POLICY_VERSION}
        if provider is None or identity != pins:
            raise ValueError("identidade incompatível com a candidata Luna")
        if mode == "real" and budget is None:
            raise ValueError("candidata Luna real exige orçamento")
        super().__init__(pins, run_id, instructions, transport, budget, timeout_ms, body_builder=request_body)
        self._closed = False

    def classify(self, item):
        if self._closed:
            raise ConnectionError("sessão Luna encerrada")
        try:
            self._validate_budget()
            obs = super().classify(item)
            if self.budget is None:
                for usage in obs["request_usage"]:
                    usage.update(estimated_api_usd=None, tariff=None)
            if any(choice["status"] in ("error", "invalid") for choice in obs["choices"].values()):
                self.close()
            return obs
        except BaseException:
            self.close()
            raise

    def _validate_budget(self):
        budget = self.budget
        if budget is None:
            if self.identity["mode"] == "real":
                raise ValueError("candidata Luna real exige orçamento")
            return
        if not budget or not all(callable(getattr(budget, name, None)) for name in ("reserve", "observe")):
            raise ValueError("orçamento Luna exige operações de reserva e registro de uso")
        if not all(hasattr(budget, name) for name in ("max_tokens", "reasoning", "cost_unit", "tariff")):
            raise ValueError("orçamento Luna sem os atributos exigidos pelo adaptador")
        if type(budget.max_tokens) is not int or budget.max_tokens != MAX_COMPLETION_TOKENS:
            raise ValueError("orçamento Luna exige limite solicitado de 128 tokens")
        if budget.cost_unit not in (None, "USD"):
            raise ValueError("orçamento Luna exige custo em USD ou unidade indisponível")
        rates(budget.tariff)

    def close(self):
        if not self._closed:
            self._closed = True
            close = getattr(self.transport, "close", None)
            if close is not None:
                close()
