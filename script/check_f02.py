"""Verifica a F02 usando HTTP, cookies e os registros do Kafka real."""

import argparse
import hashlib
import hmac
import json
import os
import subprocess
import time
import uuid
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener


def body(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()


def require(condition, description):
    if not condition:
        raise SystemExit(description)


def kafka_events(project, topic, case_id):
    command = [
        "docker", "compose", "-p", project, "exec", "-T", "kafka",
        "/opt/kafka/bin/kafka-console-consumer.sh", "--bootstrap-server", "kafka:9092",
        "--topic", topic, "--from-beginning", "--timeout-ms", "5000",
        "--property", "print.key=true",
    ]
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
    records = []
    for line in process.stdout.splitlines():
        key, separator, raw = line.partition(b"\t")
        if separator and key == case_id.encode():
            records.append((json.loads(raw), raw))
    require(records, f"Não encontrei o caso {case_id} em {topic}. {process.stderr.decode(errors='replace')}")
    return records


class Demo:
    def __init__(self, args):
        self.api = args.api.rstrip("/")
        self.project = args.project
        self.channel = "/webhooks/v1/channels/" + args.channel_id + "/messages"
        self.channel_secret = hmac.new(
            os.environ["CLOUDWALK_CHANNEL_SECRET"].encode(), f"channel:{args.channel_id}".encode(), hashlib.sha256
        ).hexdigest()
        self.agent_secret = os.environ["CLOUDWALK_AGENT_EVENTS_SECRET"]
        self.browser = build_opener(HTTPCookieProcessor(CookieJar()))

    def call(self, path, *, data=None, method=None, secret=None, csrf=None, expected=200):
        headers = {}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if csrf is not None:
            headers["X-CSRF-Token"] = csrf
        if secret is not None:
            timestamp = str(int(time.time()))
            headers["X-Webhook-Timestamp"] = timestamp
            headers["X-Webhook-Signature"] = hmac.new(
                secret.encode(), timestamp.encode() + b"." + data, hashlib.sha256
            ).hexdigest()

        request = Request(self.api + path, data=data, method=method, headers=headers)
        try:
            response = self.browser.open(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            require(response.code == expected, f"{path}: HTTP {response.code}, esperado {expected}. {raw!r}")
            return json.loads(raw) if raw else None

    def send(self, raw, expected=202):
        return self.call(self.channel, data=raw, secret=self.channel_secret, expected=expected)

    def login(self):
        token = self.call("/api/v1/session")["csrf_token"]
        email = "bia@example.test"
        password = json.loads(os.environ["CLOUDWALK_DEMO_PASSWORDS"])[email]
        session = self.call("/api/v1/session", data=body({"email": email, "password": password}), csrf=token)
        require(session["user"] and session["user"]["name"] == "Bia",
                "A sessão não foi autenticada como Bia.")
        return session

    def wait_messages(self, path, count):
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            items = self.call(path)["items"]
            if len(items) >= count:
                return items
            time.sleep(0.4)
        raise SystemExit(f"Histórico não chegou a {count} mensagens. Confira os logs da ponte, do mock e do outbox.")

    def wait_ready(self):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                with self.browser.open(self.api + "/api/v1/health", timeout=3) as response:
                    if response.status == 200:
                        return
            except (URLError, TimeoutError):
                pass
            time.sleep(0.5)
        raise SystemExit("API indisponível. Confira os logs de cloudwalk-f02-api e a porta configurada.")

    def run(self):
        self.wait_ready()
        suffix = uuid.uuid4().hex
        channel_message = {
            "source_event_id": f"f02-{suffix}-1", "external_conversation_id": f"f02-{suffix}",
            "external_customer_id": "f02-demo", "text": "Qual é o prazo de confirmação de um Pix?",
            "category": "pix", "priority": "basic",
        }
        initial = body(channel_message)
        receipt = self.send(initial)
        case_id = receipt["case_id"]
        print(f"Entrada persistida case_id={case_id} correlation_id={receipt['correlation_id']}", flush=True)
        require(self.send(initial) == receipt, "A reentrega mudou o recibo da entrada.")
        self.send(initial + b" ", expected=409)
        path = f"/api/v1/cases/{case_id}"
        self.call(path + "/messages", expected=401)
        self.login()
        self.wait_messages(path + "/messages", 2)

        followup = body({
            "source_event_id": f"f02-{suffix}-2", "external_conversation_id": f"f02-{suffix}",
            "external_customer_id": "f02-demo", "text": "Funcionou. Obrigado!",
        })
        require(self.send(followup) == receipt, "A continuação abriu outro atendimento.")
        transcript = self.wait_messages(path + "/messages", 4)
        require(self.call(path)["status"] == "resolved", "O atendimento não foi resolvido.")
        require([message["sequence"] for message in transcript] == [1, 2, 3, 4], "Sequência inesperada no histórico.")
        require([message["author"]["type"] for message in transcript] == ["customer", "ai"] * 2, "Autoria inesperada.")

        requests = kafka_events(self.project, "agent.requests", case_id)
        results = kafka_events(self.project, "agent.events", case_id)
        request_ids = {event["event_id"] for event, _ in requests}
        require(len(request_ids) == 2, "O Kafka deve conter dois IDs de solicitação distintos.")
        require({event["payload"]["request_event_id"] for event, _ in results} == request_ids,
                "Os retornos Kafka devem corresponder aos dois pedidos.")
        require({event["correlation_id"] for event, _ in requests + results} == {receipt["correlation_id"]},
                "Correlação alterada durante a passagem pelo Kafka.")
        for event, raw in results:
            replay = self.call("/webhooks/v1/agent/events", data=raw, secret=self.agent_secret)
            require(replay == {"event_id": event["event_id"], "disposition": "duplicate"}, "Callback repetido sem deduplicação.")
            print(f"Kafka pedido={event['payload']['request_event_id']} retorno={event['event_id']} rodada={event['turn_id']}")
        require(self.call(path + "/messages")["items"] == transcript, "A reentrega alterou o histórico.")
        for message in transcript:
            print(f"{message['sequence']} {message['author']['type']}  {message['text']}")
        print("Verificação F02 concluída: dois turnos, resolução e um efeito por entrada e retorno.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:3000")
    parser.add_argument("--project", default="cloudwalk_f02")
    parser.add_argument("--channel-id", required=True)
    Demo(parser.parse_args()).run()


if __name__ == "__main__":
    main()
