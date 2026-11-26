"""Identifica as distribuições efetivas do venv pinado e de seu overlay SF1."""
import base64
import hashlib
from contextlib import contextmanager
from importlib.metadata import distributions
from importlib.machinery import EXTENSION_SUFFIXES
from tempfile import TemporaryDirectory
import os
from pathlib import Path
import stat
import sys

from .bootstrap import MAIN, PYTHON
from .storage import canonical, digest, encoded, read, require

SITE = PYTHON.parents[1] / "lib/python3.11/site-packages"
OVERLAY = MAIN / ".worktrees/c05-setfit/script/classification_comparison/setfit_pilot/.venv/lib/python3.11/site-packages"


def verify_member(path, destination):
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW), "rb") as fp:
        require(stat.S_ISREG(os.fstat(fp.fileno()).st_mode), "dependência não regular")
        if destination is None:
            return hashlib.file_digest(fp, "sha256").digest()
        destination.parent.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha256()
        with destination.open("xb") as out:
            while block := fp.read(1024 * 1024):
                h.update(block)
                out.write(block)
            if os.fstat(fp.fileno()).st_mode & 0o111:
                os.fchmod(out.fileno(), 0o700)
        return h.digest()


def installed(name, version, dist, roots, *, target=None, members=None):
    origin = Path(dist.locate_file(""))
    require(origin in roots and version == dist.version and dist.files, "origem/versão da distribuição: " + name)
    hashes = {}
    for entry in dist.files:
        name_in_wheel = str(entry)
        if name_in_wheel.startswith("../"):
            continue
        require(not entry.is_absolute() and ".." not in entry.parts and
                not any(p.startswith(".env") for p in entry.parts), "nome de membro não permitido")
        if entry.suffix == ".pyc":
            # O snapshot gera código exclusivamente a partir das fontes autenticadas.
            continue
        path = canonical(origin / entry)
        actual = verify_member(path, target / entry if target is not None else None)
        if entry.hash:
            require(entry.hash.mode == "sha256" and
                    base64.urlsafe_b64encode(actual).decode().rstrip("=") == entry.hash.value,
                    "arquivo instalado diverge do RECORD: " + name_in_wheel)
        else:
            require(entry.name == "RECORD" and entry.parent.name.endswith(".dist-info"), "membro sem digest no RECORD")
        hashes[name_in_wheel] = actual.hex()
        if members is not None:
            members.add(path)
    return dict(origin=str(origin), version=version, members=len(hashes), files_sha256=digest(encoded(hashes)))


def reject_shadows(roots, known):
    """Um módulo extra em qualquer raiz pode vencer a distribuição atestada na ordem de pesquisa."""
    for root in roots:
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for subdir in dirs:
                require(not (Path(directory) / subdir).is_symlink(), "diretório de imports redirecionado")
            for name in files:
                if name.endswith((".py", ".pyc", *EXTENSION_SUFFIXES)):
                    require(Path(directory) / name in known, "módulo importável fora do RECORD: " + name)


def reject_preloaded(roots):
    for module in tuple(sys.modules.values()):
        for origin in (getattr(module, "__file__", None), getattr(getattr(module, "__spec__", None), "origin", None)):
            if isinstance(origin, str) and any(Path(origin).is_relative_to(root) for root in roots):
                raise ValueError("dependência carregada antes da atestação: " + origin)


def build_sites(versions, roots, directory):
    versions = {name.lower().replace("_", "-"): v for name, v in versions.items() if name != "python"}
    receipt, found, known, targets = {}, set(), set(), []
    for i, root in enumerate(roots):
        target = directory / str(i) / "site-packages"
        target.mkdir(parents=True)
        targets.append(str(target))
        for dist in distributions(path=[str(root)]):
            name = dist.metadata["Name"].lower().replace("_", "-")
            require(name in versions, "distribuição fora do ambiente aceito: " + name)
            found.add(name)
            receipt[str(i) + "/" + name] = installed(name, versions[name], dist, roots, target=target, members=known)
    require(found == versions.keys(), "distribuição ausente")
    reject_shadows(roots, known)
    top_names = set()
    for path in known:
        root = next(r for r in roots if path.is_relative_to(r))
        top = path.relative_to(root).parts[0]
        top_names.add(top.removesuffix(".py"))
    require(not (top_names & sys.modules.keys()), "nome de terceiro já carregado antes da atestação")
    return receipt, targets


@contextmanager
def environment(versions):
    roots = [SITE, OVERLAY]
    reject_preloaded(roots)
    require(not any(p.endswith("/site-packages") for p in sys.path), "use Python -I -B -S sem site pré-carregado")
    pth = {str(path): digest(read(path)) for root in roots for path in root.glob("*.pth")}
    expected = {str(SITE / "sf1-readonly.pth"), str(SITE / "distutils-precedence.pth"),
                str(OVERLAY / "distutils-precedence.pth")}
    require(set(pth) == expected and read(SITE / "sf1-readonly.pth").decode().strip() == str(OVERLAY),
            "overlay efetivo diferente do previsto")
    with TemporaryDirectory(prefix="sf2-site-") as tmp:
        receipt, targets = build_sites(versions, roots, Path(tmp))
        original_prefix = sys.prefix, sys.exec_prefix
        sys.prefix = sys.exec_prefix = str(PYTHON.parents[1])
        sys.path.extend(targets)
        try:
            yield dict(pth=pth, distributions=receipt)
        finally:
            sys.prefix, sys.exec_prefix = original_prefix
            for target in targets:
                sys.path.remove(target)
