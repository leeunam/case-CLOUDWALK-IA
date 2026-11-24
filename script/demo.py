"""Inicia e verifica a demonstração local com dados e chaves sintéticas."""

import argparse
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env.demo.local"
COMPOSE_FILES = [ROOT / "compose.yml", ROOT / "compose.demo.yml"]
SECRET_KEYS = (
    "DEMO_POSTGRES_PASSWORD",
    "DEMO_RAILS_SECRET",
    "DEMO_CHANNEL_SECRET",
    "DEMO_AGENT_REQUESTS_SECRET",
    "DEMO_AGENT_EVENTS_SECRET",
)
EMAILS = tuple(f"{name}@example.test" for name in ("alex", "bia", "cris", "supervisor"))


def create_env():
    if os.path.lexists(ENV_FILE):
        return
    values = {key: secrets.token_hex(64) for key in SECRET_KEYS}
    passwords = {email: secrets.token_urlsafe(24) for email in EMAILS}
    with tempfile.NamedTemporaryFile(mode="w", dir=ROOT, prefix=".env.demo.local.") as temporary:
        for key, value in values.items():
            temporary.write(f"{key}={value}\n")
        temporary.write(f"DEMO_PASSWORDS='{json.dumps(passwords, separators=(',', ':'))}'\n")
        temporary.flush()
        try:
            os.link(temporary.name, ENV_FILE)
        except FileExistsError:
            pass


def read_env():
    def open_private(path, flags):
        return os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK)

    try:
        with open(ENV_FILE, encoding="utf-8", opener=open_private) as source:
            metadata = os.fstat(source.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
                raise SystemExit("Use um .env.demo.local regular e privado (chmod 600).")
            if metadata.st_size > 4096:
                raise SystemExit("O arquivo .env.demo.local é maior que o gerado pela demo.")
            lines = source.read().splitlines()
    except FileNotFoundError:
        raise SystemExit("Crie as credenciais da demo com python3 script/demo.py init.") from None
    except (OSError, UnicodeError):
        raise SystemExit("Não foi possível ler .env.demo.local como arquivo privado.") from None

    values = dict(line.split("=", 1) for line in lines if "=" in line)
    try:
        if len(lines) != len(SECRET_KEYS) + 1 or values.keys() != {*SECRET_KEYS, "DEMO_PASSWORDS"}:
            raise ValueError
        if not all(re.fullmatch(r"[a-f0-9]{128}", values[key]) for key in SECRET_KEYS):
            raise ValueError
        raw_passwords = values["DEMO_PASSWORDS"]
        if not re.fullmatch(r"'[{}\"a-zA-Z0-9@.\-_:,]+'", raw_passwords):
            raise ValueError
        values["DEMO_PASSWORDS"] = raw_passwords[1:-1]
        passwords = json.loads(values["DEMO_PASSWORDS"])
        if not isinstance(passwords, dict) or passwords.keys() != set(EMAILS):
            raise ValueError
        if not all(isinstance(item, str) and re.fullmatch(r"[a-zA-Z0-9_-]{32}", item)
                   for item in passwords.values()):
            raise ValueError
    except ValueError:
        raise SystemExit("O formato de .env.demo.local não corresponde ao arquivo gerado pela demo.") from None
    return values


class Compose:
    def __init__(self, args):
        overridden = {"POSTGRES_USER", "POSTGRES_PASSWORD", "API_PORT", "WEB_PORT", "KAFKA_RETENTION_MS",
                      "FEITA_API_KEY", "TYPESAFE_API_KEY", "SECRET_KEY_BASE"}
        self.env = {key: os.environ[key] for key in os.environ
                    if not key.startswith(("COMPOSE_", "DEMO_", "CLOUDWALK_")) and key not in overridden}
        self.env.update(DEMO_API_PORT=str(args.api_port), DEMO_WEB_PORT=str(args.web_port),
                        DEMO_CLASSIFIER_MODE=args.classifier)
        self.prefix = ["docker", "compose", "--project-name", args.project, "--env-file", str(ENV_FILE)]
        for file in COMPOSE_FILES:
            self.prefix.extend(["-f", str(file)])

    def run(self, *arguments, capture=False):
        return subprocess.run([*self.prefix, *arguments], cwd=ROOT, env=self.env, check=True,
                              text=True, stdout=subprocess.PIPE if capture else None).stdout


def check_demo(args, compose, values):
    # O verificador canônico consulta o broker com seu próprio `docker compose exec`.
    api = compose.run("port", "web", "5173", capture=True).strip()
    if not re.fullmatch(r"127\.0\.0\.1:[0-9]+", api):
        raise SystemExit("O frontend precisa estar em execução e publicado no loopback.")
    channel_id = compose.run(
        "exec", "-T", "api", "bundle", "exec", "rails", "runner",
        'puts Operations::Brand.find_by!(code: "aurora").channels.find_by!(kind: "chat").id',
        capture=True,
    ).strip()
    if not re.fullmatch(r"[\da-f-]{36}", channel_id):
        raise SystemExit("O canal Chat da Aurora não está disponível no seed.")
    check_env = {
        **compose.env,
        "COMPOSE_FILE": os.pathsep.join(map(str, COMPOSE_FILES)),
        "COMPOSE_ENV_FILES": str(ENV_FILE),
        "CLOUDWALK_CHANNEL_SECRET": values["DEMO_CHANNEL_SECRET"],
        "CLOUDWALK_AGENT_EVENTS_SECRET": values["DEMO_AGENT_EVENTS_SECRET"],
        "CLOUDWALK_DEMO_PASSWORDS": values["DEMO_PASSWORDS"],
        "no_proxy": "127.0.0.1",
        "NO_PROXY": "127.0.0.1",
    }
    subprocess.run([
        sys.executable, "-B", str(ROOT / "script/check_f02.py"), "--api", f"http://{api}",
        "--project", args.project, "--channel-id", channel_id,
    ], cwd=ROOT, env=check_env, check=True)


def port(value):
    number = int(value)
    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError("use uma porta entre 1 e 65535")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="cloudwalk_demo", help="nome do projeto Compose da demo")
    parser.add_argument("--api-port", type=port, default=43109)
    parser.add_argument("--web-port", type=port, default=45179)
    parser.add_argument("--classifier", choices=("fixture", "disabled"), default="fixture")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("init", help="criar o arquivo privado de credenciais")
    commands.add_parser("config", help="validar a configuração sem exibir seu conteúdo")
    commands.add_parser("up", help="construir e iniciar a pilha completa")
    commands.add_parser("status", help="listar os serviços")
    commands.add_parser("down", help="encerrar a pilha preservando volumes")
    logs = commands.add_parser("logs", help="mostrar as últimas 80 linhas dos serviços")
    logs.add_argument("services", nargs="*")
    commands.add_parser("check", help="verificar dois turnos e reentrega criando um atendimento sintético")
    login = commands.add_parser("login", help="mostrar uma credencial sintética no terminal")
    login.add_argument("email", choices=EMAILS)
    args = parser.parse_args()
    if not re.fullmatch(r"cloudwalk_demo(?:_[a-z0-9]+)*", args.project):
        parser.error("use cloudwalk_demo ou um nome como cloudwalk_demo_apresentacao")
    if args.api_port == args.web_port:
        parser.error("escolha portas distintas para API e frontend")

    if args.action in {"init", "config", "up"}:
        try:
            create_env()
        except OSError:
            raise SystemExit("Não foi possível criar .env.demo.local neste checkout.") from None
    values = read_env()
    if args.action == "init":
        print("Credenciais sintéticas disponíveis em .env.demo.local.")
        return
    if args.action == "login":
        print(args.email)
        print(json.loads(values["DEMO_PASSWORDS"])[args.email])
        return

    compose = Compose(args)
    try:
        if args.action in {"config", "up"}:
            compose.run("config", "--quiet")
        if args.action == "up":
            compose.run("up", "--build", "--wait", "--wait-timeout", "180")
            print(f"Simulador: http://127.0.0.1:{args.web_port}")
            print(f"Operação:  http://127.0.0.1:{args.web_port}/analista")
        elif args.action == "status":
            compose.run("ps", "--all")
        elif args.action == "down":
            compose.run("down")
        elif args.action == "logs":
            compose.run("logs", "--tail", "80", "--", *args.services)
        elif args.action == "check":
            check_demo(args, compose, values)
    except FileNotFoundError:
        raise SystemExit("Instale Docker com o plugin Compose.") from None
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from None


if __name__ == "__main__":
    main()
