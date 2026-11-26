"""Exercita o HTTP com um único subprocesso JSONL e o núcleo R1 verdadeiro."""
import contextlib
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
import json
import multiprocessing
from pathlib import Path
import signal
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import time
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from script.classification_comparison.setfit_sf2 import runtime_r1
from script.classification_comparison.setfit_sf2.contracts import ipc
from script.classification_comparison.setfit_sf2.runtime_r1.context import encoded
from script.classification_comparison.setfit_sf2.serving import bootstrap
from script.classification_comparison.setfit_sf2.serving.server import COMPLETE, Handler, Server, Supervisor

FIXTURES = bootstrap.ROOT / "docs/contratos/classification-http/fixtures"
MANIFEST = bootstrap.CAPTURE.parents[1] / "pacote/manifest.json"


def child_main(root, pipe):
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    verify = runtime_r1.verify
    def measured_verify(*args):
        if (root / "mode").read_text() == "slow-verify":
            time.sleep(8)
        return verify(*args)
    runtime_r1.verify = measured_verify

    def settings():
        pins, schema = bootstrap.sources()
        context = runtime_r1.load_context(bootstrap.CAPTURE.read_bytes(), bootstrap.SELECTED.read_bytes(),
                                          MANIFEST.read_bytes())
        argv = [sys.executable, "-B", str(Path(__file__).with_name("test_fixture_worker.py")), str(root), str(FIXTURES)]
        return (argv, Draft202012Validator({**schema, "$ref": "#/$defs/Request"}), context,
                lambda text, fields: len(text.split()) + 2)

    supervisor = Supervisor(settings, process_seconds=0.65, boot_seconds=0.75)
    with Server(("127.0.0.1", 0), Handler) as server:
        server.supervisor = supervisor
        Thread(target=server.serve_forever, daemon=True).start()
        pipe.send(server.server_port)
        pipe.close()
        supervisor.run()


class TransportTest(unittest.TestCase):
    def start(self, mode="complete", ready=True):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.mode(mode)
        ctx = multiprocessing.get_context("fork")
        read, write = ctx.Pipe(duplex=False)
        proc = ctx.Process(target=child_main, args=(self.root, write))
        proc.start()
        write.close()
        def cleanup():
            proc.terminate()
            proc.join(3)
            self.assertFalse(proc.is_alive())
            proc.close()
        self.addCleanup(cleanup)
        self.port = read.recv()
        read.close()
        if ready:
            return self.wait_ready()["worker_pid"]

    def mode(self, value):
        (self.root / "mode").write_text(value)

    def http(self, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=3)
        with contextlib.closing(connection):
            if body is None:
                connection.request("GET", "/ready")
            else:
                if isinstance(body, dict):
                    body = json.dumps(body).encode()
                connection.request("POST", COMPLETE, body, headers=headers or {"Content-Type": "application/json"})
            response = connection.getresponse()
            return response.status, json.loads(response.read())

    def wait_ready(self, old=None):
        for _ in range(150):
            status, state = self.http()
            if status == 200 and state["worker_pid"] != old:
                return state
            time.sleep(0.02)
        self.fail("não ficou pronto")

    def req(self, filename="request.json"):
        return json.loads((FIXTURES / filename).read_bytes())

    def test_four_vectors_one_pid(self):
        pid = self.start()
        for scenario in ("complete", "error", "review", "complete-both"):
            self.mode(scenario)
            status, result = self.http(self.req("request-both.json" if scenario == "complete-both" else "request.json"))
            self.assertEqual(status, 200)
            expected = self.req(f"response-{scenario}.json")
            elapsed = result.pop("elapsed_ms")
            self.assertLess(elapsed, 650)
            expected.pop("elapsed_ms")
            self.assertEqual(result, expected)
        self.assertEqual(self.wait_ready()["worker_pid"], pid)
        self.assertEqual((self.root / "received").read_text().splitlines(),
                         ['["priority"]'] * 3 + ['["category", "priority"]'])

    def test_request_rejections_never_write(self):
        pid = self.start()
        req = self.req()
        for value in (0, 7.0, True):
            self.assertEqual(self.http({**req, "catalog_version": value})[1]["error"], "invalid_request")
        for value in ({"category": "pix", "priority": "urgent"}, {"category": " ", "priority": None}):
            self.assertEqual(self.http({**req, "received": value})[1]["error"], "invalid_request")
        for body in (b" " * 65537, b'{"a":0,"a":1}', b'{"v":NaN}', b"\xff", b'{}', b'[]'):
            self.assertEqual(self.http(body)[0], 422)
        for header in ({"Content-Type": "text/plain"}, {"Content-Length": "65537"},
                       {"Content-Type": "application/json", "Transfer-Encoding": "identity"}):
            self.assertEqual(self.http(b"{}", header)[1]["error"], "invalid_request")
        req["catalog"]["priority"]["basic"] += "!"
        self.assertEqual(self.http(req)[1]["error"], "unsupported_catalog")
        self.assertFalse((self.root / "received").exists())
        self.assertEqual(self.wait_ready()["worker_pid"], pid)

    def test_token_boundary_before_worker(self):
        pid = self.start()
        at, above = self.req("token-boundaries.json")
        req = self.req()
        self.assertEqual(self.http({**req, "text": above["text"]})[1]["error"], "text_out_of_scope")
        self.assertFalse((self.root / "received").exists())
        self.assertEqual(self.http({**req, "text": at["text"]})[0], 200)
        self.assertEqual(self.wait_ready()["worker_pid"], pid)

    def test_busy(self):
        self.start("delay")
        req = self.req()
        with ThreadPoolExecutor(1) as pool:
            first = pool.submit(self.http, req)
            for _ in range(60):
                if (self.root / "received").exists():
                    break
                time.sleep(0.005)
            self.assert_headers_refused("busy")
            self.assertEqual(first.result()[0], 200)
        self.assertEqual(self.wait_ready()["counts"]["pipe_writes"], 1)

    def test_slot_is_rechecked_after_body(self):
        supervisor = Supervisor(load=None)
        supervisor.ready = True
        self.assertIsNone(supervisor.preflight())
        supervisor.active = object()
        self.assertEqual(supervisor.submit(b"{}"), (503, self.req("503-busy.json")))

    def assert_headers_refused(self, reason):
        with contextlib.closing(HTTPConnection("127.0.0.1", self.port, timeout=1)) as client:
            client.putrequest("POST", COMPLETE)
            client.putheader("Content-Type", "application/json")
            client.putheader("Content-Length", "1024")
            client.endheaders()
            response = client.getresponse()
            self.assertEqual((response.status, json.loads(response.read())), (503, self.req(f"503-{reason}.json")))

    def test_inclusive_byte_limits(self):
        self.start("exact-limit")
        body = json.dumps(self.req()).encode()
        self.assertEqual(self.http(body.ljust(65536))[0], 200)
        self.assertEqual(self.http(body.ljust(65537))[0], 422)
        self.assertEqual(self.wait_ready()["counts"]["pipe_writes"], 1)

    def test_valid_full_body_can_grow_in_ipc_projection(self):
        pid = self.start()
        req = self.req()
        req["text"] = "a"
        req["text"] += " " * (65536 - len(encoded(req)))
        body = encoded(req)
        self.assertEqual(len(body), 65536)
        _, schema = bootstrap.sources()
        Draft202012Validator({**schema, "$ref": "#/$defs/Request"}).validate(req)
        item = ipc.project(req, {"version": "1.0.0", **req["catalog"]})
        self.assertGreater(len(encoded(item) + b"\n"), 65536)
        self.assertEqual(self.http(body)[0], 200)
        self.assertEqual(self.wait_ready()["counts"]["pipe_writes"], 1)
        self.assertEqual(self.wait_ready()["worker_pid"], pid)

    def test_abandoned_client_does_not_release_slot_or_leave_frame(self):
        pid = self.start("delay")
        client = HTTPConnection("127.0.0.1", self.port)
        client.request("POST", COMPLETE, json.dumps(self.req()), {"Content-Type": "application/json"})
        client.close()
        for _ in range(60):
            if (self.root / "received").exists():
                break
            time.sleep(0.005)
        self.assertEqual(self.http(self.req())[1]["error"], "busy")
        for _ in range(100):
            if self.http()[1]["counts"].get("verified") == 1:
                break
            time.sleep(0.01)
        self.mode("complete-both")
        self.assertEqual(self.http(self.req("request-both.json"))[1]["calls"], {"category": 1, "priority": 1})
        self.assertEqual(self.wait_ready()["worker_pid"], pid)

    def test_bad_frame_eof_deadline_reaped_before_next_call(self):
        pid = self.start()
        for behavior in ("id", "policy_sha256", "package_sha256", "too-long", "duplicate", "nan", "utf8",
                         "oversize", "extra", "eof", "timeout", "slow-verify"):
            with self.subTest(behavior=behavior):
                self.mode(behavior)
                started = time.monotonic()
                status, body = self.http(self.req())
                self.assertLess(time.monotonic() - started, 1.65)
                if behavior in ("timeout", "slow-verify"):
                    self.assertEqual((status, body), (504, self.req("504-processing-timeout.json")))
                elif behavior == "eof":
                    self.assertEqual((status, body), (502, self.req("502-worker-failure.json")))
                else:
                    self.assertEqual((status, body), (502, self.req("502-invalid-worker-frame.json")))
                self.mode("complete")
                next_pid = self.wait_ready(pid)["worker_pid"]
                self.assertFalse(Path(f"/proc/{pid}").exists())
                self.assertEqual(self.http(self.req())[0], 200)
                pid = next_pid

    def test_boot_failure_has_two_attempts(self):
        self.start("early", ready=False)
        for _ in range(100):
            if self.http()[1]["counts"].get("session_failures") == 2:
                break
            time.sleep(0.015)
        self.assertEqual(self.http(self.req()), (503, self.req("503-not-ready.json")))
        pids = (self.root / "starts").read_text().splitlines()
        self.assertEqual(len(pids), 2)
        self.assertFalse(any(Path(f"/proc/{pid}").exists() for pid in pids))

    def test_boot_timeout_reaps_child(self):
        self.start("boot-timeout", ready=False)
        self.assert_headers_refused("not-ready")
        for _ in range(175):
            if self.http()[1]["counts"].get("session_failures") == 2:
                break
            time.sleep(0.015)
        starts = (self.root / "starts").read_text().splitlines()
        self.assertEqual(len(starts), 2)
        self.assertFalse(any(Path(f"/proc/{pid}").exists() for pid in starts))

    def test_source_identity_checked_before_model_loading(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "pins.json"
            path.write_text("{}")
            with patch.dict("os.environ", CLASSIFICATION_CONTRACT_DIR=temp), self.assertRaises(ValueError):
                bootstrap.load()
