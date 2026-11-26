import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import tempfile
from threading import Event, Lock
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
import uuid

from agent_flow import Contracts, DEFAULT_SCHEMA, EVENTS, json_bytes
from e01_backend import CONTEXT_LIMIT, InferenceFailure, validate_context
from e01_contracts import read_private_schema
from e01_executor import Executor, ExecutorError
from e01_knowledge import Knowledge
from e01_ledger import LedgerClient
from test_e01_knowledge import (
    HORIZONTE, ROOT, message, proposed_handoff, proposed_reply, requested,
)
from test_e01_transport import SECRET, USAGE


def record(request):
    raw = json_bytes(request) + b"\n"
    key = request["case_id"].encode()
    return SimpleNamespace(value=lambda: raw, key=lambda: key)


class Clock:
    def __init__(self):
        self.seconds = 0.0

    def monotonic(self):
        return self.seconds

    def wall(self):
        return 1795687200.0 + self.seconds

    def sleep(self, seconds):
        self.seconds += seconds


class LedgerStore:
    """Estado do servidor que sobrevive à criação de outro Executor/cliente HTTP."""

    def __init__(self, request, *, now, fail=None):
        self.now = now
        self.event = json.loads(request.value())
        self.origin = hashlib.sha256(request.value()).hexdigest()
        self.token = str(uuid.uuid4())
        self.owner = None
        self.expires = 0.0
        self.state = None
        self.saved = None
        self.completion = None
        self.fail = fail
        self.calls = []
        self.nonces = set()
        self.lock = Lock()
        self.second_owner_observed = Event()

    def expires_at(self):
        return datetime.fromtimestamp(self.expires, timezone.utc).isoformat().replace("+00:00", "Z")

    def __call__(self, path, headers, raw, *, deadline):
        request_id, op = path.rsplit("/", 2)[-2:]
        assert request_id == self.event["event_id"]
        body = json.loads(raw)
        with self.lock:
            nonce = headers["X-E01-Nonce"]
            assert nonce not in self.nonces
            self.nonces.add(nonce)
            self.calls.append((op, body))
            if self.expires <= self.now():
                if self.state == "started":
                    self.state = "unknown"
                elif self.state == "reserved":
                    self.state = None
                    self.token = str(uuid.uuid4())
            status, response = getattr(self, op)(body)
            return status, json_bytes(response)

    def claim(self, body):
        if body["request_sha256"] != self.origin:
            return 409, {"error": "request_mismatch"}
        if self.state is None:
            self.state = "reserved"
            self.owner = body["owner_id"]
            self.expires = self.now() + 10
        if self.state == "reserved":
            if self.owner != body["owner_id"]:
                return 409, {"error": "busy"}
            return 200, {"state": "reserved", "lease_token": self.token,
                         "lease_expires_at": self.expires_at(), "currency": "USD", "reserved_usd": "0.010000000000"}
        if self.state == "started":
            if self.owner != body["owner_id"]:
                self.second_owner_observed.set()
            return 200, {"state": "started", "dispatch": False}
        if self.state == "result_saved":
            return 200, self.saved
        return 200, {"state": self.state}

    def start(self, body):
        if body != {"owner_id": self.owner, "lease_token": self.token} or self.state not in {"reserved", "started"}:
            return 409, {"error": "lease_lost"}
        if self.state == "started":
            return 200, {"state": "started", "dispatch": False}
        self.state = "started"
        self.expires = self.now() + (1 if self.fail in {"start_lost", "start_false"} else 40)
        if self.fail == "start_lost":
            raise TimeoutError
        if self.fail == "start_false":
            return 200, {"state": "started", "dispatch": False}
        return 200, {"state": "started", "dispatch": True, "lease_expires_at": self.expires_at()}

    def complete(self, body):
        if self.completion == body:
            return 200, self.saved or {"state": self.state}
        if self.completion:
            return 409, {"error": "result_mismatch"}
        if body["owner_id"] != self.owner or body["lease_token"] != self.token or self.state != "started":
            return 409, {"error": "lease_lost"}
        if self.fail == "usage_out_of_caps":
            return 422, {"error": "invalid_body"}
        if self.fail == "complete_lost_before_save":
            self.fail = None
            raise TimeoutError
        self.completion = body
        if self.fail == "discard":
            self.state = "discarded"
            return 200, {"state": "discarded"}
        if body["outcome"] == "failed":
            self.state = "failed"
            return 200, {"state": "failed"}
        self.state = "result_saved"
        self.saved = {"state": self.state, "result_b64": body["result_b64"], "result_sha256": body["result_sha256"]}
        if self.fail == "complete_lost_after_save":
            raise TimeoutError
        if self.fail == "changed_response":
            altered = json.loads(base64.b64decode(body["result_b64"]))
            altered["payload"]["text"] = "Resposta diferente"
            raw = json_bytes(altered)
            return 200, {"state": self.state, "result_b64": base64.b64encode(raw).decode(),
                         "result_sha256": hashlib.sha256(raw).hexdigest()}
        return 200, self.saved

    def unknown(self, body):
        if body["owner_id"] != self.owner or body["lease_token"] != self.token or self.state != "started":
            return 409, {"error": "lease_lost"}
        self.state = "unknown"
        return 200, {"state": "unknown"}

    def published(self, body):
        if self.state not in {"result_saved", "published"} or body["result_sha256"] != self.saved["result_sha256"]:
            return 409, {"error": "result_mismatch"}
        if self.fail == "published_lost_before_save":
            self.fail = None
            raise TimeoutError
        self.state = "published"
        if self.fail == "published_lost_after_save":
            raise TimeoutError
        return 200, {"state": "published"}


class ExecutorTest(unittest.TestCase):
    def setUp(self):
        self.request = requested(message(1, "Onde consulto o comprovante de Pix?"), category="pix")
        self.record = record(self.request)
        self.clock = Clock()
        self.knowledge = Knowledge.load(ROOT / "knowledge")
        self.contracts = Contracts(DEFAULT_SCHEMA)
        self.backend = Mock()
        self.backend.infer.side_effect = lambda req, ctx, timeout_s: (proposed_reply(req, ctx), USAGE)
        self.publisher = Mock()

    def executor(self, server, *, real_clock=False, **options):
        hooks = {} if real_clock else {"monotonic": self.clock.monotonic, "wall_clock": self.clock.wall,
                                       "pause": self.clock.sleep}
        ledger = LedgerClient("http://backend:3000", SECRET, transport=server, now=server.now)
        return Executor(self.knowledge, self.backend, ledger, self.contracts, **hooks, **options)

    def test_initial_effect_and_restart_use_exact_saved_bytes(self):
        server = LedgerStore(self.record, now=self.clock.wall)
        self.executor(server).handle(self.record, self.publisher)
        self.executor(server).handle(self.record, self.publisher)
        self.assertEqual([op for op, _ in server.calls], ["claim", "start", "complete", "published", "claim"])
        self.assertEqual(self.backend.infer.call_count, 1)
        self.assertEqual(self.backend.infer.call_args.kwargs["timeout_s"], 37.0)
        topic, key, raw = self.publisher.publish.call_args.args
        self.assertEqual((topic, key, raw), (EVENTS, self.request["case_id"], base64.b64decode(server.saved["result_b64"])))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), server.saved["result_sha256"])
        self.assertEqual(self.publisher.publish.call_count, 1)
        self.assertEqual(self.contracts.read("AgentResult", raw)["payload"]["request_event_id"], self.request["event_id"])
        self.assertEqual(server.calls[0][1]["request_sha256"], hashlib.sha256(self.record.value()).hexdigest())

    def test_v11_handoff_projection_and_bytes_pass_independent_checker(self):
        request = requested(message(1, "Onde consulto o status do repasse?"),
                            message(2, "Ainda não resolveu, quero falar com uma pessoa."), brand=HORIZONTE,
                            category="payouts")
        request["schema_version"] = "1.1"
        self.record = record(request)

        def infer(req, ctx, *, timeout_s):
            decision = proposed_handoff(req, ctx, "human_requested")
            # O resumo publicado segue sequência, independentemente da ordem do modelo.
            decision["message_ids"].append(req["payload"]["history"][0]["id"])
            return decision, USAGE

        self.backend.infer.side_effect = infer
        server = LedgerStore(self.record, now=self.clock.wall)
        self.executor(server).handle(self.record, self.publisher)
        raw = self.publisher.publish.call_args.args[-1]
        result = json.loads(raw)
        self.assertEqual(result["schema_version"], "1.0")
        self.assertEqual(result["payload"]["summary"], "\n".join(row["text"] for row in request["payload"]["history"]))
        complete = server.completion
        self.assertEqual(complete["handoff_rule"], {"id": "horizonte.humano", "reason": "human_requested"})
        self.assertEqual(complete["source_refs"], [{"id": "horizonte.manual", "version": "1.0.0"}])
        check = runpy.run_path(str(ROOT.parent / "script/e01/check_contracts.py"))
        check["schema_check"](json.loads(DEFAULT_SCHEMA.read_bytes()), result, "AgentResult")
        check["schema_check"](read_private_schema("ledger"), complete, "complete_result")
        check["validate_projection"](request, infer(request, self.knowledge.select(request), timeout_s=1)[0], result)

    def test_invalid_record_precedes_all_http(self):
        bad_key = SimpleNamespace(value=self.record.value, key=lambda: b"another-case")
        unordered = record(requested(message(2, "uma mensagem"), message(1, "outra")))
        duplicate_id = message(2, "outra")
        duplicate_id["id"] = message(1, "uma")["id"]
        duplicated = record(requested(message(1, "uma"), duplicate_id))
        no_customer = record(requested(message(1, "Sem cliente", "system")))
        server = LedgerStore(self.record, now=self.clock.wall)
        for invalid in (bad_key, unordered, duplicated, no_customer):
            with self.assertRaises(ExecutorError) as caught:
                self.executor(server).handle(invalid, self.publisher)
            self.assertFalse(caught.exception.retryable)
        self.assertFalse(server.calls)
        self.backend.infer.assert_not_called()

    def test_invalid_context_on_new_claim_does_not_start_or_dispatch(self):
        unknown = record(requested(message(1, "Pix"), brand="99999999-9999-4999-8999-999999999999"))
        too_large = record(requested(message(1, "x" * (65 * 1024))))
        for invalid in (unknown, too_large):
            server = LedgerStore(invalid, now=self.clock.wall)
            with self.assertRaisesRegex(ExecutorError, "invalid_e01_context") as caught:
                self.executor(server).handle(invalid, self.publisher)
            self.assertFalse(caught.exception.retryable)
            self.assertEqual([op for op, _ in server.calls], ["claim"])
            self.assertEqual(server.state, "reserved")
        self.backend.infer.assert_not_called()
        self.publisher.publish.assert_not_called()

    def test_start_without_ack_or_dispatch_flag_reconciles_with_no_model_post(self):
        for failure in ("start_lost", "start_false"):
            with self.subTest(failure=failure):
                server = LedgerStore(self.record, now=self.clock.wall, fail=failure)
                self.executor(server, poll_interval_s=0.1).handle(self.record, self.publisher)
                self.assertEqual(server.state, "unknown")
                self.assertEqual(Counter(op for op, _ in server.calls)["start"], 1)
                self.assertGreater(Counter(op for op, _ in server.calls)["claim"], 2)
                self.executor(server).handle(self.record, self.publisher)
                self.assertEqual(server.calls[-1][0], "claim")
        self.backend.infer.assert_not_called()
        self.publisher.publish.assert_not_called()

    def test_started_without_terminal_raises_retryable_instead_of_ack(self):
        server = LedgerStore(self.record, now=self.clock.wall)
        server.state = "started"
        server.expires = server.now() + 40
        with self.assertRaises(ExecutorError) as caught:
            self.executor(server, poll_timeout_s=0.5, poll_interval_s=0.1).handle(self.record, self.publisher)
        self.assertTrue(caught.exception.retryable)
        self.assertEqual(caught.exception.code, "ledger_still_pending")
        self.assertGreaterEqual(self.clock.seconds, 0.5)
        self.assertEqual({op for op, _ in server.calls}, {"claim"})
        self.backend.infer.assert_not_called()
        self.publisher.publish.assert_not_called()

    def test_two_handles_wait_for_same_durable_execution(self):
        server = LedgerStore(self.record, now=time.time)
        release = Event()
        entered = Event()

        def infer(req, ctx, *, timeout_s):
            entered.set()
            if not release.wait(3):
                raise AssertionError("inference gate not released")
            return proposed_reply(req, ctx), USAGE

        self.backend.infer.side_effect = infer
        with ThreadPoolExecutor(max_workers=2) as workers:
            first = workers.submit(self.executor(server, real_clock=True).handle, self.record, self.publisher)
            self.assertTrue(entered.wait(2))
            second = workers.submit(self.executor(server, real_clock=True, poll_interval_s=0.01).handle,
                                    self.record, self.publisher)
            try:
                self.assertTrue(server.second_owner_observed.wait(2))
                self.assertFalse(second.done())
                self.publisher.publish.assert_not_called()
            finally:
                release.set()
            self.assertIsNone(first.result(timeout=3))
            self.assertIsNone(second.result(timeout=3))
        self.assertEqual(self.backend.infer.call_count, 1)
        self.assertTrue(self.publisher.publish.called)
        self.assertEqual({call.args[-1] for call in self.publisher.publish.call_args_list},
                         {base64.b64decode(server.saved["result_b64"])})
        self.assertEqual(Counter(op for op, _ in server.calls)["complete"], 1)
        self.assertEqual(server.state, "published")

    def test_reentry_after_publish_failure_uses_same_digest_and_avoids_new_inference(self):
        server = LedgerStore(self.record, now=self.clock.wall)
        broken = Mock()
        broken.publish.side_effect = TimeoutError("sensitive text")
        with self.assertRaisesRegex(ExecutorError, "e01_publication_unconfirmed"):
            self.executor(server).handle(self.record, broken)
        self.assertEqual(server.state, "result_saved")
        self.assertNotIn("published", [op for op, _ in server.calls])
        self.executor(server).handle(self.record, self.publisher)
        self.assertEqual(broken.publish.call_args, self.publisher.publish.call_args)
        self.assertEqual(self.backend.infer.call_count, 1)
        self.assertEqual(server.state, "published")

    def test_replay_uses_old_saved_bytes_even_when_current_context_is_too_large(self):
        request = self.request
        payload = request["payload"]
        context = self.knowledge.select(request)
        initial_size = len(json_bytes({"history": payload["history"], "category": "pix", "knowledge": context}))
        payload["history"][0]["text"] += " " + "x" * (CONTEXT_LIMIT - initial_size - 8)
        original = record(request)
        server = LedgerStore(original, now=self.clock.wall)

        broken = Mock()
        broken.publish.side_effect = TimeoutError
        with self.assertRaisesRegex(ExecutorError, "e01_publication_unconfirmed"):
            self.executor(server).handle(original, broken)
        self.assertEqual(server.state, "result_saved")

        with tempfile.TemporaryDirectory() as directory:
            edited_root = Path(directory) / "knowledge"
            shutil.copytree(ROOT / "knowledge", edited_root)
            edition = edited_root / "brands/aurora.json"
            catalog = json.loads(edition.read_bytes())
            catalog["version"] = "1.1.0"
            catalog["sources"][0]["title"] += " " + "x" * 256
            edition.write_bytes(json_bytes(catalog))
            self.knowledge = Knowledge.load(edited_root)
            edited = self.knowledge.select(request)
            self.assertEqual(edited["knowledge_version"], "1.1.0")
            with self.assertRaisesRegex(ValueError, "context_too_large"):
                validate_context(request, edited)
            self.executor(server).handle(original, self.publisher)

        self.assertEqual(broken.publish.call_args, self.publisher.publish.call_args)
        self.assertEqual(self.backend.infer.call_count, 1)
        self.assertEqual(server.completion["knowledge_version"], "1.0.0")
        self.assertEqual(server.calls[-1], ("published", {"result_sha256": server.saved["result_sha256"]}))
        self.assertEqual(server.state, "published")

    def test_lost_completion_and_published_replies_recover_without_new_post(self):
        for failure in ("complete_lost_before_save", "complete_lost_after_save",
                        "published_lost_before_save", "published_lost_after_save"):
            with self.subTest(failure=failure):
                self.backend.reset_mock()
                self.publisher.reset_mock()
                server = LedgerStore(self.record, now=self.clock.wall, fail=failure)
                self.executor(server).handle(self.record, self.publisher)
                self.assertEqual(server.state, "published")
                self.assertEqual(self.backend.infer.call_count, 1)
                self.assertEqual(self.publisher.publish.call_count, 1)
                complete = [body for op, body in server.calls if op == "complete"]
                self.assertEqual(len(complete), 2 if failure == "complete_lost_before_save" else 1)
                self.assertTrue(all(body == complete[0] for body in complete))

    def test_known_failure_unknown_and_discard_are_terminal(self):
        cases = [
            (InferenceFailure("usage_missing"), None, "unknown", "usage_missing"),
            (InferenceFailure("provider_rejected", USAGE), None, "failed", "provider_rejected"),
            (None, "usage_out_of_caps", "unknown", "usage_invalid"),
            (None, "discard", "discarded", None),
        ]
        for failure, mode, end, reason in cases:
            with self.subTest(mode=mode, outcome=end):
                server = LedgerStore(self.record, now=self.clock.wall, fail=mode)
                self.backend.reset_mock()
                self.backend.infer.side_effect = failure or (lambda req, ctx, timeout_s: (proposed_reply(req, ctx), USAGE))
                self.executor(server).handle(self.record, self.publisher)
                self.executor(server).handle(self.record, self.publisher)
                self.assertEqual(server.state, end)
                self.assertEqual(self.backend.infer.call_count, 1)
                if reason:
                    self.assertEqual(server.calls[-2][1]["reason"], reason)
                self.assertEqual(server.calls[-1][0], "claim")
                self.publisher.publish.assert_not_called()

    def test_bad_decision_with_trustworthy_usage_is_failed(self):
        self.backend.infer.side_effect = lambda req, ctx, timeout_s: ({"action": "resolve"}, USAGE)
        server = LedgerStore(self.record, now=self.clock.wall)
        self.executor(server).handle(self.record, self.publisher)
        self.assertEqual(server.state, "failed")
        self.assertEqual(server.completion["reason"], "invalid_decision")
        self.assertEqual(server.completion["usage"], USAGE)
        self.publisher.publish.assert_not_called()

    def test_changed_saved_bytes_are_not_published_from_complete(self):
        server = LedgerStore(self.record, now=self.clock.wall, fail="changed_response")
        with self.assertRaisesRegex(ExecutorError, "invalid_ledger_saved_result"):
            self.executor(server).handle(self.record, self.publisher)
        self.publisher.publish.assert_not_called()
        self.executor(server).handle(self.record, self.publisher)
        self.assertEqual(self.publisher.publish.call_args.args[-1], base64.b64decode(server.saved["result_b64"]))
        self.assertEqual(self.backend.infer.call_count, 1)
