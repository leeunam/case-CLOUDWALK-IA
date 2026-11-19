"""Verifica o handoff pelo Kafka e o atendimento humano por HTTP.

Use um canal da Aurora e configure a Bia como única analista disponível nessa
marca, com capacidade para Maquininha de prioridade avançada. O roteiro envia
o relato, acompanha a troca de responsável, pede informação, retoma e resolve.
"""

import argparse
import json
import os
import subprocess
import time
import uuid
from collections import Counter
from urllib.error import HTTPError
from urllib.request import Request

from check_f02 import Demo, body, kafka_events, require


class HumanDemo(Demo):
    def command(self, path, data, *, csrf, key, expected=200):
        request = Request(self.api + path, data=body(data), headers={
            "Content-Type": "application/json", "X-CSRF-Token": csrf, "Idempotency-Key": key,
        })
        try:
            response = self.browser.open(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            require(response.code == expected, f"{path} retornou HTTP {response.code} com {raw!r}")
            return json.loads(raw)

    def wait_active(self, path):
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            record = self.call(path)
            if record["status"] == "human_active":
                return record
            time.sleep(0.4)
        raise SystemExit(f"O atendimento não ficou ativo. Último estado recebido: {record!r}")

    def replay_kafka(self, case_id, request_bytes):
        result = subprocess.run([
            "docker", "compose", "-p", self.project, "exec", "-T", "kafka",
            "/opt/kafka/bin/kafka-console-producer.sh", "--bootstrap-server", "kafka:9092",
            "--topic", "agent.requests", "--property", "parse.key=true",
        ], input=case_id.encode() + b"\t" + request_bytes + b"\n", capture_output=True, timeout=30, check=False)
        require(result.returncode == 0, f"Falha na reentrega Kafka. {result.stderr.decode(errors='replace')}")


def verify(args):
    demo = HumanDemo(args)
    demo.wait_ready()
    csrf = demo.login()["csrf_token"]
    suffix = uuid.uuid4().hex
    conversation = {"external_conversation_id": f"f03-{suffix}", "external_customer_id": "f03-demo"}
    initial_text = "O visor da maquininha está apagado desde a troca de bateria."
    initial = body({
        **conversation, "source_event_id": f"f03-{suffix}-1", "text": initial_text,
        "category": "terminal", "priority": "advanced",
    })
    receipt = demo.send(initial)
    require(demo.send(initial) == receipt, "A reentrega da entrada mudou o recibo.")
    case_id = receipt["case_id"]
    path = f"/api/v1/cases/{case_id}"
    print(f"Entrada persistida case_id={case_id} correlation_id={receipt['correlation_id']}", flush=True)
    active = demo.wait_active(path)
    owner = active["assignee"]
    initial_history = demo.call(path + "/messages")["items"]
    require([message["author"]["type"] for message in initial_history] == ["customer", "ai"],
            "O histórico do handoff deve conter o relato e a mensagem de encaminhamento.")
    require(active["handoff"]["message_ids"] == [initial_history[0]["id"]],
            "O handoff deve referenciar o relato original.")
    require(initial_text in active["handoff"]["summary"], "O resumo deve incluir o relato original.")

    reply = {"text": "Vou conferir o problema com o visor.", "expected_version": active["version"]}
    reply_kwargs = {"csrf": csrf, "key": f"f03-{suffix}-reply", "expected": 201}
    replied = demo.command(path + "/messages", reply, **reply_kwargs)
    require(demo.command(path + "/messages", reply, **reply_kwargs) == replied, "A reentrega mudou a resposta humana.")
    waiting = demo.command(path + "/actions", {
        "type": "wait_for_customer", "text": "A luz de carga acende?", "expected_version": replied["case"]["version"],
    }, csrf=csrf, key=f"f03-{suffix}-wait")
    require(waiting["status"] == "waiting_customer" and waiting["assignee"] == owner,
            "A espera deve preservar a responsável.")
    followup = body({
        **conversation, "source_event_id": f"f03-{suffix}-2", "text": "A luz acende, mas o visor continua apagado.",
    })
    require(demo.send(followup) == receipt, "O retorno do cliente abriu outro caso.")
    resumed = demo.wait_active(path)
    require(resumed["assignee"] == owner, "A retomada mudou a responsável.")
    resolved = demo.command(path + "/actions", {
        "type": "resolve", "expected_version": resumed["version"],
    }, csrf=csrf, key=f"f03-{suffix}-resolve")
    require(resolved["status"] == "resolved" and resolved["assignee"] is None, "O caso deve encerrar sem responsável ativo.")

    requests = kafka_events(demo.project, "agent.requests", case_id)
    require(len({raw for _, raw in requests}) == 1, "Somente a entrada inicial deve solicitar a IA.")
    request, request_bytes = requests[0]
    require(request["correlation_id"] == receipt["correlation_id"], "A solicitação perdeu a correlação da entrada.")
    demo.replay_kafka(case_id, request_bytes)
    results = kafka_events(demo.project, "agent.events", case_id)
    require(len(results) >= 2 and len({raw for _, raw in results}) == 1,
            "A reentrega Kafka deve publicar novamente os mesmos bytes.")
    result, result_bytes = results[0]
    require(result["event_type"] == "agent.handoff.proposed"
            and result["payload"]["request_event_id"] == request["event_id"]
            and result["turn_id"] == request["turn_id"] and result["correlation_id"] == receipt["correlation_id"],
            "A proposta de handoff deve corresponder à rodada original.")
    callback = "/webhooks/v1/agent/events"
    duplicate = demo.call(callback, data=result_bytes, secret=demo.agent_secret)
    require(duplicate == {"event_id": result["event_id"], "disposition": "duplicate"},
            "O Rails deve reconhecer a proposta repetida.")
    late_id = str(uuid.uuid4())
    late = {**result, "event_id": late_id, "event_type": "agent.reply.proposed",
            "payload": {"request_event_id": request["event_id"], "text": "Resposta atrasada."}}
    require(demo.call(callback, data=body(late), secret=demo.agent_secret) == {
        "event_id": late_id, "disposition": "discarded",
    }, "Uma resposta da IA após o handoff deve ser descartada.")

    supervisor = Demo(args)
    token = supervisor.call("/api/v1/session")["csrf_token"]
    email = "supervisor@example.test"
    password = json.loads(os.environ["CLOUDWALK_DEMO_PASSWORDS"])[email]
    supervisor.call("/api/v1/session", data=body({"email": email, "password": password}), csrf=token)
    audit = Counter(item["type"] for item in supervisor.call(path + "/audit")["items"])
    expected_events = (
        "agent.handoff.proposed", "case.human.assigned", "case.human.replied", "case.human.waiting_customer",
        "case.human.customer_returned", "case.human.resumed", "case.human.resolved", "agent.result.discarded",
    )
    require(all(audit[event] == 1 for event in expected_events), f"Eventos de auditoria inesperados. {dict(audit)}")
    history = demo.call(path + "/messages")["items"]
    require([message["author"]["type"] for message in history] == ["customer", "ai", "human", "human", "customer"],
            "As reentregas devem preservar a autoria e quantidade de mensagens.")
    print(f"Kafka pedido={request['event_id']} handoff={result['event_id']} rodada={result['turn_id']}")
    print("F03 verificada. Handoff, espera, retomada e resolução no mesmo caso, com reentrega idempotente.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:3000")
    parser.add_argument("--project", default="cloudwalk_integracao_f03f04")
    parser.add_argument("--channel-id", required=True)
    verify(parser.parse_args())
