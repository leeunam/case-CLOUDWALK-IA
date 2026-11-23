"""Coordenador dirigido: efeito, perda no commit, mudança de proprietário e replay."""
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import agent_flow as flow


class EndTrial(Exception):
    pass


try:
    from confluent_kafka import KafkaError, KafkaException as BrokerException
except ImportError:
    KafkaError = None

    class BrokerException(Exception):
        pass


class CoordinatorTest(unittest.TestCase):
    def exercise(self, topic, mode, *, cause="UNKNOWN_MEMBER_ID", fatal=False, ambiguous=False):
        group = "mock-agent-v1" if topic == flow.REQUESTS else "platform-agent-events-v1"
        if KafkaError is None:
            error = Mock()
            error.__str__ = lambda _: cause
            error.code.return_value = 25 if cause == "UNKNOWN_MEMBER_ID" else 30
            error.name.return_value = cause
            error.fatal.return_value = fatal
        else:
            error = KafkaError(getattr(KafkaError, cause), cause, fatal)
        old, replacement = Mock(), Mock()
        old.memberid.return_value = "A"
        replacement.memberid.return_value = "B"
        for client in (old, replacement):
            client.assignment.return_value = [SimpleNamespace(topic=topic, partition=1)]
        records = []
        for offset in (17, 18):
            record = Mock()
            record.topic.return_value = topic
            record.partition.return_value = 1
            record.offset.return_value = offset
            record.value.return_value = flow.json_bytes({"event_id": f"id-{offset}", "text": "Olá"})
            record.error.return_value = None
            records.append(record)

        def subscribe(client, _topics, **callbacks):
            if "on_assign" in callbacks:
                callbacks["on_assign"](client, [SimpleNamespace(partition=1)])

        old.subscribe.side_effect = lambda *a, **kw: subscribe(old, *a, **kw)
        replacement.subscribe.side_effect = lambda *a, **kw: subscribe(replacement, *a, **kw)
        old.poll.side_effect = [records[0], AssertionError("cursor antigo reutilizado")]
        replacement.poll.side_effect = [*records[int(ambiguous):], EndTrial()]
        accepted, deliveries, commits = {}, [], []

        def effect(record):
            raw = record.value()
            key = record.offset()
            self.assertEqual(accepted.setdefault(key, raw), raw)
            deliveries.append(key)

        def refuse(message, asynchronous):
            self.assertFalse(asynchronous)
            self.assertEqual(deliveries, [17])
            if ambiguous:
                commits.append(message.offset() + 1)
            if mode == "exception":
                raise BrokerException(error)
            return [SimpleNamespace(error=error)]

        old.commit.side_effect = refuse

        def confirm(message, asynchronous):
            self.assertFalse(asynchronous)
            self.assertEqual(commits[-1] if commits else 17, message.offset())
            commits.append(message.offset() + 1)
            return [SimpleNamespace(error=None)]

        replacement.commit.side_effect = confirm
        factory = Mock(side_effect=[old, replacement])
        driver = SimpleNamespace(Consumer=factory, KafkaException=BrokerException)
        recoverable = cause == "UNKNOWN_MEMBER_ID" and not fatal
        with (patch.dict(sys.modules, {"confluent_kafka": driver}), patch.object(flow.time, "sleep"),
              self.assertLogs(level="INFO") as logs,
              self.assertRaises(EndTrial if recoverable else BrokerException)):
            flow.consume(topic, group, effect, Mock(), "broker")
        old.close.assert_called_once()
        old.commit.assert_called_once()
        for call in factory.call_args_list:
            self.assertFalse(call.args[0]["enable.auto.commit"])
            self.assertFalse(call.args[0]["enable.auto.offset.store"])
        if recoverable:
            replacement.close.assert_called_once()
            self.assertEqual(commits, [18, 19])
            self.assertEqual(deliveries, [17, 18] if ambiguous else [17, 17, 18])
            self.assertEqual(list(accepted), [17, 18])
            self.assertTrue(any("primeiro progresso" in line and "membro=B" in line for line in logs.output))
        else:
            self.assertEqual(factory.call_count, 1)
        self.assertTrue(any(cause in line and "offset=17" in line for line in logs.output))

    def test_membership_loss_after_effect(self):
        for topic in (flow.REQUESTS, flow.EVENTS):
            for mode in ("exception", "partition"):
                with self.subTest(topic=topic, mode=mode):
                    self.exercise(topic, mode)

    def test_broker_position_wins_if_offset_already_advanced(self):
        self.exercise(flow.EVENTS, "exception", ambiguous=True)

    def test_fatal_and_unrelated_errors_stop_consumer(self):
        for mode in ("exception", "partition"):
            self.exercise(flow.EVENTS, mode, cause="GROUP_AUTHORIZATION_FAILED")
            self.exercise(flow.REQUESTS, mode, fatal=True)

    def test_generation_changes_even_if_member_name_is_reused(self):
        consumer = Mock()
        consumer.memberid.return_value = "A"
        consumer.consumer_group_metadata.side_effect = [b"generation-1", b"generation-2"]
        with self.assertRaises(flow.MembershipLost):
            flow.process_record(consumer, Mock(), Mock(), "group", Mock())
        consumer.commit.assert_not_called()

    def test_revoked_partition_skips_commit(self):
        consumer = Mock()
        consumer.assignment.return_value = []
        with self.assertRaises(flow.MembershipLost):
            flow.process_record(consumer, Mock(), Mock(), "group", Mock())
        consumer.commit.assert_not_called()

    def test_known_loss_skips_commit(self):
        consumer = Mock()
        consumer.memberid.side_effect = ["A", None]
        effect = Mock()
        with self.assertRaises(flow.MembershipLost):
            flow.process_record(consumer, Mock(), Mock(), "group", effect)
        effect.assert_called_once()
        consumer.commit.assert_not_called()


class PollTest(unittest.TestCase):
    def exercise(self, name, *, partition=1, offset=17, fatal=False, safe=False):
        error = Mock()
        error.name.return_value = name
        error.code.return_value = -170
        error.fatal.return_value = fatal
        error.__str__ = lambda _: "diagnóstico do broker"
        notice = Mock()
        notice.topic.return_value = flow.EVENTS if partition == 1 else None
        notice.partition.return_value = partition
        notice.offset.return_value = offset
        notice.error.return_value = error
        next_record = Mock()
        next_record.topic.return_value = flow.EVENTS
        next_record.partition.return_value = 1
        next_record.offset.return_value = 18
        next_record.error.return_value = None
        consumer, handle, publisher = Mock(), Mock(), Mock()
        consumer.poll.side_effect = [notice, next_record, EndTrial()]
        consumer.assignment.return_value = [SimpleNamespace(topic=flow.EVENTS, partition=1)]
        consumer.commit.return_value = [SimpleNamespace(error=None)]
        driver = SimpleNamespace(Consumer=Mock(return_value=consumer), KafkaException=BrokerException)
        with (patch.dict(sys.modules, {"confluent_kafka": driver}), self.assertLogs(level="WARNING") as logs,
              self.assertRaises(EndTrial if safe else BrokerException)):
            flow.consume(flow.EVENTS, "grupo", handle, publisher, "broker")
        diagnostic = logs.output[0]
        for field in ("classe=aviso" if safe else "classe=interromper", "grupo=grupo", f"topico={notice.topic()}",
                      f"particao={partition}", f"offset={offset}", f"codigo={name}", "numero=-170",
                      "causa=diagnóstico do broker"):
            self.assertIn(field, diagnostic)
        publisher.publish.assert_not_called()
        consumer.close.assert_called_once()
        if safe:
            handle.assert_called_once_with(next_record)
            consumer.commit.assert_called_once_with(message=next_record, asynchronous=False)
        else:
            consumer.poll.assert_called_once()
            handle.assert_not_called()
            consumer.commit.assert_not_called()

    def test_localized_poll_error_never_reaches_offset_18(self):
        for code in ("_NOT_IMPLEMENTED", "_TRANSPORT", "_MAX_POLL_EXCEEDED"):
            with self.subTest(code=code):
                self.exercise(code)

    def test_global_poll_timeout_rejoins_from_group_position(self):
        old, new = Mock(), Mock()
        topic, group = flow.EVENTS, "platform-agent-events-v1"
        notice = Mock()
        notice.topic.return_value = None
        notice.partition.return_value = -1
        notice.offset.return_value = None
        if KafkaError is None:
            error = Mock()
            error.name.return_value = "_MAX_POLL_EXCEEDED"
            error.fatal.return_value = False
        else:
            error = KafkaError(KafkaError._MAX_POLL_EXCEEDED)
        notice.error.return_value = error
        old.poll.side_effect = [notice, AssertionError("cursor antigo reutilizado")]

        pending = Mock()
        pending.topic.return_value = topic
        pending.partition.return_value = 1
        pending.offset.return_value = 17
        pending.error.return_value = None
        new.poll.side_effect = [pending, EndTrial()]
        new.assignment.return_value = [SimpleNamespace(topic=topic, partition=1)]
        new.commit.return_value = [SimpleNamespace(error=None)]
        sessions = iter((old, new))

        def create(config):
            client = next(sessions)
            self.assertEqual(config["group.id"], group)
            self.assertFalse(config["enable.auto.commit"])
            if client is new:
                old.close.assert_called_once_with()
            return client

        publisher, handle = Mock(), Mock()
        driver = SimpleNamespace(Consumer=create, KafkaException=BrokerException)
        with (patch.dict(sys.modules, {"confluent_kafka": driver}), patch.object(flow.time, "sleep"),
              self.assertRaises(EndTrial)):
            flow.consume(topic, group, handle, publisher, "broker")
        old.poll.assert_called_once()
        old.commit.assert_not_called()
        self.assertEqual(new.subscribe.call_args.args, ([topic],))
        new.seek.assert_not_called()
        handle.assert_called_once_with(pending)
        new.commit.assert_called_once_with(message=pending, asynchronous=False)
        publisher.publish.assert_not_called()
        new.close.assert_called_once_with()

    def test_fatal_or_partially_localized_poll_timeout_stops(self):
        self.exercise("_MAX_POLL_EXCEEDED", partition=-1, offset=None, fatal=True)
        self.exercise("_MAX_POLL_EXCEEDED", partition=1, offset=None)
        self.exercise("_MAX_POLL_EXCEEDED", partition=-1, offset=17)

    def test_only_known_nonfatal_notices_allow_progress(self):
        self.exercise("_PARTITION_EOF", safe=True)
        self.exercise("_TRANSPORT", partition=None, offset=None, safe=True)
        self.exercise("_ALL_BROKERS_DOWN", partition=-1, offset=-1, safe=True)
        self.exercise("_PARTITION_EOF", fatal=True)
        self.exercise("_UNKNOWN", partition=-1, offset=-1)
