"""Regressões C02 1/3/4. Subprocesso sintético isolado, sem modelo."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from argparse import Namespace
from unittest.mock import patch
from types import SimpleNamespace

import journal
import run as runner

from run import HERE, ResponseStream, c01, decode, encode, run


def adapter(action, observations_path=c01.FIXTURES / "observations.jsonl"):
    ready = Path(os.environ["CLASSIFICATION_READY_FILE"])
    tmp = ready.with_suffix(".tmp")
    tmp.write_text(encode(dict(runtime="fixture", hardware="cpu", peak_memory_bytes=10)))
    tmp.replace(ready)
    with Path(observations_path).open(encoding="utf8", newline="\n") as stream:
        fixtures = {o["id"]: o for o in map(decode, stream)}
    for line in sys.stdin.buffer:
        case_id = json.loads(line)["id"]
        if case_id == "ctl-duplo":
            if action == "die":
                os._exit(7)
            if action == "silent":
                time.sleep(30)
            if action == "invalid":
                print('{"bad":"id"}', flush=True)
                continue
        obs = dict(fixtures[case_id], run_id=os.environ["CLASSIFICATION_RUN_ID"],
                   identity=json.loads(os.environ["CLASSIFICATION_IDENTITY"]))
        if action == "spoof":
            obs["origin"] = "injected_control"
        if action == "always_valid":
            if obs["origin"] != "candidate":
                raise AssertionError("ID reservado chegou ao subprocesso")
            obs.update(choices={f: {"status": "predicted", "raw": {"category": "pix", "priority": "basic"}[f], "reason": None}
                                for f in obs["choices"]},
                       returned_model=obs["identity"]["requested_model"], requests=1,
                       questions=len(obs["choices"]), request_usage=[dict(input_tokens=3, output_tokens=1,
                       observed_api_usd=.01, estimated_api_usd=None, tariff=None)])
            obs.pop("version_error_raw", None)
        if case_id == "ctl-simples":
            obs["request_usage"][0]["observed_api_usd"] = 0.01
        sys.stdout.buffer.write(encode(obs).encode("utf8") + b"\r\n")
        sys.stdout.buffer.flush()
    if action == "trailing":
        os.write(1, b"fragment")
    if action == "exit_error":
        sys.exit(7)
    if action.startswith("peak="):
        final = Path(os.environ["CLASSIFICATION_FINAL_FILE"])
        tmp = final.with_suffix(".tmp")
        tmp.write_text(encode({"peak_memory_bytes": json.loads(action[5:])}))
        tmp.replace(final)


class RoundOne(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def execute(self, action, answers=None):
        config = c01.read(HERE / "fixture.json")
        config["command"] = [sys.executable, "-B", str(Path(__file__).resolve()), "--adapter", action]
        split = "control"
        if answers is not None:
            config["command"].append(str(answers))
            config["identity"]["mode"] = "real"
            split = "final_test"
        config_path = self.path / "config.json"
        config_path.write_text(encode(config))
        self.output = self.path / action
        run(Namespace(config=config_path, split=split, limit=None, mode=config["identity"]["mode"], output=self.output,
                      concurrency=1, attempts=1, dry_run=False))

    def synthetic_final_answers(self, downgrade_urgent=False):
        _, _, split, _, cases, example = runner.preflight()
        observations = [o for o in example["observations"] if o["origin"] == "candidate"]
        template = next(o for o in observations if o["id"] == "ctl-simples")
        for group in split["final_test"].values():
            for case_id in group:
                choices = {}
                for field, raw in cases[case_id]["expected"].items():
                    if downgrade_urgent and field == "priority" and raw == "urgent":
                        raw = "basic"
                    abstained = raw == c01.ABSTENTION
                    choices[field] = dict(raw=raw, status="abstained" if abstained else "predicted",
                                          reason="explicit" if abstained else None)
                observations.append(dict(template, id=case_id, choices=choices, questions=len(choices),
                                         temperature_state="warm"))
        path = self.path / "synthetic-answers.jsonl"
        path.write_text("".join(encode(o) + "\n" for o in observations), encoding="utf-8")
        return path

    def check_interrupted_final(self):
        manifest = c01.read(self.output / "interruption.json")
        plan = c01.read(self.output / "plan.json")
        self.assertEqual(manifest["eligibility"], "inconclusive")
        self.assertEqual(manifest["completed_ids"], plan["planned_ids"] + plan["control_ids"])
        self.assertEqual(len(manifest["completed_ids"]), 49)
        self.assertIsNone(manifest["interrupted_id"])
        self.assertEqual(manifest["not_started_ids"], [])
        self.assertEqual(manifest["injected_controls"]["count"], 1)
        self.assertEqual(manifest["verified_prefix_usage"]["attempts"]["value"], 44)
        for kind in c01.KINDS:
            path = c01.source_path(manifest["artifacts"][f"verified_{kind}.jsonl"])
            self.assertEqual(c01.read_records(path), c01.read_records(self.output / f"{kind}.jsonl"))
        for name in ("report.md", "report.json", "report.tmp", "prefix-report.json"):
            self.assertFalse((self.output / name).exists(), name)
        descriptive = (self.output / "prefix-report.md").read_text(encoding="utf-8")
        self.assertIn("Elegibilidade inconclusiva", descriptive)
        self.assertNotRegex(descriptive, r"\b(pass|fail)\b")
        self.assertIn("36 relatos e 13 controles", descriptive)
        self.assertIn("ms (n=36)", descriptive)

    def test_interrupted_final_after_all_decisions(self):
        for action, message, downgrade in (("trailing", "stdout adicional", False),
                                           ("exit_error", "encerrou com erro", True),
                                           ("peak=true", "peak_memory_bytes", False)):
            with self.subTest(action=action):
                answers = self.synthetic_final_answers(downgrade)
                with self.assertRaisesRegex(ValueError, message):
                    self.execute(action, answers)
                self.check_interrupted_final()

    def test_successful_final_publishes_verdict(self):
        for verdict in ("pass", "fail"):
            with self.subTest(verdict=verdict):
                self.execute(verdict, self.synthetic_final_answers(downgrade_urgent=verdict == "fail"))
                report = c01.read(self.output / "report.json")
                self.assertEqual(report["eligibility"], verdict)
                self.assertEqual(report["identity"]["mode"], "real")
                self.assertEqual(len(report["completed_ids"]), 36)
                self.assertEqual(len(report["control_ids"]), 13)
                self.assertEqual(report["latency_p50_ms"]["denominator"], 36)
                self.assertTrue(all(m["state"] == "measured" for m in report["gates"].values()))
                self.assertIn(f"Elegibilidade {verdict}", (self.output / "report.md").read_text())
                self.assertFalse((self.output / "interruption.json").exists())

    def test_interruption_during_final_publication(self):
        dump = json.dump
        event = journal.Journal.event
        answers = self.synthetic_final_answers()

        def partial_json(value, file, **kwargs):
            if Path(file.name).name == "report.tmp":
                file.write("{")
                raise OSError("gravação parcial do relatório")
            dump(value, file, **kwargs)

        def unfinished(journal, name, **details):
            if name == "finished":
                raise OSError("falha no fechamento do diário")
            event(journal, name, **details)

        for stage, failure in (("partial-json", patch("run.json.dump", partial_json)),
                               ("finished", patch.object(journal.Journal, "event", unfinished))):
            with self.subTest(stage=stage):
                with failure, self.assertRaises(OSError):
                    self.execute(stage, answers)
                self.check_interrupted_final()

    def run_timed_control_cli(self, inference_ms):
        rows = c01.read_records(c01.FIXTURES / "observations.jsonl")
        first = next(o for o in rows if o["id"] == "ctl-simples")
        first.update(inference_ms=inference_ms, elapsed_ms=None)
        answers = self.path / "answers.jsonl"
        answers.write_text("".join(encode(o) + "\n" for o in rows), encoding="utf-8")
        config = c01.read(HERE / "fixture.json")
        config["identity"]["mode"] = "real"
        config["command"] = [sys.executable, "-B", str(Path(__file__).resolve()), "--adapter", "timed", str(answers)]
        config_path = self.path / "config.json"
        config_path.write_text(encode(config), encoding="utf-8")
        self.output = self.path / "run"
        return subprocess.run([sys.executable, "-B", str(HERE / "run.py"), "--mode", "real", "--split", "control",
                               "--config", str(config_path), "--output", str(self.output)],
                              capture_output=True, text=True, timeout=30)

    def test_cli_rejects_inference_longer_than_final_elapsed_at_first_dispatch(self):
        result = self.run_timed_control_cli(500)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("inference_duration: ctl-simples", result.stderr)
        m = c01.read(self.output / "interruption.json")
        self.assertEqual(m["completed_ids"], ["ctl-completo"])
        self.assertEqual(m["dispatched_ids"], ["ctl-simples"])
        self.assertEqual(m["interrupted_id"], "ctl-simples")
        self.assertEqual(m["not_started_ids"], c01.read(self.output / "plan.json")["control_ids"][2:])
        self.assertEqual(m["eligibility"], "inconclusive")
        self.assertIsNone(m["interrupted_observation"]["elapsed_ms"])
        self.assertEqual(m["interrupted_usage"]["requests"], 1)
        self.assertEqual(m["interrupted_usage"]["observed_api_usd"], .01)
        self.assertEqual(m["verified_prefix_usage"]["attempts"]["value"], 0)
        self.assertFalse((self.output / "report.json").exists())
        self.assertFalse((self.output / "report.md").exists())
        self.assertEqual(c01.read_records(self.output / "observations.jsonl"), [])

        validation, protocol, split, catalog, cases, _ = runner.preflight()
        prefix = c01.load_bundle(validation, self.output / "prefix-report.json")
        c01.verify_run(prefix, validation, protocol, split, catalog, cases)
        self.assertEqual(prefix["report"]["eligibility"], "inconclusive")
        self.assertEqual(prefix["observations"], [])
        self.assertEqual([d["id"] for d in prefix["decisions"]], ["ctl-completo"])

    def test_cli_commits_compatible_final_elapsed_and_continues(self):
        result = self.run_timed_control_cli(.001)
        self.assertEqual(result.returncode, 0, result.stderr)
        observations = c01.read_records(self.output / "observations.jsonl")
        first = observations[0]
        self.assertEqual(first["id"], "ctl-simples")
        self.assertEqual(first["inference_ms"], .001)
        self.assertGreaterEqual(first["elapsed_ms"], first["inference_ms"])
        report = c01.read(self.output / "report.json")
        self.assertEqual(len(report["control_ids"]), 13)
        self.assertEqual(report["usage"]["attempts"]["value"], 8)
        self.assertFalse((self.output / "interruption.json").exists())

    def check_interruption(self, action, error):
        with self.assertRaises(error):
            self.execute(action)
        m = c01.read(self.output / "interruption.json")
        self.assertEqual(m["eligibility"], "inconclusive")
        prefix = c01.read(self.output / "prefix-report.json")
        self.assertEqual(prefix["eligibility"], "inconclusive")
        self.assertEqual(m["injected_controls"], {"ids": [], "count": 0})
        self.assertEqual(prefix["injected_controls"], m["injected_controls"])
        self.assertEqual(prefix["control_ids"], m["completed_ids"])
        self.assertEqual(prefix["usage"], m["verified_prefix_usage"])
        self.assertEqual(m["completed_ids"], ["ctl-completo", "ctl-simples"])
        self.assertEqual(m["dispatched_ids"], ["ctl-simples", "ctl-duplo"])
        self.assertEqual(m["interrupted_id"], "ctl-duplo")
        self.assertEqual(m["delivery"], "stdin_flushed")
        self.assertTrue(all(v is None for v in m["interrupted_usage"].values()))
        self.assertEqual(m["not_started_ids"], c01.read(self.output / "plan.json")["control_ids"][3:])
        self.assertFalse((self.output / "report.json").exists())
        for name, entry in m["artifacts"].items():
            self.assertEqual(c01.source_path(entry), self.output / name)
        self.assertEqual(m["verified_prefix_usage"]["observed_api_usd"]["value"], .01)
        self.assertEqual(m["verified_prefix_usage"]["requests"]["value"], 1)
        self.assertEqual(m["verified_prefix_usage"]["attempts"]["value"], 1)
        for name, ids in [("observations", ["ctl-simples"]), ("decisions", m["completed_ids"]),
                          ("verified_inputs", m["completed_ids"])]:
            with (self.output / (name + ".jsonl")).open(encoding="utf8", newline="\n") as rows:
                self.assertEqual([row["id"] for row in map(decode, rows)], ids)
        with (self.output / "journal.jsonl").open() as file:
            events = list(map(decode, file))
        self.assertEqual([e["event"] for e in events], ["planned", "completed", "dispatch_started", "dispatched",
                                                       "completed", "dispatch_started", "dispatched", "interrupted"])
        self.assertEqual(events[-1]["id"], "ctl-duplo")

    def test_dies_after_receiving_second_attempt(self):
        self.check_interruption("die", ValueError)

    def test_silent_after_receiving_second_attempt(self):
        self.check_interruption("silent", TimeoutError)

    def test_invalid_answer_is_not_evidence(self):
        self.check_interruption("invalid", ValueError)

    def test_extra_fragment_after_complete_prefix(self):
        with self.assertRaisesRegex(ValueError, "stdout adicional"):
            self.execute("trailing")
        m = c01.read(self.output / "interruption.json")
        self.assertIsNone(m["interrupted_id"])
        self.assertEqual(len(m["completed_ids"]), 13)
        self.assertFalse(m["not_started_ids"])

    def test_ctrl_c_at_each_completion_write(self):
        original = journal.append
        for target in ("observation", "decision", "completed"):
            for side in ("before", "after"):
                with self.subTest(target=target, side=side):
                    def interrupt(stream, row):
                        selected = row.get("id") == "ctl-simples" and (
                            (target == "completed" and row.get("event") == "completed") or
                            (target == "observation" and "choices" in row) or
                            (target == "decision" and "fields" in row))
                        if selected and side == "before":
                            raise KeyboardInterrupt()
                        original(stream, row)
                        if selected and side == "after":
                            raise KeyboardInterrupt()

                    with patch("journal.append", interrupt), self.assertRaises(KeyboardInterrupt):
                        self.execute(target + "-" + side)
                    m = c01.read(self.output / "interruption.json")
                    committed = target == "completed" and side == "after"
                    ids = ["ctl-completo", "ctl-simples"] if committed else ["ctl-completo"]
                    self.assertEqual(m["completed_ids"], ids)
                    self.assertEqual(m["dispatched_ids"], ["ctl-simples"])
                    self.assertEqual(m["interrupted_id"], None if committed else "ctl-simples")
                    self.assertEqual(m["not_started_ids"], c01.read(self.output / "plan.json")["control_ids"][2:])
                    for name in ("inputs", "observations", "decisions"):
                        entry = m["artifacts"][f"verified_{name}.jsonl"]
                        with c01.source_path(entry).open(newline="\n") as stream:
                            actual = [r["id"] for r in map(decode, stream)]
                        self.assertEqual(actual, (ids[1:] if name == "observations" else ids))
                    self.assertEqual(m["verified_prefix_usage"]["observed_api_usd"]["value"], .01 if committed else None)
                    self.assertEqual(m["verified_prefix_usage"]["requests"]["value"], int(committed))
                    if committed:
                        self.assertIsNone(m["interrupted_usage"])
                        self.assertIsNone(m["interrupted_observation"])
                    else:
                        self.assertEqual(m["interrupted_observation"]["id"], "ctl-simples")
                        self.assertEqual(m["interrupted_usage"]["observed_api_usd"], .01)
                        self.assertEqual(m["interrupted_usage"]["requests"], 1)

    def test_uncommitted_observation_with_partial_billing(self):
        original = journal.append
        def interrupt(stream, row):
            if row.get("id") == "ctl-duplo" and "fields" in row:
                raise KeyboardInterrupt()
            original(stream, row)

        with patch("journal.append", interrupt), self.assertRaises(KeyboardInterrupt):
            self.execute("partial-billing")
        m = c01.read(self.output / "interruption.json")
        self.assertEqual(m["completed_ids"], ["ctl-completo", "ctl-simples"])
        self.assertEqual(m["verified_prefix_usage"]["requests"]["value"], 1)
        self.assertEqual(m["verified_prefix_usage"]["observed_api_usd"]["value"], .01)
        self.assertEqual(m["interrupted_id"], "ctl-duplo")
        self.assertEqual(m["interrupted_usage"]["requests"], 2)
        self.assertIsNone(m["interrupted_usage"]["observed_api_usd"])
        self.assertEqual(m["interrupted_usage_samples"]["observed_api_usd"],
                         dict(value=.01, samples=1, expected_samples=2, state="partial"))

    def test_deadline_includes_validation_and_dispatch_sync(self):
        original_append = journal.append
        original_structure = c01.structure
        original_record = ResponseStream.record
        # Real pipe and schema validation; advance a deterministic monotonic clock at
        # the same boundaries as input validation, fsync and observation delivery.
        for case_id, arrival, accepted in (("ctl-simples", 5.13, False), ("ctl-timeout", 5.13, True),
                                            ("ctl-timeout", 5.26, False), ("ctl-simples", 4.99, True)):
            with self.subTest(case_id=case_id, arrival=arrival):
                now = 0.0
                def validate(checks, kind, row):
                    nonlocal now
                    original_structure(checks, kind, row)
                    if kind == "input" and row["id"] == case_id:
                        now += .10

                def slow_sync(stream, row):
                    nonlocal now
                    original_append(stream, row)
                    if row.get("event") == "dispatched" and row["id"] == case_id:
                        now += .45

                def deliver(reader, deadline):
                    nonlocal now
                    row = original_record(reader, deadline)
                    if row["id"] == case_id:
                        self.assertAlmostEqual(deadline - now, 5.25 - .55)
                        now += arrival - .55
                    return row

                clock = SimpleNamespace(monotonic=lambda: now, sleep=time.sleep)
                with patch("run.time", clock), patch("journal.append", slow_sync), patch.object(
                        c01, "structure", validate), patch.object(ResponseStream, "record", deliver):
                    action = f"{case_id}-{arrival}"
                    if accepted:
                        self.execute(action)
                        self.assertTrue((self.output / "report.json").exists())
                    else:
                        with self.assertRaisesRegex(TimeoutError, "fora do prazo"):
                            self.execute(action)
                        m = c01.read(self.output / "interruption.json")
                        self.assertEqual(m["interrupted_id"], case_id)
                        self.assertNotIn(case_id, m["completed_ids"])

    def test_always_predicting_candidate_has_independent_mixed_control(self):
        self.execute("always_valid")
        r = c01.read(self.output / "report.json")
        policy_ref = c01.read(c01.PLAN / "protocolo-comparacao.json")["control_policy"]
        policy = c01.read(c01.source_path(policy_ref))
        reserved, = policy["controls"]
        self.assertEqual(r["injected_controls"], dict(count=1, ids=[reserved], policy=policy_ref,
                                                    identity=policy["identity"]))
        rows = c01.read_records(self.output / "observations.jsonl")
        candidate = [row for row in rows if row["origin"] == "candidate"]
        self.assertEqual(len(candidate), 8)
        self.assertTrue(all(c["status"] == "predicted" for o in candidate for c in o["choices"].values()))
        events = c01.read_records(self.output / "journal.jsonl")
        self.assertEqual([e["id"] for e in events if e["event"] == "dispatched"], [o["id"] for o in candidate])
        self.assertEqual(r["usage"]["attempts"]["value"], 8)
        self.assertEqual(r["usage"]["requests"]["value"], 8)
        self.assertEqual(r["usage"]["observed_api_usd"]["value"], .08)
        self.assertEqual(r["usage"]["input_tokens"]["samples"], 8)
        self.assertEqual(r["gates"]["partial_application_after_abstention_or_error"],
                         dict(state="measured", value=0, numerator=0, denominator=1))
        self.assertEqual(rows[-1]["id"], reserved)
        self.assertEqual(rows[-1]["choices"], policy["controls"][reserved]["choices"])
        self.assertEqual(rows[-1]["request_usage"], [])
        self.assertIsNone(rows[-1]["elapsed_ms"])
        self.assertEqual(r["eligibility"], "inconclusive")

    def test_preflight_refuses_plan_without_reserved_control(self):
        prepared = runner.preflight()
        example = prepared[-1]
        reserved, = example["report"]["injected_controls"]["ids"]
        example["inputs"] = [i for i in example["inputs"] if i["id"] != reserved]
        with patch("run.preflight", return_value=prepared), self.assertRaisesRegex(ValueError, "omite controle"):
            self.execute("missing-control")
        self.assertFalse(self.output.exists())

    def test_candidate_cannot_claim_origin_of_evaluator(self):
        with self.assertRaises(ValueError):
            self.execute("spoof")
        m = c01.read(self.output / "interruption.json")
        self.assertEqual(m["interrupted_id"], "ctl-simples")
        self.assertEqual(m["injected_controls"], {"count": 0, "ids": []})
        self.assertEqual(m["verified_prefix_usage"]["attempts"]["value"], 0)
        self.assertIsNone(m["interrupted_usage"]["observed_api_usd"])
        self.assertFalse((self.output / "report.json").exists())

    def test_modified_injection_rejected_before_commit(self):
        original = runner.injected_observation
        def tamper(*args):
            obs = original(*args)
            obs["choices"] = dict(obs["choices"], category={"raw": "terminal", "status": "predicted", "reason": None})
            return obs

        with patch("run.injected_observation", tamper), self.assertRaisesRegex(ValueError, "control_policy_choices"):
            self.execute("tamper")
        r = c01.read(self.output / "prefix-report.json")
        self.assertEqual(len(r["control_ids"]), 12)
        self.assertEqual(r["injected_controls"], {"ids": [], "count": 0})
        self.assertFalse((self.output / "report.json").exists())

    def test_final_memory_and_unavailable(self):
        for action, expected in [("peak=777", 777), ("peak=0", 0), ("peak=null", None), ("omit", None)]:
            with self.subTest(action=action):
                self.execute(action)
                self.assertEqual(c01.read(self.output / "report.json")["environment"]["peak_memory_bytes"], expected)
        with self.assertRaisesRegex(ValueError, "peak_memory_bytes"):
            self.execute("peak=true")
        self.assertTrue((self.output / "interruption.json").exists())

    def test_jsonl_frames_independent_of_chunking(self):
        sample = {"id": "a\u0085b\u2028c\u2029d"}
        row = encode(sample).encode("utf8")
        for size in [1, 5, 65536]:
            for payload, valid in [(row+b"\n", True), (row+b"\r\n", True), (row, False),
                                   (b"\n"+row+b"\n", False), (row+b"\n\n", False),
                                   (row+b"\n"+row+b"\n", False), (row+b"\n{", False),
                                   (b'{\n"id": 1\n}\n', False)]:
                with self.subTest(size=size, payload=payload):
                    read_fd, write_fd = os.pipe()
                    os.write(write_fd, payload)
                    os.close(write_fd)
                    read = os.read
                    with os.fdopen(read_fd, "rb") as source, patch("run.os.read", lambda fd, n: read(fd, min(size, n))):
                        stream = ResponseStream(source)
                        def parse():
                            result = stream.record(time.monotonic() + 1)
                            stream.finish()
                            return result
                        if valid:
                            self.assertEqual(parse(), sample)
                        else:
                            with self.assertRaises(ValueError):
                                parse()


if __name__ == "__main__":
    if sys.argv[1:2] == ["--adapter"]:
        adapter(*sys.argv[2:])
    else:
        unittest.main()
