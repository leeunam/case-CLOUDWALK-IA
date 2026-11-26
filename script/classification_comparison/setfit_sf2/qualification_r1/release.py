"""Recebo um digest externo e reconstruo o pré-voo sobre as entradas públicas."""
from pathlib import Path

from ..contracts.core import decode
from .bootstrap import public_argument
from .storage import digest, encoded, mkdir, publish, read, require


def freeze(config_path, destination, inspect_public, *, layout):
    public_argument(layout, "config", config_path)
    public_argument(layout, "release", destination)
    raw = read(config_path)
    config = decode(raw)
    public_argument(layout, "release", config["release"])
    public_argument(layout, "run", config["run"])
    frozen, _, _ = inspect_public(config)
    mkdir(destination)
    command, inventory = encoded(config["command"]), encoded(frozen)
    publish(destination / "command.json", command)
    publish(destination / "freeze.json", inventory)
    receipt = encoded(dict(config=str(config_path), config_sha256=digest(raw),
                           command_sha256=digest(command), freeze_sha256=digest(inventory)))
    publish(destination / "release.json", receipt)
    return digest(receipt)


def chain(destination, expected, *, layout):
    public_argument(layout, "release", destination)
    receipt = decode(read(destination / "release.json", expected))
    require(set(receipt) == {"config", "config_sha256", "command_sha256", "freeze_sha256"}, "recibo inválido")
    public_argument(layout, "config", receipt["config"])
    config = decode(read(layout["config"], receipt["config_sha256"]))
    public_argument(layout, "release", config["release"])
    public_argument(layout, "run", config["run"])
    command = decode(read(destination / "command.json", receipt["command_sha256"]))
    frozen = decode(read(destination / "freeze.json", receipt["freeze_sha256"]))
    require(config["release"] == str(destination) and config["command"] == command, "destino/comando divergente")
    return config, frozen, command


def check(destination, expected, inspect_public, *, layout):
    config, saved, command = chain(destination, expected, layout=layout)
    frozen, context, seal = inspect_public(config)
    require(encoded(saved) == encoded(frozen), "inventário efetivo diverge da liberação")
    return frozen, context, seal, command

