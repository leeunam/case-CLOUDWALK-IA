"""Preflight financeiro e reserva cumulativa para um lote piloto."""
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path


HERE = Path(__file__).resolve().parent
PUBLIC_TARIFF = json.loads((HERE / "tarifas-publicas.json").read_text(encoding="utf-8"))


class Blocked(ValueError):
    pass


def money(value):
    try:
        amount = Decimal(str(value))
        if amount.is_finite() and amount >= 0:
            return amount
    except (InvalidOperation, ValueError):
        pass
    return None


def rates(tariff):
    if not isinstance(tariff, dict) or tariff.get("unit") != "USD/Mtoken":
        raise Blocked("tarifa USD/Mtoken indisponível")
    try:
        if not isinstance(tariff["source"], str) or not tariff["source"].strip():
            raise ValueError
        date.fromisoformat(tariff["date"])
    except (KeyError, TypeError, ValueError):
        raise Blocked("tarifa sem fonte e data válidas") from None
    values = {name: money(tariff.get(name)) for name in ("input", "output", "cache_read", "cache_write")}
    if any(value is None for value in values.values()):
        raise Blocked("tarifa por tipo de token indisponível")
    return values


def identity_digest(identity):
    content = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return sha256(content.encode("utf-8")).hexdigest()


def authorized_cap(manifest, *, scope, identity, protocol_sha256, pilot_sha256):
    if not isinstance(manifest, dict) or manifest.get("authorized") is not True:
        raise Blocked("manifesto sem autorização de execução")
    bindings = {"scope": scope, "model": identity["requested_model"], "model_identity_sha256": identity_digest(identity),
                "protocol_sha256": protocol_sha256, "pilot_sha256": pilot_sha256}
    if any(manifest.get(field) != expected for field, expected in bindings.items()):
        raise Blocked("manifesto incompatível com escopo, modelo, protocolo ou piloto")
    cap = money(manifest.get("budget_cap_usd"))
    if cap is None or cap <= 0:
        raise Blocked("manifesto sem teto positivo")
    return cap


class Budget:
    def __init__(self, settings, cap, development_ids, control_ids, has_credential):
        self.cap = money(settings.get("budget_usd"))
        if cap is None or self.cap is None or not 0 < self.cap <= cap:
            raise Blocked("teto ausente ou acima do orçamento autorizado")
        if settings.get("tariff_verified") is not True:
            raise Blocked("tarifa da conta ainda não confirmada")
        self.tariff = settings.get("tariff")
        price = rates(self.tariff)
        integers = ("development_cases", "max_cases", "max_requests", "max_tokens", "input_token_ceiling", "concurrency")
        if any(type(settings.get(key)) is not int or settings[key] < 1 for key in integers):
            raise Blocked("limites do piloto ausentes ou inválidos")
        count = settings["development_cases"]
        if not 1 <= count <= len(development_ids) or settings["concurrency"] != 1:
            raise Blocked("piloto exige desenvolvimento e concorrência 1")
        if settings.get("token_limits_confirmed") is not True:
            raise Blocked("limites de tokens cobrados pelo gateway ainda não confirmados")
        self.allowed = set(development_ids[:count]) | set(control_ids)
        self.max_cases = settings["max_cases"]
        self.max_requests = settings["max_requests"]
        self.max_tokens = settings["max_tokens"]
        self.input_ceiling = settings["input_token_ceiling"]
        # Reserva o pior caso, incluindo eventual cobrança adicional de cache.
        self.per_request = (
            self.input_ceiling * (price["input"] + price["cache_read"] + price["cache_write"])
            + self.max_tokens * price["output"]
        ) / 1_000_000
        if (len(self.allowed) > min(self.max_cases, self.max_requests)
                or len(self.allowed) * self.per_request > self.cap):
            raise Blocked("reserva prevista do piloto excede os limites")
        self.cost_unit = settings.get("usage_cost_unit")
        if self.cost_unit not in (None, "USD"):
            raise Blocked("unidade de usage.cost incompatível")
        # A primeira inspeção do ambiente ocorre após todos os gates anteriores.
        if not has_credential():
            raise Blocked("credencial local Feita ausente")
        self.seen = set()
        self.requests = 0
        self.reserved = Decimal(0)
        self.stopped = False

    def reserve(self, case_id, body_size):
        if self.stopped or case_id not in self.allowed or case_id in self.seen or len(self.seen) >= self.max_cases:
            raise Blocked("caso fora do piloto autorizado ou já despachado")
        self.seen.add(case_id)
        if body_size > self.input_ceiling:
            raise Blocked("requisição excede o limite local de tamanho")
        if self.requests >= self.max_requests or self.reserved + self.per_request > self.cap:
            raise Blocked("reserva excede os limites de requisições ou orçamento")
        # Mesmo um timeout pode ser faturado. A reserva não é devolvida.
        self.requests += 1
        self.reserved += self.per_request

    def observe(self, usage):
        observed = money(usage["observed_api_usd"])
        self.stopped = (observed is not None and observed > self.per_request) or any(
            usage[field] is not None and usage[field] > limit
            for field, limit in (("input_tokens", self.input_ceiling), ("output_tokens", self.max_tokens))
        )
