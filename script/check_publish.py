"""Confere a pilha F10 no HTTPS de loopback, usando apenas dados sintéticos."""

import argparse
import base64
import hashlib
import hmac
import http.client
import json
import re
import secrets
import ssl
import time
import uuid
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, HTTPSHandler, ProxyHandler, Request, build_opener

from publish import ENV_FILE, PASSWORD_KEY, PROJECT, Stack, private_env


def require(condition, message):
    if not condition:
        raise SystemExit(message)


class Smoke:
    def __init__(self, stack, settings):
        self.stack = stack
        self.settings = settings
        self.cookies = CookieJar()
        self.tls = ssl.create_default_context(cadata=stack.ca())
        self.browser = build_opener(ProxyHandler({}), HTTPSHandler(context=self.tls), HTTPCookieProcessor(self.cookies))

    def request(self, path, data=None, *, headers=(), expected=200):
        if data is not None and not isinstance(data, bytes):
            data = json.dumps(data).encode()
        request = Request(self.stack.local_url + path, data, {
            "Origin": self.stack.local_url,
            "Content-Type": "application/json",
            **dict(headers),
        })
        try:
            response = self.browser.open(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            statuses = (expected,) if isinstance(expected, int) else expected
            require(response.status in statuses, f"{path} retornou HTTP {response.status}, esperado {statuses}.")
            return response.read(), response.headers

    def json(self, *args, **kwargs):
        return json.loads(self.request(*args, **kwargs)[0])

    def routes(self):
        index, headers = self.request("/analista")
        require(index == self.request("/")[0] and headers.get("Cache-Control") == "no-cache", "Fallback SPA inválido.")
        asset = re.search(rb'(/assets/[^"]+\.js)', index)
        require(asset, "Bundle do frontend não encontrado.")
        _, headers = self.request(asset.group(1).decode())
        require("immutable" in headers.get("Cache-Control", ""), "Bundle sem cache imutável.")
        self.request("/assets/inexistente.js", expected=404)
        self.request("/.env.publish.local", expected=404)
        invalid, _ = self.request("/api/v1/inexistente", expected=404)
        require(index != invalid, "Rota da API entregou o HTML da SPA.")
        self.request("/webhooks/v1/agent/events", {}, expected=401)
        connection = http.client.HTTPConnection("127.0.0.1", self.stack.args.http_port, timeout=5)
        try:
            connection.request("GET", "/analista", headers={"Host": "nao-configurado.trycloudflare.com"})
            require(connection.getresponse().status == 421, "Origem HTTP não configurada foi aceita.")
        finally:
            connection.close()

    def login(self):
        path = "/api/v1/session"
        email = "bia@example.test"
        login = {"email": email, "password": json.loads(self.settings[PASSWORD_KEY])[email]}
        token = self.json(path)["csrf_token"]
        headers = {"X-CSRF-Token": token}
        self.request(path, login, expected=403)
        self.request(path, login, headers={**headers, "Origin": "https://origem-incorreta.invalid"}, expected=403)
        self.request(path, b"{", headers=headers, expected=(400, 422))
        self.request(path, {"email": email}, headers=headers, expected=422)
        self.request(path, {**login, "password": secrets.token_urlsafe(32)}, headers=headers, expected=401)
        result, response_headers = self.request(path, login, headers=headers)
        cookie = response_headers.get("Set-Cookie", "").lower()
        require(all(flag in cookie for flag in ("; secure", "; httponly", "samesite=lax")), "Cookie de sessão inseguro.")
        staff = json.loads(result)
        require(staff["user"]["name"] == "Bia" and staff["user"]["role"] == "analyst", "Identidade inesperada.")
        require(self.json(path)["user"] == staff["user"], "Sessão autenticada não foi reaproveitada.")

    def cable(self, origin):
        connection = http.client.HTTPSConnection("127.0.0.1", self.stack.args.https_port, context=self.tls, timeout=5)
        try:
            connection.request("GET", "/cable", headers={
                "Connection": "Upgrade", "Upgrade": "websocket", "Sec-WebSocket-Version": "13",
                "Sec-WebSocket-Key": base64.b64encode(secrets.token_bytes(16)).decode(),
                "Sec-WebSocket-Protocol": "actioncable-v1-json",
                "Cookie": "; ".join(f"{cookie.name}={cookie.value}" for cookie in self.cookies),
                "Origin": origin,
            })
            with connection.getresponse() as response:
                return response.status
        finally:
            connection.close()

    def start(self):
        channels = self.json("/api/v1/channels")["items"]
        channel = next(item for item in channels if item["brand_name"] == "Aurora Pagamentos" and item["type"] == "chat")
        channel_id = channel["id"]
        root = self.settings["PUBLISH_CHANNEL_SECRET"].encode()
        key = hmac.new(root, f"channel:{channel_id}".encode(), hashlib.sha256).hexdigest()
        event = uuid.uuid4().hex
        payload = json.dumps({
            "source_event_id": f"f10-{event}", "external_conversation_id": f"f10-{event}",
            "external_customer_id": "f10-sintetico", "text": "A maquininha apagou durante o atendimento.",
        }).encode()
        timestamp = str(int(time.time()))
        signature = hmac.new(key.encode(), timestamp.encode() + b"." + payload, hashlib.sha256).hexdigest()
        receipt = self.json(f"/webhooks/v1/channels/{channel_id}/messages", payload, headers={
            "X-Webhook-Timestamp": timestamp, "X-Webhook-Signature": signature,
        }, expected=202)
        case_id = receipt["case_id"]
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            case = self.json(f"/api/v1/cases/{case_id}")
            if case["status"] in {"human_active", "waiting_human"}:
                self.history(case_id)
                print(f"Fixture e handoff concluídos. Caso {case_id}, correlação {receipt['correlation_id']}.")
                return
            time.sleep(0.5)
        raise SystemExit(f"Handoff não observado no caso {case_id}.")

    def history(self, case_id):
        case = self.json(f"/api/v1/cases/{case_id}")
        require(case["handoff"], "Resumo de handoff ausente.")
        messages = self.json(f"/api/v1/cases/{case_id}/messages")["items"]
        require([item["author"]["type"] for item in messages[:2]] == ["customer", "ai"], "Histórico incompleto.")
        print(f"Caso {case_id} em {case['status']}, com relato original e encaminhamento do mock.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="cloudwalk_publish")
    parser.add_argument("--http-port", type=int, default=18080)
    parser.add_argument("--https-port", type=int, default=18443)
    parser.add_argument("--case-id", type=uuid.UUID)
    args = parser.parse_args()
    if not PROJECT.fullmatch(args.project):
        parser.error("use um projeto exclusivo cloudwalk_publish.")
    with private_env(ENV_FILE) as settings:
        stack = Stack(args, settings)
        smoke = Smoke(stack, settings)
        smoke.routes()
        smoke.login()
        require(smoke.cable(stack.local_url) == 101, "Upgrade WebSocket recusado.")
        require(smoke.cable("https://origem-incorreta.invalid") != 101, "WebSocket aceitou origem indevida.")
        if args.case_id:
            smoke.history(args.case_id)
        else:
            smoke.start()


if __name__ == "__main__":
    main()
