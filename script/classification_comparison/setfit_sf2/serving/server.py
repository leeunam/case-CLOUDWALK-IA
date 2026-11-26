"""HTTP privado. A thread principal possui a sessão e o prazo POSIX."""
from collections import Counter
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from threading import Condition, Event, Thread
from time import monotonic

from .session import Expired, LIMIT, Session, refusal, until

COMPLETE = "/internal/classification/v1/complete"


@dataclass
class Call:
    body: bytes
    started: float = field(default_factory=monotonic)
    done: Event = field(default_factory=Event)
    result: tuple | None = None


class Supervisor:
    def __init__(self, load, *, process_seconds=5, boot_seconds=60):
        self.load = load
        self.process_seconds = process_seconds
        self.boot_seconds = boot_seconds
        self.condition = Condition()
        self.ready = False
        self.active = None
        self.worker_pid = None
        self.counters = Counter()

    def _slot_refusal(self):
        if not self.ready:
            reason = "not_ready"
        elif self.active is not None:
            reason = "busy"
        else:
            return None
        self.counters[reason] += 1
        return refusal(503, reason)

    def preflight(self):
        with self.condition:
            return self._slot_refusal()

    def submit(self, body):
        with self.condition:
            if blocked := self._slot_refusal():
                return blocked
            self.active = call = Call(body)
            self.condition.notify()
        call.done.wait()
        return call.result

    def health(self):
        with self.condition:
            return {"ready": self.ready, "worker_pid": self.worker_pid, "counts": dict(self.counters)}

    def run(self):
        attempts = 0
        while attempts < 2:
            attempts += 1
            session = None
            phase = "bootstrap"
            try:
                started = monotonic()
                with until(started + self.boot_seconds):
                    session = Session(self.load())
                    phase = "worker_start"
                    session.start()
                with self.condition:
                    self.worker_pid = session.child.pid
                    self.ready = True
                    self.counters["starts"] += 1
                print(json.dumps({"event": "ready", "pid": session.child.pid,
                                  "startup_ms": round(1000 * (monotonic() - started))}), flush=True)
                phase = "serving"
                while True:
                    with self.condition:
                        self.condition.wait_for(lambda: self.active is not None, timeout=0.05)
                        call = self.active
                    if call is None:
                        if session.has_output():
                            raise ValueError("sessão interrompida")
                        continue
                    invalid = False
                    before = session.writes
                    try:
                        with until(call.started + self.process_seconds):
                            result = session.complete(call.body, call.started)
                    except Expired:
                        result, invalid = refusal(504, "processing_timeout"), True
                    except (EOFError, OSError):
                        result, invalid = refusal(502, "worker_failure"), True
                    except (ValueError, RecursionError):
                        result, invalid = refusal(502, "invalid_worker_frame"), True
                    except Exception:
                        result, invalid = refusal(502, "worker_failure"), True
                    with self.condition:
                        self.counters["pipe_writes"] += session.writes - before
                        self.counters[result[1].get("error", "verified")] += 1
                        self.ready = not invalid
                        self.active = None
                        call.result = result
                        call.done.set()
                    if invalid:
                        break
                    if result[0] == 200:
                        attempts = 1
                        response = result[1]
                        print(json.dumps({"event": "verified", "id": response["id"], "pid": session.child.pid,
                                          "worker_elapsed_ms": session.worker_elapsed_ms,
                                          "elapsed_ms": response["elapsed_ms"]}), flush=True)
            except (Expired, Exception) as error:
                with self.condition:
                    self.counters["session_failures"] += 1
                print(json.dumps({"event": "session_failure", "phase": phase,
                                  "timeout": isinstance(error, Expired)}), flush=True)
            finally:
                with self.condition:
                    self.ready = False
                    self.worker_pid = None
                    if self.active is not None:
                        self.active.result = refusal(502, "worker_failure")
                        self.active.done.set()
                        self.active = None
                if session is not None:
                    session.close()
        # Uma nova partida após duas sessões falhas requer reinício pelo operador.
        Event().wait()


class Handler(BaseHTTPRequestHandler):
    timeout = 6

    def log_message(self, *args):
        pass

    def reply(self, status, obj):
        data = json.dumps(obj, allow_nan=False, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        state = self.server.supervisor.health()
        if self.path == "/live":
            self.reply(200, {"live": True})
        elif self.path == "/ready":
            self.reply(200 if state["ready"] else 503, state)
        else:
            self.reply(404, {})

    def do_POST(self):
        if self.path != COMPLETE:
            self.reply(404, {})
            return
        sizes = self.headers.get_all("Content-Length", [])
        types = self.headers.get_all("Content-Type", [])
        if (len(sizes) != 1 or not re.fullmatch(r"[0-9]{1,5}", sizes[0]) or int(sizes[0]) > LIMIT
                or "Transfer-Encoding" in self.headers or len(types) != 1
                or self.headers.get_content_type() != "application/json"
                or self.headers.get_content_charset("utf-8") != "utf-8"):
            self.reply(*refusal(422, "invalid_request"))
            return
        size = int(sizes[0])
        if blocked := self.server.supervisor.preflight():
            self.reply(*blocked)
            return
        body = self.rfile.read(size)
        if len(body) != size:
            self.reply(*refusal(422, "invalid_request"))
            return
        self.reply(*self.server.supervisor.submit(body))


class Server(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # Um cliente desconectado não invalida a sessão de inferência.
        pass


def serve(address, supervisor):
    with Server(address, Handler) as server:
        server.supervisor = supervisor
        Thread(target=server.serve_forever, daemon=True).start()
        try:
            supervisor.run()
        finally:
            server.shutdown()
