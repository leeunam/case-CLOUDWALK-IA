"""Único dono do subprocesso e dos pipes JSONL da sessão."""
import os
import select
import signal
import subprocess
from contextlib import contextmanager
from time import monotonic

LIMIT = 65_536
VERSION = "classification-http/1.0"


class Expired(BaseException):
    """Interrompe também a verificação Python e as operações bloqueantes do pipe."""


@contextmanager
def until(deadline):
    def expire(*_):
        raise Expired()

    remaining = deadline - monotonic()
    if remaining <= 0:
        raise Expired()
    previous = signal.signal(signal.SIGALRM, expire)
    try:
        signal.setitimer(signal.ITIMER_REAL, remaining)
        yield
        if monotonic() >= deadline:
            raise Expired()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def refusal(status, reason):
    return status, {"contract_version": VERSION, "error": reason}


class Session:
    def __init__(self, settings):
        self.command, self.validator, self.context, self.token_length = settings
        self.child = None
        self.writes = 0
        self.worker_elapsed_ms = None

    def start(self):
        self.child = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, bufsize=0, start_new_session=True)
        if self.frame() != b'{"type":"ready"}\n' or self.has_output():
            raise ValueError("READY divergente")

    def close(self):
        if self.child is not None:
            try:
                os.killpg(self.child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.child.wait()
            self.child.stdin.close()
            self.child.stdout.close()
            self.child = None

    def has_output(self):
        return bool(select.select([self.child.stdout], [], [], 0)[0])

    def frame(self):
        data = bytearray()
        while len(data) < LIMIT:
            chunk = os.read(self.child.stdout.fileno(), LIMIT - len(data))
            if not chunk:
                if data:
                    raise ValueError("frame incompleto")
                raise EOFError()
            data.extend(chunk)
            if b"\n" in chunk:
                if data[-1] != 10 or data.count(10) != 1:
                    raise ValueError("saída fora do frame")
                return bytes(data)
        raise ValueError("frame excessivo")

    def complete(self, body, started):
        from ..contracts import ipc
        from ..contracts.core import decode
        from ..runtime_r1 import derive, verify
        from ..runtime_r1.context import digest, encoded

        try:
            request = decode(body.decode("utf-8"))
            if not self.validator.is_valid(request) or type(request["catalog_version"]) is not int:
                return refusal(422, "invalid_request")
            catalog = {"version": "1.0.0", **request["catalog"]}
            item = ipc.project(request, catalog)
            missing, invalid, _, known = ipc.validate_input(item)
            wire = encoded(item) + b"\n"
            if invalid or not missing:
                return refusal(422, "invalid_request")
            if not known:
                return refusal(422, "unsupported_catalog")
        except (ValueError, RecursionError, TypeError):
            return refusal(422, "invalid_request")
        if self.token_length(item["text"], missing) > 128:
            return refusal(422, "text_out_of_scope")
        if self.has_output():
            raise ValueError("saída inesperada antes da escrita")
        self.writes += 1
        pending = memoryview(wire)
        while pending:
            count = os.write(self.child.stdin.fileno(), pending)
            pending = pending[count:]
        frame = self.frame()
        decision = derive(item, frame, self.context)
        verify(item, frame, decision, self.context)
        self.worker_elapsed_ms = decode(frame.decode("utf-8"))["elapsed_ms"]
        if self.has_output():
            raise ValueError("saída inesperada após frame")
        result = {key: decision[key] for key in ("id", "outcome", "applied", "calls", "fields",
                                                  "package_sha256", "model_sha256", "capture_policy_sha256")}
        result.update(contract_version=VERSION, catalog_version=request["catalog_version"],
                      catalog_sha256=digest(encoded(request["catalog"])),
                      decision_policy_sha256=decision["selected_policy_sha256"],
                      raw_frame_sha256=decision["raw_sha256"], elapsed_ms=(monotonic() - started) * 1000)
        return 200, result
