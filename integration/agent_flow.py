"""Ponte HTTP/Kafka e consumidores de pedidos e retornos do atendente."""

import argparse
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from jsonschema import Draft202012Validator, FormatChecker

REQUESTS = "agent.requests"
EVENTS = "agent.events"
FAILURES = "agent.failures"
DISPOSITIONS = {"applied", "duplicate", "discarded"}
REQUEST_PATH = "/webhooks/v1/agent/requests"
HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = HERE.parent / "docs/contratos/schemas/v1.json"
REQUEST_GROUP = "mock-agent-v1"


class InvalidEvent(ValueError):
    pass


class RecordPending(RuntimeError):
    """Reobservar o registro a partir do offset confirmado do grupo."""


def signed_headers(secret, body, timestamp=None):
    timestamp = str(int(time.time()) if timestamp is None else timestamp)
    signature = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256)
    return {
        "Content-Type": "application/json",
        "X-Webhook-Timestamp": timestamp,
        "X-Webhook-Signature": signature.hexdigest(),
    }


def authenticate(headers, secret, body, now=None):
    timestamps = headers.get_all("X-Webhook-Timestamp", [])
    signatures = headers.get_all("X-Webhook-Signature", [])
    if len(timestamps) != 1 or len(signatures) != 1:
        return False
    timestamp, signature = timestamps[0], signatures[0]
    if not (timestamp.isascii() and timestamp.isdecimal()):
        return False
    clock = int(time.time()) if now is None else now
    seconds = timestamp.lstrip("0") or "0"
    if len(seconds) > 20 or abs(clock - int(seconds)) > 300 or not signature.isascii():
        return False
    expected = signed_headers(secret, body, timestamp)["X-Webhook-Signature"]
    return hmac.compare_digest(expected, signature)


def json_bytes(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()


class Contracts:
    def __init__(self, path):
        schema = json.loads(Path(path).read_bytes())
        self.validators = {
            name: Draft202012Validator(
                {**schema, "$ref": f"#/$defs/{name}"}, format_checker=FormatChecker()
            )
            for name in ("AgentTurnRequested", "AgentResult", "AgentReceipt")
        }

    def read(self, name, raw):
        try:
            data = json.loads(raw)
        except (ValueError, TypeError) as error:
            raise InvalidEvent("invalid_json") from error
        if not self.validators[name].is_valid(data):
            raise InvalidEvent(f"invalid_{name}")
        return data


def validate_history(event):
    history = event["payload"]["history"]
    sequences = [message["sequence"] for message in history]
    if sequences != sorted(set(sequences)) or len({message["id"] for message in history}) != len(history):
        raise InvalidEvent("unordered_or_repeated_history")


def require_key(event, record):
    if record.key() != event["case_id"].encode():
        raise InvalidEvent("invalid_case_key")


def propose_result(request):
    history = request["payload"]["history"]
    classification = request["payload"]["classification"]
    category = classification["category"]
    payload = {"request_event_id": request["event_id"]}
    if category == "terminal" and classification["priority"] == "advanced":
        event_type = "agent.handoff.proposed"
        latest = history[-1]
        payload.update(
            summary=f"Atendimento avançado sobre maquininha. {latest['text']}",
            message_ids=[latest["id"]],
            text="Vou encaminhar para a equipe que atende maquininhas.",
        )
    elif any(message["author"]["type"] == "ai" for message in history):
        event_type = "agent.resolve.proposed"
        payload["text"] = "Certo. Vou encerrar este atendimento."
    else:
        event_type = "agent.reply.proposed"
        suggestions = {
            "pix": "Consulte o comprovante no histórico para conferir a confirmação.",
            "payouts": "Confira a data prevista e o status do repasse no extrato.",
            "terminal": "Confira a conexão da maquininha e tente novamente.",
        }
        payload["text"] = suggestions.get(
            category, "Confira as informações do atendimento e me diga se a orientação resolveu."
        )
    return {
        **request,
        "schema_version": "1.0",
        "event_id": str(uuid.uuid5(uuid.NAMESPACE_URL, "cloudwalk:mock-agent-v1:" + request["event_id"])),
        "event_type": event_type,
        "payload": payload,
    }


class Publisher:
    def __init__(self, producer):
        self.producer = producer

    def publish(self, topic, key, body):
        # Cada chamada guarda sua própria confirmação, inclusive entre threads HTTP.
        delivery = []

        def on_delivery(error, _message):
            delivery.append(error)

        self.producer.produce(topic, key=key, value=body, on_delivery=on_delivery)
        deadline = time.monotonic() + 1.6
        while not delivery and time.monotonic() < deadline:
            self.producer.poll(0.05)
        if not delivery:
            raise TimeoutError("publication_unconfirmed")
        if delivery[0] is not None:
            raise RuntimeError(str(delivery[0]))


def request_handler(publisher, contracts, secret):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != REQUEST_PATH:
                self.respond(404, "not_found")
                return
            lengths = self.headers.get_all("Content-Length", ["0"])
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal() or len(lengths[0]) > 8:
                self.respond(422, "invalid_content_length")
                return
            self.connection.settimeout(2)
            try:
                body = self.rfile.read(int(lengths[0]))
            except TimeoutError:
                self.respond(422, "incomplete_body")
                return

            if len(body) != int(lengths[0]):
                self.respond(422, "incomplete_body")
                return

            if not authenticate(self.headers, secret, body):
                self.respond(401, "unauthenticated")
                return
            try:
                event = contracts.read("AgentTurnRequested", body)
                validate_history(event)
            except InvalidEvent as error:
                self.respond(422, str(error))
                return
            try:
                publisher.publish(REQUESTS, event["case_id"], body)
            except Exception as error:
                logging.warning("publicação pendente event_id=%s: %s", event["event_id"], error)
                self.respond(503, "publication_unconfirmed")
                return

            logging.info("publicado topic=%s case_id=%s event_id=%s",
                         REQUESTS, event["case_id"], event["event_id"])
            self.respond(202)

        def respond(self, status, code=None):
            body = json_bytes({"error": {"code": code, "message": code}}) if code else b""
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def forward_result(record, contracts, url, secret):
    raw = record.value()
    event = contracts.read("AgentResult", raw)
    require_key(event, record)
    request = Request(url, data=raw, headers=signed_headers(secret, raw), method="POST")
    try:
        with urlopen(request, timeout=2) as response:
            receipt = contracts.read("AgentReceipt", response.read())
            if response.status != 200 or receipt["event_id"] != event["event_id"] or receipt["disposition"] not in DISPOSITIONS:
                raise RuntimeError("unexpected_receipt")
    except HTTPError as error:
        if error.code in (409, 422):
            raise InvalidEvent(f"rails_http_{error.code}") from error
        raise
    logging.info("retorno case_id=%s event_id=%s disposition=%s",
                 event["case_id"], event["event_id"], receipt["disposition"])


def run_mock(record, contracts, publisher):
    event = contracts.read("AgentTurnRequested", record.value())
    require_key(event, record)
    validate_history(event)
    result = propose_result(event)
    publisher.publish(EVENTS, result["case_id"], json_bytes(result))
    logging.info("mock publicou case_id=%s request_event_id=%s event_id=%s",
                 result["case_id"], event["event_id"], result["event_id"])


def load_agent_backend(name, contracts, environ):
    if name == "mock":
        return lambda record, publisher: run_mock(record, contracts, publisher)
    if name not in {"luna", "luna_fixture"}:
        raise ValueError("CLOUDWALK_AGENT_BACKEND deve ser mock, luna ou luna_fixture.")

    if __package__:
        from .e01_backend import LunaBackend
        from .e01_executor import Executor, ExecutorError
        from .e01_knowledge import Knowledge
        from .e01_ledger import LedgerClient
    else:
        from e01_backend import LunaBackend
        from e01_executor import Executor, ExecutorError
        from e01_knowledge import Knowledge
        from e01_ledger import LedgerClient

    transport = None
    if name == "luna":
        key_path = environ.get("CLOUDWALK_E01_FEITA_KEY_FILE", "")
        if not key_path:
            raise ValueError("CLOUDWALK_E01_FEITA_KEY_FILE é obrigatório para luna.")
        try:
            key = Path(key_path).read_text(encoding="utf-8").rstrip("\r\n")
        except (OSError, UnicodeError):
            raise ValueError("CLOUDWALK_E01_FEITA_KEY_FILE deve ser um arquivo legível em UTF-8.") from None
        audit_dir = environ.get("CLOUDWALK_E01_AUDIT_DIR")
        if audit_dir:
            if __package__:
                from .e01_audit import AuditedPost
                from .e01_backend import FEITA_HOST, RESPONSE_LIMIT
                from .e01_http import DeadlinePost
            else:
                from e01_audit import AuditedPost
                from e01_backend import FEITA_HOST, RESPONSE_LIMIT
                from e01_http import DeadlinePost
            transport = AuditedPost(DeadlinePost(FEITA_HOST, response_limit=RESPONSE_LIMIT), audit_dir)
    else:
        if environ.get("RAILS_ENV") != "test" or environ.get("CLOUDWALK_E01_FEITA_KEY_FILE"):
            raise ValueError("luna_fixture exige RAILS_ENV=test e configuração sem credencial Feita.")
        if __package__:
            from .e01_fixture import fixture_post
        else:
            from e01_fixture import fixture_post
        key = "offline-test-fixture"
        transport = fixture_post

    ledger = LedgerClient(environ.get("CLOUDWALK_E01_LEDGER_URL", ""),
                          environ.get("CLOUDWALK_E01_LEDGER_SECRET", ""))
    try:
        knowledge = Knowledge.load(Path(environ.get("CLOUDWALK_E01_KNOWLEDGE_DIR", HERE / "knowledge")))
        backend = LunaBackend(key, transport=transport)
    except (OSError, UnicodeError):
        raise ValueError("Verifique os arquivos de conhecimento e contratos E01.") from None
    executor = Executor(knowledge, backend, ledger, contracts)

    def handle(record, publisher):
        try:
            executor.handle(record, publisher)
        except ExecutorError as error:
            if error.retryable:
                raise RecordPending(error.code) from None
            raise InvalidEvent(error.code) from None
        except Exception:
            # Um erro imprevisto pode ter ocorrido depois de start ou complete.
            # O ledger continua sendo a autoridade sobre o efeito da tentativa.
            raise RecordPending("e01_executor_interrupted") from None

    return handle


def publish_failure(publisher, record, group, message):
    try:
        event = json.loads(record.value())
    except (ValueError, TypeError):
        event = {}
    if not isinstance(event, dict):
        event = {}
    origin = {"group": group, "topic": record.topic(), "partition": record.partition(), "offset": record.offset()}
    identifiers = {}
    for field in ("event_id", "case_id", "correlation_id"):
        try:
            identifiers[field] = str(uuid.UUID(event[field]))
        except (KeyError, ValueError, TypeError, AttributeError):
            identifiers[field] = None
    failure = {**identifiers, "reason": message, "origin": origin}
    publisher.publish(FAILURES, record.key(), json_bytes(failure))
    logging.error("falha Kafka registrada: %s", failure)


def process_record(consumer, publisher, record, group, handle, *, pause=time.sleep):
    """Conclui este registro antes de buscar o seguinte."""
    member = consumer.memberid()
    if not member:
        raise MembershipLost("registro recebido sem membro vigente")
    generation = consumer.consumer_group_metadata()
    for attempt in range(3):
        try:
            handle(record)
            break
        except RecordPending:
            raise
        except InvalidEvent as error:
            publish_failure(publisher, record, group, str(error))
            break
        except Exception as error:
            if attempt == 2:
                publish_failure(publisher, record, group, str(error))
            else:
                pause(attempt + 1)

    # O coordenador arbitra a corrida restante entre esta leitura e o commit.
    if consumer.memberid() != member or consumer.consumer_group_metadata() != generation:
        raise MembershipLost("membro ou geração alterados durante o efeito")
    if not any(p.topic == record.topic() and p.partition == record.partition() for p in consumer.assignment()):
        raise MembershipLost("partição fora da atribuição vigente")
    try:
        commits = consumer.commit(message=record, asynchronous=False)
    except Exception as exc:
        from confluent_kafka import KafkaException
        if not isinstance(exc, KafkaException):
            raise
        classify_commit_error(exc.args[0], group, record)
        raise
    for commit in commits:
        if commit.error:
            classify_commit_error(commit.error, group, record)
            from confluent_kafka import KafkaException
            raise KafkaException(commit.error)


class MembershipLost(RuntimeError):
    """O cliente atual não pode continuar do cursor local."""


def classify_commit_error(error, group, record):
    membership = not error.fatal() and error.name() in {
        "UNKNOWN_MEMBER_ID", "ILLEGAL_GENERATION", "REBALANCE_IN_PROGRESS",
        "_ASSIGNMENT_LOST", "_MAX_POLL_EXCEEDED",
    }
    logging.warning("commit recusado classe=%s grupo=%s topico=%s particao=%d offset=%d codigo=%s numero=%s causa=%s",
                    "associacao" if membership else "interromper", group, record.topic(),
                    record.partition(), record.offset(), error.name(), error.code(), error)
    if membership:
        raise MembershipLost(str(error))


def poll_error_action(error, partition, offset):
    if error.fatal():
        return "interromper"
    name = error.name()
    if name == "_PARTITION_EOF":
        return "aviso"
    global_notice = (partition is None or partition < 0) and (offset is None or offset < 0)
    if global_notice:
        if name == "_MAX_POLL_EXCEEDED":
            return "reingresso"
        if name in {"_TRANSPORT", "_ALL_BROKERS_DOWN"}:
            return "aviso"
    return "interromper"


def consume(topic, group, handle, publisher, brokers):
    from confluent_kafka import Consumer, KafkaException

    config = {
        "bootstrap.servers": brokers, "group.id": group, "auto.offset.reset": "earliest",
        "enable.auto.commit": False, "enable.auto.offset.store": False,
    }
    while True:
        consumer = Consumer(config)
        first_progress = set()

        def assigned(client, partitions):
            first_progress.update(p.partition for p in partitions)
            logging.info("atribuicao grupo=%s membro=%s topico=%s particoes=%s", group,
                         client.memberid(), topic, [p.partition for p in partitions])

        def removed(client, partitions):
            first_progress.difference_update(p.partition for p in partitions)
            logging.info("retirada grupo=%s membro=%s topico=%s particoes=%s", group,
                         client.memberid(), topic, [p.partition for p in partitions])

        try:
            consumer.subscribe([topic], on_assign=assigned, on_revoke=removed, on_lost=removed)
            while True:
                record = consumer.poll(1)
                if record is None:
                    continue
                error = record.error()
                if error is not None:
                    partition, offset = record.partition(), record.offset()
                    action = poll_error_action(error, partition, offset)
                    logging.warning("poll grupo=%s classe=%s topico=%s particao=%s offset=%s codigo=%s numero=%s causa=%s",
                                    group, action, record.topic(), partition, offset, error.name(), error.code(), error)
                    if action == "reingresso":
                        break
                    if action == "interromper":
                        raise KafkaException(error)
                    continue
                try:
                    process_record(consumer, publisher, record, group, handle)
                except RecordPending as error:
                    logging.info("registro pendente grupo=%s topico=%s particao=%d offset=%d codigo=%s",
                                 group, topic, record.partition(), record.offset(), error)
                    break
                except MembershipLost as error:
                    logging.warning("reingresso grupo=%s topico=%s particao=%d offset=%d causa=%s",
                                    group, topic, record.partition(), record.offset(), error)
                    break
                if record.partition() in first_progress:
                    first_progress.remove(record.partition())
                    logging.info("primeiro progresso grupo=%s membro=%s topico=%s particao=%d offset=%d proximo=%d",
                                 group, consumer.memberid(), topic, record.partition(), record.offset(), record.offset() + 1)
        finally:
            consumer.close()
        # Nenhum seek/commit no membro antigo. Nova assinatura parte do offset do grupo.
        time.sleep(1)


def main():
    from confluent_kafka import Producer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("requests", "events", "mock"))
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    secret = None
    if args.role != "mock":
        variable = f"CLOUDWALK_AGENT_{args.role.upper()}_SECRET"
        secret = os.environ.get(variable, "")
        if not secret.strip():
            parser.error(f"{variable} deve conter um segredo.")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    brokers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    contracts = Contracts(os.environ.get("CLOUDWALK_CONTRACT_SCHEMA", DEFAULT_SCHEMA))
    if args.role == "mock":
        backend_name = os.environ.get("CLOUDWALK_AGENT_BACKEND", "mock")
        try:
            backend = load_agent_backend(backend_name, contracts, os.environ)
        except (ValueError, OSError) as error:
            parser.error(str(error))
        logging.info("atendente backend=%s grupo=%s", backend_name, REQUEST_GROUP)
    publisher = Publisher(Producer({
        "bootstrap.servers": brokers,
        "acks": "all",
        "enable.idempotence": True,
        "message.timeout.ms": 1500,
    }))

    if args.role == "requests":
        with ThreadingHTTPServer(("0.0.0.0", args.port), request_handler(publisher, contracts, secret)) as server:
            server.serve_forever()
    elif args.role == "events":
        url = os.environ["CLOUDWALK_AGENT_EVENTS_URL"]
        consume(EVENTS, "platform-agent-events-v1", lambda record: forward_result(record, contracts, url, secret),
                publisher, brokers)
    else:
        consume(REQUESTS, REQUEST_GROUP, lambda record: backend(record, publisher), publisher, brokers)


if __name__ == "__main__":
    main()
