"""Delimitação e diagnóstico da captura de evidência posterior à janela."""
import re
import time

from protocol import append, now_ms, write_json

CAPTURE_SECONDS = 52
BOUNDS_SECONDS = 18
MAX_ATTEMPTS = 3
REQUEST_SECONDS = 6


def error_fields(error):
    fields = {"error": type(error).__name__}
    detail = error.args[0] if error.args else None
    if hasattr(detail, "code") and hasattr(detail, "name"):
        code, name = detail.code(), detail.name()
        if type(code) is int:
            fields["kafka_code"] = code
        if isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_]{1,64}", name):
            fields["kafka_name"] = name
    return fields


def freeze_range(output, baseline, read_offsets, retry_errors):
    deadline = time.monotonic() + BOUNDS_SECONDS
    journal = output / "kafka-capture-attempts.jsonl"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError
        started = now_ms()
        timeout = min(REQUEST_SECONDS, remaining)
        event = {"phase": "final_offsets", "attempt": attempt, "started_ms": started,
                 "request_timeout_ms": round(timeout * 1000)}
        append(journal, {**event, "status": "started"})
        try:
            ends = read_offsets(timeout)
            if time.monotonic() > deadline:
                raise TimeoutError
            if ends.keys() != baseline.keys() or any(type(end) is not int or end < baseline[k] for k, end in ends.items()):
                raise ValueError("intervalo final inválido")
        except Exception as error:
            append(journal, {**event, "status": "failed", "finished_ms": now_ms(), **error_fields(error)})
            if not isinstance(error, retry_errors) or attempt == MAX_ATTEMPTS:
                raise
            continue
        finished = now_ms()
        write_json(output / "kafka-offset-range.json", {
            "attempt": attempt, "observed_ms": finished,
            "partitions": [{"topic": t, "partition": p, "start": baseline[t, p], "end": end}
                           for (t, p), end in ends.items()]})
        append(journal, {**event, "status": "fixed", "finished_ms": finished})
        return ends
