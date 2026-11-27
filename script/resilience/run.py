"""Executa a F07-A em um projeto Compose novo e escreve um relatório JSON."""

import argparse
import datetime
import fcntl
import json
import os
import secrets
import selectors
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT = "cloudwalk_f07_a"
BASE = "2b17a2f45753e39825b8316c31781f0be51f2c25"
CATALOG = json.loads(Path(__file__).with_name("catalog.json").read_text())
ROOT = Path(__file__).resolve().parents[2]
COMPOSE = [
    "docker", "compose", "--project-name", PROJECT, "--env-file", "script/resilience/stack.env",
    "-f", "compose.yml", "-f", "script/resilience/compose.yml",
]
CONTROLLED_SERVICES = {"kafka", "outbox", "events"}


class StackUnavailable(RuntimeError):
    pass


def environment():
    env = os.environ.copy()
    env.update({
        "POSTGRES_USER": "f07_probe",
        "POSTGRES_PASSWORD": secrets.token_hex(24),
        "F07_RAILS_SECRET": secrets.token_hex(64),
        "CLOUDWALK_CHANNEL_SECRET": secrets.token_hex(32),
        "CLOUDWALK_AGENT_REQUESTS_SECRET": secrets.token_hex(32),
        "CLOUDWALK_AGENT_EVENTS_SECRET": secrets.token_hex(32),
        "CLOUDWALK_DEMO_PASSWORDS": json.dumps({
            f"{name}@example.test": secrets.token_hex(24) for name in ("alex", "bia", "cris", "supervisor")
        }, separators=(",", ":")),
        "KAFKA_RETENTION_MS": "604800000",
        "COMPOSE_PROFILES": "",
        "COMPOSE_MENU": "false",
        "COMPOSE_PROGRESS": "plain",
    })
    return env


def invoke(args, env, label, timeout=120, *, capture=False):
    try:
        process = subprocess.run(args, cwd=ROOT, env=env, text=True, timeout=timeout,
                                 stdout=subprocess.PIPE if capture else sys.stderr, stderr=sys.stderr)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise StackUnavailable(f"{label}: {type(error).__name__}") from error
    if process.returncode:
        raise StackUnavailable(f"{label}: código {process.returncode}; confira stderr")
    return process.stdout


def require_fresh(env):
    checks = [
        COMPOSE + ["ps", "-a", "-q"],
        ["docker", "volume", "ls", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}"],
        ["docker", "network", "ls", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}"],
    ]
    for args in checks:
        if invoke(args, env, "verificação de isolamento", capture=True).strip():
            raise StackUnavailable(f"há recursos de {PROJECT}; o ensaio exige um projeto vazio")


def control(message, env):
    action = message["action"]
    service = message.get("service")
    if ((action in {"stop", "start", "state"} and service in CONTROLLED_SERVICES)
            or (action == "state" and service == "worker")):
        if action == "state":
            rows = invoke(COMPOSE + ["ps", "-a", "--format", "json", service], env,
                          "estado do serviço", capture=True)
            if not rows.strip():
                raise StackUnavailable(f"serviço ausente: {service}")
            if rows.lstrip().startswith("["):
                row, = json.loads(rows)
            else:
                row = json.loads(rows)
            return {key: row.get(key) for key in ("State", "ExitCode")}
        args = ["stop", "-t", "2", service] if action == "stop" else ["start", service]
        invoke(COMPOSE + args, env, f"{action} {service}")
        return None
    if action == "failure_limit" and type(message.get("enabled")) is bool:
        modify = ["--add-config", "max.message.bytes=1"] if message["enabled"] else [
            "--delete-config", "max.message.bytes",
        ]
        invoke(COMPOSE + ["exec", "-T", "kafka", "/opt/kafka/bin/kafka-configs.sh",
                          "--bootstrap-server", "kafka:9092", "--entity-type", "topics",
                          "--entity-name", "agent.failures", "--alter", *modify],
               env, "alteração temporária de agent.failures")
        return None
    if action == "frontend":
        plan = json.dumps(message["plan"], separators=(",", ":"))
        output = invoke(COMPOSE + ["exec", "-T", "web", "node", "--experimental-strip-types",
                                   "/f07/frontend.mjs", plan],
                        env, "cliente real do simulador", timeout=60, capture=True)
        return json.loads(output)
    raise StackUnavailable("operação de controle desconhecida")


def protocol_lines(stream, *, lifetime, idle=240):
    end = time.monotonic() + lifetime
    last_line = time.monotonic()
    pending = bytearray()
    with selectors.DefaultSelector() as selector:
        selector.register(stream, selectors.EVENT_READ)
        while True:
            remaining = min(end, last_line + idle) - time.monotonic()
            if remaining <= 0 or not selector.select(remaining):
                raise StackUnavailable("Prazo de execução ou inatividade do verificador esgotado")
            part = os.read(stream.fileno(), 65536)
            if not part:
                if pending:
                    raise StackUnavailable("Verificador encerrou com mensagem incompleta")
                return
            pending.extend(part)
            while b"\n" in pending:
                line, _, pending = pending.partition(b"\n")
                if line.strip():
                    if len(line) > 2_000_000:
                        raise StackUnavailable("Mensagem extensa demais no protocolo do verificador")
                    yield line
                    last_line = time.monotonic()
            if len(pending) > 2_000_000:
                raise StackUnavailable("Mensagem extensa demais no protocolo do verificador")


def stop_probe(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def probe(scenarios, report, env):
    args = COMPOSE + ["run", "--no-deps", "--rm", "-T", "-i", "probe",
                      "python", "-B", "/f07/scenarios.py", *scenarios]
    process = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr)
    try:
        for line in protocol_lines(process.stdout, lifetime=300 + 600 * len(scenarios)):
            message = json.loads(line)
            if "action" in message:
                try:
                    response = {"ok": True, "result": control(message, env)}
                except (StackUnavailable, ValueError) as error:
                    response = {"ok": False, "reason": str(error)}
                process.stdin.write(json.dumps(response).encode() + b"\n")
                process.stdin.flush()
            elif "result" in message:
                result = message["result"]
                report["scenarios"][result["id"]] = result
                print(f"{result['id']} {result['status']}: {result['reason']}", file=sys.stderr)
            else:
                raise StackUnavailable("mensagem inesperada do verificador")
        if process.wait(timeout=15):
            raise StackUnavailable("processo de verificação terminou com erro; confira stderr")
    finally:
        try:
            stop_probe(process)
        finally:
            process.stdin.close()
            process.stdout.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", action="append", choices=tuple(CATALOG), help="executa somente os IDs informados")
    parser.add_argument("--check-config", action="store_true", help="valida somente a composição, sem Docker daemon")
    args = parser.parse_args()
    env = environment()
    if args.check_config:
        try:
            invoke(COMPOSE + ["config", "-q"], env, "validação Compose")
        except StackUnavailable as error:
            print(error, file=sys.stderr)
            return 2
        return 0

    scenarios = sorted(set(args.scenario or CATALOG))
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True)
    report = {
        "task": "F07-A", "base": BASE, "revision": revision.stdout.strip() or None, "project": PROJECT,
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "scenarios": {},
    }
    blocker = "nenhum resultado devolvido pelo verificador"
    owns_stack = False
    # O descritor é liberado pelo SO se o runner for interrompido.
    lock = None
    try:
        lock_root = Path(tempfile.gettempdir())
        lock = (lock_root / f"{PROJECT}-{os.getuid()}.lock").open("a")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise StackUnavailable(f"outro runner mantém o bloqueio de {PROJECT}") from error
        invoke(["docker", "info", "--format", "{{.ServerVersion}}"], env, "daemon Docker indisponível", capture=True)
        invoke(COMPOSE + ["config", "-q"], env, "validação Compose")
        require_fresh(env)
        owns_stack = True
        invoke(COMPOSE + ["up", "-d", "--build", "api", "writer", "worker", "requests", "events",
                          "mock", "outbox", "fault", "web"],
               env, "criação da pilha F07-A", timeout=900)
        invoke(COMPOSE + ["build", "probe"], env, "imagem do verificador", timeout=900)
        probe(scenarios, report, env)
    except (StackUnavailable, OSError, ValueError, subprocess.SubprocessError) as error:
        blocker = str(error)
        report["runner_error"] = blocker
    except KeyboardInterrupt:
        blocker = "execução interrompida"
        report["runner_error"] = blocker
    finally:
        if owns_stack:
            try:
                invoke(COMPOSE + ["down", "--volumes", "--remove-orphans"], env, "remoção da pilha F07-A")
            except StackUnavailable as error:
                report["cleanup_error"] = str(error)
        if lock is not None:
            lock.close()

    report["scenarios"] = {
        item: report["scenarios"].get(item, {
            **CATALOG[item], "status": "bloqueado", "reason": blocker, "evidence": {},
        }) for item in scenarios
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    statuses = {item["status"] for item in report["scenarios"].values()}
    if "reprovado" in statuses:
        return 1
    return 2 if "bloqueado" in statuses or "cleanup_error" in report or "runner_error" in report else 0


if __name__ == "__main__":
    sys.exit(main())
