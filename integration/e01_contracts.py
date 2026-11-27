"""Leitura dos contratos privados e de objetos JSON do piloto."""

import json
import math
import os
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def _reject_number(_value):
    raise ValueError("non_finite_json_number")


def _finite_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        _reject_number(value)
    return parsed


def _unique_fields(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate_json_field")
        result[key] = value
    return result


def read_json_object(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    value = json.loads(raw, object_pairs_hook=_unique_fields,
                       parse_constant=_reject_number, parse_float=_finite_float)
    if not isinstance(value, dict):
        raise ValueError("expected_json_object")
    return value


def read_private_schema(name):
    default = Path(__file__).resolve().parents[1] / "contracts/agent-pilot"
    directory = Path(os.environ.get("E01_CONTRACT_DIR", default))
    return read_json_object((directory / f"{name}.schema.json").read_bytes())


def validator(schema, fragment=None):
    if fragment is not None:
        schema = {"$defs": schema["$defs"], "$ref": "#/$defs/" + fragment}
    return Draft202012Validator(schema, format_checker=FormatChecker())
