"""Percorre a instalação local pelos cliques do simulador e confere a persistência."""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import sync_playwright

from script import demo
from script.classification_acceptance.aceite_integrado import Actor, readiness, records, resources, snapshot

CASES = (
    (
        "direto",
        "Aurora Pagamentos",
        "WhatsApp",
        "terminal",
        "advanced",
        "A tela da maquininha do quiosque ficou preta durante o último pagamento.",
    ),
    (
        "complemento",
        "Horizonte Negócios",
        "E-mail",
        "pix",
        "",
        "Urgente. O Pix parou em todos os caixas da padaria. Nenhum pagamento entra e as vendas estão totalmente interrompidas.",
    ),
    (
        "revisao",
        "Aurora Pagamentos",
        "Chat",
        "",
        "",
        "Boa tarde. Abri este atendimento para conversar, mas ainda não tenho detalhes.",
    ),
)


def cli(*args):
    return subprocess.check_output(args, text=True).strip()


def environment(project):
    web = project + "-web-1"
    checkout = cli(
        "docker",
        "inspect",
        "-f",
        '{{index .Config.Labels "com.docker.compose.project.working_dir"}}',
        web,
    )
    if Path(checkout).resolve() != Path.cwd():
        raise ValueError("Abra a raiz do clone que iniciou este projeto.")
    address = cli("docker", "port", web, "5173/tcp")
    if not re.fullmatch(r"127\.0\.0\.1:[0-9]+", address):
        raise ValueError("O simulador deve estar publicado somente em loopback.")
    demo.ENV_FILE = Path.cwd() / ".env.demo.local"
    passwords = json.loads(demo.read_env()["DEMO_PASSWORDS"])
    origin = "http://" + address
    staff = {}
    for name in ("supervisor", "bia", "alex", "cris"):
        actor = staff[name] = Actor(origin)
        email = name + "@example.test"
        actor.login(email, passwords[email])
    return origin, staff


def browser_entry(page, origin, brand, channel, category, priority, text):
    page.goto(origin)
    page.get_by_role("combobox", name="Marca", exact=True).select_option(label=brand)
    page.get_by_role("radio", name=channel, exact=True).check()
    page.get_by_text("Classificação da mensagem", exact=False).first.click()
    page.get_by_role("combobox", name="Categoria", exact=True).select_option(
        value=category
    )
    page.get_by_role("combobox", name="Prioridade", exact=True).select_option(
        value=priority
    )
    page.get_by_label("Mensagem", exact=True).fill(text)
    with page.expect_response(
        lambda r: r.request.method == "POST" and "/simulator/channels/" in r.url
    ) as sent:
        page.get_by_role("button", name="Enviar mensagem").click()
    response = sent.value
    assert response.status == 202, response.status
    assert response.request.post_data_json == {
        k: v
        for k, v in dict(text=text, category=category, priority=priority).items()
        if v
    }
    return response.json()


def run(args, origin, staff):
    result = {
        "base": cli("git", "rev-parse", "HEAD"),
        "project": args.project,
        "mode": args.classifier,
        "cases": {},
    }
    supervisor = staff["supervisor"]
    real = args.classifier == "setfit"
    if real:
        result["ready_before"] = readiness(args.project)
        assert result["ready_before"]["ready"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            channel="chrome" if shutil.which("google-chrome") else None
        )
        for label, brand, channel, category, priority, text in CASES:
            page = browser.new_page()
            receipt = browser_entry(
                page, origin, brand, channel, category, priority, text
            )
            ident = receipt["case_id"]
            path = "/api/v1/cases/" + ident
            expected_status = {
                "direto": "human_active",
                "complemento": "ai_active",
                "revisao": "classification_review",
            }[label]
            case = supervisor.wait_case(
                path,
                lambda c: (
                    c["status"] == expected_status and c["integration_status"] == "idle"
                ),
            )
            before = snapshot(args.project, ident)
            assert before["correlation_id"] == receipt["correlation_id"]
            assert (
                before["brand"]
                == {"Aurora Pagamentos": "aurora", "Horizonte Negócios": "horizonte"}[
                    brand
                ]
            )
            assert (
                before["channel"]
                == {"WhatsApp": "whatsapp", "E-mail": "email", "Chat": "chat"}[channel]
            )
            row = result["cases"][label] = {"receipt": receipt, "before": before}
            if label == "direto":
                assert not before["attempts"] and before["requests"] == 0
                assert (before["category_source"], before["priority_source"]) == (
                    "channel",
                    "channel",
                )
                assert case["handoff"]["message_ids"] == [before["messages"][0]["id"]]
                owner = next(
                    actor
                    for actor in staff.values()
                    if actor.user.get("attendant_id") == case["assignee"]["id"]
                )
                reply = owner.call(
                    "POST",
                    path + "/messages",
                    {
                        "text": "Vou conferir o visor do quiosque.",
                        "expected_version": case["version"],
                    },
                    status=201,
                    key=str(uuid4()),
                )
                owner.call(
                    "POST",
                    path + "/actions",
                    {"type": "resolve", "expected_version": reply["case"]["version"]},
                    key=str(uuid4()),
                )
                row["owner"] = owner.user["name"]
            else:
                (attempt,) = before["attempts"]
                assert (attempt["provider"], attempt["provider_mode"]) == (
                    ("setfit", "http") if real else ("jev", "fixture")
                )
                if real:
                    assert attempt["calls"] == {
                        "category": int(not category),
                        "priority": int(not priority),
                    }
                    assert (
                        attempt["package_sha256"]
                        == "224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872"
                    )
                if label == "complemento":
                    assert (before["category"], before["priority"]) == ("pix", "urgent")
                    assert (before["category_source"], before["priority_source"]) == (
                        "channel",
                        attempt["provider"],
                    )
                    assert attempt["disposition"] == "applied"
                else:
                    assert attempt["disposition"] == "review" and not before["turns"]
                    supervisor.call(
                        "POST",
                        path + "/classification",
                        {
                            "category": "payouts",
                            "priority": "basic",
                            "reason": "Cliente confirmou uma dúvida de repasse na reprodução local.",
                            "expected_version": case["version"],
                        },
                        key=str(uuid4()),
                    )
                    supervisor.wait_case(
                        path,
                        lambda c: (
                            c["status"] == "ai_active"
                            and c["integration_status"] == "idle"
                        ),
                    )
            final = row["final"] = snapshot(args.project, ident)
            history = page.request.get(
                f"{origin}/api/v1/simulator/cases/{ident}/messages"
            )
            assert history.ok
            messages = history.json()["items"]
            assert messages[0]["text"] == text and any(
                m["author"]["type"] == "ai" and m["text"] for m in messages
            )
            assert [m["id"] for m in messages] == [m["id"] for m in final["messages"]]
            if label == "direto":
                assert (
                    final["status"] == "resolved"
                    and messages[-1]["author"]["type"] == "human"
                )
            if label == "revisao":
                assert (final["category_source"], final["priority_source"]) == (
                    "supervisor",
                    "supervisor",
                )
            for name, allowed in (("bia", brand.startswith("Aurora")), ("alex", True)):
                status = 200 if allowed else 404
                visible = {
                    c["id"]
                    for c in staff[name].call("GET", "/api/v1/cases?limit=100")["items"]
                }
                assert (ident in visible) == allowed
                for suffix in ("", "/messages"):
                    staff[name].call("GET", path + suffix, status=status)
                row.setdefault("access", {})[name] = {
                    "listed": ident in visible,
                    "detail_and_history_http": status,
                }
            page.close()
        browser.close()
    for topic in ("agent.requests", "agent.events"):
        wire = [event for event, _ in records(args.project, topic)]
        for row in result["cases"].values():
            case = row["final"]
            (turn,) = case["turns"]
            matched = [e for e in wire if e["case_id"] == case["case_id"]]
            assert matched and all(
                e["correlation_id"] == case["correlation_id"]
                and e["turn_id"] == turn["id"]
                for e in matched
            )
            if topic == "agent.events":
                assert all(
                    e["payload"]["request_event_id"] == turn["request_id"]
                    for e in matched
                )
            event_id = turn["request_id" if topic == "agent.requests" else "result_id"]
            assert {e["event_id"] for e in matched} == {event_id}
            row.setdefault("kafka", {})[topic] = {
                "event_id": event_id,
                "records": len(matched),
                "schema": matched[0]["schema_version"],
            }
    if real:
        result["ready_after"] = readiness(args.project)
        assert (
            result["ready_after"]["worker_pid"] == result["ready_before"]["worker_pid"]
        )
    result["resources"] = resources(args.project, args.classifier)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    if not __debug__:
        parser.error("Use Python sem otimização para executar as verificações.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--classifier", choices=("setfit", "fixture"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--after-restart",
        type=Path,
        help="JSON salvo antes de derrubar e subir a pilha",
    )
    args = parser.parse_args()
    if not re.fullmatch(r"cloudwalk_demo(?:_[a-z0-9]+)+", args.project):
        parser.error("Escolha um projeto de demonstração local próprio.")
    if args.output.exists():
        parser.error("Escolha um arquivo de saída novo.")
    origin, staff = environment(args.project)
    if args.after_restart:
        prior = json.loads(args.after_restart.read_text())
        if set(prior["cases"]) != {case[0] for case in CASES}:
            parser.error(
                "O registro inicial deve conter os três atendimentos do roteiro."
            )
        assert (prior["project"], prior["mode"], prior["base"]) == (
            args.project,
            args.classifier,
            cli("git", "rev-parse", "HEAD"),
        )
        result = {"project": args.project, "base": prior["base"], "cases": {}}
        for label, row in prior["cases"].items():
            ident = row["receipt"]["case_id"]
            fresh = snapshot(args.project, ident)
            assert fresh == row["final"]
            path = "/api/v1/cases/" + ident
            public = staff["supervisor"].call("GET", path)
            messages = staff["supervisor"].call("GET", path + "/messages")["items"]
            assert public["status"] == fresh["status"]
            assert [m["id"] for m in messages] == [m["id"] for m in fresh["messages"]]
            result["cases"][label] = {
                "case_id": ident,
                "status": public["status"],
                "messages": len(messages),
                "snapshot_identical": True,
            }
    else:
        result = run(args, origin, staff)
    with args.output.open("x") as out:
        json.dump(result, out, indent=2, ensure_ascii=False)
        out.write("\n")
    print(f"{len(result['cases'])} atendimentos verificados em {args.output}")


if __name__ == "__main__":
    main()
