"""Leituras limitadas por watermark e observações SQL somente leitura."""

import json
import os
import time
import uuid
from dataclasses import dataclass

import psycopg
from confluent_kafka import Consumer, ConsumerGroupTopicPartitions, KafkaException, Producer, TopicPartition
from confluent_kafka.admin import AdminClient, ConfigResource, ResourceType

TOPICS = ("agent.requests", "agent.events", "agent.failures")
EVENTS_GROUP = "platform-agent-events-v1"
GROUPS = {"agent.requests": "mock-agent-v1", "agent.events": EVENTS_GROUP}
BROKERS = "kafka:9092"


class Blocked(RuntimeError):
    pass


class Failed(AssertionError):
    pass


def verify(condition, reason):
    if not condition:
        raise Failed(reason)


def until(label, sample, predicate=bool, *, timeout=100):
    deadline = time.monotonic() + timeout
    while True:
        result = sample()
        if predicate(result):
            return result
        if time.monotonic() >= deadline:
            raise Blocked(f"Condição não observada no prazo: {label}")
        time.sleep(0.2)


@dataclass
class Record:
    topic: str
    partition: int
    offset: int
    key: bytes
    raw: bytes

    def position(self):
        return {"topic": self.topic, "partition": self.partition, "offset": self.offset}

    @property
    def data(self):
        return json.loads(self.raw)


class Kafka:
    def __init__(self):
        self.admin = AdminClient({"bootstrap.servers": BROKERS, "log_level": 0})
        self.producer = Producer({
            "bootstrap.servers": BROKERS, "acks": "all", "enable.idempotence": True,
            "message.timeout.ms": 4500, "log_level": 0,
        })
        self.reader = Consumer({
            "bootstrap.servers": BROKERS, "log_level": 0,
            "group.id": "f07-observer-" + uuid.uuid4().hex,
            "enable.auto.commit": False, "enable.auto.offset.store": False,
            "enable.partition.eof": True,
        })

    def close(self):
        self.reader.close()

    def topics_ready(self):
        try:
            metadata = self.admin.list_topics(timeout=2)
            return all(
                topic in metadata.topics and len(metadata.topics[topic].partitions) == 3
                and all(part.leader >= 0 for part in metadata.topics[topic].partitions.values())
                for topic in TOPICS
            )
        except (RuntimeError, KafkaException):
            return False

    def group_ready(self, group, topic):
        try:
            description = self.admin.describe_consumer_groups([group], request_timeout=3)[group].result()
            if description.state.name != "STABLE":
                return False
            assignments = {(part.topic, part.partition) for member in description.members
                           for part in member.assignment.topic_partitions}
            return assignments == {(topic, p) for p in range(3)}
        except (RuntimeError, KafkaException):
            return False

    def group_empty(self, group):
        try:
            description = self.admin.describe_consumer_groups([group], request_timeout=3)[group].result()
            return not description.members and description.state.name == "EMPTY"
        except (RuntimeError, KafkaException):
            return False

    def failure_limit(self):
        resource = ConfigResource(ResourceType.TOPIC, "agent.failures")
        config = self.admin.describe_configs([resource], request_timeout=5)[resource].result()
        return config["max.message.bytes"].value

    def bounds(self, topic, partition):
        return self.reader.get_watermark_offsets(TopicPartition(topic, partition), timeout=5)

    def offsets(self, group, topic, partition):
        future = self.admin.list_consumer_group_offsets(
            [ConsumerGroupTopicPartitions(group, [TopicPartition(topic, partition)])], request_timeout=6
        )[group]
        committed, = future.result().topic_partitions
        if committed.error:
            raise Blocked(f"Consulta de offset falhou: {committed.error.name()}")
        low, high = self.bounds(topic, partition)
        return {
            "group": group, "topic": topic, "partition": partition,
            "committed_next_offset": committed.offset if committed.offset >= 0 else None,
            "low_watermark": low, "log_end_offset": high,
            "backlog": high - (committed.offset if committed.offset >= 0 else low),
        }

    def records(self, topic, *, key=None):
        ranges = {partition: self.bounds(topic, partition) for partition in range(3)}
        positions = {p: low for p, (low, high) in ranges.items() if low < high}
        records = []
        if not positions:
            return records
        self.reader.assign([TopicPartition(topic, p, offset) for p, offset in positions.items()])
        deadline = time.monotonic() + 10
        try:
            while positions:
                if time.monotonic() >= deadline:
                    raise Blocked(f"Leitura não alcançou watermarks de {topic}: {sorted(positions)}")
                message = self.reader.poll(0.3)
                if message is None:
                    continue
                partition = message.partition()
                if message.error():
                    if message.error().name() != "_PARTITION_EOF":
                        raise Blocked(f"Leitura de {topic} falhou: {message.error().name()}")
                    if partition in positions and message.offset() >= ranges[partition][1]:
                        del positions[partition]
                    continue
                if partition not in positions:
                    continue
                offset = message.offset()
                if offset < ranges[partition][1] and (key is None or message.key() == key.encode()):
                    records.append(Record(topic, partition, offset, message.key(), message.value()))
                if offset + 1 >= ranges[partition][1]:
                    del positions[partition]
        finally:
            self.reader.unassign()
        return records

    def publish(self, topic, key, raw, *, partition=None, expect_error=None):
        deliveries = []

        def delivered(error, message):
            deliveries.append((error, message))

        options = {} if partition is None else {"partition": partition}
        self.producer.produce(topic, key=key, value=raw, on_delivery=delivered, **options)
        self.producer.flush(7)
        if not deliveries:
            raise Blocked(f"Broker não confirmou tentativa de produção em {topic}")
        error, message = deliveries[0]
        if expect_error:
            if not error or error.name() != expect_error:
                raise Blocked(f"Injeção Kafka não confirmada em {topic}: {error.name() if error else 'aceito'}")
            return error.name()
        if error:
            raise Blocked(f"Produção em {topic} falhou: {error.name()}")
        return Record(topic, message.partition(), message.offset(), key, raw)


class Database:
    def __init__(self):
        self.connection = psycopg.connect(
            host="db", dbname="cloudwalk_development", user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"], connect_timeout=5, autocommit=True,
            options="-c default_transaction_read_only=on -c statement_timeout=4000",
        )

    def query(self, sql, *params):
        return self.connection.execute(sql, params).fetchone()[0]

    def channel(self, brand, kind="chat"):
        return self.query("""
            SELECT c.id::text FROM channels c JOIN brands b ON b.id = c.brand_id
            WHERE b.code = %s AND c.kind = %s AND c.active
        """, brand, kind)

    def entry(self, event_id):
        return self.query("SELECT count(*) FROM channel_entries WHERE source_event_id = %s", event_id)

    def request_body(self, event_id):
        return self.query("SELECT body::jsonb FROM agent_outboxes WHERE event_id = %s", event_id)

    def receipt(self, event_id):
        return self.query("""
            SELECT coalesce(jsonb_agg(jsonb_build_object('id', id, 'event_id', event_id, 'disposition', disposition,
                                                      'sha256', body_sha256)), '[]')
            FROM agent_receipts WHERE event_id = %s
        """, event_id)

    def simulator_cases(self, *identities):
        return self.query("""
            SELECT coalesce(jsonb_agg(jsonb_build_object('case_id', s.id, 'correlation_id', s.correlation_id,
                                                     'simulator_id', c.simulator_session_id) ORDER BY s.id), '[]')
            FROM support_cases s JOIN channel_conversations c ON c.id = s.channel_conversation_id
            WHERE c.simulator_session_id = ANY(%s::uuid[])
        """, list(identities))

    def case(self, case_id):
        row = self.query("""
            SELECT jsonb_build_object(
                'id', c.id, 'correlation_id', c.correlation_id, 'brand_id', c.brand_id, 'status', c.status,
                'version', c.version, 'assignment_generation', c.assignment_generation, 'assignee_id', c.assignee_id,
                'integration_status', c.integration_status, 'category', c.category, 'category_source', c.category_source,
                'priority', c.priority, 'priority_source', c.priority_source,
                'entries', (SELECT count(*) FROM channel_entries x WHERE x.support_case_id = c.id),
                'messages', (SELECT coalesce(jsonb_agg(jsonb_build_object('id', m.id, 'sequence', m.sequence,
                     'type', m.author_type, 'event_id', m.source_event_id) ORDER BY m.sequence), '[]')
                     FROM case_messages m WHERE m.support_case_id = c.id),
                'audits', (SELECT coalesce(jsonb_agg(jsonb_build_object('id', a.id, 'type', a.event_type,
                     'event_id', a.details->'event_id', 'reason', a.reason) ORDER BY a.created_at, a.id), '[]')
                     FROM case_audits a WHERE a.support_case_id = c.id),
                'outbox', (SELECT coalesce(jsonb_agg(jsonb_build_object('event_id', o.event_id, 'turn_id', o.agent_turn_id,
                     'attempts', o.attempts, 'published', o.published_at IS NOT NULL, 'failed', o.failed_at IS NOT NULL,
                     'claimed', o.claim_token IS NOT NULL) ORDER BY o.created_at, o.id), '[]')
                     FROM agent_outboxes o JOIN agent_turns t ON o.agent_turn_id = t.id WHERE t.support_case_id = c.id)
            ) FROM support_cases c WHERE c.id = %s
        """, case_id)
        if row is not None:
            row["message_count"] = len(row["messages"])
            row["audit_count"] = len(row["audits"])
        return row
