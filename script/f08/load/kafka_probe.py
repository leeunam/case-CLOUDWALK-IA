"""Canal de controle limitado do leitor Kafka. Nenhum cliente nativo vive neste processo."""
import json
import os
import re
import selectors
import subprocess
import sys
import time

from protocol import DIRECTORY, append, now_ms


GROUPS = {"agent.requests": "mock-agent-v1", "agent.events": "platform-agent-events-v1"}
TOPICS = (*GROUPS, "agent.failures")
READER = DIRECTORY / "kafka_reader.py"
MAX_CONTROL_BYTES = 8192


class KafkaProbeError(RuntimeError):
    pass


def validate(operation, reply):
    if not isinstance(reply, dict):
        raise ValueError
    if "error" in reply:
        name = reply["error"]
        raise KafkaProbeError(name if isinstance(name, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", name)
                              else "erro_do_leitor")
    if operation == "ready":
        if type(reply.get("ready")) is not bool:
            raise ValueError
    elif operation == "records":
        n, expected = reply["records_read"], reply["expected_offsets"]
        if (type(reply["complete"]) is not bool or type(n) is not int or type(expected) is not int
                or not 0 <= n <= expected or (reply["complete"] and n != expected)):
            raise ValueError
    elif operation == "sample":
        offsets = reply["offsets"]
        parts = reply["partitions"]
        bounds = {(row["topic"], row["partition"]): row["offset"] for row in offsets}
        if (len(offsets) != 9 or set(bounds) != {(t, p) for t in TOPICS for p in range(3)}
                or any(type(n) is not int or n < 0 for n in bounds.values())):
            raise ValueError
        if len(parts) != 6 or {(r["topic"], r["partition"]) for r in parts} != {(t, p) for t in GROUPS for p in range(3)}:
            raise ValueError
        for r in parts:
            topic, partition = r["topic"], r["partition"]
            if (r["group"] != GROUPS[topic] or r["end_offset"] != bounds[topic, partition]
                    or any(type(r[k]) is not int or r[k] < 0 for k in ("lag", "start_offset", "effective_next"))
                    or r["lag"] != max(0, r["end_offset"] - r["effective_next"])):
                raise ValueError
        if not all(isinstance(reply["versions"][key], str) and reply["versions"][key]
                   for key in ("confluent_kafka", "librdkafka")):
            raise ValueError
    else:
        raise ValueError
    return reply


def probe(operation, timeout=8):
    deadline = time.monotonic() + timeout
    if timeout <= 0:
        raise KafkaProbeError("prazo_excedido")
    try:
        child = subprocess.Popen([sys.executable, "-B", str(READER), operation], env={},
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError as error:
        raise KafkaProbeError("falha_ao_iniciar") from error
    payload = bytearray()
    try:
        with selectors.DefaultSelector() as poll:
            poll.register(child.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not poll.select(remaining):
                    raise KafkaProbeError("prazo_excedido")
                chunk = os.read(child.stdout.fileno(), MAX_CONTROL_BYTES + 1 - len(payload))
                if not chunk:
                    break
                payload.extend(chunk)
                if len(payload) > MAX_CONTROL_BYTES:
                    raise KafkaProbeError("resposta_excessiva")
        status = child.wait(timeout=max(0, deadline - time.monotonic()))
        if status < 0:
            raise KafkaProbeError(f"sinal_{-status}")
        if status:
            raise KafkaProbeError(f"saida_{status}")
        if time.monotonic() > deadline:
            raise KafkaProbeError("prazo_excedido")
        if not payload.endswith(b"\n") or payload.count(b"\n") != 1:
            raise KafkaProbeError("resposta_incompleta")
        return validate(operation, json.loads(payload))
    except subprocess.TimeoutExpired:
        raise KafkaProbeError("prazo_excedido") from None
    except (ValueError, KeyError, TypeError, OSError, RecursionError):
        raise KafkaProbeError("resposta_invalida") from None
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()
        child.stdout.close()


def sample_kafka(output):
    start = now_ms()
    try:
        lag = probe("sample")["partitions"]
        row = {"partitions": lag, "total_lag": sum(p["lag"] for p in lag)}
    except KafkaProbeError as error:
        row = {"partitions": None, "total_lag": None, "error": str(error)}
    append(output / "kafka-lag.jsonl", {"sample_ms": start, "cost_ms": now_ms() - start, **row})
