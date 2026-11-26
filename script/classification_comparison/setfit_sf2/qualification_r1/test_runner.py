import base64
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from ..contracts.core import CATALOG, decode
from ..contracts.ipc import validate_decision
from ..contracts.test_contracts import fixture
from ..evaluation.test_evaluation import POLICY, records, templates
from . import execution, runner
from .storage import digest, encoded, read


def dummy_derive(item, raw, context):
    obj = decode(raw)
    validate_decision(item, obj, POLICY, context["classes"], context["identities"])
    return dict(obj, raw_sha256=digest(raw))


def dummy_verify(item, raw, decision, context):
    if decision != dummy_derive(item, raw, context):
        raise ValueError("decisão incoerente")


def worker(root, rows, mode="ok", mutate=None):
    scaffold = fixture("both")
    ctx = dict(classes=scaffold["class_order"], identities=scaffold["identities"])
    responses = templates(rows)
    for frame in responses.values():
        for name, field in frame["fields"].items():
            if field["cut"] is not None:
                field["cut"] = POLICY[name]
    if mutate:
        mutate(responses[rows[0]["id"]])
    frames = {i: base64.b64encode(b"  " + encoded({**d, **ctx["identities"]})).decode()
              for i, d in responses.items()}
    path = root / "fixture.json"
    path.write_bytes(encoded(frames))
    return [sys.executable, "-I", "-B", str(Path(__file__).with_name("fixture_worker.py")), mode, str(path)], ctx


class Supervision(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rows = records("final")[:2]

    def batch(self, mode="ok", *, mutate=None, derive=dummy_derive, verify=dummy_verify, timeout=500, name="run"):
        argv, self.ctx = worker(self.root, self.rows, mode, mutate)
        self.run_dir = self.root / name
        return runner.supervise(self.rows, argv, self.ctx, self.run_dir, 3, derive=derive, verify=verify,
                                catalog=CATALOG, timeout_ms=timeout)

    def evidence(self, name):
        return [decode(line) for line in read(self.run_dir / name).splitlines()]

    def test_complete_preserves_bytes_order_resources_and_external_clock(self):
        def slow(*args):
            time.sleep(.019)
            return dummy_verify(*args)
        seal = self.batch(verify=slow)
        self.assertIsNone(seal["failure"])
        self.assertGreater(seal["startup_ms"], 60)
        self.assertEqual(len(self.evidence("controls-r1.jsonl")), 5)
        self.assertEqual([x["id"] for x in self.evidence("timings.jsonl")],
                         [r["id"] for _, r in runner.schedule(self.rows)])
        self.assertTrue(all(t["elapsed_ms"] >= 18 for t in self.evidence("timings.jsonl")))
        for name in seal["files"]:
            self.assertEqual(digest(read(self.run_dir / name)), seal["files"][name])
        self.assertTrue(read(self.run_dir / "raw.jsonl").startswith(b"  {"))
        self.assertEqual(seal["resources"]["supervisor"]["pid"], os.getpid())
        self.assertNotEqual(seal["resources"]["worker"]["pid"], os.getpid())
        for scope in seal["resources"].values():
            self.assertGreater(scope["peak_ram_bytes"], 0)
            self.assertGreaterEqual(scope["peak_cpu_percent"], 0)
        self.assertEqual(seal["case_latency_ms"]["n"], 2)
        self.assertEqual(seal["historical_capture_costs"]["training_ms"], 913684.5375259982)

    def test_preemption_for_derive_verify_and_controls(self):
        for phase in ("derive", "verify", "control"):
            def delayed(*args):
                if phase != "control" or args[0]["id"].startswith("sf2-control-"):
                    time.sleep(1)
                return (dummy_derive if phase == "derive" else dummy_verify)(*args)
            with self.subTest(phase=phase):
                kwargs = {"derive" if phase == "derive" else "verify": delayed}
                seal = self.batch(**kwargs, timeout=100, name=phase)
                t = self.evidence("timings.jsonl")[-1]
                self.assertFalse(t["valid"])
                self.assertEqual(seal["failure"]["type"], "TimeoutError")
                self.assertTrue(90 <= t["elapsed_ms"] < 550)
                self.assertEqual(seal["interrupted_ids"], [t["id"]])
                self.assertEqual(t["kind"], "control" if phase == "control" else "case")
                self.assertEqual(len(self.evidence("decisions.jsonl")), 2 if phase == "control" else 0)

    def test_eof_premature_invalid_bytes_and_extra_stdout(self):
        for mode in ("eof", "early", "invalid-utf8", "extra"):
            with self.subTest(mode=mode):
                seal = self.batch(mode, name=mode)
                self.assertTrue(seal["failure"])
                if mode == "extra":
                    self.assertEqual(len(self.evidence("timings.jsonl")), 7)
                    self.assertIsNone(seal["failure"]["attempt"])
                else:
                    self.assertEqual(len(self.evidence("timings.jsonl")), 1)
                    unit = decode(read(self.run_dir / "observations/0000.json"))
                    self.assertFalse(unit["timing"]["valid"])
                    self.assertTrue(base64.b64decode(unit["rejected_base64"]))
                    self.assertEqual(read(self.run_dir / "raw.jsonl"), b"")

    def test_identity_vector_channel_and_returned_digest(self):
        def wrong_vector(obj):
            obj["fields"]["category"]["vector"]["scores"][0] = -1
        def bad_hash(*args):
            return dict(dummy_derive(*args), raw_sha256="a"*64)
        def wrong_identity(item, raw, ctx):
            return dummy_derive(item, raw, dict(ctx, identities=dict(ctx["identities"], package_sha256="0"*64)))
        for i, options in enumerate(({"mutate": wrong_vector}, {"mutate": lambda d: d.update(received={})},
                                     {"derive": wrong_identity}, {"derive": bad_hash, "verify": lambda *args: None},
                                     {"mutate": lambda d: d.update(id="troca")})):
            with self.subTest(i=i):
                seal = self.batch(name=str(i), **options)
                self.assertEqual(len(seal["unstarted_ids"]), 6)
                self.assertEqual(len(seal["interrupted_ids"]), 1)
                self.assertEqual(self.evidence("decisions.jsonl"), [])
                self.assertTrue(decode(read(self.run_dir / "observations/0000.json"))["rejected_base64"])

    def test_sigint_before_or_after_atomic_publication(self):
        original = runner.publish
        for before in (True, False):
            sent = False
            def interrupt(path, raw):
                nonlocal sent
                if path.name == "0000.json" and not sent:
                    sent = True
                    if not before:
                        original(path, raw)
                    os.kill(os.getpid(), signal.SIGINT)
                original(path, raw)
            with self.subTest(before=before), patch.object(runner, "publish", interrupt):
                seal = self.batch(name=str(before))
                self.assertEqual(seal["failure"]["type"], "KeyboardInterrupt")
                timing = self.evidence("timings.jsonl")
                self.assertEqual([t["valid"] for t in timing], [not before])
                self.assertEqual(len(self.evidence("decisions.jsonl")), int(not before))
                audited = execution.audit_run(self.run_dir, digest(read(self.run_dir/"seal.json")),
                                               self.rows, self.ctx, dummy_verify)
                self.assertEqual(audited["verified_cases"], int(not before))
                self.assertEqual(audited["status"], "inconclusive")

    def test_ctrl_c_during_jsonl_materialization_preserves_confirmed_units(self):
        original = runner.materialize
        def interrupt(*args):
            os.kill(os.getpid(), signal.SIGINT)
            return original(*args)
        with patch.object(runner, "materialize", interrupt):
            seal = self.batch()
        self.assertEqual(seal["failure"]["type"], "KeyboardInterrupt")
        self.assertEqual(len(self.evidence("timings.jsonl")), 7)
        result = execution.audit_run(self.run_dir, digest(read(self.run_dir/"seal.json")), self.rows,
                                     self.ctx, dummy_verify)
        self.assertEqual((result["status"], result["verified_cases"]), ("inconclusive", 2))

    def test_full_synthetic_run_and_audit_from_one_seal(self):
        self.rows = records("final")
        self.batch()
        expected = digest(read(self.run_dir / "seal.json"))
        report = execution.audit_run(self.run_dir, expected, self.rows, self.ctx, dummy_verify)
        self.assertEqual((report["status"], report["verified_cases"], report["verified_controls"]), ("eligible", 120, 5))
        self.assertEqual(report["latency_ms"]["n"], 120)
        seal_path = self.run_dir / "seal.json"
        original = read(seal_path)
        missing = decode(original)
        missing["resources"]["worker"]["peak_cpu_percent"] = None
        seal_path.write_bytes(encoded(missing))
        partial = execution.audit_run(self.run_dir, digest(read(seal_path)), self.rows, self.ctx, dummy_verify)
        self.assertEqual((partial["status"], partial["verified_cases"]), ("inconclusive", 120))
        seal_path.write_bytes(original)
        with (self.run_dir / "raw.jsonl").open("ab") as f:
            f.write(b"\n")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            execution.audit_run(self.run_dir, expected, self.rows, self.ctx, dummy_verify)

