"""Reconcilia o plano, recibos HTTP, persistência e offsets; gera JSON e Markdown."""
import hashlib
import json
import math
import re
import uuid
from collections import Counter, defaultdict
from datetime import datetime

from protocol import bytes_json, rows, utc, write_json


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def distribution(values):
    data = sorted(value for value in values if value is not None)
    return {"unit": "ms", "n": len(data),
            **{f"p{p}": data[math.ceil(len(data) * p / 100) - 1] if data else None for p in (50, 95)}}


def all_measured(*checks):
    """Uma contraprova basta, enquanto a aprovação exige todas as observações."""
    if False in checks:
        return False
    return None if None in checks else True


def index_cases(cases):
    result = defaultdict(list)
    for case in cases:
        for entry in case["entries"] or []:
            result[(case["channel_id"], entry["source_event_id"])].append((case, entry))
    return result


def turn_messages(case, source):
    messages = case.get("messages") or []
    customer = [message for message in messages if message["author"] == "customer"
                and message["source_event_id"] == source]
    turns = [turn for turn in case.get("turns") or [] if customer and turn["through_sequence"] == customer[0]["sequence"]]
    turn = turns[0] if turns else {}
    result_id = turn.get("result_event_id")
    expected_result_id = (str(uuid.uuid5(uuid.NAMESPACE_URL, "cloudwalk:mock-agent-v1:" + turn["request_event_id"]))
                          if turn else None)
    replies = [message for message in messages if message["author"] == "ai"
               and message["source_event_id"] is not None and message["source_event_id"] in {result_id, expected_result_id}]
    return customer, turns, expected_result_id, replies


def reconcile(body, channel, attempt, persisted, failures, snapshot, *, human=False):
    source = body["source_event_id"]
    attempt = attempt or {}
    sent = attempt.get("sent_ms")
    http_202 = attempt.get("status") == 202
    planned_digest = hashlib.sha256(bytes_json(body)).hexdigest()
    matching = persisted.get((channel, source), [])
    case, entry = matching[0] if matching else ({}, {})
    customer, turns, expected_result_id, replies = turn_messages(case, source)
    turn = turns[0] if turns else {}
    result_id = turn.get("result_event_id")
    case_audits = case.get("audits") or []
    audits = [audit for audit in case_audits if expected_result_id and audit["event_id"] == expected_result_id]
    types = Counter(audit["type"] for audit in audits)
    effects = {
        "case_open_audits": sum(audit["type"] == "case.opened" for audit in case_audits),
        "channel_received_audits": sum(audit["type"] == "channel.message.received" and
                                       audit.get("source_event_id") == source for audit in case_audits),
        "entries": len(matching), "customer_messages": len(customer), "turns": len(turns),
        "outboxes": sum(bool(item.get("outbox_event_id")) for item in turns), "ai_messages": len(replies),
        "applied_audits": sum(types[kind] for kind in ("agent.reply.proposed", "agent.resolve.proposed",
                                                       "agent.handoff.proposed")),
    }
    duplicate = any(count > 1 for count in effects.values())
    case_identity_wrong = (http_202 and matching and
                           (attempt.get("case_id") != case["case_id"] or
                            attempt.get("correlation_id") != case["correlation_id"]))
    loss = bool(snapshot and ((http_202 and not matching) or (matching and not customer) or
                              (turn.get("disposition") == "applied" and not replies)))
    published = turn.get("published_ms")
    persisted_ms = min((message["created_ms"] for message in replies), default=None)
    failure = (turn.get("failed_ms") is not None or
               case.get("integration_status") == "failed" and not replies or
               "agent.result.discarded" in types or
               any(event in failures for event in (expected_result_id, turn.get("request_event_id")) if event))
    expected_audit = ("agent.handoff.proposed" if human else
                      "agent.resolve.proposed" if source.endswith("-2") else "agent.reply.proposed")
    resolution_required = expected_audit == "agent.resolve.proposed"
    resolution_applied = case.get("status") == "resolved" and case.get("resolved_ms") is not None
    complete = ((not resolution_required or resolution_applied) and all(count == 1 for count in effects.values())
                and published is not None and types[expected_audit] == 1
                and turn.get("disposition") == "applied" and result_id == expected_result_id
                and not (duplicate or case_identity_wrong or entry["sha256"] != planned_digest))
    if not snapshot:
        state = "indisponível"
    elif duplicate or case_identity_wrong or loss or (matching and entry["sha256"] != planned_digest):
        state = "inconsistente"
    elif complete:
        state = "concluído"
    elif failure:
        state = "falho"
    elif matching:
        state = "pendente"
    elif sent is None:
        state = "não enviado"
    else:
        state = "ausente sem aceite"
    timestamps = {"ai_message": persisted_ms, "turn_completed": turn.get("completed_ms"),
                  "outbox_published": published,
                  "result_audit": next((a.get("at_ms") for a in audits if a["type"] == expected_audit), None)}
    if resolution_required:
        timestamps["case_resolved"] = case.get("resolved_ms") if resolution_applied else None
    return {
        "expected_result_type": expected_audit, "effect_timestamps_ms": timestamps,
        "last_effect_ms": max(timestamps.values()) if all(t is not None for t in timestamps.values()) else None,
        "resolution_required": resolution_required, "resolution_applied": resolution_applied if resolution_required else None,
        "source_event_id": source, "channel_id": channel, "case_id": case.get("case_id"),
        "correlation_id": case.get("correlation_id"), "http_case_id": attempt.get("case_id"),
        "http_correlation_id": attempt.get("correlation_id"), "sent_ms": sent, "http_status": attempt.get("status"),
        "finished_ms": attempt.get("finished_ms"), "request_ms": attempt.get("elapsed_ms"),
        "error": attempt.get("error") or attempt.get("error_code"),
        "turn_id": turn.get("id"), "generation": turn.get("generation"), "through_sequence": turn.get("through_sequence"),
        "request_event_id": turn.get("request_event_id"), "result_event_id": result_id,
        "expected_result_event_id": expected_result_id, "expected_body_sha256": planned_digest,
        "actual_body_sha256": entry.get("sha256"), "expected_effects": {name: 1 for name in effects},
        "effects": effects if snapshot else None, "customer_message_ids": [m["id"] for m in customer],
        "ai_message_ids": [m["id"] for m in replies], "ai_persisted_timestamp_ms": persisted_ms,
        "observed_ms": attempt.get("observed_ms"), "due_ms": attempt.get("due_ms"), "reason": attempt.get("reason"),
        "support_case_status": case.get("status"), "blocking_reason": case.get("blocking_reason"),
        "state": state, "confirmed_loss": loss, "duplicate_effect": duplicate,
        "identity_inconsistent": bool(case_identity_wrong),
    }


def kafka_offsets(row, records_by_id):
    offsets = {}
    for topic, event_id, event_type in (
        ("agent.requests", row["request_event_id"], "agent.turn.requested"),
        ("agent.events", row["expected_result_event_id"], row["expected_result_type"]),
    ):
        offsets[topic] = [{"partition": entry["partition"], "offset": entry["offset"]}
                          for entry in records_by_id.get((topic, event_id), [])
                          if event_id and entry.get("event_type") == event_type
                          and all(row[k] and entry.get(k) == row[k] for k in ("turn_id", "case_id", "correlation_id"))
                          and (topic == "agent.requests" or entry.get("request_event_id") == row["request_event_id"])
                          and isinstance(entry.get("partition"), int) and isinstance(entry.get("offset"), int)]
    return offsets


def evidence(output, manifest, plan, events):
    snapshot = load(output / "persistence.json", None)
    cases = snapshot["cases"] if snapshot else []
    existing = index_cases(cases)
    ready = load(output / "ready.json", {})
    channels = ready.get("channels", {})
    initial_events = {row["source_event_id"]: row for row in events if row["type"] == "initial"}
    second_events = {row["source_event_id"]: row for row in rows(output / "followups.jsonl")}
    kafka = list(rows(output / "kafka-records.jsonl"))
    failures = {row["event_id"] for row in kafka if row["topic"] == "agent.failures" and row["event_id"]}
    records_by_id = defaultdict(list)
    for record in kafka:
        records_by_id[(record["topic"], record["event_id"])].append(record)
    observations = []
    for item in plan:
        channel = channels.get(item["brand"], {}).get(item["kind"])
        one = reconcile(item["initial"], channel, initial_events.get(item["initial"]["source_event_id"]), existing,
                        failures, bool(snapshot), human=manifest["scenario"] == "human")
        one.update(run_id=manifest["run_id"], turn_number=1, index=item["index"], brand=item["brand"], kind=item["kind"])
        observations.append(one)
        if item["second"]:
            two = reconcile(item["second"], channel, second_events.get(item["second"]["source_event_id"]),
                            existing, failures, bool(snapshot))
            two.update(run_id=manifest["run_id"], turn_number=2, index=item["index"], brand=item["brand"], kind=item["kind"],
                       initial_case_id=one["case_id"])
            if two["case_id"] and two["case_id"] != one["case_id"]:
                two.update(state="inconsistente", identity_inconsistent=True)
            if two["sent_ms"] is None and not two["reason"] and snapshot:
                two["reason"] = ("primeira_resposta_ausente_na_janela" if not one["ai_message_ids"] else
                                 "primeira_resposta_observada_tarde_ou_envio_não_executado")
            observations.append(two)
    attributed = defaultdict(set)
    known_entries = {(row["channel_id"], row["source_event_id"]) for row in observations}
    for row in observations:
        attributed[row["case_id"]].update(row["customer_message_ids"], row["ai_message_ids"])
    # Chat e atendimento humano também geram entradas fora do plano do k6.
    extra_sources = defaultdict(set)
    for event in events:
        if event["type"] == "chat_write":
            source = event["source_event_id"]
            matching = existing.get((event["channel_id"], source), [])
            if len(matching) == 1:
                extra_sources[matching[0][0]["case_id"]].add(source)
    for event in rows(output / "human.jsonl"):
        if event.get("operation") == "retorno_cliente":
            case_id = event["case_id"]
            extra_sources[case_id].add(f"{manifest['run_id']}-{case_id}-2")
    for case in cases:
        case_id = case["case_id"]
        entry_ids = {entry["source_event_id"] for entry in case["entries"] or []}
        for source in extra_sources[case_id] & entry_ids:
            customer, _, _, replies = turn_messages(case, source)
            attributed[case_id].update(m["id"] for m in customer[:1] + replies[:1])
            known_entries.add((case["channel_id"], source))
        case["unplanned_entries"] = sorted(source for source in entry_ids
                                          if (case["channel_id"], source) not in known_entries)
        case["unattributed_messages"] = [
            {"case_id": case_id, **{k: message[k] for k in ("id", "sequence", "author", "source_event_id")}}
            for message in case["messages"] or [] if message["author"] in ("customer", "ai")
            and message["id"] not in attributed[case_id]]
    for row in observations:
        row["kafka_offsets"] = kafka_offsets(row, records_by_id)
    return observations, kafka, cases


def times(groups):
    sent = [row for row in groups if row["sent_ms"] is not None]
    accepted = [row for row in sent if row["http_status"] == 202]
    persisted = [row for row in sent if row["ai_persisted_timestamp_ms"] is not None]
    offsets = [row["ai_persisted_timestamp_ms"] - row["sent_ms"] for row in persisted]
    return {
        "planned": len(groups), "offered": len(sent), "http_202": len(accepted),
        "accepted_with_ids": sum(bool(row["http_case_id"] and row["http_correlation_id"]) for row in accepted),
        "acceptance_of_planned": len(accepted) / len(groups) if groups else None,
        "acceptance_of_offered": len(accepted) / len(sent) if sent else None,
        "non_202": len(sent) - len(accepted),
        "latency_accept": distribution([row["request_ms"] for row in accepted]),
        "latency_persisted": distribution([value for value in offsets if value >= 0]),
        "negative_clock_deltas": sum(value < 0 for value in offsets),
        "statuses": dict(Counter(str(row["http_status"]) for row in sent)),
        "error_codes": dict(Counter(str(row["error"]) for row in sent if row["error"] is not None)),
        "timeouts": sum(str(row["error"]) in {"1050", "TimeoutError", "timeout"} for row in sent),
        "states": dict(Counter(row["state"] for row in groups)),
    }


def human_summary(events, cases, window):
    active = [item["active_work"] for item in events if item.get("active_work") is not None]
    portfolios = [item["portfolio"] for item in events if item.get("portfolio") is not None]
    operations = Counter(f"{item['operation']}:{item['status']}" for item in events if "operation" in item)
    return {"states_observed": dict(Counter(item["state"] for item in events if "state" in item)),
            "max_active_per_analyst_observed": max(active, default=None),
            "max_portfolio_per_analyst_observed": max(portfolios, default=None),
            "above_active_profile": sum(item.get("active_work", 0) > (item.get("advanced_terminal_limit") or 0)
                                        for item in events),
            "above_portfolio_limit": sum(item.get("portfolio_limit") is not None
                                         and item["portfolio"] > item["portfolio_limit"] for item in events),
            "operation_statuses": dict(operations),
            "operation_errors": sum(item["status"] != item["expected_status"] for item in events if "operation" in item),
            "resolved": sum(case["status"] == "resolved" and case["resolved_ms"] <= window.get("end_ms", 0)
                            for case in cases)}


def chat_recovery(events, probe, indexed):
    if not probe or probe["status"] != 202 or probe.get("opened_case") is not False:
        return False, False
    timeline = [event for event in events if event.get("client") == probe["client"]]
    write_at = timeline.index(probe)
    transitions = [row for row in timeline[:write_at] if row["type"] in {"subscription_confirmed", "subscription_closed"}]
    if len(transitions) < 2:
        return False, False
    confirmed, closed = transitions[-2:]
    signature = closed.get("identifier")
    cursor = closed.get("cursor", 0)
    case_id = probe["case_id"]
    if not (confirmed["type"] == "subscription_confirmed" and closed["type"] == "subscription_closed"
            and closed.get("reason") == "prova_reconexao" and signature and cursor > 0
            and confirmed.get("identifier") == signature and confirmed.get("case_id") == closed.get("case_id") == case_id
            and closed["at_ms"] <= probe["sent_ms"]):
        return False, False
    matching = indexed.get((probe["channel_id"], probe["source_event_id"]), [])
    ids = {message["id"] for case, _ in matching if len(matching) == 1 and case["case_id"] == case_id
           and case["correlation_id"] == probe["correlation_id"] for message in case["messages"] or []
           if message["source_event_id"] == probe["source_event_id"] and message["author"] == "customer"
           and message["sequence"] > cursor}
    reconnected = False
    for row in timeline[write_at + 1:]:
        if row["type"] == "subscription_closed":
            break
        if row["type"] == "subscription_confirmed":
            reconnected = row.get("reconnect") and row.get("identifier") == signature and row.get("case_id") == case_id
        if reconnected and row["type"] == "chat_read" and row["reason"] == "reconnect":
            return True, bool(row["status"] == 200 and row.get("identifier") == signature and row["case_id"] == case_id
                              and row["after_sequence"] == cursor and row["through_sequence"] > cursor
                              and ids.intersection(row.get("recovered_ids", [])))
    return True, False


def chat_summary(events, config, window, cases):
    start = window.get("start_ms", 0) + config["ramp_seconds"] * 1000
    end = window.get("arrivals_end_ms", 0)
    clients = set()
    unique = set()
    steady_peak = 0
    integral = 0
    last = start
    transitions = []
    for row in sorted(events, key=lambda item: item.get("at_ms", 0)):
        name = row["type"]
        if name not in {"subscription_confirmed", "subscription_closed"}:
            continue
        at = row["at_ms"]
        if at >= start and last < end:
            steady_peak = max(steady_peak, len(clients))
            integral += max(0, min(at, end) - last) * len(clients)
            last = min(at, end)
        if name == "subscription_confirmed":
            clients.add(row["client"])
            unique.add(row["client"])
        else:
            clients.discard(row["client"])
        if start <= at <= end:
            steady_peak = max(steady_peak, len(clients))
        transitions.append({"at_ms": at, "confirmed_concurrent": len(clients)})
    integral += max(0, end - last) * len(clients)
    traffic = [row for row in events if row["type"] == "chat_write" and not row["preparation"]]
    preparation = [row for row in events if row["type"] == "chat_write" and row["preparation"]]
    accepted = [row for row in traffic if row["status"] == 202]
    indexed = index_cases(cases)
    traffic_reconciliation = []
    for row in traffic + preparation:
        source = row["source_event_id"]
        matching = indexed.get((row["channel_id"], source), [])
        case = matching[0][0] if len(matching) == 1 else {}
        customer = [message["id"] for message in case.get("messages") or []
                    if message["source_event_id"] == source and message["author"] == "customer"]
        traffic_reconciliation.append({"client": row["client"], "key": row["key"], "source_event_id": source,
                                       "http_status": row["status"], "case_id": row.get("case_id"),
                                       "correlation_id": row.get("correlation_id"), "channel_id": row["channel_id"],
                                       "receipt_mismatches": [key for key in ("case_id", "correlation_id")
                                                              if case and row.get(key) is not None
                                                              and row[key] != case[key]],
                                       "stored_case_id": case.get("case_id"), "customer_message_ids": customer,
                                       "stored_correlation_id": case.get("correlation_id"), "entry_count": len(matching)})
    reads = [row for row in events if row["type"] == "chat_read" and row["reason"] == "reconnect"]
    probe = next((row for row in preparation if row.get("reconnect_probe_write")), None)
    disconnected_write, probe_recovered = chat_recovery(events, probe, indexed)
    steady_seconds = config["hold_seconds"]
    expected_slots = sum(max(0, math.ceil(steady_seconds / config["period_seconds"] - offset / config["target"]))
                         for offset in range(config["target"]))
    return {"target": config["target"], "unique_confirmed_clients": len(unique), "peak_confirmed_steady": steady_peak,
            "average_confirmed_steady": integral / max(1, end - start) if end else None,
            "target_rate_messages_per_s": config["target"] / config["period_seconds"],
            "emitted": len(traffic), "emitted_per_s": len(traffic) / steady_seconds if end else None,
            "expected_messages_at_target": expected_slots,
            "emission_shortfall": max(0, expected_slots - len(traffic)),
            "recovery_probe_wrote_while_disconnected": disconnected_write,
            "recovery_probe_read_new_messages": probe_recovered,
            "accepted": len(accepted), "opened_cases": sum(row["opened_case"] for row in accepted),
            "continued_cases": sum(not row["opened_case"] for row in accepted),
            "preparation_writes": len(preparation), "http_statuses": dict(Counter(str(r["status"]) for r in traffic)),
            "socket_errors": sum(row["type"] == "socket_error" for row in events),
            "setup_errors": sum(row["type"] == "setup_error" for row in events),
            "sessions_reconfirmed": sum(row.get("reconnect", False) for row in events),
            "recovery_reads": len(reads), "recovery_reads_ok": sum(row["status"] == 200 for row in reads),
            "recovered_messages": sum(row["recovered"] for row in reads if row["status"] == 200),
            "skipped_slots_observed": sum(row["count"] for row in events if row["type"] == "chat_slots_skipped"),
            "confirmed_timeline": transitions, "traffic_reconciliation": traffic_reconciliation}


MEMORY_UNITS = {"B": 1, "kB": 1000, "MB": 1000 ** 2, "GB": 1000 ** 3, "TB": 1000 ** 4,
                "KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3, "TiB": 1024 ** 4}


def parse_memory(value):
    match = re.fullmatch(r"([0-9.]+)\s*([A-Za-z]+)", value.strip())
    return round(float(match[1]) * MEMORY_UNITS[match[2]]) if match and match[2] in MEMORY_UNITS else None


def resource_summary(samples):
    service_samples = defaultdict(list)
    for sample in samples:
        for container in sample.get("containers", []):
            name = re.sub(r"^cloudwalk_f08_load-", "", container["container"])
            service = name.split("-", 1)[0]
            service_samples[service].append(container)
    services = {}
    for service, containers in service_samples.items():
        cpu = [float(item["cpu_percent"].rstrip("%")) for item in containers
               if re.fullmatch(r"[0-9.]+%", item["cpu_percent"])]
        ram = [parse_memory(item["ram_used_limit"].split("/")[0]) for item in containers]
        limits = [parse_memory(item["ram_used_limit"].split("/")[1]) for item in containers
                  if "/" in item["ram_used_limit"]]
        services[service] = {"samples": len(containers), "cpu_percent_peak": max(cpu, default=None),
                             "ram_bytes_peak": max((value for value in ram if value is not None), default=None),
                             "ram_limit_bytes_observed": sorted({value for value in limits if value is not None})}
    host_cpu = [row["host_cpu_busy_percent"] for row in samples if "host_cpu_busy_percent" in row]
    host_memory = [1024 * (row["host_memory_kib"]["MemTotal"] - row["host_memory_kib"]["MemAvailable"])
                   for row in samples if {"MemTotal", "MemAvailable"} <= row.get("host_memory_kib", {}).keys()]
    expected = ("api", "worker", "outbox", "requests", "events", "mock", "db", "kafka", "generator")
    missing = [name for name in expected if services.get(name, {}).get("cpu_percent_peak") is None
               or services[name].get("ram_bytes_peak") is None]
    missing_host = [name for name, data in (("cpu", host_cpu), ("ram", host_memory)) if not data]
    return {"expected_services": expected, "missing_services": missing, "missing_host": missing_host,
            "sample_errors": dict(Counter(row["error"] for row in samples if row.get("error"))),
            "samples_in_window": len(samples), "sufficient": not missing and not missing_host,
            "per_service": services, "host_cpu_busy_percent_peak": max(host_cpu, default=None),
            "host_ram_used_bytes_peak": max(host_memory, default=None)}


def docker_ms(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000 if value else None


def summarize(output, manifest, plan, events, reconciled, kafka, cases):
    config = manifest["parameters"]
    window = manifest.get("window", {})
    sql = list(rows(output / "sql-samples.jsonl"))
    lag = list(rows(output / "kafka-lag.jsonl"))
    resources = list(rows(output / "resources.jsonl"))
    k6 = load(output / "k6-summary.json", {})
    initial = [row for row in reconciled if row["turn_number"] == 1]
    second = [row for row in reconciled if row["turn_number"] == 2]
    accepted = [row for row in reconciled if row["http_status"] == 202]
    duration = sum(seconds for _, seconds in config["stages"])
    clock_errors = [row["db_clock_ms"] - row["sample_ms"] for row in sql if "db_clock_ms" in row]
    unsafe_sql = [row for row in sql if "error" in row]
    snapshot = load(output / "persistence.json", None)
    in_window = lambda value: value is not None and window.get("start_ms", 0) <= value <= window.get("end_ms", 0)
    def sampled_in_window(row):
        return in_window(row["sample_ms"]) and in_window(row["sample_ms"] + row["cost_ms"])

    sql_during_window = [row for row in sql if sampled_in_window(row)]
    good = [row for row in sql_during_window if "error" not in row]
    lag_during_window = [row for row in lag if sampled_in_window(row)]
    lag_good = [row for row in lag_during_window if row["total_lag"] is not None]
    tail = good[-1] if good else {}
    tail_lag = lag_good[-1] if lag_good else {}
    tail_lag_fresh = bool(lag_during_window and tail_lag and lag_during_window[-1]["sample_ms"] == tail_lag["sample_ms"]
                          and window["end_ms"] - tail_lag["sample_ms"] <= 12000)
    tail_sql_fresh = bool(tail and sql_during_window[-1] is tail and window["end_ms"] - tail["sample_ms"] <= 5000)
    fault = manifest.get("fault", {})
    stopped = docker_ms(fault.get("stopped_state", {}).get("FinishedAt"))
    started = docker_ms(fault.get("started_state", {}).get("StartedAt"))
    ready = next((row["sample_ms"] + row["cost_ms"] for row in lag_good
                  if started and row["sample_ms"] >= started), None)
    drained = next((row["sample_ms"] + row["cost_ms"] for row in good if ready and row["sample_ms"] >= ready
                    and row["outbox_pending"] == row["cases_waiting_processing"] == row["outbox_failed"] == 0
                    and any(point["total_lag"] == 0 and point["sample_ms"] >= ready
                            and 0 <= row["sample_ms"] - (point["sample_ms"] + point["cost_ms"]) <= 7000
                            for point in lag_good)), None)
    failure_offsets = {(row["topic"], row["event_id"]) for row in kafka
                       if row["event_id"] and row["topic"] == "agent.failures"}
    positions = defaultdict(set)
    for record in kafka:
        if record["event_id"] and record["topic"] != "agent.failures":
            if isinstance(record.get("partition"), int) and isinstance(record.get("offset"), int):
                positions[(record["topic"], record["event_id"])].add((record["partition"], record["offset"]))
    duplicates = {key: len(locations) for key, locations in positions.items()}
    measured_turns = [row for row in reconciled if row["http_status"] == 202 or row["case_id"]]
    missing_effect_times = [row for row in measured_turns if row["state"] == "concluído" and row["last_effect_ms"] is None]
    available_effect_times = [stamp for row in measured_turns if row["state"] == "concluído"
                              for stamp in row["effect_timestamps_ms"].values() if stamp is not None]
    known_turns_on_time = all(row["state"] == "concluído" for row in measured_turns) and all(
        in_window(stamp) for stamp in available_effect_times)
    latest_work = max([window.get("arrivals_end_ms", 0), *available_effect_times])
    initial_metrics, second_metrics = times(initial), times(second)
    dropped = (k6.get("dropped_iterations") or {}).get("count", 0) if k6 else None
    outbox_final = [turn for case in cases for turn in case["turns"] or []
                    if turn["outbox_event_id"] and turn["published_ms"] is None and turn["failed_ms"] is None]
    dangling_cases = [case for case in cases if case["integration_status"] in {"pending_delivery", "awaiting_result"}]
    failures = []
    gaps = []
    # Um efeito fora do prazo é prova independente mesmo se faltar uma leitura final.
    # Nesse caso, a última leitura dentro da janela não poderia suceder o efeito.
    tail_after = latest_work if latest_work <= window.get("end_ms", 0) else window.get("arrivals_end_ms", 0)
    sql_final = tail_sql_fresh and tail["sample_ms"] >= tail_after
    lag_final = tail_lag_fresh and tail_lag["sample_ms"] >= tail_after
    backlog_drained = all_measured(
        (known_turns_on_time and not outbox_final and not dangling_cases) if snapshot else None,
        None if missing_effect_times else True,
        all(tail[k] == 0 for k in ("outbox_pending", "cases_waiting_processing", "outbox_failed", "cases_failed"))
        if sql_final else None,
        tail_lag["total_lag"] == 0 if lag_final else None,
    )
    if window and not config["chat"]:
        if missing_effect_times:
            gaps.append(f"carimbos de efeitos indisponíveis para {len(missing_effect_times)} turnos concluídos")
        if not sql_final:
            gaps.append("leitura SQL final indisponível ou fora do intervalo exigido")
        if not lag_final:
            gaps.append("leitura final de lag indisponível ou fora do intervalo exigido")
    unattributed = [message for case in cases for message in case["unattributed_messages"]]
    unplanned = [{"case_id": case["case_id"], "source_event_id": source}
                 for case in cases for source in case["unplanned_entries"]]
    resource_metrics = resource_summary([row for row in resources if sampled_in_window(row)])
    if window and not snapshot:
        gaps.append("snapshot de persistência indisponível")
    if window and not resource_metrics["sufficient"]:
        missing = resource_metrics["missing_services"] + [f"host/{field}" for field in resource_metrics["missing_host"]]
        gaps.append("CPU/RAM com cobertura insuficiente (" + ", ".join(missing) + ")")
    missing_pairs = [row for row in reconciled if row["state"] == "concluído" and not all(row["kafka_offsets"].values())]
    if window and missing_pairs:
        gaps.append(f"captura Kafka sem par request/resultado causal para {len(missing_pairs)} turnos concluídos")
    goals = {}
    if config["chat"]:
        chat = chat_summary(events, config["chat"], window, cases)
        if chat["peak_confirmed_steady"] < chat["target"]:
            failures.append("patamar de assinaturas simultâneas não atingido")
        if chat["emission_shortfall"]:
            failures.append("padrão de emissão planejado para chat ficou abaixo do alvo")
        if chat["setup_errors"] or chat["socket_errors"] or chat["emitted"] != chat["accepted"]:
            failures.append("falhas em sessão, conexão ou escrita")
        if not chat["recovery_probe_read_new_messages"]:
            failures.append("recuperação pelo cursor não observada")
        if any(item["entry_count"] > 1 for item in chat["traffic_reconciliation"]):
            failures.append("múltiplas entradas SQL para a identidade de uma escrita de chat")
        if any(item["receipt_mismatches"] for item in chat["traffic_reconciliation"]):
            failures.append("vínculo do recibo de chat diverge da entrada SQL")
        if snapshot and any(item["http_status"] == 202 and (
                item["entry_count"] != 1 or len(item["customer_message_ids"]) != 1 or
                item["case_id"] != item["stored_case_id"] or item["correlation_id"] != item["stored_correlation_id"])
                for item in chat["traffic_reconciliation"]):
            failures.append("escritas 202 de chat sem efeito único reconciliado")
        if unattributed or unplanned:
            failures.append("mensagens ou entradas SQL de chat sem atribuição")
    else:
        chat = None
        clean_effects = all(row["state"] != "inconsistente" for row in accepted) and not unattributed and not unplanned
        classification_used = any(row["classification_requests"] or row["classification_attempts"] for row in good)
        second_completed = (second_metrics["planned"] == second_metrics["states"].get("concluído", 0)
                            if snapshot or not second else None)
        p95 = initial_metrics["latency_accept"]["p95"]
        if initial_metrics["http_202"] > initial_metrics["latency_accept"]["n"]:
            gaps.append("latência de aceite ausente em recibos 202")
            p95 = None
        goals = {
            "p95_aceite_ate_500_ms": p95 <= 500 if p95 is not None else None,
            "aceite_inicial_minimo_99_pct_do_plano": (initial_metrics["acceptance_of_planned"] or 0) >= 0.99,
            "efeitos_sem_duplicacao_ou_perda_entre_aceitos": (clean_effects if snapshot and
                                                            (accepted or not clean_effects) else None),
            "escoamento_na_janela": backlog_drained,
            "todos_segundos_turnos_enviados_e_concluidos": all_measured(
                second_metrics["planned"] == second_metrics["http_202"], second_completed),
            "jev_sem_solicitacoes_ou_tentativas": all_measured(not classification_used, True if sql_final else None),
        }
        if initial_metrics["offered"] != len(plan):
            failures.append("gerador não ofereceu todas as entradas planejadas; conferir iterações descartadas")
        if len([event for event in events if event["type"] == "initial"]) != initial_metrics["offered"]:
            failures.append("entradas iniciais repetidas no registro do gerador")
        if initial_metrics["accepted_with_ids"] != initial_metrics["http_202"]:
            failures.append("recibo 202 sem IDs")
        missed = [name for name, passed in goals.items() if passed is False]
        if missed:
            failures.append("metas do ensaio não atingidas: " + ", ".join(missed))
    human = human_summary(list(rows(output / "human.jsonl")), cases, window) if config["scenario"] == "human" else None
    if human and ((snapshot and human["resolved"] != len(plan)) or human["above_portfolio_limit"]
                  or human["above_active_profile"] or human["operation_errors"]):
        failures.append("roteiro humano incompleto ou ação, perfil ou carteira fora do esperado")
    if not k6 or manifest.get("k6_exit") != 0:
        gaps.append("k6 sem encerramento normal ou métricas")
    if (output / "observer-errors.jsonl").exists():
        gaps.append("observador de elegibilidade de continuações registrou erros")
    capture = manifest.get("observation", {}).get("kafka_records", {})
    captured_positions = {(r["topic"], r["partition"], r["offset"]) for r in kafka
                          if isinstance(r.get("partition"), int) and isinstance(r.get("offset"), int)}
    if (capture.get("complete") is not True or type(capture.get("expected_offsets")) is not int
            or type(capture.get("records_read")) is not int
            or capture["expected_offsets"] != capture["records_read"] or capture["records_read"] != len(kafka)
            or len(captured_positions) != len(kafka)):
        gaps.append("leitura de eventos Kafka incompleta")
    if config["fault_seconds"] and (not ready or not in_window(stopped) or not in_window(started)
                                    or fault.get("stopped_state", {}).get("Status") != "exited"
                                    or fault.get("started_state", {}).get("Status") != "running" or fault.get("error")):
        gaps.append("parada/partida/prontidão Kafka sem evidência completa")
    elif config["fault_seconds"] and started - stopped < config["fault_seconds"] * 1000:
        gaps.append("interrupção Kafka menor que a solicitada")
    if any(row["negative_clock_deltas"] for row in (initial_metrics, second_metrics)):
        gaps.append("carimbos UTC produziram latências negativas; verifique sincronização de relógio")
    initial_in_fault = [row for row in initial if stopped and row["sent_ms"] and
                        stopped <= row["sent_ms"] < (ready or window["end_ms"])]
    phase_start = 0
    phase_seconds = 0
    stages = []
    for rate, seconds in config["stages"]:
        phase_end = phase_start + rate * seconds
        stage = times([row for row in initial if phase_start <= row["index"] < phase_end])
        measure_from = window.get("start_ms", 0) + phase_seconds * 1000
        measure_until = measure_from + seconds * 1000
        phase_sql = [item for item in good if measure_from <= item["sample_ms"] < measure_until]
        phase_lag = [item for item in lag_good if measure_from <= item["sample_ms"] < measure_until]
        stages.append({"target_cases_per_s": rate, "seconds": seconds, **stage,
                       "max_outbox_pending": max((item["outbox_pending"] for item in phase_sql), default=None),
                       "max_cases_waiting_processing": max((item["cases_waiting_processing"] for item in phase_sql),
                                                           default=None),
                       "max_consumer_lag": max((item["total_lag"] for item in phase_lag), default=None),
                       "offered_per_s": stage["offered"] / seconds, "accepted_per_s": stage["http_202"] / seconds})
        phase_start = phase_end
        phase_seconds += seconds
    first_bottleneck = next((index + 1 for index, stage in enumerate(stages) if stage["offered"] != stage["planned"] or
                             stage["acceptance_of_planned"] < 0.99 or (stage["latency_accept"]["p95"] or 0) > 500), None)
    completed_count = sum(in_window(row["last_effect_ms"]) for row in reconciled if row["state"] == "concluído")
    resolved_count = sum(in_window(case["resolved_ms"]) for case in cases)
    measured_seconds = (window["end_ms"] - window["start_ms"]) / 1000 if window else None
    bins = defaultdict(Counter)
    for key, timestamps in {
        "initial_offered": (row["sent_ms"] for row in initial),
        "initial_202": (row["finished_ms"] for row in initial if row["http_status"] == 202),
        "followups_sent": (row["sent_ms"] for row in second),
        "turns_completed": (row["last_effect_ms"] for row in reconciled if row["state"] == "concluído"),
        "cases_resolved": (case["resolved_ms"] for case in cases),
    }.items():
        for stamp in timestamps:
            if in_window(stamp):
                bins[int((stamp - window["start_ms"]) // 1000)][key] += 1
    reasons = [manifest["blocked"]] if manifest.get("blocked") else []
    if manifest.get("cleanup") not in (None, "concluída"):
        reasons.append("limpeza interrompida: " + manifest["cleanup"])
    if window:
        reasons.extend(gaps)
    emissions = [row for row in events if row["type"] == "initial"]
    return {
        "state": "bloqueado" if reasons else "reprovado" if failures else "aprovado",
        "reason": "; ".join(reasons) or None, "measurement_gaps": gaps if window else [], "observed_failures": [] if manifest.get("blocked") and not window else failures,
        "cleanup": manifest.get("cleanup"), "goals": goals if window else {},
        "planned_inputs": len(plan), "initial": initial_metrics if window else None,
        "followups": {**second_metrics,
                      "unissued_reasons": dict(Counter(row["reason"] for row in second if row["sent_ms"] is None)),
                      "send_delay_after_target": distribution([row["sent_ms"] - row["due_ms"] for row in second
                                                               if row["sent_ms"] is not None and row["due_ms"] is not None]),
                      "visibility_observation_delay": distribution([
                          row["observed_ms"] - row["due_ms"] + 5000 for row in second
                          if row["observed_ms"] is not None and row["due_ms"] is not None])} if window else None,
        "generator_accounting": {"planned": len(plan), "http_attempt_logs": len(emissions),
                                 "unique_initial_ids": len({row["source_event_id"] for row in emissions}),
                                 "planned_not_offered": len(plan) - initial_metrics["offered"],
                                 "suppressed_stage_overflow": sum(row["type"] == "stage_overflow" for row in events),
                                 "raw_dropped_iterations": dropped} if window and not chat else None,
        "k6": k6 or None, "dropped_iterations": dropped, "stages": stages if window else [],
        "first_stage_with_shortfall": first_bottleneck if window else None,
        "arrival_clock": {"per_stage_first_iteration_schedule_ms": sorted({
            row["scenario_start_ms"] for row in events if row["type"] == "initial" and "scenario_start_ms" in row}),
            "k6_setup_anchor_ms": window.get("start_ms")} if window else None,
        "rates": {"arrival_seconds": duration, "offered_initial_per_s": initial_metrics["offered"] / duration,
                  "accepted_initial_per_s": initial_metrics["http_202"] / duration} if window and duration else None,
        "completions": {"observation_seconds_including_load": measured_seconds, "ai_turns_in_window": completed_count,
                        "resolved_cases_in_window": resolved_count,
                        "ai_turns_per_s": completed_count / measured_seconds,
                        "resolved_cases_per_s": resolved_count / measured_seconds} if measured_seconds else None,
        "per_second_counts": [{"second": index, **counts} for index, counts in sorted(bins.items())],
        "kafka": {"completed_turns_missing_causal_pair": len(missing_pairs),
                  "repeated_records_observed": sum(count - 1 for count in duplicates.values()),
                  "repeated_ids": [{"topic": topic, "event_id": event, "copies": count}
                                   for (topic, event), count in duplicates.items() if count > 1],
                  "distinct_dead_letter_event_ids": len(failure_offsets),
                  "dead_letter_records_observed": sum(row["topic"] == "agent.failures" for row in kafka),
                  "evidence": manifest.get("observation", {}).get("kafka_records")} if window else None,
        "http": {"initial_and_followup_reqs": len(emissions) + second_metrics["offered"],
                 "initial_and_followup_non_202": initial_metrics["non_202"] + second_metrics["non_202"]}
        if window and not chat else None,
        "resources": resource_metrics if window else None,
        "integrity": {"unattributed_messages": unattributed, "unattributed_message_count": len(unattributed),
                      "unplanned_entries": unplanned, "confirmed_losses": sum(row["confirmed_loss"] for row in accepted),
                      "duplicated_effect_identities": sum(row["duplicate_effect"] for row in accepted),
                      "persisted_without_http_202": sum(bool(row["case_id"]) and row["http_status"] != 202
                                                      for row in reconciled) + (sum(
                          item["entry_count"] == 1 and item["http_status"] != 202
                          for item in chat["traffic_reconciliation"]) if chat else 0),
                      "not_reconciled_http_202": sum(row["state"] != "concluído" for row in accepted)}
        if snapshot else None,
        "backlog": {**{f"max_{key}": max((row[key] for row in good), default=None) for key in
                       ("outbox_pending", "outbox_failed", "cases_waiting_processing", "cases_failed",
                        "cases_waiting_human", "cases_human_active", "cases_waiting_customer")},
                    "max_consumer_lag": max((row["total_lag"] for row in lag_good), default=None),
                    "last_sql_in_window": tail or None, "last_kafka_lag_in_window": tail_lag or None,
                    "last_kafka_lag_available_near_end": tail_lag_fresh, "latest_required_work_ms": latest_work,
                    "pending_outboxes_at_snapshot": len(outbox_final) if snapshot else None,
                    "pending_cases_at_snapshot": len(dangling_cases) if snapshot else None} if window else None,
        "outage": {"stop_observed_at_ms": stopped, "start_observed_at_ms": started, "broker_ready_observed_ms": ready,
                   "outage_to_ready_ms": ready - stopped if ready and stopped else None,
                   "process_down_ms": started - stopped if started and stopped else None,
                   "drained_sample_ms": drained, "drain_after_readiness_ms": drained - ready if drained else None,
                   "initiated_while_unavailable_or_recovering": times(initial_in_fault)} if fault else None,
        "observer": {"sql_cost": distribution([row["cost_ms"] for row in sql]),
                     "kafka_cost": distribution([row["cost_ms"] for row in lag]),
                     "resources_cost": distribution([row["cost_ms"] for row in resources]),
                     "followup_query_cost": distribution([row["cost_ms"] for row in rows(output / "followup-samples.jsonl")]),
                     "sql_sample_errors": len(unsafe_sql),
                     "kafka_samples_unavailable": sum(row["total_lag"] is None for row in lag),
                     "db_clock_max_abs_delta_ms": max(map(abs, clock_errors), default=None),
                     "db_client_connections_peak": max((sum(sum(states.values()) for states in
                         (row.get("db_client_connections") or {}).values()) for row in good), default=None),
                     "resource_samples": len(resources), "snapshot_ms": snapshot["sample_ms"] if snapshot else None},
        "human": human if window else None, "chat": chat if window else None,
    }


def render(report):
    content = [f"# F08-A — {report['run_id']}", "", f"**Estado** — {report['state']}", "",
               f"Cenário `{report['scenario']}`, revisão `{report['revision']}`.", ""]
    if report["reason"]:
        content.extend([f"Bloqueio — {report['reason']}", ""])
    capture = (report.get("kafka") or {}).get("evidence") or {}
    failed_bounds = [a for a in capture.get("attempts", []) if a["phase"] == "final_offsets" and a["status"] == "failed"]
    for attempt in failed_bounds:
        reason = attempt.get("kafka_name") or attempt.get("error")
        content.append(f"- Captura pós-janela: consulta de offsets {attempt['attempt']} falhou ({reason}).")
    for failure in report["observed_failures"]:
        content.append(f"- {failure}")
    if report["initial"]:
        content.extend(["", "| Indicador | Inicial | Segundo turno |", "| --- | ---: | ---: |"])
        def cell(values, key, percentile=None):
            value = values[key][percentile] if percentile else values[key]
            if value is None:
                return "indisponível"
            return f"{value:.2f}" if isinstance(value, float) else str(value)
        for label, key, percentile in (
            ("Planejados", "planned", None), ("Emitidos", "offered", None), ("HTTP 202", "http_202", None),
            ("Timeouts HTTP", "timeouts", None), ("Aceite p50 (ms)", "latency_accept", "p50"),
            ("Aceite p95 (ms)", "latency_accept", "p95"),
            ("Resposta persistida p50 (ms)", "latency_persisted", "p50"),
            ("Resposta persistida p95 (ms)", "latency_persisted", "p95"),
        ):
            content.append(f"| {label} | {cell(report['initial'], key, percentile)} | "
                           f"{cell(report['followups'], key, percentile)} |")
        content.extend(["", f"Iterações descartadas pelo k6 — {report['dropped_iterations']}"])
    for title, metric, facts in (
        ("Vazão", "rates", ("offered_initial_per_s", "accepted_initial_per_s")),
        ("Conclusões", "completions", ("ai_turns_in_window", "resolved_cases_in_window",
                                       "ai_turns_per_s", "resolved_cases_per_s")),
        ("Persistência", "integrity", ("confirmed_losses", "duplicated_effect_identities", "unattributed_message_count",
                                       "not_reconciled_http_202")),
        ("Recursos", "resources", ("host_cpu_busy_percent_peak", "host_ram_used_bytes_peak")),
        ("Kafka", "kafka", ("repeated_records_observed", "dead_letter_records_observed")),
        ("Backlog", "backlog", ("max_outbox_pending", "max_outbox_failed", "max_consumer_lag",
                                "max_cases_waiting_processing", "pending_cases_at_snapshot")),
        ("Interrupção", "outage", ("process_down_ms", "outage_to_ready_ms", "drain_after_readiness_ms")),
        ("Humano", "human", ("max_active_per_analyst_observed", "max_portfolio_per_analyst_observed", "resolved")),
        ("Chat", "chat", ("target", "peak_confirmed_steady", "emitted", "emitted_per_s", "opened_cases",
                         "continued_cases", "recovery_reads_ok")),
    ):
        if report[metric] is not None:
            values = report[metric]
            content.extend(["", f"## {title}", "", "| Indicador | Valor |", "| --- | ---: |"])
            for name in facts:
                if name not in values:  # Relatórios anteriores à reconciliação inversa.
                    continue
                value = values[name]
                value = "indisponível" if value is None else f"{value:.2f}" if isinstance(value, float) else value
                content.append(f"| `{name}` | {value} |")
    content.extend(["", "Consulte `report.json` para denominadores, metas e séries.",
                    "O manifesto inventaria o plano, amostras e evidências desta rodada.", ""])
    return "\n".join(content)


def publish(output, manifest, plan, events):
    reconciled, kafka, cases = evidence(output, manifest, plan, events)
    with (output / "reconciliation.jsonl").open("wb") as stream:
        for row in reconciled:
            stream.write(bytes_json(row) + b"\n")
    summary = {"schema_version": 1, "run_id": manifest["run_id"], "revision": manifest["revision"],
               "scenario": manifest["scenario"], "parameters": manifest["parameters"], "units": {
                   "epoch_timestamps": "ms UTC", "latency": "ms", "rates": "por segundo", "counts": "unidades",
                   "acceptance_ratio": "fração do plano"}, **summarize(output, manifest, plan, events, reconciled, kafka, cases)}
    if manifest.get("window"):
        summary["window_utc"] = {key: utc(value) for key, value in manifest["window"].items()}
    write_json(output / "report.json", summary)
    (output / "report.md").write_text(render(summary))
    return {key: summary[key] for key in ("run_id", "parameters", "state", "reason", "cleanup", "goals", "initial",
                                          "followups", "rates", "completions", "outage", "integrity", "chat", "human",
                                          "observed_failures")}


def render_matrix(results):
    lines = ["# F08-A — rodadas executadas", "",
             "| Rodada | Cenário | Estado | Planejadas | HTTP 202 | p95 aceite (ms) | p95 resposta (ms) |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: |"]
    skipped = [result for result in results if result.get("executed") is False]
    if skipped:
        lines[2:2] = [f"Matriz incompleta. {len(results) - len(skipped)} de {len(results)} rodadas executadas. "
                       + skipped[0]["reason"], ""]
    for result in results:
        config = result["parameters"]
        scenario = config["scenario"]
        result_id = result["run_id"]
        if scenario == "reference":
            scenario = "Kafka interrompido" if config["fault_seconds"] else "Kafka disponível"
        if scenario == "chat":
            scenario = f"Chat {config['chat']['target']}"
        initial = result.get("initial") or {}
        values = [initial.get("planned"), initial.get("http_202"),
                  (initial.get("latency_accept") or {}).get("p95"),
                  (initial.get("latency_persisted") or {}).get("p95")]
        link = result_id if result.get("executed") is False else f"[{result_id}]({result_id}/report.md)"
        cells = [link, scenario, result["state"],
                 *("—" if value is None else f"{value:.2f}" if isinstance(value, float) else str(value)
                   for value in values)]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"
