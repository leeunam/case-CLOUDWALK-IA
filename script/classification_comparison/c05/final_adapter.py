"""Processo Qwen C05 com o IPC 1.1 da C02 e evidência financeira fora do IPC."""
import argparse
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sys
import time

sys.dont_write_bytecode = True
from budget import BudgetError, usd
from settings import MAX_TOKENS, REASONING, USD_PER_CREDIT, Plan, account_from_args, resolve_account
from adapters.qwen.adapter import Adapter, atomic, integer, numeric_cost
from adapters.qwen.fixture import fake_gateway
from adapters.qwen.transport import FeitaTransport
from common import c01, decode, encode


def fixture_gateway(body, deadline, dispatched):
    status, raw = fake_gateway(body, deadline, dispatched)
    response = decode(raw)
    response["usage"] = {"prompt_tokens": 1000, "completion_tokens": 20,
                         "cost": "0.000547", "cost_unit": "USD"}
    return status, encode(response).encode("utf-8")


class RequestBudget:
    max_tokens = MAX_TOKENS
    reasoning = REASONING
    cost_unit = None  # O float do IPC nunca autoriza a liberação da reserva.

    def __init__(self, account, plan):
        self.account = account
        self.run_id = plan.report["run_id"]
        self.settings = plan.settings.data
        self.tariff = self.settings["tariff"]

    def reserve(self, case_id, body_size):
        if body_size > self.settings["billable_input_token_ceiling"]:
            raise BudgetError("tamanho local da requisição acima do limite de entrada declarado")
        self.account.mark_dispatched(self.run_id, case_id)

    def observe(self, usage):
        # A observação usada para conciliar vem da resposta original, após o Adapter.
        pass


@dataclass
class GatewayUsage:
    amount: Decimal | None = None
    receipt: str | None = None
    violation: str | None = None
    pending: Decimal | None = None
    evidence: dict = field(default_factory=dict)


def nonnegative_decimal(raw):
    if type(raw) is int:
        raw = str(raw)
    if not isinstance(raw, (str, Decimal)):
        return None
    try:
        amount = Decimal(raw)
    except InvalidOperation:
        return None
    return amount if amount.is_finite() and amount >= 0 else None


def observed_cost(raw, settings, run_id, case_id, reservation):
    result = GatewayUsage()
    try:
        response = json.loads(raw, parse_float=Decimal, object_pairs_hook=c01.unique_properties,
                              parse_constant=c01.reject_constant)
    except (ValueError, RecursionError):
        return result
    usage = response.get("usage") if isinstance(response, dict) else None
    if not isinstance(usage, dict):
        return result
    violations = []
    for field, limit in (("prompt_tokens", "billable_input_token_ceiling"),
                         ("completion_tokens", "billable_output_token_ceiling")):
        count = integer(usage.get(field))
        if count is not None and count > settings[limit]:
            violations.append(f"{field}={count} acima do teto faturável {settings[limit]}")

    # Só o uso atribuído à resposta corrente, com unidade documentada, concilia.
    candidates = {}
    if (settings["usage_cost_unit"] == "USD" and usage.get("cost_unit", "USD") == "USD"
            and usage.get("currency", "USD") == "USD"):
        observed = nonnegative_decimal(usage.get("cost"))
        if observed is not None:
            candidates["cost_usd"] = observed

    conversion = settings["usage_credits"]
    if conversion and conversion["confirmed"] and usage.get("credits_unit", "credits") == "credits":
        credits = nonnegative_decimal(usage.get("credits"))
        if credits is not None:
            result.evidence["credits"] = str(credits)
            components = credits.as_tuple()
            # Deslocamento decimal exato para a taxa documentada de US$ 0,01 por crédito.
            try:
                converted = Decimal((components.sign, components.digits,
                                     components.exponent + USD_PER_CREDIT.as_tuple().exponent))
            except InvalidOperation:
                converted = None
                # Se o expoente já era mínimo, a conversão positiva é menor que a unidade aceita.
                result.pending = Decimal("1e-30") if credits else None
            if converted is not None:
                candidates["converted_credits_usd"] = converted

    verified = []
    for name, candidate in candidates.items():
        result.evidence[name] = str(candidate)
        try:
            verified.append(usd(candidate))
        except BudgetError:
            if candidate > reservation:
                violations.append(f"custo USD {candidate} acima da reserva {reservation}")
    result.violation = ". ".join(violations) or None
    result.amount = max(verified, default=None)
    if candidates or result.pending is not None:
        possible = [*candidates.values()]
        if result.pending is not None:
            possible.append(result.pending)
        highest = max(possible)
        result.pending = highest if result.amount is None or highest > result.amount else None
        request_id = response.get("id")
        if isinstance(request_id, str) and request_id.strip():
            result.receipt = f"gateway:{request_id.strip()}"
        else:
            result.receipt = f"gateway:{run_id}/{case_id}:{sha256(raw).hexdigest()}"
    return result


def serve(args, transport=None):
    run_id = os.environ["CLASSIFICATION_RUN_ID"]
    plan = Plan(args.mode, run_id, args.config)
    account = resolve_account(args, args.mode)
    _, manifest_sha, _ = plan.authorize(args.manifest, account, args.cap_usd, confirmed=True)
    if (manifest_sha != args.manifest_sha256
            or plan.identity != decode(os.environ["CLASSIFICATION_IDENTITY"])
            or os.environ["CLASSIFICATION_CONTRACT_VERSION"] != plan.report["ipc_contract_version"]):
        raise BudgetError("execução, versão ou manifesto divergente")
    if transport is not None and args.mode != "fixture":
        raise BudgetError("transporte customizado exige modo fixture")
    account.validate(args.cap_usd)
    account.activate(run_id, manifest_sha)
    instructions = "\n\n".join(c01.source_path(plan.report["sources"][key]).read_text(encoding="utf-8")
                                for key in ("prompt", "rubric"))
    gateway = transport or (fixture_gateway if args.mode == "fixture" else FeitaTransport())
    usage = None
    financial_deadline = None

    def capture(body, deadline, dispatched):
        nonlocal usage, financial_deadline
        financial_deadline = deadline
        sent = False

        def mark_sent():
            nonlocal sent
            sent = True
            dispatched()

        result = gateway(body, deadline, mark_sent)
        if sent:
            usage = observed_cost(result[1], budget.settings, run_id, case_id, plan.settings.reservation)
            account.stage(run_id, case_id, amount=usage.amount, evidence=usage.receipt,
                          violation=usage.violation, gateway_usage=usage.evidence, pending=usage.pending)
        return result

    budget = RequestBudget(account, plan)
    adapter = Adapter(plan.identity, run_id, instructions, capture, budget,
                      timeout_ms=int(os.environ["CLASSIFICATION_TIMEOUT_MS"]))
    atomic(os.environ["CLASSIFICATION_READY_FILE"], {"runtime": platform.python_version(),
                                                     "hardware": platform.machine()})
    for line in sys.stdin.buffer:
        item = decode(line)
        case_id = item["id"]
        if plan.candidates.get(case_id) != item:
            raise BudgetError("caso ou conteúdo fora da projeção final autorizada")
        usage = None
        financial_deadline = None
        observation = adapter.classify(item)
        # O motivo canônico pode priorizar divergência de versão sobre o prazo.
        if financial_deadline is not None and time.monotonic() >= financial_deadline:
            account.mark_expired(run_id, case_id)
        if usage is not None:
            observation["request_usage"][0]["observed_api_usd"] = numeric_cost(usage.amount)
        print(encode(observation), flush=True)
    final = os.environ.get("CLASSIFICATION_FINAL_FILE")
    if final:
        atomic(final, {"peak_memory_bytes": None})


def main(transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("real", "fixture"), required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    account_from_args(parser)
    args = parser.parse_args()
    try:
        serve(args, transport)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Adaptador C05 interrompido ({type(exc).__name__}): {exc}\n")


if __name__ == "__main__":
    main()
