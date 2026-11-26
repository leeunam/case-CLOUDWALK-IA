"""Sondas do Kafka e interrupções do processo para o aceite offline E01."""

import hashlib
import json
import logging
import os
import sys
import time
import uuid
from unittest.mock import patch

import confluent_kafka

from agent_flow import (EVENTS, FAILURES, REQUESTS, REQUEST_GROUP, Contracts, Publisher, consume,
                        json_bytes, load_agent_backend)
from e01_ledger import LedgerClient


BROKERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
FAULT_EXIT = 86


def read_topic(topic, case_id):
    client = confluent_kafka.Consumer({"bootstrap.servers": BROKERS, "group.id": "e01-offline-probe",
                                      "enable.auto.commit": False, "enable.auto.offset.store": False})
    try:
        partitions = client.list_topics(topic, timeout=5).topics[topic].partitions
        limits = {}
        for part in partitions:
            bounds = client.get_watermark_offsets(confluent_kafka.TopicPartition(topic, part), timeout=5)
            if bounds[0] < bounds[1]:
                limits[part] = bounds
        client.assign([confluent_kafka.TopicPartition(topic, part, low) for part, (low, _high) in limits.items()])
        pending = set(limits)
        records = []
        deadline = time.monotonic() + 8
        while pending and time.monotonic() < deadline:
            record = client.poll(0.25)
            if record is None:
                continue
            if record.error():
                raise confluent_kafka.KafkaException(record.error())
            part = record.partition()
            if part not in pending:
                continue
            if record.key() == case_id.encode():
                records.append(record)
            if record.offset() >= limits[part][1] - 1:
                pending.discard(part)
        if pending:
            raise TimeoutError("Não foi possível ler até o último offset dos tópicos de teste.")
        return records
    finally:
        client.close()


def receipt(topic, record):
    data = json.loads(record.value())
    return {"topic": topic, "partition": record.partition(), "offset": record.offset(),
            "event_id": data.get("event_id"), "type": data.get("event_type"), "reason": data.get("reason"),
            "request_event_id": data.get("payload", {}).get("request_event_id"),
            "sha256": hashlib.sha256(record.value()).hexdigest()}


def group_offsets():
    client = confluent_kafka.Consumer({"bootstrap.servers": BROKERS, "group.id": REQUEST_GROUP,
                                       "enable.auto.commit": False, "enable.auto.offset.store": False})
    try:
        partitions = client.list_topics(REQUESTS, timeout=5).topics[REQUESTS].partitions
        return {part.partition: part.offset for part in client.committed(
            [confluent_kafka.TopicPartition(REQUESTS, part) for part in partitions], timeout=5)}
    finally:
        client.close()


def publisher():
    return Publisher(confluent_kafka.Producer({"bootstrap.servers": BROKERS, "acks": "all",
                                              "enable.idempotence": True, "message.timeout.ms": 1500}))


def interrupt(mode, request_id):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    target = publisher()
    publish = target.publish
    start = LedgerClient.start

    def commit_then_lose_ack(client, event_id, body):
        reply = start(client, event_id, body)
        if mode == "start_ack_lost" and event_id == request_id and reply.get("dispatch") is True:
            print(f"interrupt={mode} request_event_id={request_id}", flush=True)
            os._exit(FAULT_EXIT)
        return reply

    def publish_with_interruption(topic, key, raw):
        if (mode != "start_ack_lost" and topic == EVENTS
                and json.loads(raw)["payload"]["request_event_id"] == request_id):
            if mode == "after_ack":
                publish(topic, key, raw)
            print(f"interrupt={mode} request_event_id={request_id}", flush=True)
            os._exit(FAULT_EXIT)
        publish(topic, key, raw)

    target.publish = publish_with_interruption
    contracts = Contracts(os.environ["CLOUDWALK_CONTRACT_SCHEMA"])
    handle = load_agent_backend("luna_fixture", contracts, os.environ)
    consumer = confluent_kafka.Consumer
    with (patch.object(LedgerClient, "start", commit_then_lose_ack),
          patch.object(confluent_kafka, "Consumer", lambda config: consumer({**config, "session.timeout.ms": 6000}))):
        consume(REQUESTS, REQUEST_GROUP, lambda record: handle(record, target), target, BROKERS)


def main():
    mode, key = sys.argv[1:3]
    if mode in {"before_ack", "after_ack", "start_ack_lost"}:
        interrupt(mode, key)
        return
    uuid.UUID(key)
    if mode == "inspect":
        print(json.dumps({"offsets": group_offsets(), **{
            topic: [receipt(topic, row) for row in read_topic(topic, key)] for topic in (REQUESTS, EVENTS, FAILURES)
        }}))
        return
    topic = REQUESTS if mode == "replay_request" else EVENTS
    event_id = sys.argv[3]
    original = next(row.value() for row in read_topic(topic, key) if json.loads(row.value())["event_id"] == event_id)
    replay_id = event_id
    if mode == "old_generation":
        replay_id = str(uuid.uuid4())
        original = json_bytes({**json.loads(original), "event_id": replay_id})
    elif mode != "replay_request":
        raise ValueError("invalid_offline_probe")
    publisher().publish(topic, key, original)
    print(json.dumps({"event_id": replay_id, "sha256": hashlib.sha256(original).hexdigest()}))


if __name__ == "__main__":
    main()
