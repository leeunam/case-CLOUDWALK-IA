"""Identidades, parâmetros e transporte HTTP comuns ao ensaio."""
import hashlib
import hmac
import json
import os
import random
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = Path(__file__).resolve().parent
RESULTS = Path("/results")
API = "http://api:3000"
BRANDS = ("aurora", "horizonte")
KINDS = ("chat", "whatsapp", "email")
PIX = {"text": "Qual é o prazo de confirmação do Pix?", "category": "pix", "priority": "basic"}


def now_ms():
    return time.time_ns() // 1_000_000


def utc(ms):
    return datetime.fromtimestamp(ms / 1000, UTC).isoformat()


def bytes_json(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def append(path, data):
    with path.open("ab") as file:
        file.write(bytes_json(data) + b"\n")


def rows(path):
    if path.exists():
        with path.open() as file:
            for line in file:
                if line.endswith("\n"):
                    yield json.loads(line)


def plan(run_id, seed, stages, *, human=False):
    """Um retorno por bloco de cinco; em seis blocos, um em cada canal."""
    rng = random.Random(seed)
    routes = [(brand, kind) for brand in BRANDS for kind in KINDS]
    rng.shuffle(routes)
    expected = sum(rate * seconds for rate, seconds in stages)
    followups = set()
    if not human:
        for first in range(0, expected // 5, 6):
            rotation = rng.randrange(1, 6)
            for block in range(first, min(first + 6, expected // 5)):
                # Resíduo módulo 6 evitado pelo bloco: (5 * bloco + 5) % 6.
                route = ((5 * block + 5) + rotation) % 6
                followups.add(5 * block + ((route - 5 * block) % 6))
    entries = []
    for index in range(expected):
        identity = f"{run_id}-{index:06}"
        brand, kind = routes[index % len(routes)]
        initial = {
            "source_event_id": f"{identity}-1", "external_conversation_id": identity,
            "external_customer_id": f"{identity}-customer", **PIX,
        }
        if human:
            initial.update(category="terminal", priority="advanced", text="A maquininha parou de funcionar.")
        second = None
        if index in followups:
            second = {**initial, "source_event_id": f"{identity}-2", "text": "Obrigado, já encontrei o comprovante."}
        entries.append({"index": index, "brand": brand, "kind": kind, "initial": initial, "second": second})
    return entries


def signed_headers(channel, raw, started_ms, secret):
    channel_secret = hmac.new(secret.encode(), f"channel:{channel}".encode(), hashlib.sha256).hexdigest()
    timestamp = str(started_ms // 1000)
    signature = hmac.new(channel_secret.encode(), timestamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
    return {"Content-Type": "application/json", "X-Webhook-Timestamp": timestamp, "X-Webhook-Signature": signature}


def receipt(data):
    return {key: data.get(key) for key in ("case_id", "correlation_id")} if isinstance(data, dict) else {}


def webhook(channel, raw, *, timeout=4):
    started = now_ms()
    begin = time.monotonic_ns()
    url = f"{API}/webhooks/v1/channels/{channel}/messages"
    headers = signed_headers(channel, raw, started, os.environ["CLOUDWALK_CHANNEL_SECRET"])
    opener = build_opener(ProxyHandler({}))
    status, error, data = 0, None, None
    try:
        try:
            response = opener.open(Request(url, data=raw, headers=headers), timeout=timeout)
        except HTTPError as exc:
            response = exc
        with response:
            status = response.status
            data = json.load(response)
    except (OSError, URLError, ValueError) as exc:
        error = type(exc).__name__
        if isinstance(exc, URLError):
            error = type(exc.reason).__name__
    return {"sent_ms": started, "finished_ms": now_ms(), "elapsed_ms": (time.monotonic_ns() - begin) / 1e6,
            "status": status, "error": error, **receipt(data)}
