"""Sobe e verifica o E01 local com transporte Feita fictício e dados isolados."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "e01-offline-password"
CHANNEL_SECRET = "e01-offline-channel"
EVENTS_SECRET = "e01-offline-events"
LEDGER_SECRET = "e01-offline-ledger"
LABEL = "E01 offline, fixture HTTP Feita, zero chamadas reais"


class Offline:
    def __init__(self, args):
        if not re.fullmatch(r"cloudwalk_e01_offline(?:_[a-z0-9]+)*", args.project):
            raise ValueError("O projeto precisa ter prefixo cloudwalk_e01_offline.")
        self.project = args.project
        self.api = f"http://127.0.0.1:{args.api_port}"
        self.command = ["docker", "compose", "--env-file", "/dev/null", "-p", self.project,
                        "-f", "compose.yml", "-f", "compose.demo.yml", "-f", "compose.e01.yml"]
        self.env = {key: os.environ[key] for key in ("PATH", "HOME", "XDG_RUNTIME_DIR") if key in os.environ}
        self.env.update(
            DEMO_RAILS_SECRET="e01-offline-rails-" + "7" * 64,
            DEMO_POSTGRES_PASSWORD="cloudwalk_local",
            DEMO_CHANNEL_SECRET=CHANNEL_SECRET,
            DEMO_AGENT_EVENTS_SECRET=EVENTS_SECRET,
            DEMO_AGENT_REQUESTS_SECRET="e01-offline-requests",
            DEMO_PASSWORDS=json.dumps({"supervisor@example.test": PASSWORD}),
            E01_LEDGER_SECRET=LEDGER_SECRET,
            E01_PREFLIGHT_FILE=str(Path(__file__).with_name("offline.preflight.json").resolve()),
            E01_RAILS_ENV="test",
            E01_BACKEND="luna_fixture",
            E01_API_PORT=str(args.api_port),
            E01_WEB_PORT=str(args.web_port),
        )

    def run(self, *arguments, capture=False, timeout=90):
        return self.invoke(*arguments, capture=capture, timeout=timeout).stdout

    def invoke(self, *arguments, capture=False, timeout=90, check=True):
        return subprocess.run([*self.command, *arguments], env=self.env, cwd=ROOT,
                              check=check, capture_output=capture, text=True, timeout=timeout)

    def sql(self, query):
        result = self.run("exec", "-T", "db", "psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-U", "cloudwalk",
                          "-d", "cloudwalk_test", "-c", query, capture=True, timeout=20)
        return [json.loads(line) for line in result.splitlines()]


def port(value):
    parsed = int(value)
    if not 1024 <= parsed <= 65535:
        raise argparse.ArgumentTypeError("Informe uma porta entre 1024 e 65535.")
    return parsed


def main():
    parser = argparse.ArgumentParser(description=f"{LABEL}. O canário real usa a operação E01-05.")
    parser.add_argument("--project", default="cloudwalk_e01_offline")
    parser.add_argument("--api-port", type=port, default=43309)
    parser.add_argument("--web-port", type=port, default=45379)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--matrix-report", type=Path)
    parser.add_argument("--correlation-id")
    parser.add_argument("--with-web", action="store_true")
    parser.add_argument("action", choices=("config", "up", "down", "status", "check", "faults"))
    args = parser.parse_args()
    if args.action == "faults" and not args.matrix_report:
        parser.error("faults exige --matrix-report com o resultado de check do mesmo projeto.")
    if args.report and args.report.exists():
        parser.error("Informe um caminho novo para o relatório.")
    try:
        stack = Offline(args)
    except ValueError as error:
        parser.error(str(error))
    print(LABEL, flush=True)
    if args.action == "config":
        stack.run("config", "--quiet")
    elif args.action == "up":
        services = ["api", "outbox", "events", "mock"]
        if args.with_web:
            services.append("web")
        stack.run("up", "--build", "--wait", "--wait-timeout", "150",
                  *services, timeout=480)
        print(f"API: {stack.api}")
    elif args.action == "down":
        stack.run("down")
    else:
        from offline_check import check, status
        if args.action == "faults":
            from offline_faults import verify_faults
            result = verify_faults(stack, json.loads(args.matrix_report.read_bytes()))
        elif args.action == "check":
            result = check(stack)
        else:
            result = status(stack, args.correlation_id)
        output = json.dumps({"mode": LABEL, "project": stack.project, **result}, ensure_ascii=False, indent=2) + "\n"
        if args.report:
            with args.report.open("x", encoding="utf-8") as report:
                report.write(output)
        print(output, end="")


if __name__ == "__main__":
    main()
