import json
import unittest
from contextlib import redirect_stderr
from email.message import Message
from io import BytesIO, StringIO
from types import SimpleNamespace
from unittest.mock import ANY, Mock, call, patch

from agent_flow import (
    DEFAULT_SCHEMA,
    EVENTS,
    FAILURES,
    REQUEST_PATH,
    REQUESTS,
    Contracts,
    InvalidEvent,
    Publisher,
    RecordPending,
    REQUEST_GROUP,
    authenticate,
    forward_result,
    json_bytes,
    load_agent_backend,
    main,
    process_record,
    propose_result,
    request_handler,
    run_mock,
    signed_headers,
)


class AgentFlowTest(unittest.TestCase):
    def setUp(self):
        self.contracts = Contracts(DEFAULT_SCHEMA)
        self.request = self.fixture("agent-turn-1-request")
        self.result = self.fixture("agent-turn-1-reply")

    def fixture(self, name):
        source = DEFAULT_SCHEMA.parents[1] / "fixtures" / f"{name}.json"
        return json.loads(source.read_bytes())["data"]

    def record(self, event, topic):
        record = Mock()
        record.value.return_value = json_bytes(event)
        record.key.return_value = event["case_id"].encode()
        record.topic.return_value = topic
        record.partition.return_value = 1
        record.offset.return_value = 42
        return record

    def test_signatures_use_original_bytes_and_reject_repeated_headers(self):
        raw = json_bytes(self.request)
        headers = Message()
        for key, value in signed_headers("secret", raw, timestamp=1000).items():
            headers[key] = value
        self.assertTrue(authenticate(headers, "secret", raw, now=1300))
        self.assertFalse(authenticate(headers, "secret", raw, now=1301))
        self.assertFalse(authenticate(headers, "secret", raw + b" ", now=1300))
        headers["X-Webhook-Timestamp"] = "1000"
        self.assertFalse(authenticate(headers, "secret", raw, now=1000))

    def test_bridge_requires_secrets_before_starting(self):
        for role in ("requests", "events"):
            variable = f"CLOUDWALK_AGENT_{role.upper()}_SECRET"
            for value in (None, "", " \t "):
                with self.subTest(role=role, value=value):
                    environment = {"CLOUDWALK_AGENT_EVENTS_URL": "http://rails.test/webhooks/v1/agent/events"}
                    if value is not None:
                        environment[variable] = value
                    stderr = StringIO()
                    with (
                        patch("sys.argv", ["agent_flow.py", role]),
                        patch.dict("os.environ", environment, clear=True),
                        patch("confluent_kafka.Producer") as producer,
                        patch("agent_flow.ThreadingHTTPServer") as server,
                        patch("agent_flow.consume") as consume,
                        redirect_stderr(stderr),
                    ):
                        with self.assertRaises(SystemExit) as error:
                            main()
                        self.assertEqual(error.exception.code, 2)
                        self.assertIn(variable, stderr.getvalue())
                        producer.assert_not_called()
                        server.assert_not_called()
                        consume.assert_not_called()

    def test_bridge_preserves_whitespace_in_configured_secrets(self):
        secret = " secret \t"
        url = "http://rails.test/webhooks/v1/agent/events"
        environment = {
            "CLOUDWALK_AGENT_REQUESTS_SECRET": secret,
            "CLOUDWALK_AGENT_EVENTS_SECRET": secret,
            "CLOUDWALK_AGENT_EVENTS_URL": url,
        }
        record = Mock()
        with (
            patch.dict("os.environ", environment, clear=True),
            patch("confluent_kafka.Producer"),
            patch("agent_flow.ThreadingHTTPServer"),
            patch("agent_flow.request_handler") as handler,
            patch("agent_flow.consume") as consume,
            patch("agent_flow.forward_result") as forward,
        ):
            with patch("sys.argv", ["agent_flow.py", "requests"]):
                main()
            self.assertEqual(handler.call_args.args[2], secret)

            with patch("sys.argv", ["agent_flow.py", "events"]):
                main()
            handle = consume.call_args.args[2]
            handle(record)
            self.assertEqual(forward.call_args.args[2:], (url, secret))

    def test_invalid_backend_configuration_fails_before_constructing_producer(self):
        for env, expected in (
            ({"CLOUDWALK_AGENT_BACKEND": "bad"}, "CLOUDWALK_AGENT_BACKEND"),
            ({"CLOUDWALK_AGENT_BACKEND": "luna"}, "CLOUDWALK_E01_FEITA_KEY_FILE"),
            ({"CLOUDWALK_AGENT_BACKEND": "luna", "RAILS_ENV": "test",
              "CLOUDWALK_E01_FEITA_KEY_FILE": "/tmp/e01-fake-key"}, "luna real não pode executar com RAILS_ENV=test"),
            ({"CLOUDWALK_AGENT_BACKEND": "luna_fixture", "RAILS_ENV": "development"}, "RAILS_ENV=test"),
            ({"CLOUDWALK_AGENT_BACKEND": "luna_fixture", "RAILS_ENV": "test"}, "invalid_ledger_url"),
        ):
            with (
                self.subTest(env=env),
                patch("sys.argv", ["agent_flow.py", "mock"]),
                patch.dict("os.environ", env, clear=True),
                patch("confluent_kafka.Producer") as producer,
                patch("agent_flow.consume") as consume,
                redirect_stderr(StringIO()) as stderr,
            ):
                with self.assertRaises(SystemExit):
                    main()
                producer.assert_not_called()
                consume.assert_not_called()
                self.assertIn(expected, stderr.getvalue())

    def test_default_backend_keeps_existing_kafka_group_and_mock(self):
        record = self.record(self.request, REQUESTS)
        with (
            patch("sys.argv", ["agent_flow.py", "mock"]),
            patch.dict("os.environ", {}, clear=True),
            patch("confluent_kafka.Producer"),
            patch("agent_flow.consume") as consume,
            patch("agent_flow.run_mock") as mock,
        ):
            main()
            topic, group, handle, publisher, _brokers = consume.call_args.args
            self.assertEqual((topic, group), (REQUESTS, REQUEST_GROUP))
            handle(record)
            mock.assert_called_once_with(record, ANY, publisher)

    def test_executor_pending_state_neither_emits_failure_nor_commits(self):
        from e01_executor import ExecutorError

        environment = {"RAILS_ENV": "test", "CLOUDWALK_E01_LEDGER_URL": "http://rails.test",
                       "CLOUDWALK_E01_LEDGER_SECRET": "dummy"}
        trace = Mock()
        trace.consumer.assignment.return_value = [SimpleNamespace(topic=REQUESTS, partition=1)]
        trace.consumer.commit.return_value = []
        record = self.record(self.request, REQUESTS)
        with patch("e01_executor.Executor") as executor:
            handle = load_agent_backend("luna_fixture", self.contracts, environment)
            executor.return_value.handle.side_effect = ExecutorError("ledger_still_pending", retryable=True)
            for _attempt in range(4):
                with self.assertRaisesRegex(RecordPending, "ledger_still_pending"):
                    process_record(trace.consumer, trace.publisher, record, REQUEST_GROUP,
                                   lambda message: handle(message, trace.publisher), pause=trace.pause)
                trace.consumer.commit.assert_not_called()
                trace.publisher.publish.assert_not_called()
            trace.pause.assert_not_called()

            executor.return_value.handle.side_effect = ExecutorError("invalid_e01_context")
            process_record(trace.consumer, trace.publisher, record, REQUEST_GROUP,
                           lambda message: handle(message, trace.publisher), pause=trace.pause)
        topic, key, raw = trace.publisher.publish.call_args.args
        self.assertEqual((topic, key), (FAILURES, record.key()))
        failure = json.loads(raw)
        self.assertEqual(failure["reason"], "invalid_e01_context")
        self.assertEqual(failure["event_id"], self.request["event_id"])
        self.assertNotIn(self.request["payload"]["history"][0]["text"].encode(), raw)
        self.assertEqual(trace.mock_calls[-1], call.consumer.commit(message=record, asynchronous=False))

    def test_request_returns_202_after_publish_and_503_on_ambiguous_confirmation(self):
        for name in ("agent-turn-1-request", "agent-setfit-request", "agent-setfit-invalid-version"):
            with self.subTest(name=name):
                self.check_bridge(self.fixture(name), valid=name != "agent-setfit-invalid-version")

    def check_bridge(self, request, *, valid):
        raw = json_bytes(request)
        trace = Mock()
        handler = object.__new__(request_handler(trace, self.contracts, "secret"))
        handler.respond = trace.respond
        handler.connection = Mock()
        handler.path = REQUEST_PATH
        handler.headers = Message()
        handler.headers["Content-Length"] = str(len(raw))
        for key, value in signed_headers("secret", raw).items():
            handler.headers[key] = value
        handler.rfile = BytesIO(raw)

        handler.do_POST()
        if not valid:
            self.assertEqual(trace.mock_calls, [call.respond(422, "invalid_AgentTurnRequested")])
            return
        self.assertEqual(trace.mock_calls, [call.publish(REQUESTS, request["case_id"], raw), call.respond(202)])

        trace.reset_mock()
        trace.publish.side_effect = TimeoutError
        handler.rfile = BytesIO(raw)
        handler.do_POST()
        self.assertEqual(trace.mock_calls[-1], call.respond(503, "publication_unconfirmed"))

    def test_mock_produces_identical_bytes_for_replay_and_resolves_the_second_turn(self):
        for name in ("agent-turn-1-request", "agent-setfit-request"):
            with self.subTest(name=name):
                self.check_mock_replay(self.fixture(name))

        invalid = self.record(self.fixture("agent-setfit-invalid-version"), REQUESTS)
        with self.assertRaisesRegex(InvalidEvent, "invalid_AgentTurnRequested"):
            run_mock(invalid, self.contracts, Mock())

    def check_mock_replay(self, request):
        record = self.record(request, REQUESTS)
        publisher = Mock()
        run_mock(record, self.contracts, publisher)
        run_mock(record, self.contracts, publisher)
        calls = publisher.publish.call_args_list
        self.assertEqual(calls[0], calls[1])
        topic, key, body = calls[0].args
        self.assertEqual((topic, key), (EVENTS, request["case_id"]))
        result = self.contracts.read("AgentResult", body)
        self.assertEqual(result["schema_version"], "1.0")
        self.assertEqual(result["event_type"], "agent.reply.proposed")
        self.assertEqual(result["payload"]["request_event_id"], request["event_id"])

        second = self.fixture("agent-turn-2-request")
        self.assertEqual(propose_result(second)["event_type"], "agent.resolve.proposed")
        self.assertNotEqual(propose_result(second)["event_id"], result["event_id"])

    def test_mock_hands_off_advanced_terminal_cases_with_history_and_stable_replay(self):
        for sources in (("channel", "jev"), ("channel", "channel"), ("supervisor", "supervisor")):
            with self.subTest(sources=sources):
                request = self.fixture("agent-handoff-request")
                classification = request["payload"]["classification"]
                classification["category_source"], classification["priority_source"] = sources
                history = request["payload"]["history"]
                latest = self.fixture("case-handoff-messages")["items"][1]
                history.append(latest)
                record = self.record(request, REQUESTS)
                publisher = Mock()
                run_mock(record, self.contracts, publisher)
                run_mock(record, self.contracts, publisher)

                first, replay = publisher.publish.call_args_list
                self.assertEqual(first, replay)
                topic, key, body = first.args
                self.assertEqual((topic, key), (EVENTS, request["case_id"]))
                result = self.contracts.read("AgentResult", body)
                self.assertEqual(result["event_type"], "agent.handoff.proposed")
                self.assertNotEqual(result["event_id"], request["event_id"])
                self.assertEqual(result["turn_id"], request["turn_id"])
                payload = result["payload"]
                self.assertEqual(payload["request_event_id"], request["event_id"])
                self.assertEqual(payload["message_ids"], [latest["id"]])
                self.assertEqual(payload["summary"], f"Atendimento avançado sobre maquininha. {latest['text']}")

    def test_kafka_publish_waits_for_a_delivery_callback(self):
        producer = Mock()
        producer.produce.side_effect = lambda _topic, **kwargs: setattr(producer, "on_delivery", kwargs["on_delivery"])
        producer.poll.side_effect = lambda _timeout: producer.on_delivery(None, None)
        Publisher(producer).publish(REQUESTS, "case", b"body")
        producer.poll.assert_called_once()

        producer.poll.side_effect = lambda _timeout: producer.on_delivery("broker_error", None)
        with self.assertRaisesRegex(RuntimeError, "broker_error"):
            Publisher(producer).publish(REQUESTS, "case", b"body")

    def test_forward_uses_original_body_and_requires_matching_receipt(self):
        record = self.record(self.result, EVENTS)
        with patch("agent_flow.urlopen") as open_request:
            response = open_request.return_value.__enter__.return_value
            response.status = 200
            response.read.return_value = json_bytes({"event_id": self.result["event_id"], "disposition": "discarded"})
            forward_result(record, self.contracts, "http://rails.test/webhooks/v1/agent/events", "secret")
            self.assertEqual(open_request.call_args.args[0].data, record.value())

            response.read.return_value = json_bytes({"event_id": self.request["event_id"], "disposition": "applied"})
            with self.assertRaisesRegex(RuntimeError, "unexpected_receipt"):
                forward_result(record, self.contracts, "http://rails.test/webhooks/v1/agent/events", "secret")

    def test_failures_are_confirmed_before_the_consumer_commits(self):
        trace = Mock()
        trace.consumer.assignment.return_value = [SimpleNamespace(topic=EVENTS, partition=1)]
        trace.consumer.commit.return_value = []
        trace.handle.side_effect = OSError("temporarily unavailable")
        record = self.record(self.result, EVENTS)
        process_record(trace.consumer, trace.publisher, record, "test", trace.handle, pause=trace.pause)
        self.assertEqual(trace.handle.call_count, 3)
        self.assertEqual(trace.pause.call_args_list, [call(1), call(2)])
        topic, key, body = trace.publisher.publish.call_args.args
        self.assertEqual((topic, key), (FAILURES, record.key()))
        self.assertEqual(json.loads(body)["origin"], {"topic": EVENTS, "group": "test", "partition": 1, "offset": 42})
        self.assertEqual(trace.mock_calls[-1], call.consumer.commit(message=record, asynchronous=False))

    def test_failure_publication_failure_leaves_offset_uncommitted(self):
        consumer, publisher, handle = Mock(), Mock(), Mock()
        handle.side_effect = InvalidEvent("bad_event")
        publisher.publish.side_effect = TimeoutError("Kafka indisponível")
        with self.assertRaises(TimeoutError):
            process_record(consumer, publisher, self.record(self.result, EVENTS), "test", handle)
        consumer.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
