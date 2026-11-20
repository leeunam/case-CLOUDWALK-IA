"""Observação de leitura e envio independente dos segundos turnos."""
import heapq
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from importlib.metadata import version
from urllib.request import urlopen

from kafka_probe import KafkaProbeError, probe, sample_kafka

from human import exercise_human
from protocol import API, BRANDS, DIRECTORY, KINDS, PIX, RESULTS, append, bytes_json, now_ms, webhook, write_json


SQL_SAMPLE = (DIRECTORY / "observations.sql").read_text()
SQL_SNAPSHOT = (DIRECTORY / "snapshot.sql").read_text()
SQL_FOLLOWUPS = """
SELECT e.source_event_id, e.support_case_id AS case_id, e.channel_id, c.correlation_id,
       m.id AS message_id, extract(epoch FROM m.created_at AT TIME ZONE 'UTC') * 1000 AS persisted_ms
FROM channel_entries e JOIN support_cases c ON c.id = e.support_case_id
JOIN case_messages customer ON customer.support_case_id = c.id AND customer.source_event_id = e.source_event_id
JOIN agent_turns t ON t.support_case_id = c.id AND t.through_sequence = customer.sequence
JOIN case_messages m ON m.support_case_id = c.id AND m.source_event_id = t.result_event_id::text AND m.author_type = 'ai'
WHERE e.source_event_id = ANY(%s) AND c.status = 'ai_active'
"""


def plain(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [plain(item) for item in value]
    # psycopg devolve UUID como objeto.
    return value if value is None or isinstance(value, (str, int, float, bool)) else str(value)


def database():
    from psycopg import connect
    from psycopg.rows import dict_row

    return connect(host="db", dbname="cloudwalk_development", user=os.environ["POSTGRES_USER"],
                   password=os.environ["POSTGRES_PASSWORD"], autocommit=True, connect_timeout=5,
                   options="-c default_transaction_read_only=on -c statement_timeout=3000",
                   row_factory=dict_row)


def discover(db):
    channels = {brand: {} for brand in BRANDS}
    for row in db.execute("""
        SELECT b.code, c.kind, c.id::text FROM channels c JOIN brands b ON b.id = c.brand_id
        WHERE c.active AND b.code = ANY(%s)
          AND EXISTS (SELECT FROM categories x WHERE x.brand_id = b.id AND x.code = 'pix' AND x.active)
        """, (list(BRANDS),)):
        channels[row["code"]][row["kind"]] = row["id"]
    if any(set(kinds) != set(KINDS) for kinds in channels.values()):
        raise RuntimeError("Seed sem as seis combinações de marca e canal com Pix ativo")
    return channels


def readiness(db, channels, config):
    started = now_ms()
    until = time.monotonic() + 90
    while time.monotonic() < until:
        try:
            with urlopen(f"{API}/api/v1/health", timeout=3) as response:
                if response.status == 200 and probe("ready", timeout=min(6, until - time.monotonic()))["ready"]:
                    break
        except Exception:  # Daemon e grupos ainda podem estar iniciando.
            pass
        time.sleep(1)
    else:
        raise RuntimeError("API e grupos Kafka não ficaram prontos em 90 s")
    warmed = now_ms()
    warm_source = f"{config['run_id']}-warmup"
    warm = webhook(channels["aurora"]["chat"], bytes_json({
        **PIX, "source_event_id": warm_source, "external_conversation_id": warm_source,
        "external_customer_id": warm_source,
    }))
    if warm["status"] != 202 or not warm.get("case_id"):
        raise RuntimeError(f"Aquecimento sem recibo HTTP 202 (status {warm['status']})")
    until = time.monotonic() + 45
    while time.monotonic() < until:
        if db.execute(SQL_FOLLOWUPS, ([warm_source],)).fetchone():
            try:
                sample = probe("sample", timeout=min(8, until - time.monotonic()))
            except KafkaProbeError:
                time.sleep(0.5)
                continue
            if all(row["lag"] == 0 for row in sample["partitions"]):
                write_json(RESULTS / "kafka-baseline.json", sample["offsets"])
                return {"readiness_started_ms": started, "warmup_started_ms": warmed,
                        "warmup_finished_ms": now_ms(), "warmup_case_id": warm["case_id"],
                        "versions": {"psycopg": version("psycopg"), **sample["versions"],
                                     "postgres": db.info.server_version}}
        time.sleep(0.5)
    raise RuntimeError("Aquecimento sem resposta persistida e offsets confirmados em 45 s")


class Followups:
    def __init__(self, plan):
        self.waiting = {row["initial"]["source_event_id"]: row["second"] for row in plan if row["second"]}
        self.due = []
        self.jobs = {}
        self.pool = ThreadPoolExecutor(max_workers=32)

    def poll(self, db, stop_ms):
        if self.waiting:
            for row in db.execute(SQL_FOLLOWUPS, (list(self.waiting),)):
                item = plain(row)
                body = self.waiting.pop(item["source_event_id"], None)
                if body:
                    seen = now_ms()
                    due = item["persisted_ms"] + 5000
                    event = {**item, "first_source_event_id": item["source_event_id"],
                             "source_event_id": body["source_event_id"], "observed_ms": seen, "due_ms": due}
                    heapq.heappush(self.due, (due, event["source_event_id"], event, body))
        while self.due and self.due[0][0] <= now_ms() < stop_ms:
            _, _, event, body = heapq.heappop(self.due)
            if len(self.jobs) >= 32:
                heapq.heappush(self.due, (event["due_ms"], event["source_event_id"], event, body))
                break
            future = self.pool.submit(webhook, event["channel_id"], bytes_json(body))
            self.jobs[future] = event
        self.flush()

    def flush(self):
        for future in list(self.jobs):
            if future.done():
                event = self.jobs.pop(future)
                append(RESULTS / "followups.jsonl", {**event, **future.result()})

    def finish(self):
        self.pool.shutdown()
        self.flush()
        for _, _, event, _ in self.due:
            append(RESULTS / "followups.jsonl", {**event, "reason": "janela_encerrada_antes_do_envio"})


def main():
    config = json.loads((RESULTS / "config.json").read_text())
    plan = json.loads((RESULTS / "plan.json").read_text())
    with database() as db, ThreadPoolExecutor(max_workers=2) as housekeeping:
        channels = discover(db)
        ready = readiness(db, channels, config)
        write_json(RESULTS / "ready.json", {"channels": channels, **ready})
        armed_at = now_ms()
        followups = Followups(plan)
        next_sql, next_kafka, next_followup = 0, 0, 0
        kafka_job = human_job = None
        deadline = None
        while not (RESULTS / "finish.json").exists():
            clock = now_ms()
            window = RESULTS / "window.json"
            if deadline is None and window.exists():
                deadline = json.loads(window.read_text())["end_ms"]
                if config["scenario"] == "human":
                    human_job = housekeeping.submit(exercise_human, database, deadline)
            if clock >= next_sql:
                start = now_ms()
                try:
                    record = plain(db.execute(SQL_SAMPLE).fetchone())
                except Exception as error:
                    record = {"error": type(error).__name__}
                append(RESULTS / "sql-samples.jsonl", {"sample_ms": start, "cost_ms": now_ms() - start, **record})
                next_sql = clock + 2000
            if clock >= next_kafka and (kafka_job is None or kafka_job.done()):
                kafka_job = housekeeping.submit(sample_kafka, RESULTS)
                next_kafka = clock + 5000
            if clock >= next_followup and (deadline is None or clock < deadline):
                start = now_ms()
                try:
                    followups.poll(db, deadline or armed_at + 120000)
                except Exception as error:
                    append(RESULTS / "observer-errors.jsonl", {"sample_ms": start, "error": type(error).__name__})
                if followups.waiting or followups.due or followups.jobs:
                    append(RESULTS / "followup-samples.jsonl", {"sample_ms": start, "cost_ms": now_ms() - start,
                                                               "waiting": len(followups.waiting)})
                next_followup = clock + 250
            time.sleep(0.05)
        followups.finish()
        snapshot_started = now_ms()
        snapshot = [plain(row) for row in db.execute(SQL_SNAPSHOT, (ready["warmup_case_id"],))]
        write_json(RESULTS / "persistence.json", {"sample_ms": snapshot_started, "cost_ms": now_ms() - snapshot_started,
                                                 "cases": snapshot})
        if human_job is not None:
            human_job.result()
        if kafka_job is not None:
            kafka_job.result()
        start = now_ms()
        try:
            evidence = probe("records", timeout=52)
        except KafkaProbeError as error:
            evidence = {"complete": False, "error": str(error)}
        evidence["cost_ms"] = now_ms() - start
        write_json(RESULTS / "observed.json", {"kafka_records": evidence})


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Exceções de driver podem carregar parâmetros de conexão.
        why = str(error) if type(error) is RuntimeError else type(error).__name__
        write_json(RESULTS / "observer-failure.json", {"at_ms": now_ms(), "reason": why})
        raise SystemExit(1)
