"""Publicação durável e leitura estrita dos bytes identificados pelo recibo."""
import hashlib
import json
import os
import stat
from pathlib import Path
from tempfile import NamedTemporaryFile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode()


def canonical(path):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "caminho relativo: " + str(path))
    for component in (*reversed(path.parents), path):
        require(not component.is_symlink(), "link não permitido: " + str(component))
    return path


def read(path, expected=None):
    path = canonical(path)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as source:
        require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), "arquivo não regular")
        raw = source.read()
    if expected is not None:
        require(digest(raw) == expected, "SHA-256 divergente: " + str(path))
    return raw


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def exclusive(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(path.parent)


def publish(path, raw):
    """O nome público designa um arquivo completo mesmo se o processo for interrompido."""
    with NamedTemporaryFile(dir=path.parent, prefix=".pending-", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
            os.link(temporary, path)
            sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)

