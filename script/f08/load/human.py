"""Cliente operacional do cenário separado de handoff."""
import json
import os
import time
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener

from protocol import API, RESULTS, append, bytes_json, now_ms, webhook


class Browser:
    def __init__(self, email, password):
        self.client = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
        self.csrf = None
        status, session = self.call("/session")
        if status == 200:
            self.csrf = session["csrf_token"]
            status, session = self.call("/session", {"email": email, "password": password})
        if status != 200 or not session.get("user", {}).get("attendant_id"):
            raise RuntimeError(f"Login sintético indisponível (HTTP {status})")
        self.csrf = session["csrf_token"]
        self.attendant = session["user"]["attendant_id"]

    def call(self, path, data=None, key=None):
        headers = {"Content-Type": "application/json"}
        if self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        if key:
            headers["Idempotency-Key"] = key
        request = Request(f"{API}/api/v1{path}", data=bytes_json(data) if data is not None else None, headers=headers)
        try:
            try:
                response = self.client.open(request, timeout=3)
            except HTTPError as error:
                response = error
            with response:
                try:
                    return response.status, json.load(response)
                except ValueError:
                    return response.status, {}
        except (URLError, OSError):
            return 0, {}


HUMAN_CASES = """
SELECT c.id AS case_id, c.status, c.assignee_id, c.version, c.channel_id,
       conv.external_conversation_id, conv.external_customer_id, p.portfolio_limit,
       (SELECT count(*) FROM support_cases x WHERE x.assignee_id = c.assignee_id
         AND x.status IN ('human_active', 'waiting_customer', 'waiting_resumption')) AS portfolio,
       (SELECT count(*) FROM support_cases x WHERE x.assignee_id = c.assignee_id
         AND x.status = 'human_active') AS active_work
FROM support_cases c JOIN channel_conversations conv ON conv.id = c.channel_conversation_id
LEFT JOIN attendants a ON a.id = c.assignee_id
LEFT JOIN capacity_profiles p ON p.user_id = a.user_id AND p.active
WHERE conv.external_conversation_id LIKE %s AND c.status IN
  ('waiting_human', 'human_active', 'waiting_customer', 'waiting_resumption')
"""


def exercise_human(database, deadline):
    config = json.loads((RESULTS / "config.json").read_text())
    passwords = json.loads(os.environ["CLOUDWALK_DEMO_PASSWORDS"])
    actors = {}
    for email, password in passwords.items():
        if email != "supervisor@example.test":
            actor = Browser(email, password)
            actors[actor.attendant] = actor
    scripts = {}
    with database() as db:
        while now_ms() < deadline and not (RESULTS / "finish.json").exists():
            pending = db.execute(HUMAN_CASES, (config["run_id"] + "-%",)).fetchall()
            for row in pending:
                if now_ms() >= deadline:
                    break
                case_id = str(row["case_id"])
                if case_id not in scripts:
                    scripts[case_id] = {"step": 0, "after": 0, "state": None}
                progress = scripts[case_id]
                state = (row["status"], str(row["assignee_id"]))
                if progress["state"] != state:
                    append(RESULTS / "human.jsonl", {"at_ms": now_ms(), "case_id": case_id, "state": state[0],
                           "assignee_id": state[1], "portfolio": row["portfolio"], "active_work": row["active_work"],
                           "portfolio_limit": row["portfolio_limit"]})
                    progress["state"] = state
                if progress["after"] > now_ms():
                    continue
                actor = actors.get(state[1])
                step = progress["step"]
                if actor is None or state[0] != ("waiting_customer" if step == 2 else "human_active"):
                    continue
                case_path = f"/cases/{case_id}"
                expected = row["version"]
                key = f"{config['run_id']}-{case_id}-{step}"
                if step == 0:
                    status, _ = actor.call(case_path + "/messages", {
                        "expected_version": expected, "text": "Recebi o contexto e iniciei a análise.",
                    }, key)
                    wanted, operation = 201, "responder"
                elif step == 1:
                    status, _ = actor.call(case_path + "/actions", {
                        "expected_version": expected, "type": "wait_for_customer",
                        "text": "Pode me informar se reiniciou a maquininha?",
                    }, key)
                    wanted, operation = 200, "aguardar_cliente"
                elif step == 2:
                    response = webhook(row["channel_id"], bytes_json({
                        "source_event_id": key, "external_conversation_id": row["external_conversation_id"],
                        "external_customer_id": row["external_customer_id"], "text": "Sim, voltou a funcionar.",
                        "category": "terminal", "priority": "advanced",
                    }))
                    status = response["status"]
                    wanted, operation = 202, "retorno_cliente"
                elif step == 3:
                    status, _ = actor.call(case_path + "/actions", {
                        "expected_version": expected, "type": "resolve", "reason": "Atendimento sintético concluído.",
                    }, key)
                    wanted, operation = 200, "resolver"
                else:
                    continue
                append(RESULTS / "human.jsonl", {"at_ms": now_ms(), "case_id": case_id,
                       "operation": operation, "status": status, "expected_status": wanted})
                progress["step"] = step + 1 if status == wanted else 99
                progress["after"] = now_ms() + (5000 if step == 1 else 1000)
            time.sleep(1)
