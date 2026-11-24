"""Rodada D aprovada para preparação offline. O entry point fixa modelo e conta."""
import os
from pathlib import Path
import subprocess

from r2.plan import C02, EXECUTION_FILES, Round
from adapters.luna.adapter import LunaAdapter, MODEL
from adapters.luna.transport import LunaTransport
from budget import BudgetError, usd
from common import c01
from settings import PRICE_NAMES, Settings, read_pinned

HERE = Path(__file__).resolve().parent
SCOPE = "c05-feita-luna"
ACCOUNT_RELATIVE = Path(".worktrees/c05-comparacao/.superpowers/financial/c05-qwen/account-v4.sqlite3")
ACCOUNT_ID = "903a037b4b9140438e152ade172889ca"


def check_account(account):
    git_dir = subprocess.check_output(["rtk", "git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                      cwd=c01.ROOT, text=True).strip()
    approved = Path(git_dir).parent / ACCOUNT_RELATIVE
    if account.scope == "fixture":
        if account.path == approved or account.id == ACCOUNT_ID:
            raise BudgetError("fixture exige uma conta sintética separada")
        return
    if account.id != ACCOUNT_ID or account.path != approved or not approved.is_file():
        raise BudgetError("execução real exige a conta global existente e sua identidade explícita")


class LunaSettings(Settings):
    scope = SCOPE
    pending_example = HERE / "config-real-exemplo.json"
    request_keys = {"max_completion_tokens", "reasoning_effort", "stream"}
    extra_keys = {"financial_evidence"}
    real_minimum = (1_050_000, 128_000)

    @classmethod
    def valid_request(cls, data):
        return (type(data["max_completion_tokens"]) is int and data["max_completion_tokens"] == 128
                and data["reasoning_effort"] == "none" and data["stream"] is False)

    @classmethod
    def load(cls, path, mode, *, expected_scope=None):
        if expected_scope is None:
            expected_scope = cls.scope
        # Um exemplo pendente não possui preços nem uma reserva calculável.
        data, pin = read_pinned(path)
        if not isinstance(data, dict):
            raise BudgetError("configuração Luna exige objeto JSON")
        if mode == "real" and data.get("tariff") is None:
            if (data != c01.read(cls.pending_example) or data["scope"] != expected_scope
                    or data["billable_limits_confirmed"] is not False or data["tariff_verified"] is not False):
                raise BudgetError("tarifa real ou evidência financeira pendente")
            return cls(data, pin, None)
        result = cls.from_pinned(data, pin, mode, expected_scope)
        if mode == "fixture" and result.data["financial_evidence"] is not None:
            raise BudgetError("fixture deve usar valores sintéticos")
        if mode == "real":
            result.verify_evidence()
        return result

    def verify_execution(self):
        super().verify_execution()
        if self.data["mode"] == "real" and (self.data["usage_cost_unit"] != "USD"
                and not (self.data["usage_credits"] or {}).get("confirmed")):
            raise BudgetError("uso real exige unidade USD ou conversão documentada de créditos")

    def verify_evidence(self):
        data = self.data
        pin = data["financial_evidence"]
        if not isinstance(pin, dict) or set(pin) != {"path", "sha256"}:
            raise BudgetError("evidência financeira real exige arquivo e SHA-256")
        evidence = c01.read(c01.source_path(pin))
        # Os valores usados para reservar precisam cobrir cada faixa publicada.
        if (not isinstance(evidence, dict) or evidence.get("provider") != "feita" or evidence.get("model") != MODEL
                or evidence.get("date") != data["tariff"]["date"]
                or evidence.get("limits") != [data["billable_input_token_ceiling"], data["billable_output_token_ceiling"]]
                or evidence.get("unit") != "USD/Mtoken"
                or set(evidence.get("tiers", {})) != {"standard", "long_context"}):
            raise BudgetError("evidência não sustenta modelo, limites ou faixas de tarifa")
        for tier in evidence["tiers"].values():
            if (not isinstance(tier, dict) or set(tier) != set(PRICE_NAMES)
                    or any(usd(tier[k]) > usd(data["tariff"][k]) for k in PRICE_NAMES)):
                raise BudgetError("tarifa não cobre a maior faixa ou cache")
        if (data["usage_cost_unit"] != evidence.get("usage_cost_unit")
                or data["usage_credits"] != evidence.get("usage_credits")):
            raise BudgetError("unidade/conversão não sustentada pela evidência")
        sources = evidence.get("sources")
        required = {"route", "limits", "tariff"}
        if data["usage_cost_unit"] or data["usage_credits"]:
            required.add("usage")
        if not isinstance(sources, dict) or set(sources) != required:
            raise BudgetError("fontes financeiras incompletas")
        for kind, source in sources.items():
            origins = ("https://feita.ai/", "https://docs.feita.ai/")
            if kind == "limits":
                origins += ("https://developers.openai.com/",)
            if (not isinstance(source, dict) or set(source) != {"url", "snapshot"}
                    or not isinstance(source["url"], str) or not source["url"].startswith(origins)
                    or not c01.source_path(source["snapshot"]).read_bytes().strip()):
                raise BudgetError(f"fonte financeira inválida para {kind}")
        if (data["tariff"]["source"] != sources["tariff"]["url"]
                or data["billable_limits_reference"] != sources["limits"]["url"]
                or data["usage_cost_unit"] and data["usage_cost_reference"] != sources["usage"]["url"]
                or data["usage_credits"] and data["usage_credits"]["reference"] != sources["usage"]["url"]):
            raise BudgetError("referências da configuração divergentes das fontes verificadas")


def live_gateway():
    return LunaTransport(os.environ["FEITA_API_KEY"])


LUNA = Round(c01.get_profile(c01.LUNA), SCOPE, "luna-", c01.LUNA_FIXTURE_PROVIDER, HERE / "execute.py",
             LunaSettings, (*EXECUTION_FILES, HERE / "round_spec.py", HERE / "execute.py",
                            C02 / "adapters/luna/adapter.py", C02 / "adapters/luna/transport.py"),
             check_account=check_account, adapter=LunaAdapter, live_gateway=live_gateway, stop_on_error=True)
