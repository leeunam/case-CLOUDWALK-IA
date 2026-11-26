from contextlib import closing, redirect_stderr, redirect_stdout
from functools import partial
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback
import unittest
import uuid

from agent_flow import json_bytes
from e01_backend import FEITA_HOST, FEITA_PATH, InferenceFailure, LunaBackend, MODEL, RESPONSE_LIMIT
from e01_contracts import validator
from e01_http import DeadlinePost
from e01_knowledge import Knowledge
from e01_ledger import LedgerClient, LedgerError, signed_headers
from test_e01_knowledge import (
    FIXTURES, ROOT, message, proposed_handoff, proposed_reply, proposed_resolution, requested,
)


CREDENTIAL = "synthetic-api-key-never-log"
SECRET = "synthetic-ledger-secret-never-log"
REQUEST_ID = "00000000-0000-4000-8000-000000000601"
LARGE_BODY = b"x" * 90_000
USAGE = {"provider_response_id": "response-01", "input_tokens": 123, "cached_input_tokens": 3, "output_tokens": 21}


def completion(decision):
    return {"id": USAGE["provider_response_id"], "model": MODEL, "choices": [{
        "finish_reason": "stop", "message": {"content": json.dumps({"decision": decision})},
    }], "usage": {"prompt_tokens": 123, "prompt_tokens_details": {"cached_tokens": 3},
                  "completion_tokens": 21, "completion_tokens_details": {"reasoning_tokens": 0}, "total_tokens": 144}}


class Transport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, path, headers, body, *, deadline):
        self.calls.append((path, headers, body, deadline))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class BackendTest(unittest.TestCase):
    def setUp(self):
        self.request = requested(message(1, "Onde consulto o comprovante de Pix?"), category="pix")
        self.candidates = Knowledge.load(ROOT / "knowledge").select(self.request)
        self.decision = proposed_reply(self.request, self.candidates)

    def test_real_shape_context_and_usage(self):
        transport = Transport((200, json_bytes(completion(self.decision))))
        backend = LunaBackend(CREDENTIAL, transport=transport)
        self.assertEqual(backend.infer(self.request, self.candidates, timeout_s=1), (self.decision, USAGE))
        [(path, headers, body, _)] = transport.calls
        self.assertEqual((path, headers["Authorization"]), (FEITA_PATH, "Bearer " + CREDENTIAL))
        body = json.loads(body)
        self.assertEqual((body["model"], body["reasoning_effort"], body["stream"]), (MODEL, "none", False))
        response_format = body["response_format"]
        self.assertEqual(response_format["type"], "json_schema")
        self.assertTrue(response_format["json_schema"]["strict"])
        shape = response_format["json_schema"]["schema"]
        self.assertEqual(shape["required"], ["decision"])
        self.assertFalse(shape["additionalProperties"])
        choices = shape["properties"]["decision"]["anyOf"]
        self.assertEqual([item["properties"]["action"]["enum"] for item in choices], [["reply"], ["handoff"], ["resolve"]])
        for choice in choices:
            self.assertCountEqual(choice["required"], choice["properties"])
            self.assertFalse(choice["additionalProperties"])
        validate = validator(shape)
        for decision in (self.decision, proposed_handoff(self.request, self.candidates, "no_guidance"),
                         proposed_resolution(self.request)):
            validate.validate({"decision": decision})
        system, envelope = body["messages"]
        self.assertEqual((system["role"], envelope["role"]), ("system", "user"))
        context = json.loads(envelope["content"])
        self.assertEqual(context["knowledge"], self.candidates)
        self.assertEqual(context["history"], self.request["payload"]["history"])
        self.assertNotIn("horizonte.manual", envelope["content"])
        self.assertNotIn(CREDENTIAL, system["content"])

    def test_ambiguous_transport_or_usage_never_retries(self):
        good = completion(self.decision)
        cases = [
            ("transport_ambiguous", TimeoutError(CREDENTIAL)),
            ("transport_ambiguous", RuntimeError(CREDENTIAL)),
            ("transport_ambiguous", (307, json_bytes(good))),
            ("transport_ambiguous", (500, b"<html>bad gateway</html>")),
            ("transport_ambiguous", (200, b'{"usage":{},"usage":{}}')),
            ("transport_ambiguous", (200, b'{"usage":{"prompt_tokens":1e999}}')),
            ("transport_ambiguous", (200, b'{"usage":{"prompt_tokens":NaN}}')),
            ("usage_missing", (200, json_bytes(dict(good, usage=None)))),
            ("usage_invalid", (200, json_bytes(dict(good, model="another-model")))),
            ("usage_invalid", (200, json_bytes(dict(good, id=" ")))),
        ]
        for changes in ({"prompt_tokens": True}, {"completion_tokens": 21.0}, {"total_tokens": 12},
                        {"prompt_tokens_details": None}, {"prompt_tokens_details": {"cached_tokens": 124}},
                        {"completion_tokens_details": {"reasoning_tokens": 24}}):
            cases.append(("usage_invalid", (200, json_bytes(dict(good, usage={**good["usage"], **changes})))))
        messages = StringIO()
        with redirect_stderr(messages), redirect_stdout(messages):
            for reason, reply in cases:
                with self.subTest(reason=reason):
                    transport = Transport(reply)
                    with self.assertRaises(InferenceFailure) as caught:
                        LunaBackend(CREDENTIAL, transport=transport).infer(self.request, self.candidates, timeout_s=1)
                    self.assertEqual((caught.exception.reason, caught.exception.usage), (reason, None))
                    self.assertEqual(len(transport.calls), 1)
                    self.assertNotIn(CREDENTIAL, "".join(traceback.format_exception(caught.exception)))
        self.assertNotIn(CREDENTIAL, messages.getvalue())

    def test_refusal_and_invalid_decision_keep_proven_usage(self):
        cases = [
            ("provider_rejected", 429, "stop", {}),
            ("provider_rejected", 200, "stop", {"refusal": "fixture"}),
            ("provider_rejected", 200, "content_filter", {}),
            ("invalid_decision", 200, "length", {}),
            ("invalid_decision", 200, "stop", {"content": '{"decision":{},"decision":{}}'}),
            ("invalid_decision", 200, "stop", {"content": '{"decision":{"action":"unknown"}}'}),
        ]
        for reason, status, stop, changed in cases:
            with self.subTest(reason=reason, status=status, stop=stop):
                doc = completion(self.decision)
                doc["choices"][0]["finish_reason"] = stop
                doc["choices"][0]["message"].update(changed)
                transport = Transport((status, json_bytes(doc)))
                with self.assertRaises(InferenceFailure) as caught:
                    LunaBackend(CREDENTIAL, transport=transport).infer(self.request, self.candidates, timeout_s=1)
                self.assertEqual((caught.exception.reason, caught.exception.usage), (reason, USAGE))
                self.assertEqual(len(transport.calls), 1)


class LedgerClientTest(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((FIXTURES / "ledger.json").read_bytes())

    def test_signature_vector_and_fresh_nonce_per_attempt(self):
        vector = json.loads((FIXTURES / "signature.json").read_bytes())
        headers = signed_headers(vector["fixture_key"], vector["path"], vector["body_utf8"].encode(),
                                 timestamp=vector["timestamp"], nonce=vector["nonce"])
        self.assertEqual(headers["X-E01-Signature"], vector["signature"])
        transport = Transport((200, json_bytes(self.fixture["reserved"])))
        ledger = LedgerClient("http://backend:3000", SECRET, transport=transport, now=lambda: 12)
        for _ in range(2):
            self.assertEqual(ledger.claim(REQUEST_ID, self.fixture["claim"]), self.fixture["reserved"])
        nonces = []
        for path, headers, body, _ in transport.calls:
            self.assertEqual(path, vector["path"])
            self.assertEqual(body, vector["body_utf8"].encode())
            nonce = headers["X-E01-Nonce"]
            self.assertEqual(uuid.UUID(nonce).version, 4)
            self.assertEqual(headers, signed_headers(SECRET, path, body, timestamp="12", nonce=nonce))
            nonces.append(nonce)
        self.assertNotEqual(*nonces)

    def test_malformed_ledger_response_and_http_status_are_typed(self):
        cases = [
            ((409, b'{"error":"lease_lost"}'), 409, "lease_lost"),
            ((409, b'{"error":"not_found"}'), 409, "invalid_ledger_response"),
            ((409, b'{"error":"lease_lost","error":"busy"}'), 409, "invalid_ledger_response"),
            ((200, b'{"state":"started","dispatch":true}'), 200, "invalid_ledger_response"),
            ((307, b'{"error":"busy"}'), 307, "ledger_redirect"),
            (TimeoutError(SECRET), None, "ledger_transport"),
            (RuntimeError(SECRET), None, "ledger_transport"),
        ]
        for reply, status, code in cases:
            with self.subTest(status=status, code=code):
                transport = Transport(reply)
                ledger = LedgerClient("http://backend", SECRET, transport=transport)
                with self.assertRaises(LedgerError) as caught:
                    ledger.claim(REQUEST_ID, self.fixture["claim"])
                self.assertEqual((caught.exception.status, caught.exception.code), (status, code))
                self.assertEqual(len(transport.calls), 1)
                self.assertNotIn(SECRET, "".join(traceback.format_exception(caught.exception)))

    def test_rejects_invalid_route_and_bodies_before_transport(self):
        transport = Transport((200, b"{}"))
        ledger = LedgerClient("http://backend", SECRET, transport=transport)
        for route, body in (("../../claim", self.fixture["claim"]),
                            (REQUEST_ID, dict(self.fixture["claim"], input_rate="1"))):
            with self.subTest(route=route), self.assertRaisesRegex(LedgerError, "invalid_ledger_request"):
                ledger.claim(route, body)
        self.assertFalse(transport.calls)
        for url in ("http://a/executions", "http://a?token=x", "http://secret@a", "ftp://a"):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "invalid_ledger_url"):
                LedgerClient(url, SECRET, transport=transport)


class FakeResponse:
    length = None

    def __init__(self, phase):
        self.status = 307 if phase == "redirect" else 200
        self.phase = phase

    def getheader(self, name, default):
        return "gzip" if self.phase == "compressed" and name == "Content-Encoding" else default

    def read(self, max_bytes):
        if self.phase == "read":
            time.sleep(5)
        return b"x" * max_bytes if self.phase == "oversized" else b"{}"

    def close(self):
        pass


class FakeConnection:
    def __init__(self, host, *, port, timeout, phase, trace):
        self.host = host
        self.phase = phase
        self.trace = Path(trace)
        self.sock = self

    def connect(self):
        if self.phase == "connect":
            time.sleep(5)

    def settimeout(self, _timeout):
        pass

    def request(self, method, path, *, body, headers):
        with self.trace.open("a") as output:
            output.write(f"{self.host} {method} {path}\n")
        if self.phase == "write":
            raise TimeoutError
        if self.phase == "verify_payload" and (body != LARGE_BODY or headers != {"Authorization": CREDENTIAL}):
            raise ValueError("unexpected_fixture_payload")

    def getresponse(self):
        return FakeResponse(self.phase)

    def close(self):
        pass


class DeadlineTest(unittest.TestCase):
    def test_dns_and_read_are_bounded_and_all_paths_issue_at_most_one_post(self):
        for phase, expected_posts in (("connect", 0), ("read", 1), ("write", 1), ("oversized", 1),
                                      ("compressed", 1), ("redirect", 1)):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                trace = Path(directory) / "requests"
                post = DeadlinePost(FEITA_HOST, response_limit=RESPONSE_LIMIT,
                                    connection_factory=partial(FakeConnection, phase=phase, trace=str(trace)))
                begin = time.monotonic()
                if phase == "redirect":
                    self.assertEqual(post(FEITA_PATH, {}, b"{}", deadline=begin + 1.5), (307, b"{}"))
                else:
                    with self.assertRaises((TimeoutError, ConnectionError)):
                        post(FEITA_PATH, {}, b"{}", deadline=begin + 1.5)
                elapsed = time.monotonic() - begin
                self.assertLess(elapsed, 3.0)
                lines = trace.read_text().splitlines() if trace.exists() else []
                self.assertEqual(lines, [f"{FEITA_HOST} POST {FEITA_PATH}"] * expected_posts)

    def test_transfers_body_larger_than_spawn_pipe(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "requests"
            post = DeadlinePost(FEITA_HOST, response_limit=RESPONSE_LIMIT,
                                connection_factory=partial(FakeConnection, phase="verify_payload", trace=str(trace)))
            self.assertEqual(post(FEITA_PATH, {"Authorization": CREDENTIAL}, LARGE_BODY,
                                  deadline=time.monotonic() + 2.0), (200, b"{}"))
            self.assertEqual(trace.read_text().splitlines(), [f"{FEITA_HOST} POST {FEITA_PATH}"])

    def test_cold_worker_respects_deadline_for_large_body_without_late_post(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "requests"
            fixture = Path(directory) / "cold_worker.py"
            fixture.write_text(
                f"""import sys
import time
from functools import partial
sys.path.insert(0, {str(ROOT)!r})
if __name__ == "__mp_main__":
    time.sleep(0.65)

from e01_http import DeadlinePost
from test_e01_transport import FakeConnection, FEITA_HOST, FEITA_PATH, LARGE_BODY, RESPONSE_LIMIT

if __name__ == "__main__":
    post = DeadlinePost(FEITA_HOST, response_limit=RESPONSE_LIMIT,
                        connection_factory=partial(FakeConnection, phase="redirect", trace={str(trace)!r}))
    started = time.monotonic()
    try:
        post(FEITA_PATH, {{}}, LARGE_BODY, deadline=started + 0.04)
    except TimeoutError:
        print(time.monotonic() - started, flush=True)
    else:
        raise AssertionError("cold request did not time out")
    time.sleep(0.7)
""")
            result = subprocess.run([sys.executable, "-B", str(fixture)], text=True,
                                    capture_output=True, timeout=8)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLess(float(result.stdout), 0.28)
            self.assertFalse(trace.exists(), result.stderr)

    def test_backend_uses_default_verified_tls_connection(self):
        post = LunaBackend(CREDENTIAL)._post
        with closing(post._connection_factory(FEITA_HOST)) as connection:
            self.assertEqual(connection._context.verify_mode.name, "CERT_REQUIRED")
            self.assertTrue(connection._context.check_hostname)
