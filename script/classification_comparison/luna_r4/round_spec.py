"""Descritor fixo da instrução Luna R4, sobre o mesmo motor financeiro e IPC."""
from dataclasses import replace
from pathlib import Path

from luna.round_spec import LUNA, LunaSettings
from common import c01

HERE = Path(__file__).resolve().parent


class R4Settings(LunaSettings):
    scope = "c05-feita-luna-r4"
    pending_example = HERE / "config-real-exemplo.json"


LUNA_R4 = replace(LUNA, profile=c01.get_profile(c01.LUNA_R4), scope=R4Settings.scope,
                  prefix="luna-r4-", entrypoint=HERE / "execute.py", settings_class=R4Settings,
                  execution_files=(*LUNA.execution_files, HERE / "round_spec.py", HERE / "execute.py"))
