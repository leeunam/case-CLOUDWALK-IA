"""Permissões do pacote montado no contêiner com UID 65534."""
import hashlib
import os
from pathlib import Path
import stat
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from script.classification_comparison.setfit_sf2.serving import provision


class ProvisionTest(unittest.TestCase):
    def test_restrictive_umask_keeps_installed_tree_traversable(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            (source / "category" / "body").mkdir(parents=True)
            (source / "manifest.json").write_bytes(b"{}")
            (source / "category/body/config.json").write_bytes(b"{}")
            archive = root / "synthetic.tar.gz"
            with tarfile.open(archive, "w:gz") as tar:
                tar.add(source, arcname="package")
            dest = root / "installed"
            old_mask = os.umask(0o077)
            try:
                with patch.object(provision, "ARCHIVE_SHA", hashlib.sha256(archive.read_bytes()).hexdigest()), \
                     patch.object(provision, "MANIFEST_SHA", hashlib.sha256(b"{}").hexdigest()):
                    provision.install(archive, dest)
            finally:
                os.umask(old_mask)
            for path in (dest, *dest.rglob("*")):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o755 if path.is_dir() else 0o444, path)
