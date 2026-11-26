"""Regressões do pré-voo. As origens modificadas e o destino restrito são fictícios."""
from contextlib import ExitStack
import errno
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ..revision_r1 import cli as replay
from . import bootstrap, cli, package, preflight
from .storage import digest, read
from .test_preflight import tiny_package
from .test_release_bootstrap import no_target_operations


class PublicIO(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.blocked = self.root / "restricted-target"
        self.blocked.mkdir()

    def test_first_temporary_lookup_and_snapshots_ignore_all_environment_candidates(self):
        raw, sha, _ = tiny_package(self.root / "package")
        def probe(args):
            # Arquivos e diretórios temporários de terceiros, mesmo sem dir explícito.
            with tempfile.NamedTemporaryFile() as file, tempfile.TemporaryDirectory() as folder:
                self.assertEqual(Path(file.name).parent, Path("/tmp"))
                self.assertEqual(Path(folder).parent, Path("/tmp"))
            for key in ("TMPDIR", "TEMP", "TMP"):
                self.assertEqual(os.environ[key], "/tmp")
            with bootstrap.snapshot(self.root, "fixture") as (source, _):
                self.assertEqual(source.parent, Path("/tmp"))
                with package.verified_package(self.root / "package", raw, sha) as (copy, _):
                    self.assertEqual(copy.parent, Path("/tmp"))

        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, dict.fromkeys(("TMPDIR", "TEMP", "TMP"), str(self.blocked))))
            stack.enter_context(patch.object(tempfile, "tempdir", None))
            for name in ("entry_environment", "checkout", "resources"):
                stack.enter_context(patch.object(bootstrap, name, return_value={}))
            stack.enter_context(patch.object(cli, "dispatch", side_effect=probe))
            with no_target_operations(self.blocked):
                cli.main(["template", "--release", "/unused", "--run", "/unused-run"])
        self.assertEqual(list(self.blocked.iterdir()), [])

    def test_historical_role_and_parent_links_are_rejected_before_target_lookup(self):
        for kind in ("file", "parent"):
            with self.subTest(kind=kind):
                source = self.root / kind
                source.mkdir()
                name = replay.EXTRA_TRAINING["review_receipt"]
                role = source / name
                link = role if kind == "file" else role.parent
                link.parent.mkdir(parents=True)
                target = self.blocked / kind
                if kind == "file":
                    target.write_bytes(b"forbidden")
                else:
                    target.mkdir()
                link.symlink_to(target)
                with no_target_operations(self.blocked, link), self.assertRaises(OSError) as refused:
                    preflight.attest_history(source, self.root / "capture", "a"*64, "b"*64)
                self.assertIn(refused.exception.errno, (errno.ENOTDIR, errno.ELOOP))
                with no_target_operations(self.blocked, link), self.assertRaises(OSError):
                    bootstrap.committed(source, "a"*40, name)

    def test_historical_verifier_consumes_the_detached_role(self):
        origin = self.root / "replay"
        name = replay.PARENT_FILES["catalog"]
        source = origin / name
        source.parent.mkdir(parents=True)
        source.write_bytes(b"catalog fixture")
        expected = digest(source.read_bytes())

        def synthetic_read(path):
            return read(source) if path == source else b"other fixture"

        def consume(replay_copy, history_copy, amendment_sha, inventory_sha):
            source.write_bytes(b"changed after snapshot")
            return replay.verified(replay_copy, name, expected)

        with patch.object(preflight, "read", synthetic_read), patch.object(replay, "attest", consume):
            self.assertEqual(preflight.attest_history(origin, self.root / "capture", "a"*64, "b"*64),
                             b"catalog fixture")

    def test_extra_package_file_directory_and_parent_links_never_query_targets(self):
        root = self.root / "package"
        raw, sha, _ = tiny_package(root)
        for kind in ("extra-file", "extra-directory", "parent"):
            with self.subTest(kind=kind):
                target = self.blocked / kind
                link = root / kind if kind != "parent" else root / "category"
                if kind == "parent":
                    link.rename(target)
                elif kind == "extra-directory":
                    target.mkdir()
                else:
                    target.write_bytes(b"forbidden")
                link.symlink_to(target)
                with no_target_operations(self.blocked, link), self.assertRaisesRegex(ValueError, "link"):
                    with package.verified_package(root, raw, sha):
                        self.fail("pacote com link aceito")
                link.unlink()
                if kind == "parent":
                    target.rename(link)

    def test_package_parent_swapped_after_enumeration_and_detached_bytes(self):
        root = self.root / "package"
        raw, sha, paths = tiny_package(root)
        member = paths["category.encoder/model.safetensors"]
        with package.verified_package(root, raw, sha) as (snapshot, manifest):
            original = member.read_bytes()
            member.write_bytes(b"changed")
            copy = read(snapshot / member.relative_to(root))
            self.assertEqual(copy, original)
            self.assertEqual(digest(copy), manifest["files"]["category.encoder/model.safetensors"])
            member.write_bytes(original)
        parent = root / "category"
        def swap(*args):
            parent.rename(self.blocked / "category")
            parent.symlink_to(self.blocked / "category")
            with no_target_operations(self.blocked, parent):
                original_copy(*args)
        original_copy = package.copy_member
        def copy(source, *args):
            if source.is_relative_to(parent):
                return swap(source, *args)
            return original_copy(source, *args)
        with patch.object(package, "copy_member", copy), self.assertRaises(OSError):
            with package.verified_package(root, raw, sha):
                self.fail("pai redirecionado aceito")
