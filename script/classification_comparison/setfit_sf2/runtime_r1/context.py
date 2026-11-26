"""Identidades e configurações usadas pelo runtime da candidata fixa."""
from functools import lru_cache
from hashlib import sha256
import json

from ..contracts import core, ipc
from ..contracts.core import FIELDS, PLAN, decode, require


def digest(data):
    return sha256(data).hexdigest()


def verified_json(data, expected, role):
    require(type(data) is bytes and digest(data) == expected, "SHA-256 divergente: " + role)
    return decode(data.decode("utf-8"))


@lru_cache
def _snapshot(path):
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ValueError(f"recurso indisponível: {path.name}") from exc


def protocol():
    return verified_json(_snapshot(PLAN / "sf2-final-r1-protocolo.json"),
                         "29605e3db4d5f6e9201fd1905dca181412755df2ac9d7b55baccd8d2ff819d1d",
                         "protocolo R1")


def schema():
    # Cada validador recebe um objeto novo, decodificado dos bytes autenticados.
    return verified_json(_snapshot(PLAN / "sf2-final-r1.schema.json"),
                         "c266b49c678685515b88f7635334a888be85104ad6e767078040f0937d3a10b9",
                         "schema R1")


def encoded(value):
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError("valor JSON inválido") from exc


def same_json(left, right):
    """Recusa conversões implícitas de Python, inclusive em valores livres do canal."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (left.keys() == right.keys()
                and all(type(k) is str and same_json(left[k], right[k]) for k in left))
    if type(left) is list:
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return type(left) in (str, int, float, bool, type(None)) and encoded(left) == encoded(right)


def check_originals(kinds):
    anchors = protocol()["anchors_sha256"]
    original = verified_json(_snapshot(PLAN / "protocolo.json"), anchors["protocol_original"], "protocolo IPC")
    catalog = original["sources"]["catalog"]
    original_catalog = verified_json(_snapshot(core.ROOT / catalog["path"]), catalog["sha256"], "catálogo")
    for module in (core, ipc):
        require(encoded(module.PROTOCOL) == encoded(original) and encoded(module.CATALOG) == encoded(original_catalog),
                "protocolo ou catálogo IPC carregado divergente")
    original_schema = verified_json(_snapshot(PLAN / "contratos/sf2.schema.json"),
                                    anchors["schema_original"], "schema IPC")
    for kind in kinds:
        expected = {**original_schema, "$ref": "#/$defs/" + kind}
        require(encoded(core.validator(kind).schema) == encoded(expected), "schema IPC carregado divergente")


def _policy(candidate):
    # Os buffers de políticas publicados representam todos os cortes como floats.
    return {"contract_version": candidate["namespace"], **{
        field: {key: float(number) for key, number in candidate[field].items()} for field in FIELDS}}


def check_context(context):
    candidate = protocol()["candidate"]
    expected = {
        "capture_policy": _policy(candidate["capture"]), "selected_policy": _policy(candidate["selected"]),
        "capture_policy_sha256": candidate["capture"]["policy_sha256"],
        "selected_policy_sha256": candidate["selected"]["policy_sha256"],
        "package_sha256": candidate["package_sha256"], "model_sha256": candidate["model_sha256"],
        "class_order": candidate["class_order"],
    }
    require(same_json(context, expected), "contexto R1 divergente")
    return expected


def load_context(capture_policy: bytes, selected_policy: bytes, package_manifest: bytes) -> dict:
    candidate = protocol()["candidate"]
    capture = verified_json(capture_policy, candidate["capture"]["policy_sha256"], "política de coleta")
    selected = verified_json(selected_policy, candidate["selected"]["policy_sha256"], "política R1")
    model = verified_json(package_manifest, candidate["package_sha256"], "manifesto")
    check_originals(("modelManifest", "policy"))
    core.structure("modelManifest", model)
    core.structure("policy", capture)
    require(model["versions"]["python"] == "3.11.13", "versão Python do pacote divergente")
    return check_context(dict(capture_policy=capture, selected_policy=selected,
                              capture_policy_sha256=digest(capture_policy), selected_policy_sha256=digest(selected_policy),
                              package_sha256=digest(package_manifest), model_sha256=model["model_sha256"],
                              class_order=model["class_order"]))
