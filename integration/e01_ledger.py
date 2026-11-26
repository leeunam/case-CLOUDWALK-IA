"""Cliente autenticado para o protocolo privado do ledger Rails da E01."""

import hmac
import math
import time
from urllib.parse import urlsplit
import uuid

if __package__:
    from .agent_flow import json_bytes
    from .e01_contracts import read_json_object, read_private_schema, validator
    from .e01_http import DeadlinePost
else:
    from agent_flow import json_bytes
    from e01_contracts import read_json_object, read_private_schema, validator
    from e01_http import DeadlinePost


HTTP_LIMIT = 128 * 1024
_OPERATIONS = ("claim", "start", "complete", "unknown", "published")
_ERROR_STATUS = {
    "unauthenticated": 401,
    "not_found": 404,
    "too_large": 413,
    "invalid_body": 422,
    "preflight_missing": 503,
    **dict.fromkeys(("nonce_reused", "request_mismatch", "lease_lost", "turn_stale", "busy",
                     "budget_exhausted", "pilot_paused", "result_mismatch", "invalid_state", "publication_pending"), 409),
}


class LedgerError(RuntimeError):
    def __init__(self, status, code):
        self.status = status
        self.code = code
        super().__init__(code)


def signed_headers(secret, path, body, *, timestamp, nonce):
    prefix = f"{timestamp}\n{nonce}\nPOST\n{path}\n".encode("ascii")
    signature = hmac.digest(secret.encode("utf-8"), prefix + body, "sha256").hex()
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-E01-Timestamp": timestamp,
        "X-E01-Nonce": nonce,
        "X-E01-Signature": signature,
    }


def canonical_uuid(value):
    try:
        return str(uuid.UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        return False


class LedgerClient:
    def __init__(self, base_url, secret, *, transport=None, timeout_s=2.0, now=time.time):
        try:
            url = urlsplit(base_url)
            port = url.port
        except (TypeError, ValueError):
            raise ValueError("invalid_ledger_url") from None
        if (url.scheme not in {"http", "https"} or not url.hostname or url.path not in {"", "/"}
                or url.username is not None or url.password is not None or "?" in base_url or "#" in base_url):
            raise ValueError("invalid_ledger_url")
        if not isinstance(secret, str) or not secret.strip():
            raise ValueError("invalid_ledger_credential")
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("invalid_ledger_timeout")
        self._secret = secret
        self._timeout = timeout_s
        self._now = now
        self._post = transport if transport is not None else DeadlinePost(
            url.hostname, port=port, tls=url.scheme == "https", response_limit=HTTP_LIMIT,
        )
        schema = read_private_schema("ledger")
        self._validators = {
            name: validator(schema, name)
            for name in (*_OPERATIONS, *(f"{op}_response" for op in _OPERATIONS), "error")
        }

    def claim(self, request_event_id, body):
        return self._exchange("claim", request_event_id, body)

    def start(self, request_event_id, body):
        return self._exchange("start", request_event_id, body)

    def complete(self, request_event_id, body):
        return self._exchange("complete", request_event_id, body)

    def unknown(self, request_event_id, body):
        return self._exchange("unknown", request_event_id, body)

    def published(self, request_event_id, body):
        return self._exchange("published", request_event_id, body)

    def _exchange(self, operation, request_event_id, body):
        if not canonical_uuid(request_event_id) or not self._validators[operation].is_valid(body):
            raise LedgerError(None, "invalid_ledger_request")
        try:
            raw = json_bytes(body)
        except (TypeError, ValueError):
            raise LedgerError(None, "invalid_ledger_request") from None
        if len(raw) > HTTP_LIMIT:
            raise LedgerError(None, "ledger_request_too_large")

        path = f"/internal/v1/e01/executions/{request_event_id}/{operation}"
        headers = signed_headers(self._secret, path, raw, timestamp=str(int(self._now())), nonce=str(uuid.uuid4()))
        deadline = time.monotonic() + self._timeout
        try:
            status, response = self._post(path, headers, raw, deadline=deadline)
            if time.monotonic() >= deadline:
                raise TimeoutError
            if type(status) is not int or not 100 <= status <= 599:
                raise ValueError
        except Exception:
            raise LedgerError(None, "ledger_transport") from None
        if 300 <= status < 400:
            raise LedgerError(status, "ledger_redirect")
        try:
            if len(response) > HTTP_LIMIT:
                raise ValueError
            document = read_json_object(response)
        except (TypeError, ValueError, RecursionError):
            raise LedgerError(status, "invalid_ledger_response") from None
        if status == 200:
            if not self._validators[f"{operation}_response"].is_valid(document):
                raise LedgerError(status, "invalid_ledger_response")
            return document
        if self._validators["error"].is_valid(document) and _ERROR_STATUS[document["error"]] == status:
            raise LedgerError(status, document["error"])
        raise LedgerError(status, "invalid_ledger_response")
