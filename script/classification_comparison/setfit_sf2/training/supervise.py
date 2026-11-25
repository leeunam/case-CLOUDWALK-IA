"""Supervisão POSIX externa ao processo de instalação/treino."""

from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
from time import monotonic

ROOT = Path(__file__).resolve().parents[4]
SF2 = Path(__file__).resolve().parents[1]
MODULE = "script.classification_comparison.setfit_sf2.training"
LIMITS = ROOT / "docs/planejamento/classificacao-comparativa/sf2/protocolo.json"
POLL = 0.1
CANCEL_SIGNALS = (signal.SIGINT, signal.SIGTERM)


def now():
    return datetime.now(timezone.utc).isoformat()


def budget(key):
    return json.loads(LIMITS.read_text(encoding="utf-8"))["training"][key]


class Interrupted(RuntimeError):
    def __init__(self, kind, code, message):
        super().__init__(message)
        self.kind = kind
        self.code = code


class Supervisor:
    def __init__(self):
        self.cancelled_by = None

    def cancel(self, signum, _frame):
        if self.cancelled_by is None:
            self.cancelled_by = signum

    def commit(self, prepared, receipt):
        previous = signal.pthread_sigmask(signal.SIG_BLOCK, CANCEL_SIGNALS)
        try:
            # Depois desta consulta, os sinais da seção protegida são posteriores ao compromisso.
            pending = signal.sigpending().intersection(CANCEL_SIGNALS)
            if pending:
                self.cancel(min(pending), None)
            self.wait_time()
            prepared.replace(receipt)
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous)

    def wait_time(self, deadline=None):
        if self.cancelled_by:
            raise Interrupted("cancelled", 128 + self.cancelled_by, "Processo cancelado por sinal")
        if deadline is None:
            return POLL
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise Interrupted("timed_out", 124, "Prazo aprovado excedido")
        return min(POLL, remaining)

    def wait(self, process, deadline=None):
        while True:
            try:
                code = process.wait(timeout=self.wait_time(deadline))
                self.wait_time(deadline)
                return code
            except subprocess.TimeoutExpired:
                continue

    @contextmanager
    def child(self, argv, **kwargs):
        env = {
            name: value for name, value in os.environ.items()
            if not name.startswith(("PIP_", "PYTHON")) and name not in
            {"HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "FEITA_API_KEY", "TYPESAFE_API_KEY"}
        }
        env.update(PIP_CONFIG_FILE=os.devnull, HF_HUB_DISABLE_IMPLICIT_TOKEN="1", HF_HUB_DISABLE_TELEMETRY="1")
        self.wait_time()
        process = subprocess.Popen(argv, cwd=ROOT, env=env, start_new_session=True, **kwargs)
        try:
            yield process
        except BaseException:
            # Mata também subprocessos do instalador/Trainer após cancelamento ou timeout.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise


def successful(code, phase):
    if code:
        raise Interrupted("failed", code if code > 0 else 128 - code, f"Falha em {phase}")


def watch_training(supervisor, process, parent, limit, expected_stages):
    remaining = limit
    deadline = None
    finished = 0
    while True:
        parent.settimeout(supervisor.wait_time(deadline))
        try:
            event = parent.recv(1)
        except TimeoutError:
            continue
        if event == b"S" and deadline is None and finished < expected_stages:
            deadline = monotonic() + remaining
            parent.settimeout(supervisor.wait_time(deadline))
            parent.sendall(b"K")
        elif event == b"E" and deadline is not None:
            supervisor.wait_time(deadline)
            remaining = deadline - monotonic()
            finished += 1
            deadline = None
        elif not event:
            code = supervisor.wait(process, deadline)
            successful(code, "treino")
            if deadline is not None or finished != expected_stages:
                raise Interrupted("failed", 1, "Treino sem confirmação dos dois ajustes")
            return limit - remaining
        else:
            raise Interrupted("failed", 1, "Evento de supervisão inesperado")


def remove_artifact(path):
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def supervise_run(output, operation, *, artifacts=()):
    output.mkdir(parents=True)
    supervisor = Supervisor()
    handlers = {signum: signal.signal(signum, supervisor.cancel) for signum in CANCEL_SIGNALS}
    initial = {"task": "SF2-03", "started_at_utc": now()}
    path = output / "status.json"
    staging = output / "staging"

    def prepare_report(status, **details):
        temp = output / "status.tmp"
        report = {**initial, "status": status, **details}
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return temp

    try:
        prepare_report("running").replace(path)
        with ExitStack() as rollback:
            if artifacts:
                rollback.callback(remove_artifact, staging)
            with (output / "commands.log").open("w", encoding="utf-8") as log:
                details = operation(supervisor, log)
            # A elegibilidade só é publicada junto ao recibo complete.
            for name in artifacts:
                supervisor.wait_time()
                destination = output / name
                rollback.callback(remove_artifact, destination)
                (staging / name).replace(destination)
            if artifacts:
                remove_artifact(staging)
            complete = prepare_report("complete", finished_at_utc=now(), exit_code=0, **details)
            supervisor.commit(complete, path)
            rollback.pop_all()
    except BaseException as error:
        try:
            supervisor.wait_time()
        except Interrupted as cancellation:
            error = cancellation
        status = error.kind if isinstance(error, Interrupted) else "failed"
        code = error.code if isinstance(error, Interrupted) else 1
        handled = isinstance(error, (Interrupted, OSError, ValueError))
        message = str(error) if handled else f"{type(error).__name__}: {error}"
        prepare_report(status, finished_at_utc=now(), exit_code=code, message=message).replace(path)
        if not handled:
            raise
        print(message, file=sys.stderr)
        return code
    finally:
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
    return 0


def install(snapshot, output):
    snapshot, output = snapshot.resolve(), output.resolve()
    venv = output / ".venv"
    executable = venv / "bin/python"
    recipe = json.loads(LIMITS.read_text(encoding="utf-8"))
    for kind in ("requirements", "model_lock"):
        source = recipe["sources"][kind]
        if hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Fonte aprovada divergente: {kind}")

    def operation(supervisor, log):
        deadline = monotonic() + budget("provision_limit_seconds")
        commands = [
            ("venv", [sys.executable, "-m", "venv", venv]),
            ("pins", [executable, "-m", "pip", "--isolated", "--disable-pip-version-check",
                      "--no-cache-dir", "install", "--index-url", "https://pypi.org/simple",
                      "--only-binary=:all:", "--timeout", "30", "--retries", "1",
                      "-r", SF2 / "training/requirements.txt"]),
            ("pip check", [executable, "-m", "pip", "check"]),
            ("snapshot e imports", [executable, "-B", "-m", MODULE, "check", "--snapshot", snapshot,
                                   "--copy-to", output / "model", "--output", output / "environment.json"]),
        ]
        for name, command in commands:
            log.write(f"[{name}]\n")
            log.flush()
            supervisor.wait_time(deadline)
            with supervisor.child(command, stdout=log, stderr=subprocess.STDOUT) as process:
                successful(supervisor.wait(process, deadline), name)
        return {"environment": str(venv), "snapshot": str(output / "model")}

    return supervise_run(output, operation)


def train(output, worker_args):
    output = output.resolve()
    limit = budget("aggregate_training_limit_seconds")

    def operation(supervisor, log):
        staging = output / "staging"
        staging.mkdir()
        parent, child = socket.socketpair()
        with parent, child:
            argv = [sys.executable, "-B", "-m", MODULE, "run-worker", *worker_args,
                    "--staging", staging, "--control-fd", str(child.fileno())]
            with supervisor.child(argv, pass_fds=(child.fileno(),), stdout=log,
                                  stderr=subprocess.STDOUT) as process:
                child.close()
                seconds = watch_training(supervisor, process, parent, limit, expected_stages=2)
        supervisor.wait_time()
        manifest = staging / "package/manifest.json"
        receipt = json.loads((staging / "evidence.json").read_text(encoding="utf-8"))
        package_digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        if receipt["package_sha256"] != package_digest:
            raise ValueError("Manifesto produzido difere do recibo de reload")
        return {"package_sha256": package_digest, "training_seconds": seconds}

    return supervise_run(output, operation, artifacts=("evidence.json", "package"))
