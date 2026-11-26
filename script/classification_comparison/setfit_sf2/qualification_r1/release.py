"""Recebo um digest externo e reconstruo o pré-voo sobre as entradas públicas."""
from pathlib import Path

from ..contracts.core import decode
from .storage import canonical, digest, encoded, publish, read, require, sync_directory


def freeze(config_path, destination, inspect_public):
    config_path = canonical(config_path)
    raw = read(config_path)
    config = decode(raw)
    require(config["release"] == str(destination), "destino diferente do planejado")
    frozen, _, _ = inspect_public(config)
    destination.mkdir()
    sync_directory(destination.parent)
    command, inventory = encoded(config["command"]), encoded(frozen)
    publish(destination / "command.json", command)
    publish(destination / "freeze.json", inventory)
    receipt = encoded(dict(config=str(config_path), config_sha256=digest(raw),
                           command_sha256=digest(command), freeze_sha256=digest(inventory)))
    publish(destination / "release.json", receipt)
    return digest(receipt)


def chain(destination, expected):
    receipt = decode(read(destination / "release.json", expected))
    require(set(receipt) == {"config", "config_sha256", "command_sha256", "freeze_sha256"}, "recibo inválido")
    config = decode(read(Path(receipt["config"]), receipt["config_sha256"]))
    command = decode(read(destination / "command.json", receipt["command_sha256"]))
    frozen = decode(read(destination / "freeze.json", receipt["freeze_sha256"]))
    require(config["release"] == str(destination) and config["command"] == command, "destino/comando divergente")
    return config, frozen, command


def check(destination, expected, inspect_public):
    config, saved, command = chain(destination, expected)
    frozen, context, seal = inspect_public(config)
    require(encoded(saved) == encoded(frozen), "inventário efetivo diverge da liberação")
    return frozen, context, seal, command

