"""Aceite de reentrega/leases em um projeto de fixture descartável."""

import hashlib
import hmac
import json
import time
import uuid
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

from offline import LABEL, LEDGER_SECRET
from offline_check import (Browser, PIX, case_executions, fixture_posts, pilot, poll, public_evidence, require, settled,
                           verify_turn)


KAFKA_CODE = Path(__file__).with_name("offline_kafka.py").read_text(encoding="utf-8")


def kafka(stack, mode, *keys):
    command = ("exec", "-T", "requests", "python", "-c", KAFKA_CODE, mode, *keys)
    return json.loads(stack.run(*command, capture=True, timeout=40))


def new_case(browser, channel):
    return browser.send(channel, {"text": PIX, "category": "pix", "priority": "basic"}, str(uuid.uuid4()))


def interrupts(stack, browser, channel, mode):
    stack.run("kill", "-s", "SIGINT", "mock", capture=True)
    poll(lambda: "mock" not in stack.run("ps", "--status", "running", "--services", capture=True).splitlines(),
         "saída do consumidor antes da reinicialização")
    try:
        receipt = new_case(browser, channel)
        case_id = receipt["case_id"]
        initial = case_executions(stack, "id", case_id)[0]
        request_id = initial["request_event_id"]
        process = stack.invoke("run", "--rm", "--no-deps", "-T", "--entrypoint", "python", "mock",
                               "-c", KAFKA_CODE, mode, request_id, check=False, capture=True, timeout=30)
        require(process.returncode == 86 and f"interrupt={mode} request_event_id={request_id}" in process.stdout,
                f"Interrupção {mode} não observada (saída {process.returncode}).")
        interrupted = case_executions(stack, "id", case_id)[0]
        records = kafka(stack, "inspect", case_id)
        requests = records["agent.requests"]
        require(len(requests) == 1 and requests[0]["event_id"] == request_id, "Pedido ausente no Kafka.")
        offset = records["offsets"][str(requests[0]["partition"])]
        require(offset <= requests[0]["offset"], "Interrupção confirmou offset prematuramente.")
        require(not records["agent.failures"], "Interrupção gerou falha terminal prematuramente.")
        return receipt, interrupted, records, process
    finally:
        stack.run("start", "mock", capture=True)


def confirmed(stack, case_id, request_offset=None):
    result = kafka(stack, "inspect", case_id)
    if not result["agent.requests"]:
        return None
    latest = max(result["agent.requests"], key=lambda record: record["offset"])
    if request_offset is not None and latest["offset"] <= request_offset:
        return None
    if result["offsets"][str(latest["partition"])] > latest["offset"]:
        return result
    return None


def bridge_confirmed(records, expected_events):
    events = records["agent.events"]
    if not events or events != expected_events:
        return None
    offsets = records["event_offsets"]
    if all(offsets.get(str(record["partition"]), -1) > record["offset"] for record in events):
        return records
    return None


def test_publish_recovery(stack, browser, channel, mode):
    receipt, interrupted, before, process = interrupts(stack, browser, channel, mode)
    case_id = receipt["case_id"]
    request_id = interrupted["request_event_id"]
    before_events = before["agent.events"]
    require(interrupted["state"] == "result_saved", "Resultado não estava salvo no momento da interrupção.")
    require(len(before_events) == (1 if mode == "after_ack" else 0), "O ponto de ACK injetado divergiu.")
    row = poll(lambda: settled(stack, case_id, 1), "republicação e aplicação da proposta salva", seconds=25)
    require(row["result_sha256"] == interrupted["result_sha256"], "Reentrada mudou os bytes persistidos.")
    provider = row["usage"]["provider_response_id"]
    original_posts = (process.stdout + process.stderr).count(f"provider_response_id={provider}")
    require(original_posts == 1 and fixture_posts(stack)[provider] == 0, "O replay despachou inferência novamente.")
    recovered = poll(lambda: confirmed(stack, case_id), "offset posterior à publicação recuperada")
    events = recovered["agent.events"]
    require(len(events) == 1 + len(before_events) and {e["sha256"] for e in events} == {row["result_sha256"]}
            and {e["event_id"] for e in events} == {row["result_event_id"]},
            "Kafka não contém somente cópias idênticas do resultado salvo.")
    original_offset = max(record["offset"] for record in recovered["agent.requests"])
    replay = kafka(stack, "replay_request", case_id, request_id)
    duplicate = poll(lambda: confirmed(stack, case_id, original_offset), "offset do mesmo request_event_id reentregue")
    require(replay["sha256"] == row["outbox_sha256"] and duplicate["agent.events"] == events
            and fixture_posts(stack)[provider] == 0, "Pedido já publicado gerou nova execução ou publicação.")

    bridge = poll(lambda: bridge_confirmed(kafka(stack, "inspect", case_id), events),
                  "commit da ponte de retorno após a última cópia em agent.events", seconds=25)
    current = settled(stack, case_id, 1)
    require(current == row and not bridge["agent.failures"], "A ponte alterou o recibo ou registrou falha após a reentrega.")
    event_id = str(uuid.UUID(row["result_event_id"]))
    receipts = stack.sql(f"""SELECT jsonb_build_object('event_id', event_id, 'digest', body_sha256,
        'disposition', disposition) FROM agent_receipts WHERE event_id = '{event_id}'""")
    require(receipts == [{"event_id": event_id, "digest": row["result_sha256"], "disposition": "applied"}],
            "As cópias devem manter um único recibo aplicado com o digest original.")
    path = f"/api/v1/simulator/cases/{case_id}"
    verify_turn(current, browser.call(path + "/messages")["items"], browser.call(path),
                "aurora", "chat", "comprovante-pix", 1)
    return {"interruption": mode, "fixture_posts": original_posts, "case": public_evidence(current),
            "broker_before_restart": before, "broker_after_replay": duplicate,
            "bridge_after_last_event": bridge, "receipts_after_bridge": receipts}


def test_lost_start_ack(stack, browser, channel):
    receipt, started, before, process = interrupts(stack, browser, channel, "start_ack_lost")
    case_id = receipt["case_id"]
    provider = "offline-fixture-" + started["messages"][0]["id"]
    require(started["state"] == "started" and started["usage"] is None and not before["agent.events"],
            "Interrupção não preservou o start autorizado e sem resposta.")
    require(provider not in process.stdout + process.stderr, "Perder o ACK de start chamou a fixture.")
    active = kafka(stack, "inspect", case_id)
    request = active["agent.requests"][0]
    observed = case_executions(stack, "id", case_id)[0]
    require(observed["state"] == "started" and active["offsets"][str(request["partition"])] <= request["offset"],
            "Reinício confirmou offset enquanto o pedido ainda estava started.")

    def expired():
        row = case_executions(stack, "id", case_id)[0]
        return row if row["state"] == "unknown" else None

    unknown = poll(expired, "transição started para unknown após reinício", seconds=55)
    require(unknown["reserved_usd"] == started["reserved_usd"] and unknown["cost_usd"] is None and
            unknown["integration_status"] == "failed" and unknown["blocking_reason"] == "e01_dispatch_uncertain",
            "A expiração perdeu a reserva ou não mostrou a falha recuperável.")
    after = poll(lambda: confirmed(stack, case_id), "confirmação após estado unknown", seconds=25)
    require(not after["agent.events"] and not after["agent.failures"] and fixture_posts(stack)[provider] == 0,
            "O reinício despachou novamente ou publicou resposta incerta.")

    blocked = new_case(browser, channel)
    blocked_id = blocked["case_id"]
    records = poll(lambda: confirmed(stack, blocked_id), "offset do pedido recusado pela pausa", seconds=25)
    row = case_executions(stack, "id", blocked_id)[0]
    failures = records["agent.failures"]
    require(not records["agent.events"] and len(failures) == 1 and failures[0]["reason"] == "pilot_paused"
            and failures[0]["event_id"] == row["request_event_id"], "A pausa não produziu falha rastreável.")
    blocked_provider = "offline-fixture-" + row["messages"][0]["id"]
    require(row["state"] is None and row["blocking_reason"] == "e01_pilot_paused" and len(row["messages"]) == 1
            and fixture_posts(stack)[blocked_provider] == 0,
            "A pausa permitiu uma nova reserva ou alterou indevidamente o histórico.")
    return {"interruption": "start_ack_lost", "fixture_posts": 0, "started": public_evidence(started),
            "probe_while_started": active, "unknown": public_evidence(unknown), "probe_after_restart": after,
            "blocked": public_evidence(row), "blocked_failure": failures[0]}


def test_old_generation(stack, staff, matrix):
    original = next(row for row in matrix if row["scenario"] == "P2" and row["action"] == "resolve")
    case_id = original["case_id"]
    path = f"/api/v1/cases/{case_id}"
    previous = staff.call(path), staff.call(path + "/messages")
    latest = case_executions(stack, "id", case_id)[-1]
    require(original["generation"] < latest["case_generation"], "O evento escolhido não pertence a geração antiga.")
    replay = kafka(stack, "old_generation", case_id, original["result_event_id"])
    event_id = str(uuid.UUID(replay["event_id"]))
    sql = f"SELECT jsonb_build_object('disposition', disposition, 'sha256', body_sha256) FROM agent_receipts WHERE event_id = '{event_id}'"
    observed = poll(lambda: stack.sql(sql), "recibo da geração antiga")[0]
    require(observed == {"disposition": "discarded", "sha256": replay["sha256"]}, "Rails não descartou a geração antiga.")
    require(previous == (staff.call(path), staff.call(path + "/messages")), "Geração antiga alterou caso ou mensagens.")
    return {**replay, **observed, "case_id": case_id, "request_event_id": original["request_event_id"],
            "event_generation": original["generation"], "case_generation": latest["case_generation"]}


def test_nonce(stack, row):
    request_id = str(uuid.UUID(row["request_event_id"]))
    path = f"/internal/v1/e01/executions/{request_id}/claim"
    now, nonce = str(int(time.time())), str(uuid.uuid4())
    body = json.dumps({"request_sha256": row["request_sha256"], "owner_id": str(uuid.uuid4())}).encode()
    signed = f"{now}\n{nonce}\nPOST\n{path}\n".encode() + body
    signature = hmac.new(LEDGER_SECRET.encode(), signed, hashlib.sha256).hexdigest()
    headers = {"Content-Type": "application/json", "X-E01-Timestamp": now, "X-E01-Nonce": nonce,
               "X-E01-Signature": signature}
    client = build_opener(ProxyHandler({}))

    def post():
        try:
            response = client.open(Request(stack.api + path, data=body, headers=headers), timeout=6)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    require(post() == (200, {"state": "published"}), "Claim autenticado do resultado publicado falhou.")
    require(post() == (409, {"error": "nonce_reused"}), "Replay do nonce não retornou 409.")
    return {"request_event_id": request_id, "http_first": 200, "http_replay": 409, "error": "nonce_reused"}


def verify_faults(stack, report):
    stack.require_api_binding()
    require(report["mode"] == LABEL and report["project"] == stack.project and len(report["matrix"]) == 9,
            "Relatório deve ser a matriz fictícia deste mesmo projeto.")
    before = pilot(stack)
    require(not before["active_reservations"] and before["dispatch_count"] <= 21,
            "Projeto já está pausado ou sem saldo de start para a prova.")
    browser = Browser(stack.api)
    staff = Browser(stack.api)
    staff.supervise()
    channel = next(item["id"] for item in browser.simulator()
                   if item["brand_name"].startswith("Aurora") and item["type"] == "chat")
    nonce = test_nonce(stack, report["matrix"][0])
    obsolete = test_old_generation(stack, staff, report["matrix"])
    publication = [test_publish_recovery(stack, browser, channel, mode) for mode in ("before_ack", "after_ack")]
    lost_start = test_lost_start_ack(stack, browser, channel)
    after = pilot(stack)
    require(after["dispatch_count"] - before["dispatch_count"] == 3 and after["active_reservations"] == 1
            and after["unknown_count"] == 1 and Decimal(after["spent_usd"]) - Decimal(before["spent_usd"]) == Decimal("0.002640"),
            "Orçamento incompatível com os três starts injetados e dois POSTs fictícios conciliados.")
    return {"nonce_replay": nonce, "old_generation": obsolete, "publication": publication,
            "lost_start": lost_start, "pilot_before": before, "pilot_after": after}
