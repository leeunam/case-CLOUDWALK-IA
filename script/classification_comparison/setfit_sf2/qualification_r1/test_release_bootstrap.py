"""A liberação é autenticada sem importar terceiros. Raízes e recibos são todos sintéticos."""
import base64
from contextlib import ExitStack, nullcontext
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from . import bootstrap, cli, dependencies, release
from .exposure import Guard
from .storage import digest, encoded


def wheel(root, code):
    meta = root / "demo-1.dist-info"
    meta.mkdir(exist_ok=True)
    source = root / "sf2_fake_module.py"
    source.write_bytes(code)
    (meta / "METADATA").write_bytes(b"Metadata-Version: 2.1\nName: demo\nVersion: 1\n")
    lines = []
    for path in (source, meta / "METADATA"):
        raw = path.read_bytes()
        sha = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")
        lines.append(f"{path.relative_to(root)},sha256={sha},{len(raw)}")
    (meta / "RECORD").write_text("\n".join([*lines, "demo-1.dist-info/RECORD,,"]) + "\n")
    return meta


class EarlyTrust(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.first, self.second = self.root / "venv", self.root / "overlay"
        for folder in (self.first, self.second):
            folder.mkdir()
            (folder / "distutils-precedence.pth").write_bytes(b"# fixture\n")
        (self.first/"sf1-readonly.pth").write_text(str(self.second) + "\n")

    def test_all_locked_commands_refuse_a_consistent_changed_wheel_before_any_third_party_import(self):
        if not sys.flags.no_site:
            # A suíte convencional já pode ter carregado terceiros. A sonda sempre parte de um processo limpo.
            subprocess.run([sys.executable, "-I", "-B", "-S", "-c",
                            "import os,sys,unittest; sys.path.insert(0,os.getcwd()); unittest.main(module=None)",
                            self.id()], cwd=Path(__file__).absolute().parents[4], check=True)
            return
        committed = "c" * 40
        sources = {"source.py": digest(b"source")}
        layout = bootstrap.public_layout(self.root)
        rel, run, config = (layout[k] for k in ("release", "run", "config"))
        config.parent.mkdir(parents=True)
        config.write_bytes(encoded(dict(accepted_commit=committed, release=str(rel), run=str(run), command={})))
        versions = {"demo": "1"}
        manifest = self.root / "docs/evidencias/c05/sf2/qualificacao-01/execucao-02/pacote/manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_bytes(encoded(dict(versions=versions)))
        seal = digest(b"fake seal")
        protocol = self.root / bootstrap.FINAL_PROTOCOL
        protocol.parent.mkdir(parents=True)
        protocol.write_bytes(encoded({"anchors_sha256": {"public_final_seal": seal}}))
        cust = self.root / "fictional-custody"
        inventory = cust / "inventory.json"
        guard = Guard(self.root/"shared", self.root/"legacy", self.root/"old", self.root/"auth", cust)
        guard.authorizations.mkdir()
        wheel(self.second, b"value = 'original'\n")
        with ExitStack() as stack:
            for owner, key, value in ((dependencies, "SITE", self.first), (dependencies, "OVERLAY", self.second),
                (cli, "ROOT", self.root), (bootstrap, "CUSTODY", cust), (bootstrap, "PLAN_SHA", digest(protocol.read_bytes())),
                (bootstrap, "PACKAGE_SHA", digest(manifest.read_bytes())), (cli, "bootstrap", lambda: (bootstrap, committed)),
                (bootstrap, "snapshot", lambda *args: nullcontext((self.root, sources))), (Guard, "production", lambda: guard)):
                stack.enter_context(patch.object(owner, key, value))
            with dependencies.environment(versions, expected=None) as initial:
                frozen = dict(accepted_commit=committed, current_sources=sources, dependencies=deepcopy(initial),
                              python_executable=bootstrap.interpreter(), final_seal_sha256=seal)
            sha = release.freeze(config, rel, lambda cfg: (frozen, {}, {}), layout=layout)
            members = {role: str(cust/role) for role in ("final", "annotations", "review_receipt", "token_lengths")}
            (guard.authorizations/(sha+".json")).write_bytes(encoded(dict(action="execute_once", release_sha256=sha,
                final_seal_sha256=seal, custody=dict(inventory=str(inventory), members=members))))
            guard.reserve(rel, sha, seal, run, inventory)
            wheel(self.second, b"value = 'changed'\n")
            activated, third_party = [], []
            class ObservedPath(list):
                def extend(self, names):
                    activated.extend(names)
                    super().extend(names)
            class ObserveImports:
                def find_spec(self, fullname, path=None, target=None):
                    if fullname.split(".")[0] not in sys.stdlib_module_names and not fullname.startswith("script."):
                        third_party.append(fullname)
                    return None
            verified = stack.enter_context(patch.object(cli, "dispatch_verified", side_effect=AssertionError("import prematuro")))
            stack.enter_context(patch.object(sys, "path", ObservedPath(sys.path)))
            stack.enter_context(patch.object(sys, "meta_path", [ObserveImports(), *sys.meta_path]))
            for cmd in (
                ["check", "--expect", sha],
                ["execute", "--expect", sha, "--custody", str(inventory), "--out", str(run)],
                ["audit", "--expect", sha, "--custody", str(inventory), "--run", str(run), "--execution-sha256", "0"*64],
                ["_worker", "--commit", committed, "--run", str(run), "--package", str(bootstrap.PACKAGE),
                 "--package-sha256", bootstrap.PACKAGE_SHA, "--policy", str(self.root/bootstrap.CAPTURE_POLICY)],
            ):
                with self.subTest(command=cmd[0]), self.assertRaisesRegex(ValueError, "cópia de dependências"):
                    cli.dispatch(cli.parse([*cmd, "--release", str(rel)]))
            self.assertEqual((activated, third_party), ([], []))
            verified.assert_not_called()
            with patch.object(dependencies, "build_sites") as build, self.assertRaisesRegex(ValueError, "SHA-256"):
                cli.dispatch(cli.parse(["check","--expect","0"*64,"--release",str(rel)]))
            build.assert_not_called()
            # Mesmo com um digest externo correto, referências nulas não autenticam os bytes do inventário.
            receipt_path = rel / "release.json"
            bad = json.loads(receipt_path.read_bytes())
            bad["freeze_sha256"] = None
            receipt_path.write_bytes(encoded(bad))
            with patch.object(dependencies, "build_sites") as build, self.assertRaisesRegex(ValueError, "referência"):
                cli.dispatch(cli.parse(["check", "--expect", digest(receipt_path.read_bytes()), "--release", str(rel)]))
            build.assert_not_called()

    def test_metadata_directory_metadata_file_and_record_file_never_follow_links(self):
        blocked = self.root / "restricted-target"
        blocked.mkdir()
        meta = wheel(self.second, b"fixture")
        for kind in ("directory", "METADATA", "RECORD"):
            link = meta if kind == "directory" else meta / kind
            target = blocked / kind
            link.rename(target)
            link.symlink_to(target, target_is_directory=kind == "directory")
            attempted = []
            original_readlink = os.readlink
            def monitored(fn, opname):
                def observed(path, *args, **kwargs):
                    if not isinstance(path, int):
                        name = Path(path)
                        if not name.is_absolute() and kwargs.get("dir_fd") is not None:
                            parent = Path(original_readlink("/proc/self/fd/" + str(kwargs["dir_fd"])))
                            name = parent / name
                        follows_final = (opname == "open" and not (args[0] & os.O_NOFOLLOW)
                                         or opname == "stat" and kwargs.get("follow_symlinks", True)
                                         or opname in ("io.open", "scandir"))
                        if (name.is_relative_to(blocked) or (name != link and name.is_relative_to(link))
                                or name == link and follows_final):
                            attempted.append((opname, str(name)))
                            raise AssertionError("consulta chegaria ao alvo restrito")
                    return fn(path, *args, **kwargs)
                return observed
            try:
                with self.subTest(kind=kind), ExitStack() as stack:
                    for owner, name, label in ((os,"open","open"),(os,"stat","stat"),(os,"lstat","lstat"),
                                                (os,"scandir","scandir"),(io,"open","io.open")):
                        stack.enter_context(patch.object(owner, name, monitored(getattr(owner,name), label)))
                    with self.assertRaises(OSError):
                        dependencies.build_sites({"demo": "1"}, [self.first,self.second], self.root/("copy-"+kind))
                    self.assertEqual(attempted, [])
            finally:
                link.unlink()
                target.rename(link)
