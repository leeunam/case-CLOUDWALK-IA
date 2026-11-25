"""Uma execução local serial. Cada arquivo de evidência é criado exclusivamente."""
import json
import os
import select
import signal
import subprocess
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from ..contracts.core import CATALOG, PROTOCOL, VERSION, decode, require, sha256
from ..contracts.ipc import project, validate_decision

TIMEOUT_MS = PROTOCOL["execution"]["timeout_ms_per_case"]


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode()


def append(stream, value):
    stream.write(encoded(value))
    stream.flush()


def finish_append(stream, offset, payload):
    """Só acrescenta bytes faltantes de uma observação já medida, mesmo após SIGINT."""
    stream.seek(offset)
    prefix = stream.read()
    require(payload.startswith(prefix), "bytes inesperados na tentativa interrompida")
    remaining = memoryview(payload)[len(prefix):]
    while remaining:
        remaining = remaining[stream.write(remaining):]


def save(path, value):
    with Path(path).open("xb") as stream:
        append(stream, value)


def check_command(argv):
    require(isinstance(argv, list) and argv and all(isinstance(arg, str) and arg and "\0" not in arg for arg in argv),
            "comando exige argv não vazio, sem shell")
    return argv


def controls():
    # Mesma ordem e IDs no executor e no auditor. São observações adicionais após as narrativas.
    examples = {"complete": {"category": "pix", "priority": "basic"}, "invalid": {"priority": 3},
                "blank-category": {"category": " ", "priority": "basic"},
                "null-priority": {"category": "pix", "priority": None}, "omitted-both": {}}
    return [dict(id="sf2-control-" + name, text="Fixture de controle SF2 para o adaptador.", received=received)
            for name, received in examples.items()]


@contextmanager
def case_deadline(seconds):
    """O prazo inclui o processamento local do frame, além das esperas nos pipes."""
    def expire(signum, frame):
        raise TimeoutError("prazo externo do caso excedido")

    previous = signal.getsignal(signal.SIGALRM)
    require(signal.getitimer(signal.ITIMER_REAL) == (0, 0), "executor requer timer POSIX exclusivo")
    signal.signal(signal.SIGALRM, expire)
    try:
        signal.setitimer(signal.ITIMER_REAL, max(seconds, 1e-6))
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


class WorkerUsage:
    """Linux: RSS máxima do processo e maior uso de CPU observado em intervalos."""
    def __init__(self, pid):
        self.directory = Path("/proc") / str(pid)
        self.ram = self.cpu = None
        self.finished = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)
        self.thread.start()

    def sample(self):
        previous = None
        ticks = os.sysconf("SC_CLK_TCK")
        while True:
            try:
                for line in (self.directory / "status").read_text().splitlines():
                    if line.startswith("VmHWM:"):
                        self.ram = max(self.ram or 0, int(line.split()[1])*1024)
                        break
                fields = (self.directory / "stat").read_text().rsplit(")", 1)[1].split()
                now, cpu = time.monotonic(), (int(fields[11]) + int(fields[12])) / ticks
                if previous:
                    percent = 100 * (cpu-previous[1]) / (now-previous[0])
                    self.cpu = max(self.cpu or 0, percent)
                previous = now, cpu
            except (OSError, ValueError, IndexError):
                return
            if self.finished.wait(.05):
                return

    def stop(self):
        self.finished.set()
        self.thread.join()


class PrematureOutput(ValueError):
    """O worker já escreveu bytes antes de receber uma entrada completa."""


class Frames:
    def __init__(self, process):
        self.process = process
        self.buffer = bytearray()
        for stream in (process.stdin, process.stdout):
            os.set_blocking(stream.fileno(), False)

    def _ready(self, read, write, deadline):
        remaining = deadline - time.monotonic()
        ready = select.select(read, write, [], max(0, remaining))[:2]
        if remaining <= 0 or not any(ready):
            raise TimeoutError("prazo de transporte excedido")
        return ready

    def send(self, item, deadline):
        data = memoryview(encoded(item))
        while data:
            if self.buffer:
                raise PrematureOutput("stdout disponível antes do envio da entrada completa")
            readable, _ = self._ready([self.process.stdout], [self.process.stdin], deadline)
            if readable:
                prefix = os.read(self.process.stdout.fileno(), 1)
                raise PrematureOutput("stdout antecipado" if prefix else "EOF antes de enviar a próxima entrada")
            data = data[os.write(self.process.stdin.fileno(), data):]

    def line(self, deadline):
        while b"\n" not in self.buffer:
            self._ready([self.process.stdout], [], deadline)
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise EOFError("EOF antes do frame esperado")
            self.buffer.extend(chunk)
        line, _, rest = self.buffer.partition(b"\n")
        self.buffer = bytearray(rest)
        return line.decode("utf-8")

    def finish(self, deadline):
        self.process.stdin.close()
        require(not self.buffer, "stdout adicional após a última decisão")
        self._ready([self.process.stdout], [], deadline)
        require(not os.read(self.process.stdout.fileno(), 1), "stdout adicional após a última decisão")
        require(self.process.wait(timeout=max(0, deadline-time.monotonic())) == 0, "worker saiu com falha")


def supervise(records, argv, policy, model, identities, destination, startup_seconds, *, catalog=CATALOG, timeout_ms=TIMEOUT_MS):
    check_command(argv)
    require(startup_seconds > 0, "prazo de startup inválido")
    root = Path(destination)
    root.mkdir()
    check_ids = {r["id"] for r in controls()}
    require(not any(r["id"] in check_ids for r in records), "ID de narrativa reservado a controle")
    process, usage, failure, current = None, None, None, None
    startup_ms = None
    files = ("predictions.jsonl", "controls.jsonl", "timings.jsonl", "stderr.log")
    with (root/files[0]).open("x+b", buffering=0) as predictions, (root/files[1]).open("x+b", buffering=0) as control_log, \
         (root/files[2]).open("x+b", buffering=0) as timings, (root/files[3]).open("xb") as stderr:
        started = time.monotonic()
        try:
            process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                                       start_new_session=True, bufsize=0)
            usage = WorkerUsage(process.pid)
            transport = Frames(process)
            require(decode(transport.line(started + startup_seconds)) == {"type": "ready"}, "frame ready inválido")
            startup_ms = (time.monotonic()-started)*1000
            for kind, batch, sink in (("case", records, predictions), ("control", controls(), control_log)):
                for row in batch:
                    start = time.monotonic()
                    deadline = start + timeout_ms/1000
                    pending = None
                    current = {"kind": kind, "id": row["id"]}
                    with case_deadline(deadline-time.monotonic()):
                        item = project(row, catalog)
                        transport.send(item, deadline)
                        line = transport.line(deadline)
                        # Conservar o frame reprovado para inspeção, sem corrigi-lo.
                        current["response"] = line
                        decision = decode(line)
                        validate_decision(item, decision, policy, model["class_order"], identities)
                    elapsed = (time.monotonic()-start)*1000
                    if elapsed > timeout_ms:
                        raise TimeoutError("validação ultrapassou o prazo do caso")
                    timing = dict(kind=kind, id=row["id"], elapsed_ms=elapsed, valid=True)
                    pending = ((sink, sink.tell(), (line + "\n").encode()), (timings, timings.tell(), encoded(timing)))
                    for write in pending:
                        finish_append(*write)
                    current = None
            transport.finish(time.monotonic() + timeout_ms/1000)
        except (OSError, EOFError, ValueError, RecursionError, KeyboardInterrupt, subprocess.TimeoutExpired) as exc:
            if isinstance(exc, PrematureOutput):
                current = None
            failure = dict(type=type(exc).__name__, message=str(exc), attempt=current)
            if current is not None:
                if pending is not None:
                    for write in pending:
                        finish_append(*write)
                else:
                    append(timings, dict(kind=current["kind"], id=current["id"],
                                         elapsed_ms=(time.monotonic()-start)*1000, valid=False))
        finally:
            if usage:
                usage.stop()
            if process:
                if process.poll() is None or failure:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                process.wait()
                process.stdin.close()
                process.stdout.close()
    seal = dict(contract_version=VERSION, startup_ms=startup_ms, failure=failure,
                peak_ram_bytes=usage.ram if usage else None, peak_cpu_percent=usage.cpu if usage else None,
                files={name: sha256(root/name) for name in files})
    save(root/"seal.json", seal)
    return seal
