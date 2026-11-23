"""Regressões C02 1/3/4. Subprocesso sintético isolado, sem modelo."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from argparse import Namespace
from unittest.mock import patch

from run import HERE, ResponseStream, c01, decode, encode, run


def adapter(action):
    ready = Path(os.environ["CLASSIFICATION_READY_FILE"])
    tmp = ready.with_suffix(".tmp")
    tmp.write_text(encode(dict(runtime="fixture", hardware="cpu", peak_memory_bytes=10)))
    tmp.replace(ready)
    with (c01.FIXTURES / "observations.jsonl").open(encoding="utf8", newline="\n") as stream:
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
        obs = dict(fixtures[case_id], run_id=os.environ["CLASSIFICATION_RUN_ID"])
        if case_id == "ctl-simples":
            obs["request_usage"][0]["observed_api_usd"] = 0.01
        sys.stdout.buffer.write(encode(obs).encode("utf8") + b"\r\n")
        sys.stdout.buffer.flush()
    if action == "trailing":
        os.write(1, b"fragment")
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

    def execute(self, action):
        config = c01.read(HERE / "fixture.json")
        config["command"] = [sys.executable, "-B", str(Path(__file__).resolve()), "--adapter", action]
        config_path = self.path / "config.json"
        config_path.write_text(encode(config))
        self.output = self.path / action
        run(Namespace(config=config_path, split="control", limit=None, mode="fixture", output=self.output,
                      concurrency=1, attempts=1, dry_run=False))

    def check_interruption(self, action, error):
        with self.assertRaises(error):
            self.execute(action)
        m = c01.read(self.output / "interruption.json")
        self.assertEqual(m["eligibility"], "inconclusive")
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
        self.assertEqual(len(m["completed_ids"]), 12)
        self.assertFalse(m["not_started_ids"])

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
        adapter(sys.argv[2])
    else:
        unittest.main()
