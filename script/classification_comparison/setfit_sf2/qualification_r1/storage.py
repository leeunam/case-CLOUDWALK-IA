"""Publicação durável e leitura estrita dos bytes identificados pelo recibo."""
import hashlib
import json
import os
import math
import stat
from pathlib import Path
from contextlib import contextmanager
from secrets import token_hex


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decode(raw):
    """O bootstrap interpreta o mesmo buffer autenticado e recusa chaves duplicadas e valores não finitos."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "chave JSON duplicada")
            result[key] = value
        return result

    def finite(value):
        number = float(value)
        require(math.isfinite(number), "valor JSON não finito")
        return number

    return json.loads(raw, object_pairs_hook=unique, parse_constant=finite, parse_float=finite)


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


@contextmanager
def directory(path):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "diretório fora da raiz")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open("/", flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


@contextmanager
def open_regular(path):
    path = Path(path)
    with directory(path.parent) as parent:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as source:
            require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), "arquivo não regular")
            yield source


def read(path, expected=None):
    with open_regular(path) as source:
        raw = source.read()
    if expected is not None:
        require(digest(raw) == expected, "SHA-256 divergente: " + str(path))
    return raw


def sync_directory(path):
    with directory(path) as fd:
        os.fsync(fd)


def mkdir(path):
    with directory(path.parent) as parent:
        os.mkdir(path.name, mode=0o700, dir_fd=parent)
        os.fsync(parent)


def write_new(parent, name, raw):
    fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=parent)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def exclusive(path, raw):
    with directory(path.parent) as parent:
        write_new(parent, path.name, raw)
        os.fsync(parent)


def publish(path, raw, *, replace=False):
    """O nome público designa um arquivo completo mesmo se o processo for interrompido."""
    with directory(path.parent) as parent:
        pending = ".pending-" + token_hex(16)
        try:
            write_new(parent, pending, raw)
            if replace:
                os.rename(pending, path.name, src_dir_fd=parent, dst_dir_fd=parent)
            else:
                os.link(pending, path.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            os.fsync(parent)
        finally:
            try:
                os.unlink(pending, dir_fd=parent)
            except FileNotFoundError:
                pass
