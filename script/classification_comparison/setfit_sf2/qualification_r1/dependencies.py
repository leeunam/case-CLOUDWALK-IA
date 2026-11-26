"""Identifica as distribuições efetivas do venv pinado e de seu overlay SF1."""
import base64
import hashlib
from importlib.metadata import distribution
import os
from pathlib import Path
import stat
import sys

from .bootstrap import MAIN, PYTHON
from .storage import canonical, digest, encoded, read, require

SITE = PYTHON.parents[1] / "lib/python3.11/site-packages"
OVERLAY = MAIN / ".worktrees/c05-setfit/script/classification_comparison/setfit_pilot/.venv/lib/python3.11/site-packages"


def file_digest(path):
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW), "rb") as fp:
        require(stat.S_ISREG(os.fstat(fp.fileno()).st_mode), "dependência não regular")
        return hashlib.file_digest(fp, "sha256").digest()


def installed(name, version, dist, roots):
    origin = Path(dist.locate_file(""))
    require(origin in roots and version == dist.version and dist.files, "origem/versão da distribuição: " + name)
    hashes = {}
    for entry in dist.files:
        name_in_wheel = str(entry)
        # Scripts de console e páginas man estão fora do caminho de importação do classificador.
        if name_in_wheel.startswith("../"):
            continue
        require(not any(p.startswith(".env") for p in entry.parts), "arquivo de ambiente não permitido")
        path = canonical(origin / entry)
        if entry.suffix == ".pyc" and not path.exists():
            continue
        actual = file_digest(path)
        if entry.hash:
            require(entry.hash.mode == "sha256" and
                    base64.urlsafe_b64encode(actual).decode().rstrip("=") == entry.hash.value,
                    "arquivo instalado diverge do RECORD: " + name_in_wheel)
        hashes[name_in_wheel] = actual.hex()
    return dict(origin=str(origin), version=version, members=len(hashes), files_sha256=digest(encoded(hashes)))


def inventory(versions):
    roots = [Path(p) for p in sys.path if p.endswith("/site-packages")]
    require(roots == [SITE, OVERLAY], "origens efetivas do venv divergentes")
    pth = {str(path): digest(read(path)) for root in roots for path in root.glob("*.pth")}
    expected = {str(SITE / "sf1-readonly.pth"), str(SITE / "distutils-precedence.pth"),
                str(OVERLAY / "distutils-precedence.pth")}
    require(set(pth) == expected and read(SITE / "sf1-readonly.pth").decode().strip() == str(OVERLAY),
            "overlay efetivo diferente do previsto")
    return dict(pth=pth, distributions={name: installed(name, v, distribution(name), roots)
                                       for name, v in versions.items() if name != "python"})

