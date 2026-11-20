import hashlib
import hmac
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest
import uuid
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from protocol import BRANDS, DIRECTORY, KINDS, append, bytes_json, plan, write_json
from report import chat_summary, distribution, index_cases, publish, reconcile, resource_summary, times
from run import arguments, configurations, console, Stack


class PlanningTests(unittest.TestCase):
    def test_reference_defaults_and_balance(self):
        configs = list(configurations(arguments(["reference"])))
        self.assertEqual([item["fault_after_seconds"] for item in configs], [None, 60] * 3)
        self.assertEqual([item["fault_seconds"] for item in configs], [None, 30] * 3)
        self.assertTrue(all(item["stages"] == [(5, 300)] and item["observe_seconds"] == 120 for item in configs))
        for seed in (0, 1, 5, 8026):
            rows = plan("f08-test", seed, configs[0]["stages"])
            self.assertEqual(rows, plan("f08-test", seed, configs[0]["stages"]))
            self.assertEqual(len({row["initial"]["source_event_id"] for row in rows}), 1500)
            self.assertEqual(Counter((r["brand"], r["kind"]) for r in rows),
                             Counter({(b, k): 250 for b in BRANDS for k in KINDS}))
            followups = [row for row in rows if row["second"]]
            self.assertEqual(Counter((r["brand"], r["kind"]) for r in followups),
                             Counter({(b, k): 50 for b in BRANDS for k in KINDS}))
            self.assertEqual(len(followups), 300)
            self.assertTrue(all(r["initial"]["external_conversation_id"] == r["second"]["external_conversation_id"]
                                and r["initial"]["source_event_id"] != r["second"]["source_event_id"] for r in followups))
        self.assertNotEqual(plan("x", 10, [(5, 300)]), plan("x", 11, [(5, 300)]))

    def test_modes_and_partial_plan(self):
        self.assertEqual([c["chat"]["target"] for c in configurations(arguments(["chat"]))], [100, 1000, 10000])
        self.assertEqual(next(configurations(arguments(["smoke"])))["stages"], [(5, 3)])
        stages = next(configurations(arguments(["ramp", "--stage", "2:3", "--stage", "4:8"])))["stages"]
        self.assertEqual(stages, [(2, 3), (4, 8)])
        self.assertEqual(sum(bool(row["second"]) for row in plan("x", 8026, stages)), 7)
        self.assertTrue(all(row["second"] is None and row["initial"]["priority"] == "advanced"
                            for row in plan("x", 8026, stages, human=True)))

    @unittest.skipUnless(shutil.which("docker"), "Docker CLI ausente")
    def test_isolated_compose_compiles(self):
        config = Stack(DIRECTORY).configuration()
        self.assertIn("generator", config)
        self.assertIn("observe", config)
        self.assertIn("kafka", config)


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.body = plan("test", 1, [(1, 1)])[0]["initial"]
        source = self.body["source_event_id"]
        result = str(uuid.uuid5(uuid.NAMESPACE_URL, "cloudwalk:mock-agent-v1:request"))
        self.case = {
            "case_id": "case", "channel_id": "channel", "correlation_id": "corr", "status": "ai_active",
            "integration_status": "idle", "resolved_ms": None,
            "entries": [{"source_event_id": source, "sha256": hashlib.sha256(bytes_json(self.body)).hexdigest()}],
            "messages": [{"id": "customer", "sequence": 1, "author": "customer", "source_event_id": source},
                         {"id": "reply", "sequence": 2, "author": "ai", "source_event_id": result, "created_ms": 400}],
            "turns": [{"id": "turn", "request_event_id": "request", "result_event_id": result,
                       "through_sequence": 1, "disposition": "applied", "published_ms": 300, "outbox_event_id": "request"}],
            "audits": [{"type": "case.opened", "event_id": None},
                       {"type": "channel.message.received", "event_id": None, "source_event_id": source},
                       {"type": "agent.reply.proposed", "event_id": result}],
        }
        self.attempt = {"status": 202, "case_id": "case", "correlation_id": "corr", "sent_ms": 100, "elapsed_ms": 50}

    def outcome(self, cases, attempt=None, snapshot=True, failures=frozenset()):
        return reconcile(self.body, "channel", self.attempt if attempt is None else attempt,
                         index_cases(cases), failures, snapshot)

    def test_complete_and_ambiguous_http(self):
        complete = self.outcome([self.case])
        ambiguous = self.outcome([self.case], {"status": 0, "sent_ms": 99, "error_code": 1050})
        self.assertEqual(complete["state"], "concluído")
        self.assertEqual(ambiguous["state"], "concluído")
        result = times([complete, ambiguous])
        self.assertEqual(result["acceptance_of_planned"], 0.5)
        self.assertEqual(result["latency_accept"]["p95"], 50)
        self.assertEqual(result["latency_persisted"]["p50"], 300)
        self.assertEqual(result["latency_persisted"]["p95"], 301)
        self.assertEqual(result["timeouts"], 1)

    def test_loss_pending_failure_and_missing_observer_are_distinct(self):
        self.assertTrue(self.outcome([])["confirmed_loss"])
        self.assertFalse(self.outcome([], snapshot=False)["confirmed_loss"])
        self.assertEqual(self.outcome([], {"sent_ms": 100, "status": 503})["state"], "ausente sem aceite")
        self.case["messages"].pop()
        self.assertTrue(self.outcome([self.case])["confirmed_loss"])
        self.case["turns"][0].update(disposition=None, result_event_id=None)
        self.assertEqual(self.outcome([self.case])["state"], "pendente")
        self.assertFalse(self.outcome([self.case])["confirmed_loss"])
        self.assertEqual(self.outcome([self.case], failures={"request"})["state"], "falho")

    def test_duplicate_effect_and_mismatched_receipt(self):
        self.case["messages"].append({**self.case["messages"][-1], "id": "duplicate", "sequence": 3})
        self.assertTrue(self.outcome([self.case])["duplicate_effect"])
        different = self.outcome([self.case], {**self.attempt, "case_id": "other"})
        self.assertTrue(different["identity_inconsistent"])

    def test_full_aggregation_distinguishes_repeated_kafka_from_duplicate_effect(self):
        entries = plan("test", 1, [(1, 1)])
        entry = entries[0]
        config = next(configurations(arguments(["smoke", "--rate", "1", "--seconds", "1"])))
        manifest = {"run_id": "f08-test", "revision": "a" * 40, "scenario": "smoke", "parameters": config,
                    "window": {"start_ms": 10, "arrivals_end_ms": 1010, "end_ms": 6010}, "k6_exit": 0,
                    "observation": {"kafka_records": {"complete": True}}}
        event = {"type": "initial", "source_event_id": self.body["source_event_id"],
                 "scenario_start_ms": 10, **self.attempt}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            write_json(output / "ready.json", {"channels": {entry["brand"]: {entry["kind"]: "channel"}}})
            write_json(output / "persistence.json", {"sample_ms": 6011, "cases": [self.case]})
            write_json(output / "k6-summary.json", {"iterations": {"count": 1}})
            append(output / "sql-samples.jsonl", {"sample_ms": 5000, "cost_ms": 1,
                   "outbox_pending": 0, "outbox_failed": 0, "cases_waiting_processing": 0, "cases_failed": 0,
                   "cases_waiting_human": 0, "cases_human_active": 0, "cases_waiting_customer": 0,
                   "classification_requests": 0, "classification_attempts": 0})
            append(output / "kafka-lag.jsonl", {"sample_ms": 5000, "cost_ms": 1, "total_lag": 0})
            for offset in (0, 1):
                append(output / "kafka-records.jsonl", {"topic": "agent.events", "event_id": "repeat", "offset": offset})
            publish(output, manifest, entries, [event])
            result = json.loads((output / "report.json").read_text())
            self.assertEqual(result["state"], "aprovado")
            self.assertEqual(result["kafka"]["repeated_records_observed"], 1)
            self.assertEqual(result["integrity"]["duplicated_effect_identities"], 0)
            self.assertTrue(result["goals"]["escoamento_na_janela"])
            self.assertEqual(result["initial"]["latency_persisted"]["p95"], 300)

    def test_empty_quantiles_and_resource_units(self):
        self.assertEqual(distribution([None]), {"unit": "ms", "n": 0, "p50": None, "p95": None})
        stats = resource_summary([{"containers": [{"container": "cloudwalk_f08_load-generator-run-a",
                                                    "cpu_percent": "102.10%", "ram_used_limit": "1.5MiB / 1GiB"}]}])
        self.assertEqual(stats["per_service"]["generator"]["ram_bytes_peak"], 1572864)
        self.assertEqual(stats["per_service"]["generator"]["cpu_percent_peak"], 102.10)

    def test_chat_concurrency_counts_only_overlapping_confirmations(self):
        config = {"target": 3, "ramp_seconds": 1, "hold_seconds": 5, "period_seconds": 100}
        event = lambda at, client, name: {"type": "subscription_" + name, "at_ms": at, "client": client}
        samples = [event(100, 1, "confirmed"), event(1500, 2, "confirmed"), event(3000, 2, "closed"),
                   event(4500, 3, "confirmed"), event(6000, 3, "closed")]
        result = chat_summary(samples, config, {"start_ms": 0, "arrivals_end_ms": 6000}, [])
        self.assertEqual(result["unique_confirmed_clients"], 3)
        self.assertEqual(result["peak_confirmed_steady"], 2)
        self.assertEqual(result["average_confirmed_steady"], 1.6)


@unittest.skipUnless(shutil.which("k6"), "k6 ausente no host")
class K6ConfigurationTests(unittest.TestCase):
    def test_scripts_initialize_and_emit_expected_execution_requirements(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            write_json(path / "config.json", {"stages": [(2, 1), (3, 2)], "vus": 4, "channels": {},
                       "chat": {"target": 100, "ramp_seconds": 120, "hold_seconds": 300, "period_seconds": 100}})
            write_json(path / "plan.json", [])
            for script, scenarios in (("generate.js", {"stage_0", "stage_1"}), ("chat.js", {"chat"})):
                result = subprocess.run(["k6", "inspect", "--execution-requirements", "-e",
                                         f"F08_CONFIG={path / 'config.json'}", "-e", f"F08_PLAN={path / 'plan.json'}",
                                         str(DIRECTORY / script)], text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(set(json.loads(result.stdout)["scenarios"]), scenarios)

    def test_k6_hmac_utf8_without_network(self):
        raw = bytes_json({"text": "Confirmação do Pix?"})
        key = hmac.new(b"test-only", b"channel:demo", "sha256").hexdigest()
        expected = hmac.new(key.encode(), b"1700000000." + raw, "sha256").hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            log = path / "console.jsonl"
            result = subprocess.run(["k6", "run", "--iterations", "1", "--address", "", "--log-format", "raw",
                                     "--no-usage-report", "--console-output", str(log),
                                     "-e", f"F08_K6_SUMMARY={path / 'summary.json'}", str(DIRECTORY / "test_wire.js")],
                                    text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(console(log)), [{"signature": expected}])
            self.assertEqual(json.loads((path / "summary.json").read_text())["iterations"]["count"], 1)


class Endpoint(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        stamp = self.headers["X-Webhook-Timestamp"]
        channel = self.path.split("/")[-2]
        key = hmac.new(b"test-only", ("channel:" + channel).encode(), "sha256").hexdigest()
        signature = hmac.new(key.encode(), stamp.encode() + b"." + raw, "sha256").hexdigest()
        status = 202 if signature == self.headers.get("X-Webhook-Signature") else 401
        self.server.requests.append((raw, status))
        time.sleep(self.server.delay)
        data = b'{"case_id":"case","correlation_id":"corr"}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@unittest.skipUnless(shutil.which("k6"), "k6 ausente no host")
class GeneratorTests(unittest.TestCase):
    def run_generator(self, stages, vus, delay):
        try:
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
        except PermissionError:
            self.skipTest("sandbox não permite abrir socket TCP local")
        with tempfile.TemporaryDirectory() as temporary, ThreadingHTTPServer(("127.0.0.1", 0), Endpoint) as server:
            path = Path(temporary)
            planned = plan("f08-local", 8026, stages)
            server.requests, server.delay = [], delay
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                channels = {brand: {kind: f"{brand}-{kind}" for kind in KINDS} for brand in BRANDS}
                write_json(path / "config.json", {"stages": stages, "vus": vus, "channels": channels})
                write_json(path / "plan.json", planned)
                env = {**os.environ, "F08_CONFIG": str(path / "config.json"), "F08_PLAN": str(path / "plan.json"),
                       "F08_K6_SUMMARY": str(path / "summary.json"), "CLOUDWALK_CHANNEL_SECRET": "test-only",
                       "F08_API": f"http://127.0.0.1:{server.server_port}"}
                log = path / "console.jsonl"
                result = subprocess.run(["k6", "run", "--no-usage-report", "--no-color", "--log-format", "raw",
                                         "--address", "", "--console-output", str(log), str(DIRECTORY / "generate.js")],
                                        env=env, text=True, capture_output=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((path / "summary.json").exists(), result.stderr)
                events = list(console(log))
                self.assertEqual(events[0]["type"], "setup")
                self.assertEqual({row[1] for row in server.requests}, {202})
                by_id = {row["initial"]["source_event_id"]: bytes_json(row["initial"]) for row in planned}
                for raw, _ in server.requests:
                    self.assertEqual(raw, by_id[json.loads(raw)["source_event_id"]])
                return events[1:], json.loads((path / "summary.json").read_text())
            finally:
                server.shutdown()
                thread.join()

    def test_two_open_stages_keep_distinct_planned_identities(self):
        events, summary = self.run_generator([(2, 1), (3, 1)], 4, 0)
        self.assertEqual(sorted(row["index"] for row in events), list(range(5)))
        self.assertEqual(summary["http_reqs"]["count"], 5)
        self.assertEqual(len({row["scenario_start_ms"] for row in events}), 2)

    def test_slow_endpoint_leaves_dropped_iterations_visible(self):
        events, summary = self.run_generator([(20, 1)], 1, 0.35)
        self.assertTrue(all(row["status"] == 202 for row in events))
        self.assertGreater(summary["dropped_iterations"]["count"], 0)
        self.assertEqual(summary["dropped_iterations"]["count"] + len(events), 20)


if __name__ == "__main__":
    unittest.main()
