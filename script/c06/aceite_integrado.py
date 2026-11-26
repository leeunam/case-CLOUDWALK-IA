"""Matriz funcional C06 na demo local nova. Somente dados e credenciais sintéticos."""

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import shutil
import subprocess
import time
from uuid import uuid4

import requests
from playwright.sync_api import sync_playwright
from script import demo

HERE = Path(__file__).resolve().parent

PIX = "Sou do caixa da loja. Todos os pagamentos por Pix estão falhando. Estamos sem conseguir vender agora."
CASES = [
    (
        "direto",
        "Aurora Pagamentos",
        "chat",
        "O visor desta maquininha apagou durante a venda.",
        "terminal",
        "advanced",
    ),
    (
        "invalido",
        "Horizonte Negócios",
        "email",
        "Recebi uma mensagem, podem conferir?",
        "inexistente",
        "basic",
    ),
    (
        "categoria",
        "Aurora Pagamentos",
        "whatsapp",
        "Precisamos de outra via do comprovante da transferência Pix de ontem.",
        None,
        "basic",
    ),
    ("prioridade", "Horizonte Negócios", "email", PIX, "pix", None),
    ("ambos", "Aurora Pagamentos", "chat", PIX, None, None),
    (
        "revisao",
        "Horizonte Negócios",
        "whatsapp",
        "Oi. Podem me ajudar? Ainda não consegui explicar o que aconteceu.",
        None,
        "basic",
    ),
]


class Actor:
    def __init__(self, origin):
        self.origin = origin
        self.http = requests.Session()
        self.http.trust_env = False
        self.token = None
        self.identity(self.call("GET", "/api/v1/session"))

    def identity(self, data):
        self.token = data["csrf_token"]
        self.user = data["user"]

    def call(self, method, path, data=None, status=200, key=None):
        headers = {"Origin": self.origin}
        if self.token:
            headers["X-CSRF-Token"] = self.token
        if key:
            headers["Idempotency-Key"] = key
        response = self.http.request(method, self.origin + path, json=data, headers=headers, timeout=8)
        assert response.status_code == status, (method, path, response.status_code, status)
        return response.json()

    def login(self, email, password):
        self.identity(self.call("POST", "/api/v1/session", {"email": email, "password": password}))

    def wait_case(self, path, condition):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            case = self.call("GET", path)
            if condition(case):
                return case
            time.sleep(0.2)
        raise AssertionError((path, case["status"], case["integration_status"], case["blocking_reason"]))


def container(project, service, command, *, data=None, check=True):
    return subprocess.run(
        ["docker", "exec", "-i", f"{project}-{service}-1", *command],
        input=data,
        capture_output=True,
        check=check,
        timeout=40,
    )


def snapshot(project, case_id):
    cmd = [
        "psql",
        "-XAt",
        "-v",
        "ON_ERROR_STOP=1",
        "-v",
        f"case_id={case_id}",
        "-U",
        "cloudwalk",
        "-d",
        "cloudwalk_development",
        "-f",
        "-",
    ]
    return json.loads(container(project, "db", cmd, data=(HERE / "case_snapshot.sql").read_bytes()).stdout)


def readiness(project):
    code = "from urllib.request import urlopen; print(urlopen('http://localhost:8080/ready',timeout=2).read().decode())"
    return json.loads(container(project, "setfit", ["python", "-c", code]).stdout)


def resources(project, classifier):
    services = ["api", "worker", "db", "kafka", "outbox", "requests", "events", "mock", "web"]
    if classifier == "setfit":
        services.append("setfit")
    result = {}
    for service in services:
        data = (
            container(
                project,
                service,
                [
                    "cat",
                    "/sys/fs/cgroup/memory.current",
                    "/sys/fs/cgroup/memory.peak",
                    "/sys/fs/cgroup/cpu.stat",
                ],
            )
            .stdout.decode()
            .splitlines()
        )
        result[service] = {
            "memory_bytes": int(data[0]),
            "memory_peak_bytes": int(data[1]),
            "cpu_usec": int(next(line.split()[1] for line in data[2:] if line.startswith("usage_usec "))),
        }
    return result


def records(project, topic):
    cmd = [
        "/opt/kafka/bin/kafka-console-consumer.sh",
        "--bootstrap-server",
        "kafka:9092",
        "--topic",
        topic,
        "--from-beginning",
        "--timeout-ms",
        "3000",
        "--formatter-property",
        "print.key=true",
    ]
    result = container(project, "kafka", cmd, check=False)
    assert result.returncode == 0 or b"TimeoutException" in result.stderr
    rows = []
    for line in result.stdout.splitlines():
        key, raw = line.split(b"\t", 1)
        data = json.loads(raw)
        assert key.decode() == data["case_id"]
        rows.append((data, raw))
    return rows


def subscriptions(origin, actors, targets):
    js = """id => new Promise(resolve => {
      const socket = new WebSocket('ws://' + location.host + '/cable', 'actioncable-v1-json');
      const identifier = JSON.stringify({channel:'CaseUpdatesChannel',case_id:id,audience:'staff'});
      const timer = setTimeout(() => finish('timeout'),8000);
      function finish(value){clearTimeout(timer); socket.close(); resolve(value);}
      socket.onmessage = e => {const f=JSON.parse(e.data);
        if(f.type==='welcome') socket.send(JSON.stringify({command:'subscribe',identifier}));
        if(f.identifier===identifier && ['confirm_subscription','reject_subscription'].includes(f.type)) finish(f.type);
      };
      socket.onerror=()=>finish('error');
    })"""
    evidence = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome" if shutil.which("google-chrome") else None)
        for name in ("bia", "alex"):
            actor = actors[name]
            ctx = browser.new_context()
            ctx.add_cookies([{"name": c.name, "value": c.value, "url": origin} for c in actor.http.cookies])
            page = ctx.new_page()
            page.goto(origin, wait_until="domcontentloaded")
            visible = {c["id"] for c in actor.call("GET", "/api/v1/cases?limit=100")["items"]}
            for label, case_id in targets:
                allowed = name == "alex" or label == "categoria"
                status = 200 if allowed else 404
                assert (case_id in visible) == allowed
                actor.call("GET", f"/api/v1/cases/{case_id}", status=status)
                history = actor.call("GET", f"/api/v1/cases/{case_id}/messages", status=status)
                page.goto(origin + "/analista?case=" + case_id, wait_until="domcontentloaded")
                region = page.get_by_role("region", name="Histórico da conversa")
                marker = (
                    next(m["text"] for m in history["items"] if m["author"]["type"] == "ai")
                    if allowed
                    else history["error"]["message"]
                )
                region.get_by_text(marker, exact=False).first.wait_for(timeout=10000)
                if not allowed:
                    assert (
                        region.get_by_role("listitem").count() == 0
                        and page.locator("#case-context").count() == 0
                    )
                ws = page.evaluate(js, case_id)
                assert ws == ("confirm_subscription" if allowed else "reject_subscription"), (name, label, ws)
                evidence.append(
                    dict(
                        actor=name,
                        case_id=case_id,
                        list_visible=allowed,
                        detail=status,
                        history=status,
                        panel="resposta visível" if allowed else "erro genérico",
                        ws=ws,
                    )
                )
            ctx.close()
        browser.close()
    return evidence


def run(args):
    demo.ENV_FILE = args.credentials
    values = demo.read_env()
    passwords = json.loads(values["DEMO_PASSWORDS"])
    actors = {}
    for name in ("supervisor", "bia", "alex", "cris"):
        actor = actors[name] = Actor(args.origin)
        email = name + "@example.test"
        actor.login(email, passwords[email])
    supervisor = actors["supervisor"]
    customer = Actor(args.origin)
    customer.identity(customer.call("POST", "/api/v1/simulator/session", status=201))
    channels = {
        (c["brand_name"], c["type"]): c
        for c in customer.call("GET", "/api/v1/channels?audience=simulator")["items"]
    }
    evidence = {
        "base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE).decode().strip(),
        "project": args.project,
        "classifier": args.classifier,
        "cases": {},
        "rules": {},
        "resources_before": resources(args.project, args.classifier),
    }
    real = args.classifier == "setfit"
    if real:
        evidence["ready_before"] = readiness(args.project)

    def save():
        args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")

    queues = supervisor.call("GET", "/api/v1/case-filters")["queues"]
    for brand in {c["brand_id"] for c in channels.values()}:
        specialist = next(q["id"] for q in queues if q["brand_id"] == brand and q["name"] == "Especialistas")
        route = f"/api/v1/brands/{brand}/routing-rules"
        current = supervisor.call("GET", route)["items"]
        config = dict(queue_id=specialist, active=True, position=1, category="pix", priority=None)
        rule = next((r for r in current if all(r[k] == v for k, v in config.items())), None)
        evidence["rules"][brand] = rule or supervisor.call(
            "POST", route, config, status=201, key=str(uuid4())
        )
    save()
    for label, brand, kind, text, category, priority in CASES:
        if not real and label in ("prioridade", "ambos"):
            text += " Urgente."
        ch = channels[brand, kind]
        received = {k: v for k, v in (("category", category), ("priority", priority)) if v is not None}
        payload = {"text": text, **received}
        url = f"/api/v1/simulator/channels/{ch['id']}/messages"
        key = str(uuid4())
        receipt = customer.call("POST", url, payload, status=202, key=key)
        case_id = receipt["case_id"]
        path = "/api/v1/cases/" + case_id
        row = evidence["cases"][label] = {
            "receipt": {k: receipt[k] for k in ("case_id", "correlation_id", "channel_id")}
        }
        save()
        assert customer.call("POST", url, payload, status=202, key=key) == receipt
        conflict = customer.call(
            "POST", url, {**payload, "text": text + " Outra versão."}, status=409, key=key
        )
        assert conflict["error"]["code"] == "idempotency_conflict"
        case = supervisor.wait_case(
            path,
            lambda case: (
                case["status"] == "classification_review"
                or (case["status"] in ("ai_active", "human_active") and case["integration_status"] == "idle")
            ),
        )
        row["initial"] = db = snapshot(args.project, case_id)
        row["input_replay"] = [202, 409]
        save()
        cls = case["classification"]
        assert all(db[k] == v for k, v in cls.items())
        assert db["correlation_id"] == receipt["correlation_id"] and db["channel"] == kind
        if label in ("direto", "invalido"):
            assert db["requests"] == 0 and not db["attempts"]
        else:
            (attempt,) = db["attempts"]
            assert attempt["number"] == 1
            assert (attempt["provider"], attempt["provider_mode"]) == (
                ("setfit", "http") if real else ("jev", "fixture")
            )
            if real:
                assert attempt["calls"] == {
                    "category": int(category is None),
                    "priority": int(priority is None),
                }
            assert attempt["received"] == {"category": category, "priority": priority}
            assert any(a["attempt_id"] == attempt["id"] for a in db["audit"])
        if label in ("invalido", "revisao"):
            assert case["status"] == "classification_review" and not db["turns"]
            assert (
                len(db["messages"]) == 1 and cls["priority_source"] == "channel" and cls["category"] is None
            )
            if label == "invalido":
                assert case["blocking_reason"] == "invalid_input"
                continue
            assert attempt["disposition"] == "review" and not attempt["applied"]
            corrected = supervisor.call(
                "POST",
                path + "/classification",
                {
                    "category": "pix",
                    "priority": priority,
                    "reason": "Verificação sintética da classificação",
                    "expected_version": case["version"],
                },
                key=str(uuid4()),
            )
            assert corrected["classification"]["priority_source"] == "channel"
            supervisor.wait_case(
                path, lambda x: x["status"] == "ai_active" and x["integration_status"] == "idle"
            )
            row["after_correction"] = db = snapshot(args.project, case_id)
            assert db["category_source"] == "supervisor" and db["attempts"] == row["initial"]["attempts"]
            assert db["messages"][0] == row["initial"]["messages"][0]
            assert sum(a["type"] == "case.classification.corrected" for a in db["audit"]) == 1
        elif label != "direto":
            assert attempt["disposition"] == "applied"
            if real:
                assert attempt["outcome"] == "complete"
            expected = {
                "categoria": ("pix", "basic"),
                "prioridade": ("pix", "urgent"),
                "ambos": ("pix", "urgent"),
            }[label]
            assert (cls["category"], cls["priority"]) == expected
            for field in ("category", "priority"):
                assert cls[field + "_source"] == ("channel" if field in received else attempt["provider"])
        (turn,) = db["turns"]
        assert turn["request_version"] == (
            "1.1" if real and label in ("ambos", "categoria", "prioridade") else "1.0"
        )
        assert turn["outbox_published"] and turn["result_id"]
        (routing,) = [a for a in db["audit"] if a["type"] == "case.routing.applied"]
        assert routing["queue_id"] == db["queue_id"]
        if db["category"] == "pix":
            rule = evidence["rules"][ch["brand_id"]]
            assert (routing["rule_id"], routing["rule_version"], db["queue_id"]) == (
                rule["id"],
                rule["version"],
                rule["queue_id"],
            )
        else:
            assert routing["rule_id"] is None and db["queue"] == "general"
        history = customer.call("GET", f"/api/v1/simulator/cases/{case_id}/messages")["items"]
        assert [m["author"]["type"] for m in history] == ["customer", "ai"]
        assert history[0]["text"] == text and history[1]["text"].strip()
        row["visible_ai_message"] = history[1]["id"]
        if label == "direto":
            active = supervisor.wait_case(path, lambda c: c["status"] == "human_active")
            owner = next(
                actor
                for actor in actors.values()
                if actor.user.get("attendant_id") == active["assignee"]["id"]
            )
            assert text in active["handoff"]["summary"] and active["handoff"]["message_ids"] == [
                history[0]["id"]
            ]
            msg = {"text": "Mensagem sintética do responsável.", "expected_version": active["version"]}
            ikey = str(uuid4())
            reply = owner.call("POST", path + "/messages", msg, status=201, key=ikey)
            assert reply == owner.call("POST", path + "/messages", msg, status=201, key=ikey)
            resolved = owner.call(
                "POST",
                path + "/actions",
                {"type": "resolve", "expected_version": reply["case"]["version"]},
                key=str(uuid4()),
            )
            assert resolved["status"] == "resolved" and resolved["assignee"] is None
            row["resolved"] = snapshot(args.project, case_id)
            assert [m["author"] for m in row["resolved"]["messages"]] == ["customer", "ai", "human"]
            row["owner"] = owner.user["name"]
            row["handoff_context"] = active["handoff"]["message_ids"]
        save()
    targets = [(k, evidence["cases"][k]["receipt"]["case_id"]) for k in ("categoria", "prioridade")]
    evidence["access"] = subscriptions(args.origin, actors, targets)
    save()
    verify_messaging(args, evidence, values["DEMO_AGENT_EVENTS_SECRET"])
    save()
    if real:
        subprocess.run(["docker", "restart", args.project + "-setfit-1"], check=True, capture_output=True)
        inspect_restart(args.project, evidence)
        save()
    print("Matriz, Kafka, isolamento, handoff e correção verificados.")


def verify_messaging(args, evidence, agent_secret):
    requests_wire = records(args.project, "agent.requests")
    chosen = evidence["cases"]["ambos"]["receipt"]["case_id"]
    event, raw = next((e, r) for e, r in requests_wire if e["case_id"] == chosen)
    container(
        args.project,
        "kafka",
        [
            "/opt/kafka/bin/kafka-console-producer.sh",
            "--bootstrap-server",
            "kafka:9092",
            "--topic",
            "agent.requests",
            "--property",
            "parse.key=true",
        ],
        data=chosen.encode() + b"\t" + raw + b"\n",
    )
    results = records(args.project, "agent.events")
    replay = [r for e, r in results if e["case_id"] == chosen]
    assert len(replay) >= 2 and len(set(replay)) == 1
    now = str(int(time.time()))
    digest = hmac.new(agent_secret.encode(), now.encode() + b"." + replay[0], hashlib.sha256).hexdigest()
    cb = requests.post(
        args.origin + "/webhooks/v1/agent/events",
        data=replay[0],
        timeout=5,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": now,
            "X-Webhook-Signature": digest,
        },
    )
    assert cb.status_code == 200 and cb.json()["disposition"] == "duplicate"
    evidence["kafka"] = {}
    for label, row in evidence["cases"].items():
        ident = row["receipt"]["case_id"]
        reqs = [e for e, r in requests_wire if e["case_id"] == ident]
        res = [e for e, r in results if e["case_id"] == ident]
        if label == "invalido":
            assert len(reqs) == len(res) == 0
            continue
        record = row.get("after_correction", row["initial"])
        (turn,) = record["turns"]
        assert {e["event_id"] for e in reqs} == {turn["request_id"]}
        assert {e["event_id"] for e in res} == {turn["result_id"]}
        assert {e["payload"]["request_event_id"] for e in res} == {turn["request_id"]}
        assert all(
            e["turn_id"] == turn["id"] and e["correlation_id"] == row["receipt"]["correlation_id"]
            for e in reqs + res
        )
        assert all(e["schema_version"] == "1.0" for e in res)
        evidence["kafka"][label] = dict(
            request_id=turn["request_id"],
            result_id=turn["result_id"],
            request_version=reqs[0]["schema_version"],
            result_type=res[0]["event_type"],
            result_count=len(res),
        )
    after = snapshot(args.project, chosen)
    before = evidence["cases"]["ambos"]["initial"]
    assert before["messages"] == after["messages"] and before["turns"] == after["turns"]
    evidence["kafka_replay"] = {
        "case_id": chosen,
        "identical_result_bytes": True,
        "callback": cb.json(),
        "effects": 1,
    }
    if args.classifier == "setfit":
        evidence["ready_after"] = readiness(args.project)
        assert evidence["ready_before"]["worker_pid"] == evidence["ready_after"]["worker_pid"]
        assert (
            evidence["ready_after"]["counts"]["pipe_writes"]
            - evidence["ready_before"]["counts"].get("pipe_writes", 0)
            == 4
        )
    evidence["resources_after"] = resources(args.project, args.classifier)


def inspect_restart(project, evidence):
    deadline = time.monotonic() + 65
    while time.monotonic() < deadline:
        try:
            state = readiness(project)
            if state["ready"]:
                break
        except subprocess.CalledProcessError:
            pass
        time.sleep(0.5)
    else:
        raise AssertionError("SetFit não ficou pronto após reinício")
    name = project + "-setfit-1"
    lines = subprocess.check_output(["docker", "logs", "--timestamps", name]).decode().splitlines()
    events = [{"time": line.split(" ", 1)[0], **json.loads(line.split(" ", 1)[1])} for line in lines]
    assert sum(e["event"] == "ready" for e in events) >= 2
    evidence["sidecar_events"] = events
    before = evidence["cases"]["ambos"]["initial"]
    assert snapshot(project, before["case_id"]) == before
    evidence["restart"] = {"ready": state, "retained_case_id": before["case_id"], "same_snapshot": True}
    query = (
        "SELECT json_agg(json_build_object('kind',kind,'queues',metadata::json->'queues',"
        "'threads',metadata::json->'pool_size')) FROM solid_queue_processes WHERE kind='Worker'"
    )
    rows = json.loads(
        container(
            project, "db", ["psql", "-XtAc", query, "-U", "cloudwalk", "-d", "cloudwalk_development_queue"]
        ).stdout
    )
    assert sorted((r["queues"], r["threads"]) for r in rows) == [
        ("classification_setfit", 1),
        ("default,solid_queue_recurring", 3),
    ]
    evidence["queue_workers"] = rows
    evidence["image"] = (
        subprocess.check_output(["docker", "inspect", "--format", "{{.Image}}", name]).decode().strip()
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--origin", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--classifier", choices=("fixture", "setfit"), required=True)
    p.add_argument("--credentials", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    run(p.parse_args())
