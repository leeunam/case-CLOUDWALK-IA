"""Leitura Kafka em processo independente. A saída de controle tem apenas um objeto JSON."""
import json
import sys
import time
from importlib.metadata import version

from confluent_kafka import Consumer, KafkaException, TopicPartition, libversion
from confluent_kafka.admin import AdminClient, OffsetSpec

from kafka_capture import freeze_range
from kafka_probe import GROUPS, TOPICS
from protocol import RESULTS, append, now_ms


KAFKA = "kafka:9092"


def kafka_client():
    return AdminClient({"bootstrap.servers": KAFKA, "socket.timeout.ms": 2500})


def kafka_sample(admin, groups=True):
    from confluent_kafka import ConsumerGroupTopicPartitions
    partitions = [TopicPartition(topic, partition) for topic in TOPICS for partition in range(3)]
    latest = admin.list_offsets({part: OffsetSpec.latest() for part in partitions}, request_timeout=3)
    offsets = {(part.topic, part.partition): future.result(4).offset for part, future in latest.items()}
    result = []
    if groups:
        oldest = admin.list_offsets({part: OffsetSpec.earliest() for part in partitions}, request_timeout=3)
        starts = {(part.topic, part.partition): future.result(4).offset for part, future in oldest.items()}
        requests = [ConsumerGroupTopicPartitions(group) for group in GROUPS.values()]
        # A API administrativa aceita exatamente um grupo por chamada nesta versão.
        for request in requests:
            future = admin.list_consumer_group_offsets([request], request_timeout=3)[request.group_id]
            positions = future.result(4).topic_partitions
            if any(p.error for p in positions):
                raise RuntimeError("partição indisponível")
            committed = {(p.topic, p.partition): p.offset for p in positions}
            for (topic, partition), end in offsets.items():
                if GROUPS.get(topic) != request.group_id:
                    continue
                position = committed.get((topic, partition), -1)
                earliest = starts[(topic, partition)]
                effective_next = max(earliest, position)
                result.append({"topic": topic, "group": request.group_id, "partition": partition,
                               "end_offset": end, "committed_next": position if position >= 0 else None,
                               "start_offset": earliest, "effective_next": effective_next,
                               "lag": max(0, end - effective_next)})
    return offsets, result


def kafka_ready(admin):
    groups = admin.describe_consumer_groups(list(GROUPS.values()), request_timeout=3)
    for topic, group in GROUPS.items():
        members = groups[group].result(4).members
        assigned = {(p.topic, p.partition) for member in members if member.assignment
                    for p in member.assignment.topic_partitions}
        if not {(topic, i) for i in range(3)} <= assigned:
            return False
    return True


def final_offsets(timeout):
    deadline = time.monotonic() + timeout
    admin = AdminClient({"bootstrap.servers": KAFKA, "socket.timeout.ms": max(1, round(timeout * 1000))})
    partitions = {TopicPartition(topic, p): OffsetSpec.latest() for topic in TOPICS for p in range(3)}
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError
    futures = admin.list_offsets(partitions, request_timeout=remaining)
    return {(part.topic, part.partition): future.result(max(0, deadline - time.monotonic())).offset
            for part, future in futures.items()}


def kafka_records(baseline, run_id):
    """Leitura única do primeiro intervalo final válido, sem commits de consumo."""
    ends = freeze_range(RESULTS, baseline, final_offsets, (KafkaException, TimeoutError))
    append(RESULTS / "kafka-capture-attempts.jsonl", {"phase": "read_records", "attempt": 1,
                                                     "status": "started", "started_ms": now_ms()})
    consumer = Consumer({"bootstrap.servers": KAFKA, "group.id": f"{run_id}-evidence",
                         "enable.auto.commit": False, "enable.partition.eof": True,
                         "auto.offset.reset": "error", "socket.timeout.ms": 2500})
    outstanding = {key: end - 1 for key, end in ends.items() if end > baseline[key]}
    if outstanding:
        consumer.assign([TopicPartition(topic, part, baseline[(topic, part)]) for topic, part in outstanding])
    counts = {"expected_offsets": sum(ends[key] - baseline[key] for key in ends), "records_read": 0}
    deadline = time.monotonic() + 45
    try:
        while outstanding and time.monotonic() < deadline:
            record = consumer.poll(0.5)
            if record is None or record.error():
                continue
            key = (record.topic(), record.partition())
            if key not in outstanding or record.offset() > outstanding[key]:
                continue
            counts["records_read"] += 1
            try:
                body = json.loads(record.value())
            except (TypeError, ValueError):
                body = {}
            if not isinstance(body, dict):
                body = {}
            row = {name: body.get(name) for name in ("event_id", "event_type", "occurred_at", "case_id",
                                                    "correlation_id", "turn_id")}
            payload = body.get("payload") or {}
            if isinstance(payload, dict):
                row["request_event_id"] = payload.get("request_event_id")
                row["origin_event_id"] = payload.get("event_id") or payload.get("original_event_id")
            origin = body.get("origin")
            if isinstance(origin, dict):
                row["origin"] = {key: origin.get(key) for key in ("topic", "partition", "offset", "group")}
            append(RESULTS / "kafka-records.jsonl", {
                "topic": key[0], "partition": key[1], "offset": record.offset(), **row,
            })
            if record.offset() == outstanding[key]:
                del outstanding[key]
    finally:
        consumer.close()
    counts["complete"] = not outstanding and counts["records_read"] == counts["expected_offsets"]
    return counts


def main(operation):
    if operation == "records":
        baseline = json.loads((RESULTS / "kafka-baseline.json").read_text())
        config = json.loads((RESULTS / "config.json").read_text())
        return kafka_records({(r["topic"], r["partition"]): r["offset"] for r in baseline}, config["run_id"])
    admin = kafka_client()
    if operation == "ready":
        return {"ready": kafka_ready(admin)}
    if operation == "sample":
        offsets, lag = kafka_sample(admin)
        return {"offsets": [{"topic": t, "partition": p, "offset": offset} for (t, p), offset in offsets.items()],
                "partitions": lag, "versions": {"confluent_kafka": version("confluent-kafka"),
                                                "librdkafka": libversion()[0]}}
    raise ValueError("operação desconhecida")


if __name__ == "__main__":
    try:
        result = main(sys.argv[1])
    except Exception as error:
        result = {"error": type(error).__name__}
    print(json.dumps(result), flush=True)
