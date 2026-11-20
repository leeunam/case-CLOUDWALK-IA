"""Cenários da F07-A. A saída padrão carrega somente o protocolo com o runner."""

import hashlib
import hmac
import json
import os
import sys
import time
import traceback
import uuid
from pathlib import Path

from agent_flow import propose_result, signed_headers
from confluent_kafka import ConsumerGroupTopicPartitions, KafkaException, TopicPartition
from psycopg import Error as DatabaseError

from http_client import API, CALLBACK, CONTROL, FAULT, REQUESTS, WRITER, Browser, Cable, json_bytes
from observe import EVENTS_GROUP, GROUPS, Blocked, Database, Failed, Kafka, until, verify

FIXTURES = json.loads(Path(__file__).with_name("fixtures.json").read_text())
CATALOG = json.loads(Path(__file__).with_name("catalog.json").read_text())
SCENARIOS = {}


def scenario(id_):
    def register(fn):
        SCENARIOS[id_] = (fn, CATALOG[id_])
        return fn
    return register


def uid():
    return str(uuid.uuid4())


def host(action, **options):
    print(json.dumps({"action": action, **options}), flush=True)
    line = sys.stdin.readline()
    if not line:
        raise Blocked("Runner não devolveu resposta ao verificador")
    response = json.loads(line)
    if not response["ok"]:
        raise Blocked(response["reason"])
    return response["result"]


def types(state):
    return [item["type"] for item in state["messages"]]


def audit(state, event_type, event_id=None):
    return [item for item in state["audits"] if item["type"] == event_type
            and (event_id is None or item["event_id"] == event_id)]


class Trial:
    def __init__(self, db, kafka):
        self.db = db
        self.kafka = kafka
        self.http = Browser()
        self.agent_secret = os.environ["CLOUDWALK_AGENT_EVENTS_SECRET"]
        self.passwords = json.loads(os.environ["CLOUDWALK_DEMO_PASSWORDS"])

    def group_ready(self, topic):
        until(f"grupo {GROUPS[topic]} estável com três partições",
              lambda: self.kafka.group_ready(GROUPS[topic], topic), timeout=150)

    def ready(self):
        for target, path in ((API, "/api/v1/health"), (WRITER, "/api/v1/health"), (CONTROL, "/ready")):
            def healthy():
                try:
                    return self.http.call(path, target=target, expected=(200, 503)).get("status", "ok") == "ok"
                except Blocked:
                    return False
            until(f"HTTP pronto em {target}{path}", healthy)
        def bridge_ready():
            try:
                self.http.call("/webhooks/v1/agent/requests", target=REQUESTS, expected=501)
                return True
            except Blocked:
                return False

        until("ponte HTTP pronta", bridge_ready)
        until("tópicos Kafka com três líderes", self.kafka.topics_ready)
        until("canais e demais dados sintéticos preparados", lambda: self.db.channel("aurora"))
        for topic in GROUPS:
            self.group_ready(topic)

    def channel_path(self, channel):
        return f"/webhooks/v1/channels/{channel}/messages"

    def input(self, **fields):
        return {**FIXTURES["channel"], "source_event_id": f"f07-{uid()}", "external_conversation_id": f"f07-{uid()}",
                **fields}

    def send(self, channel, raw, *, target=API, expected=202, secret=None, timestamp=None):
        if secret is None:
            secret = hmac.new(os.environ["CLOUDWALK_CHANNEL_SECRET"].encode(),
                              f"channel:{channel}".encode(), hashlib.sha256).hexdigest()
        return self.http.call(self.channel_path(channel), raw=raw, headers=signed_headers(secret, raw, timestamp),
                              target=target, expected=expected)

    def callback(self, raw, *, target=API, expected=200, secret=None):
        headers = signed_headers(self.agent_secret if secret is None else secret, raw)
        return self.http.call(CALLBACK, raw=raw, headers=headers, target=target, expected=expected)

    def arm(self, name, path, *, mode="lose_response", **options):
        self.http.call(f"/rules/{name}", target=CONTROL, payload={"path": path, "mode": mode, **options})

    def enabled(self, name, enabled):
        self.http.call(f"/rules/{name}", target=CONTROL, method="PATCH", payload={"enabled": enabled})

    def history(self, name):
        return self.http.call(f"/rules/{name}", target=CONTROL)

    def record(self, topic, case_id, event_id=None):
        def search():
            return [r for r in self.kafka.records(topic, key=case_id)
                    if event_id is None or r.data["event_id"] == event_id]
        return until(f"registro em {topic} para {case_id}", search)[0]

    def consumed(self, record):
        return until(
            f"grupo confirmou {record.topic}/{record.partition}/{record.offset}",
            lambda: self.kafka.offsets(GROUPS[record.topic], record.topic, record.partition),
            lambda state: (state["committed_next_offset"] or 0) > record.offset,
            timeout=150,
        )

    def staff(self, name):
        browser = Browser()
        return browser, browser.login(name, self.passwords)

    def await_case(self, case_id, description, predicate):
        return until(description, lambda: self.db.case(case_id), lambda row: bool(row) and predicate(row))

    def applied_pair(self, case_id):
        request = self.record("agent.requests", case_id)
        event = self.record("agent.events", case_id)
        request_offset = self.consumed(request)
        event_offset = self.consumed(event)
        self.await_case(case_id, "outbox da rodada publicado", lambda row: row["outbox"][0]["published"])
        return request, event, request_offset, event_offset


@scenario("01")
def outage(t, e):
    channel = t.db.channel("aurora")
    incoming = t.input()
    host("stop", service="outbox")
    try:
        receipt = t.send(channel, json_bytes(incoming))
        case_id = receipt["case_id"]
        e.update(channel_id=channel, source_event_id=incoming["source_event_id"], receipt=receipt)
        before = e["before_outage"] = t.db.case(case_id)
        verify(before["entries"] == 1 and types(before) == ["customer"] and len(before["outbox"]) == 1,
               "Entrada aceita sem mensagem e outbox persistidos")
        pending = before["outbox"][0]
        verify(pending["attempts"] == 0 and not pending["published"], "Envio começou antes da interrupção")
        host("stop", service="kafka")
        try:
            e["broker_during_fault"] = host("state", service="kafka")
            verify(e["broker_during_fault"]["State"] == "exited", "Kafka não estava parado")
            host("start", service="outbox")
            degraded = e["during_outage"] = t.await_case(
                case_id, "tentativa de envio concluída enquanto Kafka está parado",
                lambda row: row["outbox"][0]["attempts"] >= 1 and not row["outbox"][0]["claimed"],
            )
            host("stop", service="outbox")
            verify(degraded["outbox"][0]["event_id"] == pending["event_id"] and
                   not degraded["outbox"][0]["published"] and not degraded["outbox"][0]["failed"] and
                   degraded["entries"] == 1 and degraded["messages"] == before["messages"],
                   "Outbox deixou de estar pendente ou houve efeito durante a interrupção")
        finally:
            host("start", service="kafka")
        until("Kafka restaurado com líderes", t.kafka.topics_ready, timeout=150)
        for topic in GROUPS:
            t.group_ready(topic)
    finally:
        host("start", service="outbox")

    e["recovery"] = "runner retomou os serviços após prontidão do Kafka, dentro do orçamento de retentativas"
    request, event, mock_offset, bridge_offset = t.applied_pair(case_id)
    e["kafka"] = {"request": request.position(), "request_event_id": request.data["event_id"],
                  "result": event.position(), "result_event_id": event.data["event_id"],
                  "mock_offset": mock_offset, "bridge_offset": bridge_offset}
    after = e["after_recovery"] = t.await_case(case_id, "confirmação do outbox recuperado",
                                              lambda row: row["outbox"][0]["published"])
    e["broker_counts"] = {topic: len(t.kafka.records(topic, key=case_id))
                          for topic in ("agent.requests", "agent.events", "agent.failures")}
    verify(e["broker_counts"] == {"agent.requests": 1, "agent.events": 1, "agent.failures": 0} and
           request.data["event_id"] == pending["event_id"] and
           event.data["payload"]["request_event_id"] == pending["event_id"] and
           after["entries"] == 1 and types(after) == ["customer", "ai"] and
           len(audit(after, "agent.delivery.confirmed", pending["event_id"])) == 1 and
           len(audit(after, "agent.reply.proposed", event.data["event_id"])) == 1,
           "Recuperação sem publicação correlata ou com efeito duplicado")


@scenario("02")
def ambiguous(t, e):
    channel = t.db.channel("aurora")
    incoming = t.input()
    raw = json_bytes(incoming)
    source_id = incoming["source_event_id"]
    e.update(channel_id=channel, source_event_id=source_id)
    t.arm("channel", t.channel_path(channel), field="source_event_id", value=source_id)
    host("stop", service="outbox")
    try:
        t.send(channel, raw, target=FAULT, expected=502)
        first, = e["channel_proxy_after_loss"] = t.history("channel")
        receipt = first["receipt"]
        case_id = receipt["case_id"]
        e["after_channel_loss"] = t.db.case(case_id)
        verify(first["upstream"] == 202 and t.db.entry(source_id) == 1 and
               types(e["after_channel_loss"]) == ["customer"], "502 sem entrada persistida antes da reentrega")
        verify(t.send(channel, raw, target=FAULT) == receipt, "A reentrega mudou o recibo da entrada")
        error = t.send(channel, raw + b" ", target=FAULT, expected=409)
        verify(error["error"]["code"] == "idempotency_conflict", "Conflito inesperado na reentrega do webhook")
        e["channel_proxy"] = channel_attempts = t.history("channel")
        verify([item["downstream"] for item in channel_attempts] == [502, 202, 409] and
               channel_attempts[0]["receipt"] == channel_attempts[1]["receipt"] and
               channel_attempts[0]["body_sha256"] == channel_attempts[1]["body_sha256"] and
               channel_attempts[2]["body_sha256"] != channel_attempts[0]["body_sha256"],
               "O proxy não observou bytes idênticos e conflito de conteúdo no webhook")
        request_body = t.db.request_body(e["after_channel_loss"]["outbox"][0]["event_id"])
        event_id = propose_result(request_body)["event_id"]
        t.arm("callback", CALLBACK, field="event_id", value=event_id)
    finally:
        host("start", service="outbox")
    event = t.record("agent.events", case_id, event_id)
    e["callback_offset"] = t.consumed(event)
    t.await_case(case_id, "outbox do callback perdido confirmado", lambda row: row["outbox"][0]["published"])
    e["callback_position"] = event.position()
    e["callback_event_id"] = event_id
    repeat = e["callback_duplicate_receipt"] = t.callback(event.raw, target=FAULT)
    error = t.callback(event.raw + b" ", target=FAULT, expected=409)
    e["callback_proxy"] = attempts = t.history("callback")
    after = e["case_after_replays"] = t.db.case(case_id)
    e["callback_receipts"] = persisted = t.db.receipt(event_id)
    verify([x["downstream"] for x in attempts] == [502, 200, 200, 409] and
           attempts[0]["upstream"] == 200 and attempts[0]["receipt"] == {"event_id": event_id, "disposition": "applied"} and
           repeat == {"event_id": event_id, "disposition": "duplicate"} and
           attempts[1]["receipt"] == repeat and len({item["body_sha256"] for item in attempts[:3]}) == 1 and
           error["error"]["code"] == "idempotency_conflict" and len(persisted) == 1 and
           persisted[0]["sha256"] == attempts[0]["body_sha256"] and persisted[0]["disposition"] == "applied" and
           after["entries"] == 1 and types(after) == ["customer", "ai"] and
           len(audit(after, "channel.message.received")) == 1 and len(audit(after, "agent.reply.proposed", event_id)) == 1,
           "Callback perdido não preservou os recibos, hashes, auditoria ou contagens")

    channel = t.db.channel("aurora", "whatsapp")
    plan = {"channel": channel, "message": FIXTURES["simulator"], "same": f"f07-{uid()}",
            "changed": f"f07-{uid()}", "fresh": f"f07-{uid()}"}
    path = f"/api/v1/simulator/channels/{channel}/messages"
    for name in ("same", "changed", "fresh"):
        t.arm(name, path, key=plan[name], enabled=name != "fresh")
    client = e["frontend_client"] = host("frontend", plan=plan)
    e["frontend_keys"] = {name: plan[name] for name in ("same", "changed", "fresh")}
    a = client["identityA"]
    b = client["identityB"]
    e["frontend_proxy"] = proxy = {name: t.history(name) for name in ("same", "changed", "fresh")}
    e["simulator_cases"] = rows = t.db.simulator_cases(a, b)
    verify(a != b and client["firstLost"] == {"status": 502, "code": "f07_response_lost", "uncertain": True} and
           client["secondLost"] == client["firstLost"] and client["afterLogout"]["status"] == 401 and
           client["switchedRetry"] == {"status": 409, "code": "simulator_session_changed", "uncertain": False},
           "Cliente não classificou a entrega incerta ou permitiu reutilizar a tentativa em outra identidade")
    same, changed, fresh = (proxy[name] for name in ("same", "changed", "fresh"))
    verify([item["downstream"] for item in same] == [502, 202] and
           [item["downstream"] for item in changed] == [502, 409] and
           [item["downstream"] for item in fresh] == [202] and
           all(item["expected_simulator_id"] == a for item in same + changed) and
           fresh[0]["expected_simulator_id"] == b and
           len({item["body_sha256"] for item in same + changed + fresh}) == 1,
           "Cliente real perdeu o header de identidade, mudou os bytes ou repetiu no escopo errado")
    case_same = client["repeated"]["receipt"]
    new = client["newSend"]["receipt"]
    verify(same[0]["receipt"] == same[1]["receipt"] == {
               key: case_same[key] for key in ("case_id", "correlation_id")} and
           {(row["case_id"], row["simulator_id"]) for row in rows} ==
           {(case_same["case_id"], a), (changed[0]["receipt"]["case_id"], a), (new["case_id"], b)},
           "Recibo reentregue não corresponde ao caso original ou a troca de sessão gravou caso extra")
    for row in rows:
        t.applied_pair(row["case_id"])
    e["simulator_persistence"] = [t.db.case(row["case_id"]) for row in rows]
    verify(all(row["entries"] == 1 and types(row) == ["customer", "ai"] for row in e["simulator_persistence"]),
           "O cliente deixou entradas ou efeitos duplicados no banco")


@scenario("03")
def replay(t, e):
    payload = t.input(**FIXTURES["handoff"])
    receipt = e["receipt"] = t.send(t.db.channel("aurora"), json_bytes(payload))
    case_id = receipt["case_id"]
    request, event, request_offset, event_offset = t.applied_pair(case_id)
    e["initial_kafka"] = {"request": request.position(), "event": event.position(),
                          "request_offset": request_offset, "event_offset": event_offset,
                          "event_id": event.data["event_id"]}
    assigned = t.await_case(case_id, "handoff atribuído a humano", lambda row: row["status"] == "human_active")
    actors = (t.staff(name) for name in ("alex", "bia", "cris"))
    owner = next((browser for browser, session in actors if session["user"]["attendant_id"] == assigned["assignee_id"]), None)
    verify(owner is not None, "Handoff não pertence a analista do seed")
    owner.call(f"/api/v1/cases/{case_id}/messages",
               payload={"expected_version": assigned["version"], "text": FIXTURES["human_reply"]},
               headers=owner.write_headers(f"f07-{uid()}"), expected=201)
    before = e["before_replay"] = t.db.case(case_id)
    verify(types(before) == ["customer", "ai", "human"] and len(audit(before, "agent.handoff.proposed")) == 1,
           "Faltam handoff e resposta humana antes da releitura")
    event_id = event.data["event_id"]
    e["receipt_before_replay"] = t.db.receipt(event_id)
    t.arm("replay", CALLBACK, enabled=False, field="event_id", value=event_id)
    host("stop", service="events")
    try:
        until("grupo de retorno sem membros para rebobinar",
              lambda: t.kafka.group_empty(EVENTS_GROUP), timeout=150)
        result = t.kafka.admin.alter_consumer_group_offsets(
            [ConsumerGroupTopicPartitions(EVENTS_GROUP, [TopicPartition(event.topic, event.partition, event.offset)])],
            request_timeout=10,
        )[EVENTS_GROUP].result()
        verify(all(not part.error for part in result.topic_partitions), "Rebobinamento da partição rejeitado")
        e["rewound_offset"] = t.kafka.offsets(EVENTS_GROUP, event.topic, event.partition)
        verify(e["rewound_offset"]["committed_next_offset"] == event.offset, "Grupo não foi rebobinado ao registro retido")
    finally:
        host("start", service="events")
    t.group_ready(event.topic)
    e["replay_offset"] = t.consumed(event)
    e["replay_proxy"] = observed = t.history("replay")
    verify(len(observed) == 1 and observed[0]["receipt"] == {"event_id": event_id, "disposition": "duplicate"} and
           observed[0]["body_sha256"] == hashlib.sha256(event.raw).hexdigest() and t.db.case(case_id) == before and
           t.db.receipt(event_id) == e["receipt_before_replay"],
           "Replay do mesmo offset não recebeu duplicate ou mudou o atendimento")
    late = {**event.data, "event_id": uid(), "event_type": "agent.reply.proposed", "payload": {
        "request_event_id": request.data["event_id"], "text": "Resposta sintética tardia da rodada antiga.",
    }}
    t.arm("late", CALLBACK, enabled=False, field="event_id", value=late["event_id"])
    record = t.kafka.publish(event.topic, event.key, json_bytes(late), partition=event.partition)
    e["late"] = {**record.position(), "event_id": late["event_id"], "old_request_id": request.data["event_id"],
                 "old_turn_id": late["turn_id"], "old_assignment_generation": late["assignment_generation"],
                 "offset_after": t.consumed(record)}
    e["late_receipt"] = t.db.receipt(late["event_id"])
    e["late_proxy"] = t.history("late")
    after = e["after_late"] = t.db.case(case_id)
    discards = audit(after, "agent.result.discarded", late["event_id"])
    verify(len(discards) == 1 and discards[0]["reason"] == "non_current_turn" and
           len(e["late_receipt"]) == 1 and e["late_receipt"][0]["disposition"] == "discarded" and
           all(after[key] == before[key] for key in ("status", "version", "assignee_id", "assignment_generation", "messages", "outbox")) and
           after["assignment_generation"] > late["assignment_generation"],
           "O retorno antigo alterou o atendimento humano ou o descarte não foi auditado")

@scenario("04")
def isolation(t, e):
    channel = t.db.channel("horizonte")
    good = FIXTURES["simulator"]
    client = Browser()
    identity = e["simulator_id"] = client.start_simulator()
    initial = {key: value for key, value in good.items() if key != "category"}
    receipt = e["receipt"] = client.send_simulator(channel, initial, f"f07-{uid()}", identity)
    case_id = receipt["case_id"]
    request, event, _, offset = t.applied_pair(case_id)
    e["initial_kafka"] = {"request": request.position(), "result": event.position(), "bridge_offset": offset}
    baseline = e["baseline"] = t.db.case(case_id)
    verify(types(baseline) == ["customer", "ai"] and baseline["category"] == "pix" and
           baseline["category_source"] == "jev" and baseline["priority_source"] == "channel" and
           len(audit(baseline, "case.classification.completed")) == 1,
           "Caso inicial não completou o fluxo do simulador com categoria complementada pelo Jev fixture")

    invalid_channel = t.input()
    bad_req = {**request.data, "event_id": uid()}
    bad_result = {**event.data, "event_id": uid()}
    e["invalid_ids"] = {"source_event_id": invalid_channel["source_event_id"],
                        "request_event_id": bad_req["event_id"], "result_event_id": bad_result["event_id"]}
    raw_channel = json_bytes(invalid_channel)
    expired = t.send(channel, raw_channel, timestamp=1, expected=401)
    denied_channel = t.send(channel, raw_channel, secret="f07-invalid", expected=401)
    bad_request = json_bytes(bad_req)
    denied_bridge = t.http.call("/webhooks/v1/agent/requests", target=REQUESTS, raw=bad_request,
                               headers=signed_headers("f07-invalid", bad_request), expected=401)
    denied_callback = t.callback(json_bytes(bad_result), secret="f07-invalid", expected=401)
    e["invalid_http"] = {key: response["error"]["code"] for key, response in (
        ("expired", expired), ("channel", denied_channel), ("bridge", denied_bridge), ("callback", denied_callback),
    )}
    e["invalid_effects"] = {
        "entries": t.db.entry(invalid_channel["source_event_id"]), "receipts": len(t.db.receipt(bad_result["event_id"])),
        "request_records": sum(r.data["event_id"] == bad_req["event_id"]
                               for r in t.kafka.records("agent.requests", key=case_id)),
        "case_preserved": t.db.case(case_id) == baseline,
    }
    verify(set(e["invalid_http"].values()) == {"unauthenticated"} and
           e["invalid_effects"] == {"entries": 0, "receipts": 0, "request_records": 0, "case_preserved": True},
           "Credencial inválida provocou efeito ou não foi rejeitada")

    outsider = Browser()
    e["outsider_simulator_id"] = outsider.start_simulator()
    bia, bia_session = t.staff("bia")
    supervisor, _ = t.staff("supervisor")
    e["outsider_staff_id"] = bia_session["user"]["id"]
    sim_path = f"/api/v1/simulator/cases/{case_id}"
    staff_path = f"/api/v1/cases/{case_id}"
    e["rest_denied"] = {}
    rest = [
        ("other_simulator_case", outsider, sim_path, 404), ("other_simulator_messages", outsider, sim_path + "/messages", 404),
        ("other_brand_case", bia, staff_path, 404), ("other_brand_messages", bia, staff_path + "/messages", 404),
        ("staff_using_simulator", bia, sim_path, 401), ("simulator_using_staff", client, staff_path, 401),
    ]
    for label, browser, path, status in rest:
        response = browser.call(path, expected=status)
        e["rest_denied"][label] = {"status": status, "code": response["error"]["code"]}
    cross_write = bia.call(staff_path + "/messages", expected=404,
                           payload={"expected_version": baseline["version"], "text": FIXTURES["human_reply"]},
                           headers=bia.write_headers(f"f07-{uid()}"))
    e["rest_denied"]["other_brand_write"] = {"status": 404, "code": cross_write["error"]["code"]}
    listed = bia.call("/api/v1/cases?brand_id=" + baseline["brand_id"])
    verify(not listed["items"] and t.db.case(case_id) == baseline, "Acesso cruzado expôs lista ou alterou o caso")

    with Cable(outsider.cookie()) as wrong_customer, Cable(bia.cookie()) as wrong_staff:
        wrong_customer.welcome()
        wrong_staff.welcome()
        wrong_customer.subscribe(case_id, "simulator", allowed=False)
        wrong_staff.subscribe(case_id, "staff", allowed=False)
    host("stop", service="outbox")
    try:
        with Cable(client.cookie()) as live:
            live.welcome()
            live.subscribe(case_id, "staff", allowed=False)
            live.subscribe(case_id, "invalid", allowed=False)
            identifier = live.subscribe(case_id, "simulator", allowed=True)
            e["cable_denied"] = ["other_simulator", "other_brand", "staff_audience", "unknown_audience"]
            continuation = {**good, "external_conversation_id": receipt["external_conversation_id"],
                            "text": "Ainda estou conferindo o prazo do Pix."}
            updated = client.send_simulator(channel, continuation, f"f07-{uid()}", identity, target=WRITER)
            verify(updated["case_id"] == case_id, "Escrita no writer abriu nova conversa")
            e["cross_process"] = {"writer": WRITER, "subscriber": API, "notice": live.update(identifier, case_id)}

        disconnected = {**continuation, "text": "Recebi o comprovante e estou conferindo."}
        client.send_simulator(channel, disconnected, f"f07-{uid()}", identity, target=WRITER)
        with Cable(client.cookie()) as reconnected, Cable(supervisor.cookie()) as control:
            for cable in (reconnected, control):
                cable.welcome()
            revoked_stream = reconnected.subscribe(case_id, "simulator", allowed=True)
            control_stream = control.subscribe(case_id, "staff", allowed=True)
            client.call(sim_path)
            transcript = client.call(sim_path + "/messages")["items"]
            verify(len(transcript) == 4 and transcript[-1]["text"] == disconnected["text"],
                   "Leitura após reconexão não recuperou a escrita feita sem socket")
            e["reconnect"] = {"message_ids": [message["id"] for message in transcript], "messages": len(transcript)}
            old_cookie = client.cookie()
            client.logout()
            e["rest_after_logout"] = client.call(sim_path, expected=401)["error"]["code"]
            e["rest_old_cookie"] = Browser().call(sim_path, headers={"Cookie": old_cookie}, expected=401)["error"]["code"]
            with Cable(old_cookie) as denied:
                frame = denied.receive("disconnect unauthorized", lambda f: f.get("type") in {"disconnect", "welcome"})
                verify(frame.get("type") == "disconnect" and frame.get("reason") == "unauthorized",
                       "Cookie revogado abriu nova conexão Cable")
                e["cable_after_logout"] = {"type": frame["type"], "reason": frame["reason"]}
            before_correction = t.db.case(case_id)
            correction = {"expected_version": before_correction["version"], "category": "payouts", "priority": "basic",
                          "reason": "Correção sintética para verificar revogação da assinatura."}
            supervisor.call(staff_path + "/classification", target=WRITER, payload=correction,
                            headers=supervisor.write_headers(f"f07-{uid()}"))
            e["logout_positive_control"] = control.update(control_stream, case_id)
            observed_after = int(time.time())
            e["old_socket_observation"] = reconnected.revoked_stream_observation(revoked_stream, observed_after)
            e["before_outbox_restart"] = t.db.case(case_id)
            verify(len(audit(e["before_outbox_restart"], "case.classification.corrected")) == 1,
                   "Controle de revogação sem alteração auditada")
    finally:
        host("start", service="outbox")
    e["after_outbox_restart"] = t.await_case(
        case_id, "rodadas do caso de reconexão concluídas",
        lambda row: row["status"] == "resolved" and all(item["published"] for item in row["outbox"]),
    )
    e["drained_offsets"] = [
        {"record": record.position(), "offsets": t.consumed(record)}
        for topic in GROUPS for record in t.kafka.records(topic, key=case_id)
    ]


@scenario("05")
def failure_offset(t, e):
    # Um caso real fornece um envelope íntegro. Os resultados sintéticos têm
    # novos IDs e referenciam a rodada já concluída do mesmo caso.
    receipt = e["case"] = t.send(t.db.channel("aurora"), json_bytes(t.input()))
    case_id = receipt["case_id"]
    _, template, _, _ = t.applied_pair(case_id)
    partition = template.partition
    before = e["case_before"] = t.db.case(case_id)

    def get_offsets():
        return t.kafka.offsets(EVENTS_GROUP, "agent.events", partition)

    def failures(record):
        origin = {"group": EVENTS_GROUP, **record.position()}
        return [row for row in t.kafka.records("agent.failures", key=case_id)
                if row.data.get("origin") == origin or row.data.get("event_id") == record.data["event_id"]]

    def failed_body():
        return {**template.data, "event_id": uid()}

    def arm(label, data):
        t.arm(label, CALLBACK, mode="unavailable", field="event_id", value=data["event_id"])

    def make(data):
        return t.kafka.publish("agent.events", template.key, json_bytes(data), partition=partition)

    def failure_details(row, record):
        verify(row.data.get("origin") == {"group": EVENTS_GROUP, **record.position()} and
               row.data.get("event_id") == record.data["event_id"] and row.data.get("case_id") == case_id and
               row.data.get("correlation_id") == receipt["correlation_id"] and "503" in row.data.get("reason", ""),
               "Falha Kafka sem IDs ou motivo do callback 503")
        return {"record": row.position(), "body": row.data}

    until("partição sem backlog antes do ensaio", get_offsets, lambda row: row["backlog"] == 0)
    first = failed_body()
    arm("failure-publishable", first)
    first_before = e["publishable_before"] = get_offsets()
    first_record = make(first)
    e["publishable_input"] = {**first_record.position(), "event_id": first["event_id"]}
    after_first = e["publishable_after"] = t.consumed(first_record)
    first_messages = failures(first_record)
    first_http = e["publishable_http"] = t.history("failure-publishable")
    verify(len(first_messages) == 1 and [row["downstream"] for row in first_http] == [503] * 3 and
           first_before["committed_next_offset"] == first_record.offset and
           after_first["committed_next_offset"] == first_record.offset + 1 and after_first["backlog"] == 0,
           "Retentativas, publicação da falha ou offset fora da origem esperada")
    e["publishable_failure"] = failure_details(first_messages[0], first_record)

    pending = failed_body()
    arm("failure-blocked", pending)
    original_limit = e["original_failure_limit"] = t.kafka.failure_limit()
    host("failure_limit", enabled=True)
    try:
        until("limite do tópico de falhas ativo no Kafka", t.kafka.failure_limit, lambda value: value == "1")
        rejection = t.kafka.publish("agent.failures", f"canary-{uid()}".encode(), b"x" * 4096,
                                    partition=partition, expect_error="MSG_SIZE_TOO_LARGE")
        e["broker_rejection"] = {"topic": "agent.failures", "partition": partition, "error": rejection}
        before_pending = e["pending_before"] = get_offsets()
        pending_record = make(pending)
        e["pending_input"] = {**pending_record.position(), "event_id": pending["event_id"]}
        e["pending_http"] = pending_http = until("três HTTP 503 para o registro pendente",
                                                  lambda: t.history("failure-blocked"), lambda rows: len(rows) >= 3)
        verify([row["downstream"] for row in pending_http] == [503] * 3, "Falha HTTP do segundo registro divergiu")
        e["offset_after_http"] = get_offsets()
        verify(e["offset_after_http"]["committed_next_offset"] == pending_record.offset,
               "Consumidor confirmou o registro com agent.failures bloqueado")
        def stopped_or_advanced():
            state = host("state", service="events")
            offsets = get_offsets()
            if offsets["committed_next_offset"] != pending_record.offset or state["State"] == "exited":
                return state, offsets
            return None
        process, halted = until("processo encerra ou confirma o registro apesar da falha Kafka", stopped_or_advanced)
        e["bridge_exit"] = process
        e["pending_after_rejection"] = halted
        e["pending_failure_records"] = len(failures(pending_record))
        verify(process["State"] == "exited" and process["ExitCode"] not in (None, 0) and
               before_pending["committed_next_offset"] == pending_record.offset == halted["committed_next_offset"] and
               halted["backlog"] == 1 and e["pending_failure_records"] == 0,
               "Consumidor avançou a partição ou registrou a falha apesar da rejeição do broker")
        e["broker_fault_verified"] = True
    finally:
        host("failure_limit", enabled=False)
        e["restored_failure_limit"] = until(
            "limite original do tópico restaurado no Kafka", t.kafka.failure_limit, lambda value: value == original_limit,
        )
        # A ponte só reinicia abaixo, após guardar a condição observada.
        if not e.get("broker_fault_verified"):
            t.enabled("failure-blocked", False)
            host("start", service="events")

    tail = failed_body()
    try:
        tail_record = make(tail)
        e["tail_input"] = {**tail_record.position(), "event_id": tail["event_id"]}
        e["backlog_before_restart"] = get_offsets()
        verify(tail_record.offset == pending_record.offset + 1 and e["backlog_before_restart"]["backlog"] == 2 and
               e["backlog_before_restart"]["committed_next_offset"] == pending_record.offset,
               "Registro seguinte não ficou atrás da lacuna na mesma partição")
    finally:
        host("start", service="events")
    t.group_ready("agent.events")
    e["offset_after_recovery"] = recovered = t.consumed(tail_record)
    e["recovery_http"] = attempts = t.history("failure-blocked")
    recovered_failures = failures(pending_record)
    e["tail_receipt"] = t.db.receipt(tail["event_id"])
    e["case_after"] = after = t.db.case(case_id)
    verify(len(recovered_failures) == 1 and len(attempts) == 6 and
           all(row["downstream"] == 503 and row["body_sha256"] == hashlib.sha256(pending_record.raw).hexdigest()
               for row in attempts) and recovered["committed_next_offset"] == tail_record.offset + 1 and
           recovered["backlog"] == 0 and len(e["tail_receipt"]) == 1 and
           e["tail_receipt"][0]["disposition"] == "discarded" and
           not t.db.receipt(first["event_id"]) and not t.db.receipt(pending["event_id"]) and
           after["messages"] == before["messages"] and after["entries"] == before["entries"] and
           len(audit(after, "agent.result.discarded", tail["event_id"])) == 1,
           "Registro reentregue, retomada do offset ou efeitos de domínio divergiram")
    e["failure_after_recovery"] = failure_details(recovered_failures[0], pending_record)


def main(selected):
    kafka = Kafka()
    try:
        try:
            db = Database()
            trial = Trial(db, kafka)
            trial.ready()
        except (Blocked, Failed, DatabaseError, KafkaException) as error:
            print(f"Pré-condições da pilha: {error}", file=sys.stderr)
            for item in selected:
                print(json.dumps({"result": {**SCENARIOS[item][1], "status": "bloqueado", "reason": str(error),
                                             "evidence": {}}}), flush=True)
            return
        for item in selected:
            fn, metadata = SCENARIOS[item]
            evidence = {}
            try:
                fn(trial, evidence)
            except Failed as error:
                status, reason = "reprovado", str(error)
            except (Blocked, DatabaseError, KafkaException) as error:
                status, reason = "bloqueado", str(error)
            except Exception as error:
                traceback.print_exc(file=sys.stderr)
                status, reason = "bloqueado", f"Erro inesperado no verificador: {type(error).__name__}; confira stderr"
            else:
                status, reason = "aprovado", "Pós-condições observadas"
            print(json.dumps({"result": {**metadata, "status": status, "reason": reason, "evidence": evidence}}), flush=True)
        db.connection.close()
    finally:
        kafka.close()


if __name__ == "__main__":
    main(sys.argv[1:])

