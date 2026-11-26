"""Congela o pacote em disco temporário, copiando arquivos regulares uma vez."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory

from ..contracts.core import decode
from ..training.package import package_paths, read_verified_package
from .storage import canonical, digest, read, require


def copy_member(source, target, expected):
    canonical(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    with os.fdopen(os.open(source, os.O_NOFOLLOW | os.O_RDONLY | os.O_NONBLOCK), "rb") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "membro não regular")
        with target.open("xb") as dest:
            while block := stream.read(1024 * 1024):
                hasher.update(block)
                dest.write(block)
    require(hasher.hexdigest() == expected, "membro do pacote divergente: " + str(source))


@contextmanager
def verified_package(source, manifest_bytes, expected):
    canonical(source)
    require(digest(manifest_bytes) == expected and read(source / "manifest.json", expected) == manifest_bytes,
            "manifesto local divergente")
    manifest = decode(manifest_bytes)
    paths = package_paths(source, manifest)
    actual = set()
    for directory, dirs, files in os.walk(source, followlinks=False, onerror=_raise):
        for name in dirs:
            canonical(Path(directory) / name)
        for name in files:
            actual.add(canonical(Path(directory) / name))
    require(actual == {*paths.values(), source / "manifest.json"}, "inventário físico do pacote divergente")
    with TemporaryDirectory(prefix="sf2-weights-") as tmp:
        snapshot = Path(tmp)
        (snapshot / "manifest.json").write_bytes(manifest_bytes)
        for role, path in paths.items():
            copy_member(path, snapshot / path.relative_to(source), manifest["files"][role])
        checked, _ = read_verified_package(snapshot, expected)
        require(checked == manifest, "manifesto verificado divergente")
        yield snapshot, checked


def _raise(exc):
    raise exc

