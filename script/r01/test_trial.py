"""Regressões do verificador. Os estados observados aqui são sintéticos."""
import hashlib
import io
import json
import runpy
import sys
import unittest
from contextlib import nullcontext, redirect_stdout
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
# A lógica de leitura de snapshots é a mesma da sonda; estes testes não abrem conexões.
fallback = {}
if find_spec("confluent_kafka") is None:
    fallback["confluent_kafka"] = Mock()
    fallback["confluent_kafka"].libversion.return_value = ("2.12.0", 0x20C00FF)
    fallback["confluent_kafka"].version.return_value = "2.12.2"
    fallback["confluent_kafka.admin"] = Mock()
if find_spec("psycopg") is None:
    fallback["psycopg"] = Mock()

with (patch.dict(sys.modules, fallback),
      patch.object(sys, "path", [*sys.path, str(ROOT / "integration"), str(ROOT / "script/f07")])):
    import trial
    import observe
    import scenarios
    import http_client


class CanonicalTest(unittest.TestCase):
    def setUp(self):
        self.t = Mock()
        self.t.send.side_effect = [{"case_id": "retry"}, {"case_id": "handoff"}]
        self.t.staff.return_value = (Mock(), {})
        self.t.input.return_value = {"category": "pix"}
        self.started = False
        self.discard_visible = False
        self.drained = False
        self.receipts = {}
        self.records = {}
        self.initial = {}
        self.final = {}
        for case_id in ("retry", "handoff"):
            expired = case_id + "-A"
            customer = {"type": "customer", "event_id": "entrada"}
            original = {"id": case_id, "messages": [customer], "integration_status": "failed", "version": 1,
                        "outbox": [{"event_id": expired, "published": True}],
                        "audits": [{"type": "agent.result.expired", "event_id": expired}]}
            self.initial[case_id] = original
            row = {**original, "audits": original["audits"].copy()}
            self.final[case_id] = row
            self.records[case_id] = []
            for request in ([expired, "retry-B"] if case_id == "retry" else [expired]):
                event_id = "resultado-" + request
                event = {"case_id": case_id, "event_id": event_id, "payload": {"request_event_id": request}}
                raw = json.dumps(event).encode()
                self.records[case_id].append(observe.Record("agent.events", 0, 17, case_id.encode(), raw))
                self.receipts[event_id] = [{"event_id": event_id, "sha256": hashlib.sha256(raw).hexdigest(),
                                            "disposition": "applied" if request == "retry-B" else "discarded"}]
                if request == expired:
                    row["audits"].append({"type": "agent.result.discarded", "event_id": event_id})
                else:
                    row["audits"].append({"type": "agent.reply.proposed", "event_id": event_id})
                    row["messages"] = [customer, {"type": "ai", "event_id": event_id}]
                    row["outbox"] = [{"event_id": request, "published": True}, *original["outbox"]]
        self.human = {**self.initial["handoff"], "status": "human_active", "assignee_id": "atendente",
                      "assignment_generation": 2}
        self.final["handoff"].update({k: self.human[k] for k in ("status", "assignee_id", "assignment_generation")})
        self.seen = set()
        self.t.db.case.side_effect = self.snapshot
        self.t.db.receipt.side_effect = lambda event_id: self.receipts[event_id]
        self.t.kafka.records.side_effect = lambda topic, key: self.records[key]

    def snapshot(self, case_id):
        if self.drained:
            return self.final[case_id]
        if case_id not in self.seen:
            self.seen.add(case_id)
            return self.initial[case_id]
        if case_id == "handoff":
            return self.human
        if not self.started:
            return {**self.initial[case_id], "outbox": self.final[case_id]["outbox"]}
        if self.discard_visible:
            return self.final[case_id]
        # O descarte pode tornar-se visível só ao fim da drenagem.
        return {**self.final[case_id], "audits": self.initial[case_id]["audits"]}

    def run_trial(self):
        def spawn(*_):
            self.started = True

        def drain(_):
            self.drained = True
            return [{"backlog": 0}]

        def until(label, sample, predicate=bool, **kwargs):
            value = sample()
            self.assertTrue(predicate(value), label)
            return value

        with (patch.object(trial, "drained", side_effect=drain), patch.object(trial, "until", side_effect=until),
              patch.object(trial, "emit") as emit, patch.object(trial, "spawn", side_effect=spawn)):
            trial.canonical(self.t, None, None)
        return emit.call_args.kwargs

    def test_distinct_rounds_and_discard_after_drain(self):
        self.records["retry"].append(self.records["retry"][0])
        report = self.run_trial()
        self.assertTrue(self.drained)
        expected = [("retry-A", "discarded"), ("retry-B", "applied"), ("handoff-A", "discarded")]
        rounds = report["retry_rounds"] + report["handoff_rounds"]
        self.assertCountEqual([(r["request_event_id"], r["receipt"]["disposition"]) for r in rounds], expected)

    def test_inverted_rounds_with_consistent_counts(self):
        self.discard_visible = True
        old, fresh = "resultado-retry-A", "resultado-retry-B"
        self.final["retry"]["messages"][-1]["event_id"] = old
        for audit in self.final["retry"]["audits"]:
            if audit["type"] == "agent.result.discarded":
                audit["event_id"] = fresh
            elif audit["type"] == "agent.reply.proposed":
                audit["event_id"] = old
        self.receipts[old][0]["disposition"], self.receipts[fresh][0]["disposition"] = "applied", "discarded"
        with self.assertRaisesRegex(AssertionError, "applied divergente"):
            self.run_trial()

    def test_current_round_requires_matching_audit(self):
        self.final["retry"]["audits"][-1]["event_id"] = "resultado-retry-A"
        with self.assertRaisesRegex(AssertionError, "auditoria"):
            self.run_trial()

    def test_handoff_rejects_discard_of_another_event(self):
        self.final["handoff"]["audits"][-1]["event_id"] = "resultado-retry-A"
        with self.assertRaisesRegex(AssertionError, "discarded divergente"):
            self.run_trial()

    def test_handoff_requires_actual_kafka_result(self):
        self.records["handoff"].clear()
        with self.assertRaisesRegex(AssertionError, "retorno ausente"):
            self.run_trial()

    def test_receipt_digest_is_checked_against_kafka(self):
        self.receipts["resultado-retry-B"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "recibo divergente"):
            self.run_trial()


class RecoveryWindowTest(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.health = Mock()
        self.clock = patch.object(trial, "time").start()
        self.addCleanup(patch.stopall)
        self.clock.monotonic.side_effect = lambda: self.now
        self.clock.sleep.side_effect = self.advance

    def advance(self, delta):
        self.now += delta

    def wait(self, observer):
        return trial.wait_recovery("lag zero", observer, trial.DRAIN_SECONDS, self.health)

    def test_backlog_then_drain_within_budget(self):
        self.assertEqual(trial.DRAIN_SECONDS, 120)
        self.assertEqual(self.wait(Mock(side_effect=[None, {"backlog": 0}])), {"backlog": 0})
        self.health.assert_not_called()

    def test_backlog_through_deadline(self):
        self.now = 119.75
        with self.assertRaisesRegex(AssertionError, "120s.*lag zero"):
            self.wait(lambda: False)
        self.health.assert_called_once()
        self.assertEqual(self.now, 120)

    def test_deadline_uses_http_status_and_health_body(self):
        for code, body_status in ((500, "ok"), (502, "ok"), (503, "ok"), (504, "ok"),
                                  (200, "degraded"), (200, "ok")):
            with self.subTest(code=code, body=body_status):
                t, owner, peer = Mock(), Mock(), Mock()
                t.input.return_value = {}
                t.send.return_value = {"case_id": "case"}
                owner.events.return_value = [{"partition": 1, "offset": 17}]
                peer.events.return_value = []
                t.kafka.offsets.return_value = {"backlog": 1, "committed_next_offset": 17}
                t.db.case.return_value = {"status": "ai_active"}
                t.http = http_client.Browser()
                body = io.BytesIO(json.dumps({"status": body_status}).encode())
                # urllib entrega HTTPErrors ao mesmo decodificador que trata HTTP 200.
                if code == 200:
                    body.code = code
                    t.http.http.open = Mock(return_value=body)
                else:
                    t.http.http.open = Mock(side_effect=HTTPError("http://api/health", code, "", {}, body))
                self.clock.monotonic.side_effect = [0, 120]
                healthy = code == 200 and body_status == "ok"
                with (patch.object(trial, "spawn", side_effect=[Mock(), owner, peer]),
                      patch.object(trial, "until", side_effect=[1, 1, 1, owner.events.return_value]),
                      patch.object(trial, "emit") as emit,
                      self.assertRaisesRegex(AssertionError if healthy else observe.Blocked,
                                             "120s" if healthy else "Rails")):
                    trial.transfer(t, "mock", None, None)
                t.db.case.assert_called_once_with("case")
                self.assertEqual(t.http.http.open.call_args.args[0].selector, "/api/v1/health")
                self.assertEqual(emit.call_count, int(healthy))

    def test_late_positive_observation(self):
        def late():
            self.advance(121)
            return True
        with self.assertRaisesRegex(AssertionError, "Prazo"):
            self.wait(late)

    def test_failed_observer_is_inconclusive(self):
        with self.assertRaises(observe.Blocked):
            self.wait(Mock(side_effect=observe.Blocked("consulta de offset indisponível")))
        self.now = 120
        self.health.side_effect = OSError("banco indisponível")
        with self.assertRaises(OSError):
            self.wait(lambda: False)


class ReportTest(unittest.TestCase):
    def test_versions_and_failure_verdicts(self):
        # Executa o ponto de entrada e intercepta a abertura do banco antes de qualquer conexão.
        imports = {**fallback, "observe": observe, "scenarios": scenarios, "http_client": http_client}
        for error, status in ((AssertionError("prazo"), "reprovado"), (observe.Blocked("sonda"), "inconclusivo")):
            with self.subTest(status=status), patch.dict(sys.modules, imports), redirect_stdout(io.StringIO()) as output:
                sdk = nullcontext()
                if "confluent_kafka" in fallback:
                    sdk = patch("importlib.metadata.version", side_effect={"confluent-kafka": "2.12.2"}.__getitem__)
                with sdk, patch.object(observe, "Database", side_effect=error), self.assertRaises(type(error)):
                    runpy.run_path(trial.__file__, run_name="__main__")
                params, result = map(json.loads, output.getvalue().splitlines())
                self.assertEqual(params["confluent_kafka"], "2.12.2")
                self.assertRegex(params["librdkafka"], r"^\d+\.\d+\.\d+")
                self.assertEqual(result["status"], status)
