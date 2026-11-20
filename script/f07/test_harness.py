"""Testes isolados do verificador. Provas de produto são executadas por run.py."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import fault
import run


class ProxyTest(unittest.TestCase):
    path = "/webhooks/v1/agent/events"
    raw = b'{"event_id":"event-synthetic","text":"Caso de ensaio"}'

    def execute(self, state, status, *, body=None, headers=None, raw=None):
        raw = self.raw if raw is None else raw
        handler = SimpleNamespace(
            command="POST", path=self.path, server=SimpleNamespace(server_port=8080),
            headers={"Content-Length": str(len(raw)), **(headers or {})}, rfile=io.BytesIO(raw),
            respond=Mock(), json_response=Mock(),
        )
        origin = Mock()
        origin.getresponse.return_value = SimpleNamespace(
            status=status, read=lambda: json.dumps(body or {}).encode(), getheaders=lambda: [],
        )
        with patch.object(fault, "STATE", state), patch.object(fault.http.client, "HTTPConnection", return_value=origin):
            fault.Handler.handle_request(handler)
        return handler, origin

    def test_switches_to_502_only_after_success_then_preserves_retry(self):
        rules = fault.Rules()
        rules.arm("callback", {"path": self.path, "mode": "lose_response", "field": "event_id",
                               "value": "event-synthetic"})
        invalid, _ = self.execute(rules, 409)
        self.assertEqual(invalid.respond.call_args.args[0], 409)
        headers = {"X-Simulator-Session-Id": "simulator-synthetic", "Cookie": "private", "X-CSRF-Token": "secret"}
        first, origin = self.execute(rules, 200, body={"event_id": "event-synthetic", "disposition": "applied",
                                                       "secret": "hidden"}, headers=headers)
        first.json_response.assert_called_once_with(502, {"error": {"code": "f07_response_lost"}})
        self.assertEqual(origin.request.call_args.args[2], self.raw)
        self.assertEqual(origin.request.call_args.args[3]["Cookie"], "private")
        repeat, _ = self.execute(rules, 200, body={"event_id": "event-synthetic", "disposition": "duplicate"},
                                 headers=headers)
        self.assertEqual(repeat.respond.call_args.args[0], 200)
        attempts = rules.history("callback")
        self.assertEqual([row["downstream"] for row in attempts], [409, 502, 200])
        self.assertEqual(attempts[1]["receipt"], {"event_id": "event-synthetic", "disposition": "applied"})
        self.assertEqual(attempts[1]["expected_simulator_id"], "simulator-synthetic")
        self.assertNotIn("hidden", json.dumps(attempts))
        self.assertNotIn("private", json.dumps(attempts))
        self.assertNotIn("secret", json.dumps(attempts))

    def test_only_one_response_is_lost_when_two_matching_requests_overlap(self):
        rules = fault.Rules()
        rules.arm("callback", {"path": self.path, "mode": "lose_response", "field": "event_id",
                               "value": "event-synthetic"})
        first_match, first_mode = rules.match(self.path, self.raw, {})
        second_match, second_mode = rules.match(self.path, self.raw, {})
        self.assertEqual(rules.finish(first_match, first_mode, 202, {}, 202), 502)
        self.assertEqual(rules.finish(second_match, second_mode, 202, {}, 202), 202)

    def test_transient_failure_does_not_forward_and_is_selective(self):
        rules = fault.Rules()
        rules.arm("callback", {"path": self.path, "mode": "unavailable", "field": "event_id",
                               "value": "event-synthetic"})
        denied, origin = self.execute(rules, 200)
        denied.json_response.assert_called_once_with(503, {"error": {"code": "f07_transient"}})
        origin.request.assert_not_called()
        other, origin = self.execute(rules, 200, raw=b'{"event_id":"another-id"}')
        origin.request.assert_called_once()
        self.assertEqual(other.respond.call_args.args[0], 200)
        self.assertIsNone(rules.history("callback")[0]["upstream"])
        rules.set_enabled("callback", False)
        restored, origin = self.execute(rules, 200)
        origin.request.assert_called_once()
        self.assertEqual(restored.respond.call_args.args[0], 200)


class RunnerTest(unittest.TestCase):
    def run_with(self, *arguments, existing=False, product_status=None):
        recorded = []

        def invoke(args, *_unused, **_keywords):
            recorded.append(args)
            if args[:2] == ["docker", "info"] and not existing and product_status is None:
                raise run.StackUnavailable("daemon inacessível no teste isolado")
            if existing and args[-3:] == ["ps", "-a", "-q"]:
                return "container existente"
            return ""

        def probe(ids, report, _env):
            for item in ids:
                report["scenarios"][item] = {**run.CATALOG[item], "status": product_status, "evidence": {}}

        output = io.StringIO()
        with (
            tempfile.TemporaryDirectory() as runner_tmp,
            patch.object(sys, "argv", ["run.py", *arguments]),
            patch.object(run.tempfile, "gettempdir", return_value=runner_tmp),
            patch.object(run, "invoke", side_effect=invoke),
            patch.object(run, "probe", side_effect=probe),
            contextlib.redirect_stdout(output),
        ):
            exit_code = run.main()
        return exit_code, json.loads(output.getvalue()), recorded

    def test_daemon_block_has_five_structured_results_and_no_stack_operations(self):
        code, report, operations = self.run_with()
        self.assertEqual(code, 2)
        self.assertEqual(set(report["scenarios"]), set(run.CATALOG))
        self.assertTrue(all(item["status"] == "bloqueado" and item["precondition"] and not item["evidence"]
                            for item in report["scenarios"].values()))
        self.assertEqual([args[:2] for args in operations], [["docker", "info"]])

    def test_existing_project_is_left_alone(self):
        code, report, operations = self.run_with("--scenario", "05", existing=True)
        self.assertEqual(code, 2)
        self.assertEqual(set(report["scenarios"]), {"05"})
        self.assertIn("exige um projeto vazio", report["runner_error"])
        self.assertFalse(any("down" in args or "up" in args for args in operations))

    def test_product_regression_exits_nonzero_and_removes_only_its_project(self):
        code, report, operations = self.run_with("--scenario", "05", product_status="reprovado")
        self.assertEqual(code, 1)
        self.assertEqual(report["scenarios"]["05"]["status"], "reprovado")
        self.assertEqual(operations[-1], run.COMPOSE + ["down", "--volumes", "--remove-orphans"])


if __name__ == "__main__":
    unittest.main()
