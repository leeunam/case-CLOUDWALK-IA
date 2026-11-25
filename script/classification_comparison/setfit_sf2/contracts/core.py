"""Contratos SF2. Apenas schemas locais e referências aprovadas."""
from decimal import Decimal
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[4]
PLAN = ROOT / "docs/planejamento/classificacao-comparativa/sf2"
SCHEMA_PATH = PLAN / "contratos/sf2.schema.json"
VERSION = "sf2-ipc/1.0"
FIELDS = ("category", "priority")
REVIEW = "informacao_insuficiente"


class ContractError(ValueError):
    """Violação de forma, semântica ou integridade."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def _unique(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, "JSON contém chave repetida")
        obj[key] = value
    return obj


def _finite(value):
    number = float(value)
    require(math.isfinite(number), "JSON contém número não finito")
    return number


def decode(text):
    return json.loads(text, object_pairs_hook=_unique, parse_constant=_finite, parse_float=_finite)


def read(path):
    return decode(Path(path).read_text(encoding="utf-8"))


def read_lines(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [decode(line) for line in stream]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_files(expected, paths):
    """O chamador fornece caminhos confiáveis; o JSON identifica apenas papéis."""
    require(expected.keys() == paths.keys(), "inventário de arquivos divergente")
    for role, digest in expected.items():
        require(sha256(paths[role]) == digest, f"SHA-256 divergente para {role}")


@lru_cache
def validator(kind):
    schema = read(SCHEMA_PATH)
    require(kind in schema["$defs"], "tipo de contrato desconhecido")
    return Draft202012Validator({**schema, "$ref": "#/$defs/" + kind})


def structure(kind, obj):
    # jsonschema aceita NaN em alguns limites; esta API também recebe dicts em memória.
    try:
        json.dumps(obj, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise ContractError("valor não representável em JSON") from exc
    error = next(validator(kind).iter_errors(obj), None)
    if error:
        location = ".".join(str(k) for k in error.absolute_path)
        raise ContractError(f"{kind}.{location}: restrição {error.validator}")


PROTOCOL = read(PLAN / "protocolo.json")
LABELS = {field: PROTOCOL["labels"][field] for field in FIELDS}
CATALOG = read(ROOT / PROTOCOL["sources"]["catalog"]["path"])


def verify_sources():
    verify_files({k: v["sha256"] for k, v in PROTOCOL["sources"].items()},
                 {k: ROOT / v["path"] for k, v in PROTOCOL["sources"].items()})


def channel(received, catalog):
    missing, invalid, valid = [], [], {}
    for field in FIELDS:
        value = received.get(field)
        if value is None or isinstance(value, str) and not value.strip():
            missing.append(field)
        elif isinstance(value, str) and value in catalog[field]:
            valid[field] = value
        else:
            invalid.append(field)
    return missing, invalid, valid


def decimal(value):
    return Decimal(str(value))
