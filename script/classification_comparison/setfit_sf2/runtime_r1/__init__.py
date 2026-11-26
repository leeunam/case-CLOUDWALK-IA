"""Decisão SF2-R1 sobre uma linha original da coleta."""
from .context import load_context
from .decision import derive, verify

__all__ = ["load_context", "derive", "verify"]
