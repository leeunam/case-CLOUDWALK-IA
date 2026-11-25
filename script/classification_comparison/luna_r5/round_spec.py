"""Ponto de entrada e configuração fixos da Luna com evidência verificável."""
from dataclasses import replace
from pathlib import Path

from luna.round_spec import LUNA, LunaSettings
from common import c01
from adapters.luna.r5.adapter import MAX_COMPLETION_TOKENS, PROVIDERS, R5Adapter
from luna_r5.fixture_gateway import fixture_for

HERE = Path(__file__).resolve().parent


class R5Settings(LunaSettings):
    scope = "c05-feita-luna-r5"
    pending_example = HERE / "config-real-exemplo.json"

    @classmethod
    def valid_request(cls, data):
        return (type(data["max_completion_tokens"]) is int
                and data["max_completion_tokens"] == MAX_COMPLETION_TOKENS
                and data["reasoning_effort"] == "none" and data["stream"] is False
                and type(data["billable_output_token_ceiling"]) is int
                and data["billable_output_token_ceiling"] > MAX_COMPLETION_TOKENS)


LUNA_R5 = replace(LUNA, profile=c01.get_profile(c01.LUNA_R5), scope=R5Settings.scope,
                  prefix="luna-r5-", fixture_provider=PROVIDERS["fixture"], adapter=R5Adapter,
                  entrypoint=HERE / "execute.py", settings_class=R5Settings, fixture_for=fixture_for,
                  execution_files=(*LUNA.execution_files, *(HERE / name for name in
                                   ("round_spec.py", "execute.py", "fixture_gateway.py", "audit.py"))))
