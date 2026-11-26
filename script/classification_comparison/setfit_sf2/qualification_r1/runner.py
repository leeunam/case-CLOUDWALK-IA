"""Supervisão serial de uma tentativa por entrada, com publicação indivisível por ID."""
import base64
import os
import signal
import subprocess
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path

from ..contracts.core import decode
from ..contracts.ipc import project
from ..evaluation.metrics import percentiles
from ..evaluation.runner import Frames, WorkerUsage, case_deadline, check_command, controls
from .storage import digest, encoded, publish, read, require, sync_directory

FILES = {"case": ("raw.jsonl", "decisions.jsonl"), "control": ("controls-raw.jsonl", "controls-r1.jsonl")}
HISTORICAL_COSTS = Path(__file__).parents[4] / "docs/evidencias/c05/sf2/qualificacao-01/execucao-02/avaliacao/costs.json"


def schedule(records):
    planned = [("case", r) for r in records] + [("control", r) for r in controls()]
    require(len({r["id"] for _, r in planned}) == len(planned), "ID repetido ou reservado")
    return planned


def resource(pid, usage):
    return dict(pid=pid, scope="process", peak_ram_bytes=usage.ram if usage else None,
                peak_cpu_percent=usage.cpu if usage else None)


@contextmanager
def record_interrupt():
    received = []
    previous = signal.signal(signal.SIGINT, lambda number, frame: received.append(number))
    try:
        yield received
    finally:
        signal.signal(signal.SIGINT, previous)


def materialize(root, units, planned):
    hashes, durations, attempted = {}, [], []
    with ExitStack() as stack:
        names = [name for pair in FILES.values() for name in pair] + ["timings.jsonl"]
        streams = {name: stack.enter_context((root / name).open("xb")) for name in names}
        for i, (kind, row) in enumerate(planned):
            path = units / f"{i:04d}.json"
            if not path.exists():
                break
            blob = read(path)
            unit = decode(blob)
            timing = unit["timing"]
            require((timing["kind"], timing["id"]) == (kind, row["id"]), "unidade fora da ordem")
            hashes[str(path.relative_to(root))] = digest(blob)
            streams["timings.jsonl"].write(encoded(timing))
            if kind == "case":
                durations.append(timing["elapsed_ms"])
            attempted.append(timing)
            if timing["valid"]:
                raw = base64.b64decode(unit["frame_base64"], validate=True)
                decision = unit["decision"]
                require(decision["raw_sha256"] == digest(raw) and decision["id"] == timing["id"],
                        "decisão sem vínculo com bruto/tempo")
                raw_name, decision_name = FILES[kind]
                streams[raw_name].write(raw)
                streams[decision_name].write(encoded(decision))
        for stream in streams.values():
            stream.flush()
            os.fsync(stream.fileno())
    for name in [*names, "stderr.log"]:
        hashes[name] = digest(read(root / name))
    return hashes, attempted, percentiles(durations)


def supervise(records, argv, context, destination, startup_seconds, *, derive, verify, catalog, timeout_ms=5000):
    return _supervise(records, argv, context, destination, startup_seconds, derive=derive, verify=verify,
                      catalog=catalog, timeout_ms=timeout_ms, cwd=None, environment=None)


def _supervise(records, argv, context, destination, startup_seconds, *, derive, verify, catalog,
               timeout_ms, cwd, environment, binding=None):
    check_command(argv)
    require(startup_seconds > 0 and 0 < timeout_ms <= 5000, "prazo inválido")
    planned = schedule(records)
    costs = decode(read(HISTORICAL_COSTS))
    root = Path(destination)
    root.mkdir()
    units = root / "observations"
    units.mkdir()
    process = worker = supervisor = transport = None
    failure = active = raw = startup_ms = None
    with (root / "stderr.log").open("xb") as stderr:
        try:
            supervisor = WorkerUsage(os.getpid())
            startup = time.monotonic()
            process = subprocess.Popen(argv, cwd=cwd, env=environment, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=stderr, start_new_session=True, bufsize=0)
            worker = WorkerUsage(process.pid)
            transport = Frames(process)
            require(decode(transport.line(startup + startup_seconds)) == {"type": "ready"}, "READY inválido")
            startup_ms = (time.monotonic() - startup) * 1000
            require(startup_ms <= startup_seconds * 1000, "startup excedeu o prazo")
            for i, (kind, row) in enumerate(planned):
                path = units / f"{i:04d}.json"
                raw = None
                start = time.monotonic()
                active = (kind, row["id"], start, path)
                deadline = start + timeout_ms / 1000
                with case_deadline(deadline - time.monotonic()):
                    item = project(row, catalog)
                    transport.send(item, deadline)
                    raw = transport.raw_line(deadline)
                    decision = derive(item, raw, context)
                    verify(item, raw, decision, context)
                    require(decision["id"] == row["id"] and decision["raw_sha256"] == digest(raw),
                            "ID ou hash bruto divergente")
                    elapsed = (time.monotonic() - start) * 1000
                    if elapsed > timeout_ms:
                        raise TimeoutError("verificação excedeu o prazo")
                timing = dict(kind=kind, id=row["id"], elapsed_ms=elapsed, valid=True)
                publish(path, encoded(dict(timing=timing, decision=decision,
                                           frame_base64=base64.b64encode(raw).decode("ascii"))))
                active = None
            transport.finish(time.monotonic() + timeout_ms / 1000)
        except (KeyboardInterrupt, Exception) as exc:
            failure = dict(type=type(exc).__name__, message=str(exc), attempt=None)
            if transport is not None and raw is None:
                try:
                    while chunk := os.read(process.stdout.fileno(), 65536):
                        transport.buffer.extend(chunk)
                        if len(transport.buffer) >= 1048576:
                            break
                except BlockingIOError:
                    pass
            if transport is not None and transport.buffer:
                failure["unexpected_stdout_base64"] = base64.b64encode(transport.buffer).decode()
            if active:
                kind, identifier, start, path = active
                if path.exists():
                    failure["attempt"] = decode(read(path))["timing"]
                else:
                    timing = dict(kind=kind, id=identifier, elapsed_ms=(time.monotonic()-start)*1000, valid=False)
                    diagnostic = raw if raw is not None else bytes(transport.buffer)
                    publish(path, encoded(dict(timing=timing, rejected_base64=base64.b64encode(diagnostic).decode())))
                    failure["attempt"] = timing
        finally:
            if process:
                if process.poll() is None or failure:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                process.wait()
                process.stdin.close()
                process.stdout.close()
            for usage in (worker, supervisor):
                if usage:
                    usage.stop()
            stderr.flush()
            os.fsync(stderr.fileno())
    with record_interrupt() as interrupted:
        files, journal, latency = materialize(root, units, planned)
    if interrupted and failure is None:
        failure = dict(type="KeyboardInterrupt", message="SIGINT durante materialização", attempt=None)
    seal = dict(contract_version="sf2-final-r1/1.0", reservation_sha256=binding, files=files, startup_ms=startup_ms, failure=failure,
                resources={"worker": resource(process.pid if process else None, worker),
                           "supervisor": resource(os.getpid(), supervisor)},
                case_latency_ms=latency, historical_capture_costs=costs,
                interrupted_ids=[t["id"] for t in journal if not t["valid"]],
                unstarted_ids=[row["id"] for _, row in planned[len(journal):]])
    publish(root / "seal.json", encoded(seal))
    sync_directory(root.parent)
    return seal

