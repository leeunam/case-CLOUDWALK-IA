import base64
import hashlib
from importlib.metadata import PackagePath
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ..contracts import core
from ..training.package import package_paths
from ..revision_r1 import cli as replay
from . import bootstrap, dependencies, preflight
from .package import verified_package
from .storage import canonical, digest, encoded, read

ROOT = core.ROOT


def tiny_package(root):
    """Estrutura do manifesto público com payloads numéricos e pequenos em TODOS os membros."""
    raw = read(ROOT / replay.PARENT_FILES["package_manifest"])
    manifest = core.decode(raw)
    paths = package_paths(root, manifest)
    members, models = manifest["files"], manifest["models"]
    for key, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if "/" in key:
            raw = ("fixture " + key).encode()
        elif key in ("arguments", "training_freeze"):
            role = "training_arguments" if key == "arguments" else key
            raw = read(ROOT / replay.PARENT_FILES[role])
        else:
            continue
        path.write_bytes(raw)
        members[key] = digest(raw)
    for field, components in models.items():
        for name in components:
            key = field + "." + name
            raw = encoded({"files": {k.removeprefix(key + "/"): v for k, v in members.items() if k.startswith(key + "/")}})
            paths[key].write_bytes(raw)
            components[name] = members[key] = digest(raw)
        raw = encoded(components)
        paths[field + ".manifest"].write_bytes(raw)
        manifest["model_sha256"][field] = members[field + ".manifest"] = digest(raw)
    raw = encoded(manifest)
    (root / "manifest.json").write_bytes(raw)
    return raw, digest(raw), paths


class Provenance(unittest.TestCase):
    def test_closed_tiny_package_including_both_heads_encoder_tokenizer(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, expected, paths = tiny_package(root)
            with verified_package(root, raw, expected) as (snapshot, manifest):
                self.assertNotEqual(snapshot, root)
                self.assertEqual(len(manifest["files"]), 36)
                for key in ("category", "priority"):
                    for filename in ("body/model.safetensors", "body/tokenizer.json", "head/logistic.joblib"):
                        member = snapshot / key / filename
                        self.assertEqual(read(member), read(root / key / filename))
            self.assertFalse(snapshot.exists())
            for key in ("category.encoder/model.safetensors", "priority.head/logistic.joblib", "category.tokenizer/tokenizer.json"):
                path = paths[key]
                original = read(path)
                path.write_bytes(original + b"x")
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, "membro"):
                    with verified_package(root, raw, expected):
                        pass
                path.write_bytes(original)
            (root / "other").symlink_to(paths["category.encoder/model.safetensors"])
            with self.assertRaisesRegex(ValueError, "link"):
                with verified_package(root, raw, expected):
                    pass
            (root / "other").unlink()
            (root / "extra").touch()
            with self.assertRaisesRegex(ValueError, "inventário"):
                with verified_package(root, raw, expected):
                    pass

    def test_committed_bytes_cover_actual_member_even_when_index_unchanged(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.check_output(["/usr/bin/git", "-C", str(root), *args], stderr=subprocess.DEVNULL)
            git("init", "-q")
            (root / "member.py").write_bytes(b"pass\n")
            git("add", "member.py")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
            commit = git("rev-parse", "HEAD").decode().strip()
            self.assertEqual(bootstrap.committed(root, commit, "member.py"), b"pass\n")
            (root / "member.py").write_bytes(b"pass # impostor\n")
            with self.assertRaisesRegex(ValueError, "commit"):
                bootstrap.committed(root, commit, "member.py")

    def test_installed_distribution_requires_effective_origin_and_recorded_bytes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            member = PackagePath("module.py")
            raw = b"value = 1\n"
            (root/member).write_bytes(raw)
            member.hash = SimpleNamespace(mode="sha256", value=base64.urlsafe_b64encode(
                hashlib.sha256(raw).digest()).decode().rstrip("="))
            dist = SimpleNamespace(version="1", locate_file=lambda _: root, files=[member])
            self.assertEqual(dependencies.installed("example", "1", dist, [root])["members"], 1)
            with self.assertRaisesRegex(ValueError, "origem"):
                dependencies.installed("example", "1", dist, [root/"elsewhere"])
            (root/member).write_bytes(raw + b"other")
            with self.assertRaisesRegex(ValueError, "RECORD"):
                dependencies.installed("example", "1", dist, [root])

    def test_real_public_historical_roles_without_package_or_private_io(self):
        spec = core.decode(read(ROOT / bootstrap.FINAL_PROTOCOL, bootstrap.PLAN_SHA))
        pre = core.decode(read(ROOT / (bootstrap.REV + "/preflight.json"), spec["anchors_sha256"]["offline_preflight"]))
        origin = pre["provenance"]
        amendment, data, _, verified, _ = preflight.attest_history(
            bootstrap.REPLAY, bootstrap.HISTORY, origin["amendment_sha256"], origin["inventory_sha256"])
        self.assertEqual(verified, origin)
        self.assertEqual((len(amendment["parent"]["files"]), len(origin["historical_capture"]),
                          len(origin["historical_adapter"]), len(data)), (28, 19, 17, 29))
        for name, expected in origin["historical_adapter"].items():
            self.assertEqual(digest(read(ROOT / name)), expected)
        self.assertNotEqual(origin["historical_capture"]["evaluation/selection.py"],
                            origin["current_sources"][bootstrap.SF + "/evaluation/selection.py"])

    def test_loaded_values_alien_module_and_monkeypatch_rejected(self):
        files = {k: read(ROOT / replay.PARENT_FILES[k]) for k in ("catalog", "protocol", "schema")}
        substitute = SimpleNamespace(__name__="fixture", load_context=lambda: None, derive=lambda: None, verify=lambda: None)
        with patch.object(core, "CATALOG", {"tampered": True}), self.assertRaisesRegex(ValueError, "memória"):
            preflight.validate_state(ROOT, files, substitute)
        impostor = SimpleNamespace(__file__="/tmp/other-checkout/module.py")
        with patch.dict(sys.modules, {"script.impostor": impostor}), self.assertRaisesRegex(ValueError, "snapshot"):
            preflight.validate_state(ROOT, files, substitute)
        with self.assertRaisesRegex(ValueError, "substituído"):
            preflight.validate_state(ROOT, files, substitute)

    def test_config_cannot_redirect_guard_command_or_projected_path(self):
        projected = ROOT / bootstrap.SF / ".cache/qualificacao-r1-01"
        config = preflight.configuration(ROOT, "0"*40, projected/"release", projected/"run")
        for key in ("guard", "legacy_validation", "package", "historical_checkout", "command", "run"):
            changed = dict(config, **{key: "/tmp/forged-path"})
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "desviado|projetada"):
                preflight.inspect_public(ROOT, "0"*40, ROOT, {}, changed)

