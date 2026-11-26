import multiprocessing
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from . import execution, exposure, release
from .storage import digest, encoded, exclusive, read


def competitor(layout, rel, dest, expected, seal, gate, log):
    gate.wait(5)
    try:
        layout.reserve(rel, expected, seal, dest, log)
        with log.open("ab") as output:
            output.write(read(log.parent / "custody-fixture") + b"\n")
    except (OSError, ValueError):
        return


def legacy_writer(path, acquired, attempted):
    acquired.wait(5)
    exclusive(path, b"legacy fixture")
    attempted.set()


class Exposure(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        old = self.root / "old"
        old.mkdir()
        self.guard = exposure.Guard(self.root / "guards", old / "final-exposure.json", old / "exposure.json",
                                   self.root / "auth")
        self.guard.authorizations.mkdir()
        self.seal = digest(b"fictional final seal")
        self.custody = self.root / "custody-fixture"
        self.custody.write_bytes(b"fake data")
        self.frozen = {"final_seal_sha256": self.seal}

    def prepare(self, n):
        rel, dest = self.root / ("rel" + n), self.root / ("run" + n)
        config = self.root / ("config" + n)
        cmd = dict(argv=["fixture"], cwd=str(self.root), environment={})
        config.write_bytes(encoded(dict(command=cmd, release=str(rel), run=str(dest))))
        inspect = Mock(return_value=(self.frozen, {}, {}))
        expected = release.freeze(config, rel, inspect)
        checked = release.check(rel, expected, inspect)
        self.assertFalse((self.guard.shared / (self.seal + ".json")).exists())
        self.assertFalse(self.guard.legacy_validation.exists())
        auth = {"action": "execute_once", "release_sha256": expected, "final_seal_sha256": self.seal}
        (self.guard.authorizations / (expected + ".json")).write_bytes(encoded(auth))
        return rel, dest, expected, checked

    def invoke(self, values, opened):
        rel, dest, expected, checked = values
        return execution.execute(checked, rel, expected, self.custody, dest, self.guard,
                                 load_records=opened, supervise=Mock(side_effect=AssertionError("worker inesperado")),
                                 derive=None, verify=None)

    def test_two_processes_different_releases_and_destinations_same_seal(self):
        values = [self.prepare(n) for n in "12"]
        ctx = multiprocessing.get_context("fork")
        go = ctx.Event()
        log = self.root / "first-reads"
        procs = [ctx.Process(target=competitor, args=(self.guard, rel, dest, sha, self.seal, go, log))
                 for rel, dest, sha, _ in values]
        for p in procs:
            p.start()
        go.set()
        for p in procs:
            p.join(6)
            self.assertEqual(p.exitcode, 0)
        self.assertEqual(log.read_bytes(), b"fake data\n")
        self.assertEqual(read(self.guard.legacy_validation), read(self.guard.shared / (self.seal + ".json")))

    def test_existing_legacy_or_empty_global_or_unauthorized_never_opens(self):
        values = self.prepare("1")
        opened = Mock()
        rel, dest, expected, _ = values
        auth = self.guard.authorizations / (expected + ".json")
        original = read(auth)
        auth.write_bytes(encoded({"approved": True}))
        with self.assertRaises(ValueError):
            self.invoke(values, opened)
        auth.write_bytes(original)
        self.guard.shared.mkdir()
        for marker in (self.guard.legacy_validation, self.guard.legacy_release, self.guard.shared / (self.seal + ".json"),
                       rel / "exposure.json"):
            with self.subTest(marker=marker):
                marker.touch()
                with self.assertRaises(ValueError):
                    self.invoke(values, opened)
                opened.assert_not_called()
                marker.unlink()

    def test_race_with_legacy_writer_and_abortion_between_reservations(self):
        for abort in (False, True):
            v = self.prepare(str(abort))
            opened = Mock()
            def collision(path, raw):
                if path == self.guard.legacy_validation:
                    if abort:
                        raise KeyboardInterrupt
                    exclusive(path, b"legacy")
                exclusive(path, raw)
            with self.subTest(abort=abort), patch.object(exposure, "exclusive", collision):
                with self.assertRaises((FileExistsError, KeyboardInterrupt)):
                    self.invoke(v, opened)
                opened.assert_not_called()
                self.assertTrue((self.guard.shared / (self.seal + ".json")).exists())
                with self.assertRaises(ValueError):
                    self.invoke(v, opened)
            # As duas simulações representam selos privados distintos.
            self.seal = digest(b"other fake seal")
            self.frozen = {"final_seal_sha256": self.seal}
            self.guard.legacy_validation.unlink(missing_ok=True)

    def test_competing_legacy_process_wins_capture_marker(self):
        values = self.prepare("1")
        ctx = multiprocessing.get_context("fork")
        acquired, attempted = ctx.Event(), ctx.Event()
        old = ctx.Process(target=legacy_writer, args=(self.guard.legacy_validation, acquired, attempted))
        old.start()
        opened = Mock()
        def overlap(path, raw):
            exclusive(path, raw)
            if path.parent == self.guard.shared:
                acquired.set()
                self.assertTrue(attempted.wait(5))
        try:
            with patch.object(exposure, "exclusive", overlap), self.assertRaises(FileExistsError):
                self.invoke(values, opened)
        finally:
            old.join(6)
        self.assertEqual(old.exitcode, 0)
        opened.assert_not_called()
        self.assertEqual(read(self.guard.legacy_validation), b"legacy fixture")
        self.assertTrue((self.guard.shared / (self.seal + ".json")).exists())

    def test_after_reservation_interruption_receipt_and_retry(self):
        v = self.prepare("1")
        opened = Mock(side_effect=KeyboardInterrupt())
        execution_sha = self.invoke(v, opened)
        rel, dest, expected, checked = v
        self.assertEqual(len(execution_sha), 64)
        with self.assertRaises(ValueError):
            self.invoke(v, opened)
        self.assertEqual(opened.call_count, 1)
        result = execution.audit(checked, rel, expected, self.custody, dest, execution_sha, self.guard,
                                 load_records=opened, verify=None)
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(opened.call_count, 1)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            execution.audit(checked, rel, expected, self.custody, dest, "0"*64, self.guard,
                            load_records=opened, verify=None)
        self.guard.legacy_validation.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "recibos"):
            execution.audit(checked, rel, expected, self.custody, dest, execution_sha, self.guard,
                            load_records=opened, verify=None)
        self.assertEqual(opened.call_count, 1)

    def test_tampered_command_config_inventory_receipt_rejected_before_private_access(self):
        rel, _, expected, _ = self.prepare("1")
        opened = Mock()
        for path in [rel / "command.json", self.root / "config1", rel / "freeze.json", rel / "release.json"]:
            with self.subTest(path=path):
                original = read(path)
                path.write_bytes(original + b" ")
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    release.check(rel, expected, opened)
                path.write_bytes(original)
        with self.assertRaisesRegex(ValueError, "inventário"):
            release.check(rel, expected, lambda cfg: ({"changed": True}, {}, {}))
        opened.assert_not_called()
        self.assertFalse(self.guard.shared.exists())

