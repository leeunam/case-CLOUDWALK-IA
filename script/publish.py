"""Opera a demonstração em production com serviços e dados sintéticos."""

import argparse
import fcntl
import http.client
import json
import os
import re
import secrets
import ssl
import stat
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

if __package__:
    from .setfit_config import classifier_options, classifier_overlay
else:
    from setfit_config import classifier_options, classifier_overlay


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env.publish.local"
PROJECT = re.compile(r"cloudwalk_publish(?:_[a-z0-9][a-z0-9_-]*)?\Z")
ORIGIN = r"https://([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.trycloudflare\.com)"
TUNNEL_BANNER = re.compile(r"\|\s*(" + ORIGIN + r")\s*\|")
SECRET = re.compile(r"[A-Za-z0-9_-]{32,128}\Z")
SECRET_KEYS = (
    "PUBLISH_DB_PASSWORD", "PUBLISH_RAILS_SECRET", "PUBLISH_CHANNEL_SECRET",
    "PUBLISH_REQUESTS_SECRET", "PUBLISH_EVENTS_SECRET",
)
PASSWORD_KEY = "PUBLISH_DEMO_PASSWORDS"
USERS = ("alex@example.test", "bia@example.test", "cris@example.test", "supervisor@example.test")
SERVICES = ("db", "kafka", "api", "worker", "outbox", "requests", "events", "mock", "web")
HEALTH = "/api/v1/health"
CA = "/data/caddy/pki/authorities/local/root.crt"


class PublishError(Exception):
    pass


def generate_env(path):
    settings = {key: secrets.token_urlsafe(48) for key in SECRET_KEYS}
    settings[PASSWORD_KEY] = json.dumps({email: secrets.token_urlsafe(32) for email in USERS})
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".env.publish.") as config:
        os.fchmod(config.fileno(), 0o600)
        for key, value in settings.items():
            config.write(f"{key}={value}\n")
        config.flush()
        os.link(config.name, path)


def read_settings(config):
    invalid = PublishError("Configuração local inválida. Confira .env.publish.local sem compartilhar seu conteúdo.")
    try:
        rows = [line.rstrip("\n").split("=", 1) for line in config]
        settings = dict(rows)
        passwords = json.loads(settings.get(PASSWORD_KEY, "null"))
    except ValueError as error:
        raise invalid from error
    if (set(settings) != {*SECRET_KEYS, PASSWORD_KEY} or len(rows) != len(settings)
            or not all(SECRET.fullmatch(settings[key]) for key in SECRET_KEYS)
            or not isinstance(passwords, dict) or set(passwords) != set(USERS)
            or not all(isinstance(value, str) and SECRET.fullmatch(value) for value in passwords.values())):
        raise invalid
    return settings


@contextmanager
def private_env(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, encoding="utf-8") as config:
        mode = os.fstat(config.fileno())
        if not stat.S_ISREG(mode.st_mode) or stat.S_IMODE(mode.st_mode) != 0o600 or mode.st_uid != os.getuid():
            raise PublishError("Use um arquivo privado .env.publish.local com permissão 0600 e de sua propriedade.")
        fcntl.flock(config, fcntl.LOCK_EX)
        yield read_settings(config)


def tunnel_origin(logs):
    origins = {match.group(1) for match in TUNNEL_BANNER.finditer(logs)}
    return next(iter(origins)) if len(origins) == 1 else None


def ready(url, context):
    address = re.fullmatch(ORIGIN, url)
    host, port = (address.group(1), 443) if address else ("127.0.0.1", int(url.rsplit(":", 1)[1]))
    connection = http.client.HTTPSConnection(host, port, context=context, timeout=5)
    try:
        connection.request("GET", HEALTH, headers={"Accept": "application/json"})
        response = connection.getresponse()
        return response.status == 200 and json.loads(response.read(4096)) == {"status": "ok", "database": "ok"}
    except (OSError, ValueError, http.client.HTTPException):
        return False
    finally:
        connection.close()


class Stack:
    def __init__(self, args, settings):
        self.args = args
        self.local_url = f"https://127.0.0.1:{args.https_port}"
        self.env = {key: value for key, value in os.environ.items() if not key.startswith(("COMPOSE_", "PUBLISH_"))}
        self.env.update(settings, PUBLISH_PROJECT=args.project, PUBLISH_HTTP_PORT=str(args.http_port),
                        PUBLISH_HTTPS_PORT=str(args.https_port))
        self.command = [
            "docker", "compose", "--project-name", args.project, "--env-file", os.devnull,
            "--file", str(ROOT / "compose.publish.yml"),
        ]
        self.services = SERVICES
        for overlay in classifier_overlay(args, ROOT, self.env):
            self.command.extend(["--file", str(overlay)])
            self.services += ("setfit",)

    def compose(self, *args, tunnel=False, capture=False, origin=None, timeout=None):
        profile = ["--profile", "tunnel"] if tunnel else []
        env = self.env.copy()
        if origin:
            match = re.fullmatch(ORIGIN, origin)
            if not match:
                raise PublishError("Origem pública do Quick Tunnel inválida.")
            env.update(PUBLISH_PUBLIC_ORIGIN=origin, PUBLISH_PUBLIC_HOST=match.group(1))
        result = subprocess.run(
            [*self.command, *profile, *args], cwd=ROOT, env=env, check=False, timeout=timeout,
            capture_output=capture, text=True,
        )
        if result.returncode:
            raise PublishError(f"Falha no Docker Compose ({args[0]}). Confira o status e os logs locais.")
        return result.stdout

    def tunnel_running(self):
        output = self.compose("ps", "--status", "running", "--services", "cloudflared", tunnel=True, capture=True)
        return "cloudflared" in output.splitlines()

    def up(self):
        if self.tunnel_running():
            raise PublishError("O túnel está ativo. Use unpublish antes de atualizar a pilha local.")
        self.compose("up", "--build", "--wait", "--wait-timeout", "180")
        self.check()

    def ca(self):
        return self.compose("exec", "-T", "web", "cat", CA, capture=True, timeout=10)

    def check(self):
        running = set(self.compose("ps", "--status", "running", "--services", capture=True).splitlines())
        if missing := set(self.services) - running:
            raise PublishError("Serviços ausentes: " + ", ".join(sorted(missing)) + ".")
        context = ssl.create_default_context(cadata=self.ca())
        if not ready(self.local_url, context):
            raise PublishError("API ou banco indisponível pelo HTTPS local.")
        if "setfit" in self.services:
            try:
                self.compose("exec", "-T", "setfit", "python", "-c",
                             "from urllib.request import urlopen; urlopen('http://127.0.0.1:8080/ready', timeout=2).close()",
                             capture=True, timeout=5)
            except (PublishError, subprocess.TimeoutExpired) as error:
                raise PublishError("O classificador SetFit está indisponível.") from error
        print(f"Pilha pronta em {self.local_url}. A CA local pode ser obtida com ca.")

    def prepare(self):
        self.compose("config", "--quiet", tunnel=True)
        self.compose("pull", "cloudflared", tunnel=True)

    def configure_web(self, origin=None):
        for service in ("api", "web"):
            self.compose("up", "--no-deps", "--no-build", "--wait", "--wait-timeout", "90",
                         service, origin=origin)

    def check_running_classifier(self):
        # Consulte somente os seletores dos contêineres ativos, inclusive em imagens fixture legadas.
        probe = """
            if [ "${CLASSIFICATION_PROVIDER-jev}" = setfit ]; then
                echo setfit
            elif [ "${CLASSIFICATION_PROVIDER-jev}" = jev ] && [ "${CLOUDWALK_JEV_MODE-disabled}" = fixture ]; then
                echo fixture
            else
                echo desconhecido
            fi
        """
        for service in ("api", "worker"):
            mode = self.compose("exec", "-T", service, "sh", "-c", probe, capture=True, timeout=5).strip()
            if mode != self.args.classifier:
                raise PublishError(f"O modo de classificação em execução no serviço {service} diverge do solicitado. "
                                   "Use unpublish no modo vigente antes de atualizar a pilha.")

    def unpublish(self):
        self.compose("rm", "--stop", "--force", "cloudflared", tunnel=True, capture=True)
        running = self.compose("ps", "--status", "running", "--services", capture=True)
        if {"api", "web"} <= set(running.splitlines()):
            self.configure_web()
        print("Túnel parado. Os dados da demonstração foram preservados.")

    def publish(self):
        running = self.tunnel_running()
        if running:
            self.check_running_classifier()
            self.check()
        else:
            self.up()
            self.prepare()

        try:
            if not running:
                self.compose("up", "-d", "--no-deps", "--force-recreate", "cloudflared", tunnel=True, capture=True)
            origin = self.wait_for_origin()
            self.configure_web(origin)
            deadline = time.monotonic() + 90
            context = ssl.create_default_context()
            while time.monotonic() < deadline:
                if ready(origin, context) and self.tunnel_running():
                    print(f"Demonstração publicada em {origin}")
                    return
                time.sleep(2)
            raise PublishError("A verificação HTTPS do Quick Tunnel excedeu o prazo.")
        except (PublishError, OSError, subprocess.TimeoutExpired, KeyboardInterrupt):
            self.unpublish()
            raise

    def wait_for_origin(self):
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline and self.tunnel_running():
            logs = self.compose("logs", "--no-color", "--no-log-prefix", "cloudflared", tunnel=True,
                                capture=True, timeout=10)
            if origin := tunnel_origin(logs):
                return origin
            time.sleep(1)
        raise PublishError("O cloudflared não forneceu uma URL HTTPS válida no prazo.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="cloudwalk_publish")
    parser.add_argument("--http-port", type=int, default=18080)
    parser.add_argument("--https-port", type=int, default=18443)
    classifier_options(parser, ("fixture",))
    parser.add_argument("action", choices=(
        "init", "credentials", "config", "up", "check", "status", "down", "logs", "ca", "prepare", "publish", "unpublish",
    ))
    args = parser.parse_args()
    if not PROJECT.fullmatch(args.project):
        parser.error("use cloudwalk_publish ou um nome exclusivo com prefixo cloudwalk_publish_.")
    if args.http_port == args.https_port or any(port not in range(1024, 65536)
                                                for port in (args.http_port, args.https_port)):
        parser.error("informe duas portas diferentes entre 1024 e 65535.")

    try:
        if args.action == "init":
            try:
                generate_env(ENV_FILE)
                print("Arquivo .env.publish.local criado com permissão 0600.")
            except FileExistsError:
                with private_env(ENV_FILE):
                    print("Arquivo .env.publish.local já provisionado.")
            return

        with private_env(ENV_FILE) as settings:
            stack = Stack(args, settings)
            if args.action == "credentials":
                if not sys.stdout.isatty():
                    raise PublishError("Abra credentials em um terminal privado para ver as senhas sintéticas.")
                for email, password in json.loads(settings[PASSWORD_KEY]).items():
                    print(f"{email}  {password}")
            elif args.action == "config":
                stack.compose("config", "--quiet", tunnel=True)
            elif args.action == "status":
                stack.compose("ps", "--all", tunnel=True)
            elif args.action == "down":
                stack.compose("down", tunnel=True)
            elif args.action == "logs":
                stack.compose("logs", "--tail", "80", "db_setup", "kafka_setup", *stack.services)
            elif args.action == "ca":
                print(stack.ca(), end="")
            else:
                getattr(stack, args.action)()
    except FileNotFoundError as error:
        missing = "Use init para provisionar a configuração local." if error.filename == str(ENV_FILE) else (
            "Instale Docker com Docker Compose v2 e confira sua disponibilidade."
        )
        parser.exit(1, f"Erro: {missing}\n")
    except (PublishError, OSError, subprocess.TimeoutExpired) as error:
        message = str(error) if isinstance(error, PublishError) else "Falha de acesso ao arquivo local ou ao Docker."
        parser.exit(1, f"Erro: {message}\n")
    except KeyboardInterrupt:
        parser.exit(130, "Operação interrompida. Confira o status local.\n")


if __name__ == "__main__":
    main()
