"""Recebo um digest externo e reconstruo o pré-voo sobre as entradas públicas."""
from dataclasses import dataclass
import re

from .bootstrap import public_argument
from .storage import decode, digest, encoded, mkdir, publish, read, require


@dataclass(frozen=True)
class AuthenticatedRelease:
    sha256: str
    config: dict
    frozen: dict
    command: dict


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
    require(type(expected) is str and re.fullmatch("[0-9a-f]{64}", expected), "digest externo inválido")
    receipt = decode(read(destination / "release.json", expected))
    require(set(receipt) == {"config", "config_sha256", "command_sha256", "freeze_sha256"}, "recibo inválido")
    require(all(type(receipt[key]) is str and re.fullmatch("[0-9a-f]{64}", receipt[key])
                for key in ("config_sha256", "command_sha256", "freeze_sha256")), "referência sem SHA-256 válido")
    public_argument(layout, "config", receipt["config"])
    config = decode(read(layout["config"], receipt["config_sha256"]))
    public_argument(layout, "release", config["release"])
    public_argument(layout, "run", config["run"])
    command = decode(read(destination / "command.json", receipt["command_sha256"]))
    frozen = decode(read(destination / "freeze.json", receipt["freeze_sha256"]))
    require(config["release"] == str(destination) and config["command"] == command, "destino/comando divergente")
    return AuthenticatedRelease(expected, config, frozen, command)


def check(destination, expected, inspect_public, *, layout):
    return check_authenticated(chain(destination, expected, layout=layout), inspect_public)


def check_authenticated(authenticated, inspect_public):
    frozen, context, seal = inspect_public(authenticated.config)
    require(encoded(authenticated.frozen) == encoded(frozen), "inventário efetivo diverge da liberação")
    return frozen, context, seal, authenticated.command

