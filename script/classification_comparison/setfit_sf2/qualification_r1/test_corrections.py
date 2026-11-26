"""Regressões da revisão independente da qualificação. Todas as raízes sensíveis são fictícias."""
import base64
from contextlib import ExitStack
import hashlib
import importlib
import os
from pathlib import Path
import signal
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ..contracts import core, ipc
from . import bootstrap, cli, dependencies, execution, preflight, release, runner
from .exposure import Guard
from .storage import digest
from .storage import encoded, publish, read
from .test_runner import dummy_derive, dummy_verify, records, worker


class Fixes(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.layout = bootstrap.public_layout(self.root)
        self.public = self.layout["config"].parent
        self.public.mkdir(parents=True)
        self.private = self.root / "fictional-restricted"

    def test_public_arguments_and_receipt_config_rejected_without_private_filesystem_operations(self):
        bad = self.private / "secret"
        fake = dict(config=bad, release=bad, run=bad, out=bad, expect="0"*64, custody=bad)
        with ExitStack() as stack:
            for f in ("stat", "lstat", "open", "listdir", "scandir", "readlink"):
                stack.enter_context(patch.object(os, f, side_effect=AssertionError("consultou filesystem")))
            for action in ("template", "freeze", "check", "execute", "audit", "_worker"):
                with self.subTest(action=action), self.assertRaises(ValueError):
                    bootstrap.arguments(self.root, "0"*40, SimpleNamespace(action=action, **fake))
            with self.assertRaises(ValueError):
                release.freeze(bad, self.layout["release"], Mock(), layout=self.layout)
            with self.assertRaises(ValueError):
                release.check(bad, "0"*64, Mock(), layout=self.layout)
            internal = dict(release=self.layout["release"], run=self.layout["run"], commit="0"*40,
                            package=str(bootstrap.PACKAGE), package_sha256=bootstrap.PACKAGE_SHA, policy=str(bad))
            with self.assertRaises(ValueError):
                bootstrap.arguments(self.root, "0"*40, SimpleNamespace(action="_worker", **internal))
        rel = self.layout["release"]
        rel.mkdir()
        raw = encoded(dict(config=str(bad), config_sha256="0"*64, command_sha256="0"*64, freeze_sha256="0"*64))
        (rel/"release.json").write_bytes(raw)
        with patch.object(release, "read", wraps=read) as opened, self.assertRaises(ValueError):
            release.check(rel, digest(raw), Mock(), layout=self.layout)
        self.assertEqual([c.args[0] for c in opened.call_args_list], [rel/"release.json"])
        # A mesma apresentação lexical com pai redirecionado é recusada por openat sem seguir o link.
        rel.rename(self.private)
        rel.symlink_to(self.private, target_is_directory=True)
        with self.assertRaises(OSError):
            release.chain(rel, digest(raw), layout=self.layout)

    def test_shadow_with_unchanged_record_and_snapshot_consumption(self):
        first, second = self.root/"first", self.root/"second"
        first.mkdir()
        second.mkdir()
        top = "sf2_fixture_dependency"
        code = b"origin = 'verified'\n"
        path = second / (top + ".py")
        path.write_bytes(code)
        dist = second / "demo-1.dist-info"
        dist.mkdir()
        (dist/"METADATA").write_text("Metadata-Version: 2.1\nName: demo\nVersion: 1\n")
        lines = []
        for file in (path, dist/"METADATA"):
            raw = read(file)
            sha = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")
            lines.append(f"{file.relative_to(second)},sha256={sha},{len(raw)}")
        (dist/"RECORD").write_text("\n".join([*lines, "demo-1.dist-info/RECORD,,"]) + "\n")
        shadow = first / (top + ".py")
        shadow.write_bytes(b"origin = 'stray'\n")
        with self.assertRaisesRegex(ValueError, "fora do RECORD"):
            dependencies.build_sites({"demo": "1"}, [first, second], self.root/"bad-copy")
        shadow.unlink()
        with patch.dict(sys.modules, {top: SimpleNamespace(__file__="/other/module.py")}), self.assertRaisesRegex(
                ValueError, "já carregado"):
            dependencies.build_sites({"demo": "1"}, [first, second], self.root/"preloaded")
        _, targets = dependencies.build_sites({"demo": "1"}, [first, second], self.root/"good-copy")
        path.write_bytes(b"origin = 'changed'\n")
        with patch.object(sys, "path", [*targets, *sys.path]):
            try:
                mod = importlib.import_module(top)
                self.assertEqual(mod.origin, "verified")
                self.assertTrue(Path(mod.__file__).is_relative_to(Path(targets[1])))
            finally:
                sys.modules.pop(top, None)

    def test_only_execution_alias_changed(self):
        original = ipc.project
        catalog = core.CATALOG
        preflight.validate_bindings()
        for owner, name, replacement in ((runner, "project", Mock()), (execution, "project", Mock()),
                                          (execution, "CATALOG", dict(catalog)), (execution, "_supervise", Mock())):
            with self.subTest(name=name), patch.object(owner, name, replacement), self.assertRaisesRegex(ValueError, "alias"):
                preflight.validate_bindings()
            self.assertIs(original, ipc.project)
            self.assertIs(catalog, core.CATALOG)

    def test_loaded_python_identity_and_venv_configuration(self):
        root = self.root / "venv"
        (root/"bin").mkdir(parents=True)
        invoke = root/"bin/python"
        actual = self.root/"live"
        actual.write_bytes(b"python fixture")
        invoke.symlink_to(actual)
        (root/"pyvenv.cfg").write_bytes(b"fixture-v1")
        baseline = bootstrap.interpreter(invoke, actual, allowed=(invoke.parent, self.root))
        frozen = {"python_executable": baseline}
        cli.verify_interpreter(frozen, bootstrap.interpreter(invoke, actual, allowed=(invoke.parent, self.root)))
        (root/"pyvenv.cfg").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Python"):
            cli.verify_interpreter(frozen, bootstrap.interpreter(invoke, actual, allowed=(invoke.parent, self.root)))
        other = self.root/"other"
        other.write_bytes(read(actual))
        invoke.unlink()
        invoke.symlink_to(other)
        with self.assertRaisesRegex(ValueError, "diverge"):
            bootstrap.interpreter(invoke, actual, allowed=(invoke.parent, self.root))
        with self.assertRaisesRegex(ValueError, "Python"):
            cli.verify_interpreter(frozen, bootstrap.interpreter(invoke, other, allowed=(invoke.parent, self.root)))
        # Identidade do processo real pinado, sem carregar modelos.
        self.assertEqual(bootstrap.interpreter()["target"], str(Path("/proc/self/exe").resolve()))

    def setup_flow(self, name):
        group = self.root/name
        group.mkdir()
        private = group/"custody"
        private.mkdir()
        inv = private/"inventory.json"
        members = {k: str(private/(k+".data")) for k in ("final", "annotations", "review_receipt", "token_lengths")}
        inv.write_bytes(encoded(members))
        auth = group/"auth"
        auth.mkdir()
        guard = Guard(group/"shared", group/"legacy", group/"old", auth, private)
        rel, dest = group/"release", group/"run"
        rel.mkdir()
        sha = digest(encoded({"release": name}))
        seal_sha = digest(b"public seal")
        (auth/(sha+".json")).write_bytes(encoded(dict(action="execute_once", release_sha256=sha,
            final_seal_sha256=seal_sha, custody=dict(inventory=str(inv), members=members))))
        rows = records("final")[:2]
        argv, context = worker(group, rows)
        checked = dict(final_seal_sha256=seal_sha), context, {}, dict(argv=argv, cwd=str(group), environment={})
        return checked, rel, sha, inv, dest, guard, rows

    def test_sigint_after_seal_and_during_external_receipt_preserve_verified_prefix(self):
        for mode in ("after-seal", "during-receipt"):
            checked, rel, sha, inv, dest, guard, rows = self.setup_flow(mode)
            emitted = []
            def supervise(*args, **kwargs):
                result = runner._supervise(*args, **kwargs)
                emitted.append(True)
                if mode == "after-seal":
                    os.kill(os.getpid(), signal.SIGINT)
                return result
            signals = []
            def inside(path, raw, **kwargs):
                publish(path, raw, **kwargs)
                if mode == "during-receipt" and not signals:
                    signals.append(True)
                    os.kill(os.getpid(), signal.SIGINT)
            with patch.object(execution, "publish", inside):
                receipt_sha = execution.execute(checked, rel, sha, inv, dest, guard, load_records=lambda *args: rows,
                    supervise=supervise, derive=dummy_derive, verify=dummy_verify)
            receipt = core.decode(read(dest/"execution.json", receipt_sha))
            self.assertEqual(receipt["seal_sha256"], digest(read(dest/"run/seal.json")))
            self.assertEqual(receipt["interruption"]["type"], "KeyboardInterrupt")
            result = execution.audit(checked, rel, sha, inv, dest, receipt_sha, guard,
                                     load_records=lambda *args: rows, verify=dummy_verify)
            self.assertEqual((result["status"], result["verified_cases"], result["verified_controls"]), ("inconclusive",2,5))
            self.assertEqual(emitted, [True])

    def test_confirmed_execution_with_corrupt_artifacts_is_inconclusive(self):
        checked, rel, sha, inv, dest, guard, rows = self.setup_flow("corrupt")
        receipt = execution.execute(checked, rel, sha, inv, dest, guard, load_records=lambda *args: rows,
                                    supervise=runner._supervise, derive=dummy_derive, verify=dummy_verify)
        for victim in ("raw.jsonl", "seal.json", "decisions.jsonl"):
            path = dest/"run"/victim
            original = read(path)
            path.unlink()
            if victim == "raw.jsonl":
                path.write_bytes(b"tampered")
            result = execution.audit(checked, rel, sha, inv, dest, receipt, guard,
                                     load_records=lambda *args: rows, verify=dummy_verify)
            self.assertEqual((result["status"], result["verified_cases"]), ("inconclusive", 0))
            self.assertIn("integrity_error", result)
            path.write_bytes(original)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            execution.audit(checked, rel, sha, inv, dest, "0"*64, guard, load_records=Mock(), verify=dummy_verify)

    def test_redirected_custody_rejected_before_reservation_and_before_first_member(self):
        checked, rel, sha, inv, dest, guard, rows = self.setup_flow("scope")
        opened = Mock()
        with self.assertRaisesRegex(ValueError, "custódia|inventário"):
            execution.execute(checked, rel, sha, self.private/"inventory", dest, guard, load_records=opened,
                              supervise=Mock(), derive=dummy_derive, verify=dummy_verify)
        opened.assert_not_called()
        self.assertFalse(guard.shared.exists())
        with patch("script.classification_comparison.setfit_sf2.qualification_r1.exposure.read") as opened, self.assertRaisesRegex(
                ValueError, "digest"):
            guard.authorization("../secret", checked[0]["final_seal_sha256"])
        opened.assert_not_called()
        scope = guard.reserve(rel, sha, checked[0]["final_seal_sha256"], dest, inv)
        authorized = core.decode(read(inv))
        seal = {"files": {k: {"path": Path(v).name} for k,v in authorized.items() if k in ("final","annotations")}}
        for role in authorized:
            inv.write_bytes(encoded(dict(authorized, **{role: str(self.private/"wrong")})))
            with patch.object(execution, "read", wraps=read) as opened, self.assertRaisesRegex(ValueError, "papéis"):
                execution.records_from_custody(inv, seal, scope)
            self.assertEqual([c.args[0] for c in opened.call_args_list], [inv])
        inv.write_bytes(encoded(authorized))
        Path(authorized["token_lengths"]).symlink_to(self.private/"target")
        with patch.object(execution, "read", wraps=read) as opened, self.assertRaisesRegex(ValueError, "link"):
            execution.records_from_custody(inv, seal, scope)
        self.assertEqual([c.args[0] for c in opened.call_args_list], [inv])
