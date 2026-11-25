"""Impõe prazos e registra interrupções fora dos processos do piloto."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time

from provision import CACHE, HERE, safe_environment, write_json

INSTALL_LIMIT = 30 * 60
TRAIN_LIMIT = 15 * 60
POLL_INTERVAL = 0.1


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class Interruption(Exception):
    def __init__(self, status, exit_code, message):
        super().__init__(message)
        self.status = status
        self.exit_code = exit_code


class Supervisor:
    cancelled_by = None

    def cancel(self, signum, _frame):
        self.cancelled_by = signum

    def wait_interval(self, deadline=None):
        if self.cancelled_by is not None:
            raise Interruption("cancelled", 128 + self.cancelled_by, "Execução cancelada por sinal")
        if deadline is None:
            return POLL_INTERVAL
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Interruption("timed_out", 124, "Prazo operacional excedido")
        return min(POLL_INTERVAL, remaining)

    @contextmanager
    def child(self, command, **options):
        process = subprocess.Popen(command, cwd=HERE, env=safe_environment(), start_new_session=True, **options)
        try:
            yield process
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
            raise

    def wait(self, process, deadline=None):
        while True:
            try:
                code = process.wait(timeout=self.wait_interval(deadline))
                self.wait_interval(deadline)
                return code if code >= 0 else 128 - code
            except subprocess.TimeoutExpired:
                continue


def installation_commands(progress):
    python = HERE / ".venv/bin/python"
    return (
        ("create_environment", [sys.executable, "-m", "venv", ".venv"]),
        ("install_dependencies", [
            python, "-m", "pip", "install", "--index-url", "https://pypi.org/simple",
            "--only-binary=:all:", "--timeout", "30", "--retries", "1", "-r", "requirements.txt",
        ]),
        ("verify_dependencies", [python, "-m", "pip", "check"]),
        ("verify_model", [sys.executable, "-B", HERE / "provision.py", "--progress", progress]),
    )


def execute_installation(supervisor, attempt, report):
    status_path = attempt / "status.json"
    progress = attempt / "model-progress.json"
    deadline = time.monotonic() + INSTALL_LIMIT
    with (CACHE / "install.lock").open("a", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise Interruption("failed", 1, "Já há uma instalação do piloto em andamento") from error
        with (attempt / "commands.log").open("w", encoding="utf-8") as log:
            for phase, command in installation_commands(progress):
                report["phase"] = phase
                write_json(status_path, report)
                log.write(f"\n[{phase}]\n")
                log.flush()
                supervisor.wait_interval(deadline)
                with supervisor.child(command, stdout=log, stderr=subprocess.STDOUT) as process:
                    code = supervisor.wait(process, deadline)
                if code:
                    raise Interruption("failed", code, "Comando da instalação falhou")


def install(supervisor):
    attempts = CACHE / "installs"
    attempts.mkdir(parents=True, exist_ok=True)
    attempt = Path(tempfile.mkdtemp(prefix="attempt-", dir=attempts))
    status_path = attempt / "status.json"
    report = {"task": "C05-SF1", "status": "running", "phase": "prepare", "started_at_utc": timestamp()}
    write_json(status_path, report)
    print(f"Registro de instalação em {attempt}", flush=True)
    code = 0
    try:
        execute_installation(supervisor, attempt, report)
        report["status"] = "complete"
    except (Interruption, OSError) as error:
        code = error.exit_code if isinstance(error, Interruption) else 1
        report["status"] = error.status if isinstance(error, Interruption) else "failed"
        report["message"] = str(error)
        print(report["message"], file=sys.stderr)
    finally:
        progress = attempt / "model-progress.json"
        if progress.exists():
            report.update(json.loads(progress.read_text()))
        report["exit_code"] = code
        report["finished_at_utc"] = timestamp()
        write_json(status_path, report)
    return code


def watch_training(supervisor, process, channel):
    remaining = TRAIN_LIMIT
    deadline = None
    while True:
        channel.settimeout(supervisor.wait_interval(deadline))
        try:
            event = channel.recv(1)
        except TimeoutError:
            continue
        if not event:
            code = supervisor.wait(process, deadline)
            if deadline is not None and code == 0:
                raise Interruption("failed", 1, "Treino encerrou sem confirmar o fim da etapa")
            return code
        if event == b"S" and deadline is None:
            deadline = time.monotonic() + remaining
            supervisor.wait_interval(deadline)
            channel.sendall(b"K")
        elif event == b"E" and deadline is not None:
            supervisor.wait_interval(deadline)
            remaining = deadline - time.monotonic()
            deadline = None
        else:
            raise Interruption("failed", 1, "Evento de treino inesperado")


def train(supervisor, output):
    output = output.resolve()
    output.mkdir(parents=True)
    status_path = output / "run.json"
    started = time.monotonic()
    initial_report = {"task": "C05-SF1", "status": "running", "started_at_utc": timestamp(), "folds": []}
    write_json(status_path, initial_report)
    interruption = None
    try:
        parent, child = socket.socketpair()
        with parent, child:
            command = [HERE / ".venv/bin/python", "-B", HERE / "run.py", "--output", output,
                       "--control-fd", str(child.fileno())]
            supervisor.wait_interval()
            with supervisor.child(command, pass_fds=(child.fileno(),)) as process:
                child.close()
                code = watch_training(supervisor, process, parent)
        if code:
            interruption = Interruption("failed", code, "Processo do piloto encerrou com erro")
    except (Interruption, OSError) as error:
        interruption = error if isinstance(error, Interruption) else Interruption("failed", 1, str(error))

    report = json.loads(status_path.read_text())
    if interruption is None and report["status"] == "complete":
        return 0
    if interruption is None:
        interruption = Interruption("failed", 1, "Processo do piloto encerrou sem registrar conclusão")
    report["status"] = "interrupted"
    report.setdefault("interruption", {"message": str(interruption)})
    report["interruption"].update(kind=interruption.status, exit_code=interruption.exit_code)
    if "active_fold" in report and report["folds"][-1]["status"] != "complete":
        fold = report["folds"][-1]
        fold["interrupted_during"] = fold["status"]
        fold["status"] = "interrupted"
    report.setdefault("finished_at_utc", timestamp())
    report.setdefault("elapsed_seconds", time.monotonic() - started)
    write_json(status_path, report)
    print(str(interruption), file=sys.stderr)
    return interruption.exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("install")
    trainer = commands.add_parser("train")
    trainer.add_argument("--output", type=Path, required=True, help="Novo diretório de evidências")
    args = parser.parse_args()
    supervisor = Supervisor()
    signal.signal(signal.SIGINT, supervisor.cancel)
    signal.signal(signal.SIGTERM, supervisor.cancel)
    sys.exit(install(supervisor) if args.command == "install" else train(supervisor, args.output))


if __name__ == "__main__":
    main()
