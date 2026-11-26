"""Confere as fontes e os insumos antes de importar o runtime qualificado."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "docs/evidencias/c05/sf2"
CAPTURE = EVIDENCE / "qualificacao-01/execucao-02/avaliacao/capture-policy.json"
SELECTED = EVIDENCE / "revisao-01/selected-policy.json"
PINS_SHA = "a39450eec74c1d32915ec98f1510aecc11428281633ac9cd9cbb913d200e6897"
SCHEMA_SHA = "fa6ed7d05e3342f0e2c467c43c058854d78115ea1872a8d1ccac527481930ad3"


def authenticated(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("integridade divergente")
    return data


def sources():
    contracts = Path(os.environ.get("CLASSIFICATION_CONTRACT_DIR", ROOT / "docs/contratos/classification-http"))
    pins = json.loads(authenticated(contracts / "pins.json", PINS_SHA))
    schema = json.loads(authenticated(contracts / "v1.json", SCHEMA_SHA))
    for group in ("worker_files", "runtime_files"):
        for name, expected in pins[group].items():
            authenticated(ROOT / name, expected)
    return pins, schema


def load():
    pins, schema = sources()
    from jsonschema import Draft202012Validator
    from ..contracts.core import FIELDS
    from ..runtime_r1 import load_context
    from ..training.environment import check_pins, length
    from ..training.package import read_verified_package

    package = Path(os.environ["SETFIT_PACKAGE_DIR"])
    manifest, _ = read_verified_package(package, pins["package_sha256"])
    if check_pins() != manifest["versions"]:
        raise ValueError("ambiente diferente do pacote aprovado")
    context = load_context(CAPTURE.read_bytes(), SELECTED.read_bytes(), (package / "manifest.json").read_bytes())
    from transformers import AutoTokenizer

    tokenizers = {
        field: AutoTokenizer.from_pretrained(str(package / field / "body"), local_files_only=True,
                                              trust_remote_code=False)
        for field in FIELDS
    }
    def token_length(text, fields):
        return max(length(tokenizers[field], text) for field in fields)

    command = [sys.executable, "-B", "-m", "script.classification_comparison.setfit_sf2.adapter",
               "--package", str(package), "--package-sha256", pins["package_sha256"], "--policy", str(CAPTURE)]
    validator = Draft202012Validator({**schema, "$ref": "#/$defs/Request"})
    return command, validator, context, token_length
