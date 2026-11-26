"""Captura financeira opcional do POST à Feita, sem armazenar a conversa."""

import hashlib
import json
import os
import re
import stat
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


_SAFE_ID = re.compile(r"[A-Za-z0-9_./:-]{1,180}")
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_USAGE_FIELDS = {
    "prompt_tokens", "completion_tokens", "total_tokens", "cost", "credits",
    "input_tokens", "output_tokens", "cached_tokens", "cache_read_input_tokens",
    "cache_creation_input_tokens", "cache_write_input_tokens", "reasoning_tokens",
}
_DETAILS_FIELDS = {
    "prompt_tokens_details": {"cached_tokens", "cache_write_tokens", "cache_creation_tokens",
                              "cache_read_input_tokens", "cache_write_input_tokens", "cache_creation_input_tokens"},
    "completion_tokens_details": {"reasoning_tokens"},
}


class _RawNumber(str):
    """Conserva a representação decimal da resposta JSON sem arredondar."""


def _safe_identifier(value):
    return value if type(value) is str and _SAFE_ID.fullmatch(value) else None


def _numbers(value, allowed):
    if not isinstance(value, dict):
        return {}
    return {key: item for key, item in value.items() if key in allowed and (
        item is None or (type(item) in {str, _RawNumber} and len(item) <= 80 and _DECIMAL.fullmatch(item))
    )}


def _response_fields(raw):
    try:
        response = json.loads(raw, parse_float=_RawNumber, parse_int=_RawNumber)
    except (TypeError, ValueError, RecursionError):
        response = None
    if not isinstance(response, dict):
        response = {}
    usage = response.get("usage")
    cleaned = None
    if isinstance(usage, dict):
        cleaned = _numbers(usage, _USAGE_FIELDS)
        unit = usage.get("cost_unit")
        if type(unit) is str and unit in {"USD", "usd", "CREDITS", "credits"}:
            cleaned["cost_unit"] = unit
        invalid = [field for field in ("cost", "credits", "cost_unit")
                   if field in usage and cleaned.get(field) is None]
        if invalid:
            cleaned["invalid_fields"] = invalid
        for key, allowed in _DETAILS_FIELDS.items():
            if key in usage:
                cleaned[key] = _numbers(usage[key], allowed) if isinstance(usage[key], dict) else None
    return {"id": _safe_identifier(response.get("id")), "model": _safe_identifier(response.get("model")),
            "usage": cleaned}


def _encode(value):
    if isinstance(value, dict):
        return "{" + ",".join(f"{json.dumps(key)}:{_encode(item)}" for key, item in value.items()) + "}"
    if isinstance(value, _RawNumber):
        return value
    return json.dumps(value, allow_nan=False)


class AuditedPost:
    def __init__(self, post, directory):
        self._post = post
        self._directory = Path(directory)
        try:
            info = self._directory.lstat()
            if (not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700
                    or info.st_uid != os.geteuid() or not os.access(self._directory, os.W_OK | os.X_OK)):
                raise PermissionError
        except OSError:
            raise ValueError("CLOUDWALK_E01_AUDIT_DIR exige diretório dedicado ao consumidor, modo 0700.") from None

    def __call__(self, path, headers, body, *, deadline):
        started_at = datetime.now(timezone.utc).isoformat()
        started = time.monotonic()
        status, raw = None, None
        try:
            status, raw = self._post(path, headers, body, deadline=deadline)
            return status, raw
        finally:
            self._save({
                "status": status if type(status) is int else None,
                "started_at": started_at, "finished_at": datetime.now(timezone.utc).isoformat(),
                "duration_ms": round((time.monotonic() - started) * 1000, 3),
                "request_sha256": hashlib.sha256(body).hexdigest(), **_response_fields(raw),
            })

    def _save(self, receipt):
        receipt_path = self._directory / f"receipt-{uuid.uuid4()}.json"
        with tempfile.NamedTemporaryFile(dir=self._directory, prefix=".receipt-", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            try:
                temporary.write((_encode(receipt) + "\n").encode("ascii"))
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path.replace(receipt_path)
            finally:
                temporary_path.unlink(missing_ok=True)
        directory_fd = os.open(self._directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
