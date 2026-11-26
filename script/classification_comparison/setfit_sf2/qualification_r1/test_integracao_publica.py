"""Integração do supervisor com R1 usando um subprocesso JSON e frames públicos fixos."""
import base64
import gzip
import os
from pathlib import Path
import signal
import sys
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from ..contracts.core import CATALOG, FIELDS, PLAN, decode
from ..evaluation.metrics import metrics, quality_gates
from ..runtime_r1 import derive, load_context, verify
from ..runtime_r1.test_runtime import CAPTURE, R1, context_bytes
from . import execution, runner
from .storage import digest, encoded, read


class IntegracaoPublica(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.context = load_context(*context_bytes())
        roles = decode(read(PLAN / "sf2-r1-protocolo.json"))["parent"]["files"]
        self.rows = [decode(line) for line in read(PLAN / "dados/validation.jsonl",
                     roles["validation"]["sha256"]).splitlines()]
        capture = CAPTURE / "avaliacao/validation/run"
        self.frames = {}
        for role in ("predictions", "controls"):
            raw = read(capture / (role + ".jsonl"), roles[role]["sha256"])
            for frame in raw.splitlines(keepends=True):
                key = decode(frame)["id"]
                self.assertNotIn(key, self.frames)
                self.frames[key] = frame
        fixture = self.root / "frames.json"
        fixture.write_bytes(encoded({key: base64.b64encode(frame).decode("ascii")
                                     for key, frame in self.frames.items()}))
        self.argv = [sys.executable, "-I", "-B", "-S", str(Path(__file__).with_name("fixture_worker.py")),
                     "ok", str(fixture)]

    def batch(self, rows, name, **kwargs):
        self.dest = self.root / name
        return runner.supervise(rows, self.argv, self.context, self.dest, 5, catalog=CATALOG,
                                **{"derive": derive, "verify": verify, **kwargs})

    def journal(self, name):
        return [decode(line) for line in read(self.dest / name).splitlines()]

    def audit(self, rows):
        return execution.audit_run(self.dest, digest(read(self.dest / "seal.json")), rows, self.context, verify)

    def test_replay_integrado_de_90_relatos_e_cinco_controles(self):
        seal = self.batch(self.rows, "replay")
        self.assertIsNone(seal["failure"])
        cases = self.journal("decisions.jsonl")
        controls = self.journal("controls-r1.jsonl")
        self.assertEqual((len(cases), len(controls)), (90, 5))
        sequence = [row["id"] for _, row in runner.schedule(self.rows)]
        self.assertEqual([d["id"] for d in cases + controls], sequence)
        self.assertEqual([t["id"] for t in self.journal("timings.jsonl")], sequence)
        for decision in cases + controls:
            frame = self.frames[decision["id"]]
            self.assertEqual(decision["raw_sha256"], digest(frame))
            original = decode(frame)
            for field in FIELDS:
                before, after = original["fields"][field], decision["fields"][field]
                if after["decision"] == before["decision"]:
                    self.assertEqual(after["reason"], before["reason"])
                else:
                    self.assertEqual((before["decision"], after["reason"]), ("accept", "below_tau"))
        self.assertEqual([[c["calls"][f] for f in FIELDS] for c in controls],
                         [[0, 0], [0, 0], [1, 0], [0, 1], [1, 1]])
        self.assertTrue(all(c["applied"] == {} for c in controls))
        fixed = decode(read(PLAN / "sf2-final-r1-protocolo.json"))
        archive = decode(gzip.decompress(read(R1 / "result.json.gz", fixed["anchors_sha256"]["offline_result_gzip"])))
        selected, = [row for row in archive["policies"] if row["policy"] == self.context["selected_policy"]]
        blocked_calls = sum(sum(c["calls"].values()) for c in controls[:2])
        totals = metrics(self.rows, cases, blocked_calls)
        self.assertEqual(totals, selected["metrics"])
        self.assertEqual(quality_gates(totals, "validation"), selected["gates"])
        self.assertTrue(selected["eligible"])
        self.assertEqual(selected["failed_gates"], [])
        audit = self.audit(self.rows)
        self.assertEqual((audit["verified_cases"], audit["verified_controls"], audit["status"]),
                         (90, 5, "inconclusive"))

    def test_prazo_inclui_derivacao_e_verificacao(self):
        rows = self.rows[:1]
        for name, func in (("derive", derive), ("verify", verify)):
            with self.subTest(phase=name):
                observed = []

                def delayed(*args):
                    result = func(*args)
                    observed.append(args[0]["id"])
                    time.sleep(1)
                    return result

                seal = self.batch(rows, name, timeout_ms=150, **{name: delayed})
                self.assertEqual(seal["failure"]["type"], "TimeoutError")
                self.assertEqual(observed, [rows[0]["id"]])
                timing, = self.journal("timings.jsonl")
                self.assertFalse(timing["valid"])
                self.assertGreaterEqual(timing["elapsed_ms"], 140)
                self.assertLess(timing["elapsed_ms"], 900)
                self.assertEqual(self.audit(rows)["verified_cases"], 0)

    def test_sigint_preserva_unidade_atomica_e_auditoria(self):
        rows = self.rows[:2]
        original = runner.publish
        for after in (False, True):
            sent = []

            def interrupt(path, data):
                if path.name == "0001.json" and not sent:
                    sent.append(path)
                    if after:
                        original(path, data)
                    os.kill(os.getpid(), signal.SIGINT)
                original(path, data)

            with self.subTest(after=after), patch.object(runner, "publish", interrupt):
                seal = self.batch(rows, str(after))
                self.assertEqual(seal["failure"]["type"], "KeyboardInterrupt")
                self.assertEqual([t["valid"] for t in self.journal("timings.jsonl")], [True, after])
                audit = self.audit(rows)
                self.assertEqual((audit["verified_cases"], audit["verified_controls"], audit["status"]),
                                 (1 + int(after), 0, "inconclusive"))
