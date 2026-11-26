"""Congela o pacote em disco temporário, copiando arquivos regulares uma vez."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from ..contracts.core import decode
from ..training.package import package_paths, read_verified_package
from .storage import digest, directory, open_regular, read, require


def copy_member(source, target, expected):
    target.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    with open_regular(source) as stream:
        with target.open("xb") as dest:
            while block := stream.read(1024 * 1024):
                hasher.update(block)
                dest.write(block)
    require(hasher.hexdigest() == expected, "membro do pacote divergente: " + str(source))


@contextmanager
def verified_package(source, manifest_bytes, expected):
    require(digest(manifest_bytes) == expected and read(source / "manifest.json", expected) == manifest_bytes,
            "manifesto local divergente")
    manifest = decode(manifest_bytes)
    paths = package_paths(source, manifest)
    expected_files = {*paths.values(), source / "manifest.json"}
    expected_dirs = {parent for path in expected_files for parent in path.parents if parent.is_relative_to(source)}
    pending = [source]
    actual = set()
    while pending:
        folder = pending.pop()
        with directory(folder) as fd, os.scandir(fd) as entries:
            for entry in entries:
                path = folder / entry.name
                require(not entry.is_symlink(), "link no inventário do pacote")
                if entry.is_dir(follow_symlinks=False):
                    require(path in expected_dirs, "diretório fora do inventário do pacote")
                    pending.append(path)
                else:
                    require(entry.is_file(follow_symlinks=False), "membro não regular")
                    actual.add(path)
    require(actual == expected_files, "inventário físico do pacote divergente")
    with TemporaryDirectory(dir="/tmp", prefix="sf2-weights-") as tmp:
        snapshot = Path(tmp)
        (snapshot / "manifest.json").write_bytes(manifest_bytes)
        for role, path in paths.items():
            copy_member(path, snapshot / path.relative_to(source), manifest["files"][role])
        checked, _ = read_verified_package(snapshot, expected)
        require(checked == manifest, "manifesto verificado divergente")
        yield snapshot, checked
