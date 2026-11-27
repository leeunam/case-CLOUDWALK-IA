"""Proxy local. Guarda IDs, hash e status, sem cookies, tokens ou corpos crus."""

import hashlib
import http.client
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Rules:
    def __init__(self):
        self.lock = threading.Lock()
        self.rules = {}
        self.observed = {}

    def arm(self, name, rule):
        with self.lock:
            if name in self.rules:
                raise ValueError("ID de falha já utilizado")
            if rule["mode"] not in {"lose_response", "unavailable"}:
                raise ValueError("Modo de falha inválido")
            self.rules[name] = rule.copy()
            self.observed[name] = []

    def match(self, path, body, headers):
        with self.lock:
            if not any(rule["path"] == path for rule in self.rules.values()):
                return None, None
            try:
                payload = json.loads(body)
            except ValueError:
                return None, None
            if not isinstance(payload, dict):
                return None, None
            for name, rule in self.rules.items():
                if rule["path"] != path:
                    continue
                if "key" in rule and rule["key"] != headers.get("Idempotency-Key"):
                    continue
                if "field" in rule and payload.get(rule["field"]) != rule["value"]:
                    continue
                evidence = {
                    "body_sha256": hashlib.sha256(body).hexdigest(),
                    "expected_simulator_id": headers.get("X-Simulator-Session-Id"),
                }
                mode = rule["mode"] if rule.get("enabled", True) else None
                return (name, evidence), mode
            return None, None

    def finish(self, match, mode, upstream, receipt, downstream):
        if match is None:
            return downstream
        name, evidence = match
        with self.lock:
            rule = self.rules[name]
            if mode == "lose_response" and upstream in {200, 202} and rule.get("enabled", True):
                rule["enabled"] = False
                downstream = 502
            self.observed[name].append({
                **evidence, "upstream": upstream, "receipt": receipt, "downstream": downstream,
            })
            return downstream

    def set_enabled(self, name, enabled):
        with self.lock:
            self.rules[name]["enabled"] = enabled

    def history(self, name):
        with self.lock:
            return self.observed[name].copy()


STATE = Rules()
HOP_HEADERS = {"connection", "transfer-encoding", "content-length", "host", "server", "date"}


def response_receipt(raw):
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {key: data[key] for key in ("case_id", "correlation_id", "event_id", "disposition") if key in data}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, raw, headers=()):
        self.send_response(status)
        for key, value in headers:
            if key.lower() not in HOP_HEADERS:
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if raw:
            self.wfile.write(raw)

    def json_response(self, status, data):
        self.respond(status, json.dumps(data).encode(), [("Content-Type", "application/json")])

    def handle_request(self):
        size = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(size)
        if self.server.server_port == 8081:
            return self.control(body)
        match, mode = STATE.match(self.path, body, self.headers) if self.command == "POST" else (None, None)
        if mode == "unavailable":
            STATE.finish(match, mode, None, {}, 503)
            return self.json_response(503, {"error": {"code": "f07_transient"}})

        headers = {key: value for key, value in self.headers.items() if key.lower() not in HOP_HEADERS}
        connection = http.client.HTTPConnection("api", 3000, timeout=6)
        try:
            connection.request(self.command, self.path, body if size else None, headers)
            upstream = connection.getresponse()
            raw = upstream.read()
            response_headers = upstream.getheaders()
        except (OSError, http.client.HTTPException):
            STATE.finish(match, mode, None, {}, 504)
            return self.json_response(504, {"error": {"code": "f07_upstream_unavailable"}})
        finally:
            connection.close()

        downstream = STATE.finish(match, mode, upstream.status, response_receipt(raw) if match else {}, upstream.status)
        if downstream != upstream.status:
            return self.json_response(downstream, {"error": {"code": "f07_response_lost"}})
        return self.respond(downstream, raw, response_headers)

    def control(self, body):
        if self.path == "/ready" and self.command == "GET":
            return self.json_response(200, {"ready": True})
        prefix, _, name = self.path.rpartition("/")
        if prefix != "/rules" or not name:
            return self.json_response(404, {})
        if self.command not in {"GET", "POST", "PATCH"}:
            return self.json_response(405, {})
        try:
            if self.command == "POST":
                STATE.arm(name, json.loads(body))
            if self.command == "PATCH":
                STATE.set_enabled(name, json.loads(body)["enabled"])
            return self.json_response(200, STATE.history(name))
        except (KeyError, ValueError):
            return self.json_response(422, {})

    do_GET = do_POST = do_PATCH = do_DELETE = handle_request


def main():
    with ThreadingHTTPServer(("0.0.0.0", 8080), Handler) as data:
        with ThreadingHTTPServer(("0.0.0.0", 8081), Handler) as admin:
            threading.Thread(target=admin.serve_forever, daemon=True).start()
            data.serve_forever()


if __name__ == "__main__":
    main()
