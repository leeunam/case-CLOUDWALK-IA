"""Sessões de ensaio em HTTP e Action Cable, com cabeçalhos mantidos em memória."""

import json
import time
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener

from observe import Blocked, Failed, verify

API = "http://api:3000"
WRITER = "http://writer:3000"
FAULT = "http://fault:8080"
CONTROL = "http://fault:8081"
REQUESTS = "http://requests:8080"
CALLBACK = "/webhooks/v1/agent/events"


def json_bytes(payload):
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()


class Browser:
    def __init__(self):
        self.jar = CookieJar()
        self.http = build_opener(ProxyHandler({}), HTTPCookieProcessor(self.jar))
        self.csrf = None

    def call(self, path, *, target=API, method=None, payload=None, raw=None, headers=None, expected=200):
        additions = {} if headers is None else headers.copy()
        if target == WRITER:
            # O Rails de desenvolvimento autoriza o Host api, e os cookies da
            # sessão continuam os mesmos na segunda instância da aplicação.
            additions["Host"] = "api:3000"
            additions["Cookie"] = self.cookie()
        if payload is not None:
            raw = json_bytes(payload)
        if raw is not None:
            additions.setdefault("Content-Type", "application/json")
        request = Request(target + path, data=raw, headers=additions, method=method)
        try:
            response = self.http.open(request, timeout=8)
        except HTTPError as error:
            response = error
        except (URLError, TimeoutError, OSError) as error:
            raise Blocked(f"HTTP indisponível em {path}: {type(error).__name__}") from error
        with response:
            try:
                data = json.loads(response.read())
            except ValueError:
                data = None
            allowed = expected if isinstance(expected, tuple) else (expected,)
            code = data.get("error", {}).get("code") if isinstance(data, dict) else None
            if code == "f07_upstream_unavailable":
                raise Blocked(f"Proxy não recebeu resposta do Rails em {path}")
            verify(response.code in allowed, f"{path}: HTTP {response.code}, esperado {allowed}, código {code}")
            if data is None and response.code in {200, 201, 202} and target != REQUESTS:
                raise Blocked(f"Resposta estruturada ausente em {path}")
            return data

    def cookie(self):
        return "; ".join(f"{cookie.name}={cookie.value}" for cookie in self.jar)

    def session(self):
        session = self.call("/api/v1/session")
        self.csrf = session["csrf_token"]
        return session

    def start_simulator(self):
        self.session()
        session = self.call("/api/v1/simulator/session", method="POST", headers=self.write_headers(), expected=201)
        self.csrf = session["csrf_token"]
        return session["user"]["id"]

    def login(self, name, passwords):
        self.session()
        email = f"{name}@example.test"
        session = self.call("/api/v1/session", payload={"email": email, "password": passwords[email]},
                            headers=self.write_headers())
        self.csrf = session["csrf_token"]
        return session

    def logout(self):
        self.call("/api/v1/session", method="DELETE", headers=self.write_headers(), expected=204)

    def write_headers(self, key=None, simulator_id=None):
        headers = {"X-CSRF-Token": self.csrf}
        if key:
            headers["Idempotency-Key"] = key
        if simulator_id:
            headers["X-Simulator-Session-Id"] = simulator_id
        return headers

    def send_simulator(self, channel, payload, key, simulator_id, **kwargs):
        return self.call(f"/api/v1/simulator/channels/{channel}/messages", headers=self.write_headers(key, simulator_id),
                         payload=payload, expected=202, **kwargs)


class Cable:
    def __init__(self, cookie):
        from websockets.sync.client import connect
        try:
            self.connection = connect(
                "ws://api:3000/cable", origin=API, additional_headers={"Cookie": cookie} if cookie else {},
                subprotocols=["actioncable-v1-json"], proxy=None, open_timeout=8, close_timeout=2,
            )
        except (OSError, TimeoutError) as error:
            raise Blocked(f"Handshake WebSocket indisponível: {type(error).__name__}") from error

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.connection.close()

    def receive(self, description, predicate, *, timeout=12, reject=None):
        from websockets.exceptions import ConnectionClosed
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                frame = json.loads(self.connection.recv(timeout=max(0, deadline - time.monotonic())))
            except TimeoutError:
                break
            except ConnectionClosed as error:
                raise Blocked(f"Socket encerrou antes de {description}: código {error.code}") from error
            if reject and reject(frame):
                raise Failed(f"Aviso de outro escopo recebido durante {description}")
            if predicate(frame):
                return frame
        raise Blocked(f"Frame não observado: {description}")

    def welcome(self):
        self.receive("welcome", lambda frame: frame.get("type") == "welcome",
                     reject=lambda frame: frame.get("type") == "disconnect")

    def subscribe(self, case_id, audience, *, allowed):
        identifier = json_bytes({"channel": "CaseUpdatesChannel", "case_id": case_id, "audience": audience}).decode()
        self.connection.send(json_bytes({"command": "subscribe", "identifier": identifier}).decode())
        replies = {"confirm_subscription", "reject_subscription"}
        frame = self.receive(
            "confirmação ou rejeição de assinatura",
            lambda f: f.get("identifier") == identifier and f.get("type") in replies,
        )
        wanted = "confirm_subscription" if allowed else "reject_subscription"
        verify(frame["type"] == wanted, f"Cable {audience}: {frame['type']}, esperado {wanted}")
        return identifier

    def revoked_stream_observation(self, identifier, after):
        from websockets.exceptions import ConnectionClosed
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            try:
                frame = json.loads(self.connection.recv(timeout=max(0, deadline - time.monotonic())))
            except TimeoutError:
                break
            except ConnectionClosed as error:
                if error.code in {1000, 1001}:
                    return {"type": "closed", "code": error.code}
                raise Blocked(f"Socket revogado encerrou de forma anormal: código {error.code}") from error
            verify(frame.get("identifier") != identifier or "message" not in frame,
                   "Socket ainda entregou mensagem após revogação")
            if frame.get("type") == "ping" and frame["message"] > after:
                return {"type": "ping", "sent_at": frame["message"], "after_control_at": after}
        raise Blocked("Faltou ping posterior ao controle ou fechamento do socket revogado")

    def update(self, identifier, case_id):
        frame = self.receive("case.updated", lambda f: f.get("identifier") == identifier and "message" in f)
        verify(frame["message"] == {"type": "case.updated", "case_id": case_id}, "Aviso Cable fora do contrato")
        return frame["message"]
