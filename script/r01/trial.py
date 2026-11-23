"""Cada linha JSON é uma observação. Exige prova positiva de transferência e progresso."""
import hashlib
import json
import platform
import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import ExitStack
from pathlib import Path

from confluent_kafka import libversion, version
from http_client import REQUESTS
from observe import GROUPS, Blocked, Database, Kafka, until, verify
from scenarios import Trial, audit, json_bytes, types

TOPIC = {"mock": "agent.requests", "events": "agent.events"}
DRAIN_SECONDS = 120


def emit(stage, **values):
    print(json.dumps({"stage": stage, **values}, ensure_ascii=False), flush=True)


class Member:
    def __init__(self, role, label, directory):
        self.trace = directory / f"{role}-{label}.jsonl"
        self.trace.touch()
        self.log = self.trace.with_suffix(".log")
        with self.log.open("w") as stream:
            self.process = subprocess.Popen([sys.executable, "-B", "/r01/member.py", role, label, str(self.trace)],
                                            stdout=stream, stderr=stream)

    def events(self):
        return [json.loads(line) for line in self.trace.read_text().splitlines(keepends=True) if line.endswith("\n")]

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=5)
        print(self.log.read_text(), file=sys.stderr)


def spawn(stack, directory, role, label):
    member = Member(role, label, directory)
    stack.callback(member.close)
    return member


def ownership(t, topic, partition, client):
    desc = t.kafka.admin.describe_consumer_groups([GROUPS[topic]], request_timeout=5)[GROUPS[topic]].result()
    for member in desc.members:
        if desc.state.name == "STABLE" and member.client_id == client and any(
            p.topic == topic and p.partition == partition for p in member.assignment.topic_partitions
        ):
            return member.member_id
    return None


def drained(t):
    offsets = [t.kafka.offsets(group, topic, p) for topic, group in GROUPS.items() for p in range(3)]
    return offsets if all(x["backlog"] == 0 for x in offsets) else None


def transfer(t, role, directory, stack):
    topic = TOPIC[role]
    group = GROUPS[topic]
    companion = "mock" if role == "events" else "events"
    spawn(stack, directory, companion, "companion")
    a = spawn(stack, directory, role, "A")
    for name in GROUPS:
        t.group_ready(name)
    channel = t.db.channel("aurora")
    old_members = [until("A com atribuição inicial", lambda p=p: ownership(t, topic, p, "A"))
                   for p in range(3)]
    data = t.input()
    receipt = t.send(channel, json_bytes(data))
    case_id = receipt["case_id"]
    original = until("efeito aceito por A", a.events, timeout=30)[0]
    start = time.monotonic()

    def wait(label, condition):
        return until(label, condition, timeout=max(0, DRAIN_SECONDS - (time.monotonic() - start)))

    p, n = original["partition"], original["offset"]
    before = t.kafka.offsets(group, topic, p)
    verify((before["committed_next_offset"] in (None, n)) and before["backlog"] >= 1, "offset inicial inesperado")
    # A escreveu o efeito e parou antes de o processo poder confirmar.
    b = spawn(stack, directory, role, "B")
    replay = wait("reentrega ao par", b.events)[0]
    verify(all(original[k] == replay[k] for k in original if k != "pid"), "bytes/identidade/origem divergentes")
    peer_id = wait("B com atribuição vigente", lambda: ownership(t, topic, p, "B"))
    def peer_offset():
        offset = t.kafka.offsets(group, topic, p)
        return offset if offset["committed_next_offset"] == n + 1 else None
    confirmed = wait("confirmação de B", peer_offset)
    emit("transferencia", role=role, original=original, receipt=receipt, before=before, old_member=old_members[p], peer=peer_id,
         replay=replay, confirmed=confirmed)
    os.kill(a.process.pid, signal.SIGCONT)
    wait("A reconheceu perda da associação no commit", lambda: "reingresso grupo=" in a.log.read_text())
    # Retira somente o par B. O PID de A precisa reassumir e confirmar a continuação.
    b.process.terminate()
    b.process.wait(timeout=5)
    new_id = wait("A reassumiu a partição", lambda: ownership(t, topic, p, "A"))
    wait("primeira resposta persistida", lambda: types(t.db.case(case_id)) == ["customer", "ai"])
    t.send(channel, json_bytes({**data, "source_event_id": str(uuid.uuid4()), "text": "Entendi."}))
    def resolved():
        row = t.db.case(case_id)
        return row if row["status"] == "resolved" else None
    row = wait("resolução", resolved)
    offsets = wait("lag zero nos dois grupos", lambda: drained(t))
    later = a.events()[-1]
    marker = f"particao={p} offset={later['offset']} proximo={later['offset'] + 1}"
    verify(any("primeiro progresso" in line and marker in line for line in a.log.read_text().splitlines())
           and later["pid"] == original["pid"] and later["offset"] == n + 1, "sem primeiro progresso no mesmo PID")
    verify(types(row) == ["customer", "ai", "customer", "ai"] and row["entries"] == 2, "efeito duplicado ou ausente")
    replies = [r for r in t.kafka.records("agent.events", key=case_id)
               if r.data["event_type"] == "agent.reply.proposed"]
    verify(len(replies) == (2 if role == "mock" else 1) and len({r.raw for r in replies}) == 1,
           "replay do mock gerou bytes divergentes ou quantidade inesperada")
    receipts = t.db.receipt(replies[0].data["event_id"])
    verify(len(receipts) == 1 and receipts[0]["disposition"] == "applied" and
           receipts[0]["sha256"] == hashlib.sha256(replies[0].raw).hexdigest(),
           "recibo persistido difere do retorno confirmado")
    verify(time.monotonic() - start <= DRAIN_SECONDS, "drenagem fora da janela")
    emit("recuperado", role=role, member=new_id, progress=later, offsets=offsets, case=row, agent_receipts=receipts,
         elapsed=time.monotonic()-start, deadline=DRAIN_SECONDS)


def canonical(t, directory, stack):
    channel = t.db.channel("aurora")
    cases = [t.send(channel, json_bytes(t.input()))["case_id"] for _ in range(2)]
    # A ponte publica normalmente. Os dois grupos estão ausentes até a expiração real.
    supervisor, _ = t.staff("supervisor")
    for case_id, action in zip(cases, ["retry_agent", "force_handoff"]):
        row = until("timeout do produto", lambda: t.db.case(case_id),
                    lambda x: x["integration_status"] == "failed" and bool(audit(x, "agent.result.expired")), timeout=90)
        command = {"type": action, "expected_version": row["version"], "reason": "Recuperação R01"}
        if action == "force_handoff":
            command["summary"] = "Cliente aguarda retorno"
        supervisor.call(f"/api/v1/cases/{case_id}/actions", payload=command,
                        headers=supervisor.write_headers(str(uuid.uuid4())))
    human = until("responsável humano", lambda: t.db.case(cases[1]), lambda x: x["status"] == "human_active")
    for role in TOPIC:
        spawn(stack, directory, role, "canonical")
    retried = until("nova rodada aplicada", lambda: t.db.case(cases[0]), lambda x: types(x) == ["customer", "ai"])
    offsets = until("drenagem após ação canônica", lambda: drained(t))
    assigned = t.db.case(cases[1])
    verify(len(retried["outbox"]) == 2 and len(audit(retried, "agent.result.discarded")) == 1 and
           len(audit(assigned, "agent.result.discarded")) == 1 and
           all(human[k] == assigned[k] for k in ("assignee_id", "assignment_generation", "messages", "status")),
           "retorno obsoleto ou recuperação incompleta")
    emit("recuperacao_canonica", retry=retried, handoff=assigned, offsets=offsets)


def main():
    limits = {}
    for key in ("cpu.max", "memory.max"):
        path = Path("/sys/fs/cgroup") / key
        limits[key] = path.read_text().strip() if path.exists() else None
    emit("parametros", drain_seconds=DRAIN_SECONDS, session_ms=6000, heartbeat_ms=1500, partitions=3,
         roles=list(TOPIC), classification="pronta", agent="mock determinístico", processes="A, B e acompanhante",
         cpu_affinity=len(os.sched_getaffinity(0)), limits=limits, python=platform.python_version(),
         confluent_kafka=version()[0], librdkafka=libversion()[0])
    t = Trial(Database(), Kafka())
    try:
        until("tópicos com líderes", t.kafka.topics_ready)
        until("seed disponível", lambda: t.db.channel("aurora", optional=True))

        def routes_ready():
            try:
                health = t.http.call("/api/v1/health", expected=(200, 503))
                t.http.call("/webhooks/v1/agent/requests", target=REQUESTS, expected=501)
                return health.get("status") == "ok"
            except Blocked:
                return False

        until("Rails e ponte HTTP prontos", routes_ready)
        until("worker conectado", lambda: t.db.connected("worker", "cloudwalk_development_queue"))
        until("outbox conectado", lambda: t.db.connected("outbox", "cloudwalk_development"))
        for role in TOPIC:
            with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
                transfer(t, role, Path(tmp), stack)
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            canonical(t, Path(tmp), stack)
    finally:
        t.kafka.close()
        t.db.connection.close()
    emit("resultado", status="aprovado")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        emit("resultado", status="inconclusivo" if not isinstance(error, AssertionError) else "reprovado",
             reason=str(error))
        raise
