"""Consome um pedido E01 usando o ledger como autoridade sobre despacho e replay."""

import base64
from datetime import datetime
import hashlib
import math
import time
import uuid

if __package__:
    from .agent_flow import EVENTS, json_bytes, require_key, validate_history
    from .e01_backend import InferenceFailure, POLICY_VERSION, valid_usage, validate_context
    from .e01_contracts import read_json_object
    from .e01_knowledge import HANDOFF_TEXT, RESOLVE_TEXT
    from .e01_ledger import LedgerError, canonical_uuid
else:
    from agent_flow import EVENTS, json_bytes, require_key, validate_history
    from e01_backend import InferenceFailure, POLICY_VERSION, valid_usage, validate_context
    from e01_contracts import read_json_object
    from e01_knowledge import HANDOFF_TEXT, RESOLVE_TEXT
    from e01_ledger import LedgerError, canonical_uuid


RESULT_LIMIT = 64 * 1024
_RESULT_FIELDS = ("occurred_at", "correlation_id", "case_id", "brand_id", "assignment_generation", "turn_id")
_TERMINAL = {"published", "unknown", "failed", "discarded"}
_OBSERVE_AGAIN = {"busy", "publication_pending", "lease_lost", "nonce_reused", "ledger_transport"}
_UNKNOWN_REASONS = {"transport_ambiguous", "usage_missing", "usage_invalid", "dispatch_uncertain"}
_FAILED_REASONS = {"invalid_decision", "invalid_result", "provider_rejected"}


class ExecutorError(RuntimeError):
    """Falha para o consumidor decidir se adia ou registra o offset."""

    def __init__(self, code, *, retryable=False):
        self.code = code
        self.retryable = retryable
        super().__init__(code)


def _may_observe_again(error):
    return (error.code in _OBSERVE_AGAIN
            or (error.code == "invalid_ledger_response" and error.status == 200)
            or (error.status is not None and 500 <= error.status <= 599 and error.code != "preflight_missing"))


def _result_id(request):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "cloudwalk:e01-luna-v1:" + request["event_id"]))


def _handoff_payload(request, message_ids):
    referenced = set(message_ids)
    history = [row for row in request["payload"]["history"] if row["id"] in referenced]
    identifiers = [row["id"] for row in history]
    latest = next(row for row in reversed(request["payload"]["history"]) if row["author"]["type"] == "customer")
    if set(identifiers) != referenced or latest["id"] not in referenced:
        raise ValueError("handoff_message_origin")
    return {"message_ids": identifiers, "summary": "\n".join(row["text"] for row in history)}


def _proposal(request, decision):
    payload = {"request_event_id": request["event_id"], "text": decision["text"]}
    if decision["action"] == "handoff":
        payload.update(_handoff_payload(request, decision["message_ids"]))
    return json_bytes({
        "schema_version": "1.0", "event_id": _result_id(request),
        "event_type": f"agent.{decision['action']}.proposed",
        **{key: request[key] for key in _RESULT_FIELDS}, "payload": payload,
    })


class Executor:
    def __init__(self, knowledge, backend, ledger, contracts, *,
                 poll_timeout_s=60.0, poll_interval_s=0.25, completion_margin_s=3.0,
                 monotonic=time.monotonic, wall_clock=time.time, pause=time.sleep):
        if not all(math.isfinite(value) and value > 0 for value in
                   (poll_timeout_s, poll_interval_s, completion_margin_s)):
            raise ValueError("invalid_e01_executor_timeout")
        self._knowledge = knowledge
        self._backend = backend
        self._ledger = ledger
        self._contracts = contracts
        self._poll_timeout = poll_timeout_s
        self._poll_interval = poll_interval_s
        self._completion_margin = completion_margin_s
        self._monotonic = monotonic
        self._wall_clock = wall_clock
        self._pause = pause

    def _read_request(self, record):
        raw = record.value()
        try:
            read_json_object(raw)
            request = self._contracts.read("AgentTurnRequested", raw)
            require_key(request, record)
            validate_history(request)
            if not isinstance(raw, bytes) or not canonical_uuid(request["event_id"]):
                raise ValueError
        except (TypeError, ValueError, RecursionError):
            raise ExecutorError("invalid_e01_request") from None
        return raw, request

    def _wait(self, deadline):
        left = deadline - self._monotonic()
        if left <= 0:
            raise ExecutorError("ledger_still_pending", retryable=True)
        self._pause(min(left, self._poll_interval))

    def _lease_deadline(self, response, requested_at, cap):
        try:
            timestamp = datetime.fromisoformat(response["lease_expires_at"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError
            seconds = timestamp.timestamp() - self._wall_clock()
        except (KeyError, AttributeError, TypeError, ValueError, OverflowError, OSError):
            raise ExecutorError("invalid_ledger_lease") from None
        return min(requested_at + cap, self._monotonic() + seconds)

    def _infer(self, request, candidates, claim, dispatch_deadline):
        timeout = dispatch_deadline - self._monotonic() - self._completion_margin
        if timeout <= 0:
            return "unknown", {**claim, "reason": "dispatch_uncertain"}
        try:
            decision, usage = self._backend.infer(request, candidates, timeout_s=timeout)
        except InferenceFailure as error:
            if valid_usage(error.usage) and error.reason in _FAILED_REASONS:
                return "complete", {**claim, "outcome": "failed", "usage": error.usage, "reason": error.reason}
            reason = error.reason if error.reason in _UNKNOWN_REASONS and error.usage is None else "usage_invalid"
            return "unknown", {**claim, "reason": reason}
        if not valid_usage(usage):
            return "unknown", {**claim, "reason": "usage_invalid"}
        failure = {**claim, "outcome": "failed", "usage": usage}
        try:
            self._knowledge.validate_decision(request, candidates, decision)
        except ValueError:
            return "complete", {**failure, "reason": "invalid_decision"}
        try:
            raw = _proposal(request, decision)
            if len(raw) > RESULT_LIMIT:
                raise ValueError
            self._contracts.read("AgentResult", raw)
        except ValueError:
            return "complete", {**failure, "reason": "invalid_result"}

        handoff = None
        if decision["action"] == "handoff":
            rule = next(row for row in candidates["handoff_rules"] if row["id"] == decision["rule_id"])
            handoff = {"id": rule["id"], "reason": rule["reason"]}
        return "complete", {
            **claim, "outcome": "result", "usage": usage,
            "knowledge_version": candidates["knowledge_version"], "ontology_version": candidates["ontology_version"],
            "policy_version": POLICY_VERSION, "source_refs": decision["source_refs"], "handoff_rule": handoff,
            "result_b64": base64.b64encode(raw).decode("ascii"), "result_sha256": hashlib.sha256(raw).hexdigest(),
        }

    def _read_saved(self, request, saved, submitted):
        try:
            encoded, digest = saved["result_b64"], saved["result_sha256"]
            raw = base64.b64decode(encoded, validate=True)
            if (len(raw) > RESULT_LIMIT or base64.b64encode(raw).decode("ascii") != encoded
                    or hashlib.sha256(raw).hexdigest() != digest):
                raise ValueError
            if submitted is not None and submitted.get("outcome") == "result" and (
                    encoded != submitted["result_b64"] or digest != submitted["result_sha256"]):
                raise ValueError

            read_json_object(raw)
            event = self._contracts.read("AgentResult", raw)
            payload = event["payload"]
            if (event["event_id"] != _result_id(request) or payload["request_event_id"] != request["event_id"]
                    or any(event[key] != request[key] for key in _RESULT_FIELDS)):
                raise ValueError
            if event["event_type"] == "agent.handoff.proposed":
                projected = _handoff_payload(request, payload["message_ids"])
                if payload.get("text") != HANDOFF_TEXT or any(payload[key] != value for key, value in projected.items()):
                    raise ValueError
            if event["event_type"] == "agent.resolve.proposed" and payload["text"] != RESOLVE_TEXT:
                raise ValueError
        except (KeyError, TypeError, ValueError, RecursionError):
            raise ExecutorError("invalid_ledger_saved_result", retryable=True) from None
        return digest, raw

    def handle(self, record, publisher) -> None:
        raw, request = self._read_request(record)
        try:
            candidates = self._knowledge.select(request)
            validate_context(request, candidates)
        except (TypeError, ValueError, OSError):
            raise ExecutorError("invalid_e01_context") from None

        request_id = request["event_id"]
        owner = {"owner_id": str(uuid.uuid4())}
        claim = {**owner, "request_sha256": hashlib.sha256(raw).hexdigest()}
        deadline = self._monotonic() + self._poll_timeout
        start_attempted = False
        settlement = None
        submitted = None
        response = None
        acked_digest = None
        while True:
            try:
                if response is None:
                    claimed_at = self._monotonic()
                    response = self._ledger.claim(request_id, claim)
                state = response["state"]
                if state in _TERMINAL:
                    return
                if state == "result_saved":
                    digest, saved = self._read_saved(request, response, submitted)
                    if acked_digest != digest:
                        if acked_digest is not None:
                            raise ExecutorError("changed_ledger_saved_result", retryable=True)
                        try:
                            publisher.publish(EVENTS, request["case_id"], saved)
                        except Exception:
                            raise ExecutorError("e01_publication_unconfirmed", retryable=True) from None
                        acked_digest = digest
                    response = self._ledger.published(request_id, {"result_sha256": digest})
                    continue
                if state == "reserved":
                    # Nunca repetir start dentro da tentativa que perdeu a autorização.
                    if start_attempted:
                        raise ExecutorError("e01_start_unconfirmed", retryable=True)
                    if self._lease_deadline(response, claimed_at, 10.0) <= self._monotonic():
                        raise ExecutorError("e01_reservation_expired", retryable=True)
                    token = response["lease_token"]
                    if not canonical_uuid(token):
                        raise ExecutorError("invalid_ledger_lease")
                    credentials = {**owner, "lease_token": token}
                    start_attempted = True
                    start_at = self._monotonic()
                    response = self._ledger.start(request_id, credentials)
                    if response.get("dispatch") is True and response["state"] == "started":
                        dispatch_deadline = self._lease_deadline(response, start_at, 40.0)
                        settlement = self._infer(request, candidates, credentials, dispatch_deadline)
                        if settlement[1].get("outcome") == "result":
                            submitted = settlement[1]
                    continue
                if state != "started":
                    raise ExecutorError("invalid_ledger_state")
                if settlement and self._monotonic() < dispatch_deadline:
                    operation, body = settlement
                    try:
                        response = getattr(self._ledger, operation)(request_id, body)
                    except LedgerError as error:
                        if operation == "complete" and error.code == "invalid_body":
                            settlement = "unknown", {**credentials, "reason": "usage_invalid"}
                            continue
                        if body.get("outcome") == "result" and error.code in {"too_large", "result_mismatch"}:
                            settlement = "complete", {**credentials, "outcome": "failed",
                                                      "usage": body["usage"], "reason": "invalid_result"}
                            response = None
                            self._wait(deadline)
                            continue
                        raise
                    continue
            except LedgerError as error:
                if not _may_observe_again(error):
                    raise ExecutorError(error.code) from None

            response = None
            self._wait(deadline)
