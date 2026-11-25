import contextlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import kafka_capture
import kafka_probe
import observe
from protocol import DIRECTORY, append, now_ms, plan, rows, write_json


def sample_reply():
    parts = [{"topic": topic, "partition": part, "group": group, "start_offset": 0, "end_offset": 1,
              "effective_next": 1, "committed_next": 1, "lag": 0}
             for topic, group in kafka_probe.GROUPS.items() for part in range(3)]
    return {"partitions": parts, "offsets": [
        {"topic": topic, "partition": part, "offset": 1} for topic in kafka_probe.TOPICS for part in range(3)],
        "versions": {"confluent_kafka": "2.12.2", "librdkafka": "teste"}}


class FinalRangeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.output = Path(directory.name)
        self.baseline = {("agent.events", 0): 2, ("agent.requests", 1): 4}
        self.ends = {("agent.events", 0): 12, ("agent.requests", 1): 14}

    def attempts(self):
        return list(rows(self.output / "kafka-capture-attempts.jsonl"))

    def test_first_metadata_failure_then_fixed_valid_range(self):
        class KafkaException(Exception):
            pass

        detail = Mock()
        detail.code.return_value = -185
        detail.name.return_value = "_TIMED_OUT"
        read = Mock(side_effect=[KafkaException(detail), self.ends, RuntimeError("intervalo já fixado")])
        result = kafka_capture.freeze_range(self.output, self.baseline, read, (KafkaException, TimeoutError))
        self.assertEqual(result, self.ends)
        self.assertEqual(read.call_count, 2)
        attempts = self.attempts()
        self.assertEqual([row["status"] for row in attempts], ["started", "failed", "started", "fixed"])
        self.assertEqual(attempts[1]["kafka_name"], "_TIMED_OUT")
        self.assertEqual(attempts[1]["kafka_code"], -185)
        fixed = json.loads((self.output / "kafka-offset-range.json").read_text())
        self.assertEqual(fixed["attempt"], 2)
        self.assertEqual({(p["topic"], p["partition"]): (p["start"], p["end"]) for p in fixed["partitions"]},
                         {k: (self.baseline[k], end) for k, end in self.ends.items()})

    def test_exhausted_queries_cannot_create_artifacts_or_claim_zero_records_expected(self):
        with self.assertRaises(TimeoutError):
            kafka_capture.freeze_range(self.output, self.baseline, Mock(side_effect=TimeoutError), (TimeoutError,))
        self.assertEqual([i["attempt"] for i in self.attempts() if i["status"] == "failed"], [1, 2, 3])
        self.assertFalse((self.output / "kafka-offset-range.json").exists())
        self.assertFalse((self.output / "kafka-records.jsonl").exists())

    def test_invalid_range_or_expired_global_bound_cannot_be_frozen(self):
        for result in ({("other", 0): 5}, {**self.ends, ("agent.events", 0): 1}):
            with self.subTest(result=result), self.assertRaises(ValueError):
                read = Mock(return_value=result)
                kafka_capture.freeze_range(self.output, self.baseline, read, (TimeoutError,))
            self.assertEqual(read.call_count, 1)
        with patch.object(kafka_capture.time, "monotonic", side_effect=[0, 1, 19, 20]), self.assertRaises(TimeoutError):
            kafka_capture.freeze_range(self.output, self.baseline, Mock(return_value=self.ends), (TimeoutError,))
        self.assertFalse((self.output / "kafka-offset-range.json").exists())


class KafkaProbeTests(unittest.TestCase):
    def test_parent_imports_no_native_kafka_module(self):
        cmd = [sys.executable, "-B", "-c", "import sys, observe; assert 'confluent_kafka' not in sys.modules"]
        subprocess.run(cmd, cwd=DIRECTORY, check=True, timeout=3)

    def test_bounded_timeout_exit_eof_and_invalid_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "reader.py"
            marker = Path(tmp) / "pid"
            cases = [
                ("import time; time.sleep(50)", "prazo_excedido"),
                ("import os,time; os.close(1); time.sleep(50)", "prazo_excedido"),
                ("import os, signal; os.kill(os.getpid(),signal.SIGTERM)", f"sinal_{signal.SIGTERM.value}"),
                ("raise SystemExit(7)", "saida_7"), ("pass", "resposta_incompleta"),
                ("print('{')", "resposta_invalida"), ("print('x' * 9000)", "resposta_excessiva"),
                ("print('{}')", "resposta_invalida"), ("print('{}', end='')", "resposta_incompleta"),
            ]
            for code, reason in cases:
                with self.subTest(reason=reason, code=code):
                    script.write_text(f"import os; open({str(marker)!r}, 'w').write(str(os.getpid()))\n" + code)
                    started = time.monotonic()
                    with patch.object(kafka_probe, "READER", script), self.assertRaisesRegex(kafka_probe.KafkaProbeError, reason):
                        kafka_probe.probe("sample", timeout=0.35)
                    self.assertLess(time.monotonic() - started, 2)
                    with self.assertRaises(ProcessLookupError):
                        os.kill(int(marker.read_text()), 0)

    def test_valid_new_process_and_incomplete_partition_coverage(self):
        valid = sample_reply()
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "reader.py"
            script.write_text("import os; assert 'POSTGRES_PASSWORD' not in os.environ\nprint(" +
                              repr(json.dumps(valid)) + ")")
            with patch.dict(os.environ, POSTGRES_PASSWORD="synthetic"), patch.object(kafka_probe, "READER", script):
                self.assertEqual(kafka_probe.probe("sample"), valid)
                valid["partitions"].pop()
                script.write_text("print(" + repr(json.dumps(valid)) + ")")
                kafka_probe.sample_kafka(Path(tmp))
                row, = rows(Path(tmp) / "kafka-lag.jsonl")
                self.assertIsNone(row["total_lag"])
                self.assertEqual(row["error"], "resposta_invalida")
        for response in ({"complete": True}, {"complete": True, "records_read": 1, "expected_offsets": 2}):
            with self.assertRaises((KeyError, ValueError)):
                kafka_probe.validate("records", response)

    def test_sql_followup_and_snapshot_survive_worker_exit_and_partial_evidence(self):
        self.check_observer_continuity("os.kill(os.getpid(),signal.SIGTERM)", f"sinal_{signal.SIGTERM.value}")

    def test_sql_followup_and_snapshot_survive_hung_worker(self):
        self.check_observer_continuity("time.sleep(30)", "prazo_excedido")

    def check_observer_continuity(self, first_outcome, expected_error):
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as mocks:
            output = Path(tmp)
            script, started_marker = output / "reader.py", output / "started"
            valid_sample = repr(json.dumps(sample_reply()))
            script.write_text(
                "import sys,time,os,signal\nfrom pathlib import Path\n"
                f"marker=Path({str(started_marker)!r})\n"
                "if sys.argv[1]=='records': raise SystemExit(7)\n"
                f"if not marker.exists():\n marker.write_text(str(os.getpid()))\n time.sleep(0.45)\n {first_outcome}\n"
                f"print({valid_sample})")
            entries = plan("test", 1, [(5, 1)])
            entry = next(row for row in entries if row["second"])
            write_json(output / "plan.json", entries)
            write_json(output / "config.json", {"run_id": "test", "scenario": "smoke"})
            write_json(output / "window.json", {"end_ms": now_ms() + 120000})
            write_json(output / "kafka-offset-range.json", {"partitions": [
                {"topic": "agent.events", "partition": 0, "start": 1, "end": 3}]})
            append(output / "kafka-capture-attempts.jsonl", {"phase": "read_records", "status": "started",
                                                             "attempt": 1, "started_ms": now_ms()})
            # Registro já lido antes de o auxiliar de captura encerrar.
            append(output / "kafka-records.jsonl", {"topic": "agent.events", "partition": 0, "offset": 1})
            sql_times, sent = [], []
            start = time.monotonic()
            cutoff = start + 5

            class DB:
                def execute(self, query, *args):
                    if query == observe.SQL_SAMPLE:
                        sql_times.append(time.monotonic())
                        samples = list(rows(output / "kafka-lag.jsonl"))
                        if len(samples) >= 2:
                            write_json(output / "finish.json", {})
                        if time.monotonic() > cutoff:
                            write_json(output / "finish.json", {})
                        return self
                    if query == observe.SQL_SNAPSHOT:
                        return []
                    if query == observe.SQL_FOLLOWUPS and started_marker.exists():
                        return [{"source_event_id": entry["initial"]["source_event_id"], "channel_id": "channel",
                                 "persisted_ms": now_ms() - 6000}]
                    return []

                def fetchone(self):
                    return {"outbox_pending": 0}

            def send(*args):
                # O PID da primeira leitura ainda deve existir quando o follow-up for enviado.
                os.kill(int(started_marker.read_text()), 0)
                sent.append(time.monotonic())
                return {"status": 202}

            # Só aceleramos a cadência do laço. Os limites do subprocesso usam o relógio monotônico real.
            clock_base = now_ms()
            mocks.enter_context(patch.object(observe, "now_ms", lambda: clock_base + int((time.monotonic() - start) * 10000)))
            mocks.enter_context(patch.object(observe, "RESULTS", output))
            mocks.enter_context(patch.object(observe, "database", lambda: contextlib.nullcontext(DB())))
            mocks.enter_context(patch.object(observe, "discover", return_value={}))
            mocks.enter_context(patch.object(observe, "readiness", return_value={"warmup_case_id": "warm"}))
            mocks.enter_context(patch.object(observe, "webhook", send))
            mocks.enter_context(patch.object(kafka_probe, "READER", script))
            real_probe = kafka_probe.probe
            mocks.enter_context(patch.object(kafka_probe, "probe", lambda op: real_probe(op, timeout=0.7)))
            observe.main()
            samples = list(rows(output / "kafka-lag.jsonl"))
            self.assertIsNone(samples[0]["total_lag"])
            self.assertEqual(samples[0]["error"], expected_error)
            self.assertGreaterEqual(samples[0]["cost_ms"], 400)
            self.assertEqual(samples[1]["total_lag"], 0)
            self.assertEqual(len(sent), 1)
            self.assertGreaterEqual(len(sql_times), 3)
            self.assertTrue((output / "persistence.json").exists())
            self.assertEqual(len(list(rows(output / "followups.jsonl"))), 1)
            self.assertEqual(len(list(rows(output / "kafka-records.jsonl"))), 1)
            evidence = json.loads((output / "observed.json").read_text())["kafka_records"]
            self.assertFalse(evidence["complete"])
            self.assertEqual(evidence["error"], "saida_7")
            self.assertEqual((evidence["records_read"], evidence["expected_offsets"]), (1, 2))
            self.assertEqual([a["status"] for a in evidence["attempts"]], ["started", "incomplete"])
            self.assertEqual(evidence["timeout_ms"], 52000)
