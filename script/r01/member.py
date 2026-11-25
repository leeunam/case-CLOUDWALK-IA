"""Membro real do ensaio. Suspende o processo A na fronteira efeito/commit."""
import hashlib
import json
import os
import signal
import sys
from pathlib import Path
from unittest.mock import patch

import confluent_kafka
import agent_flow


def main():
    role, label, trace = sys.argv[1:]
    consumer = confluent_kafka.Consumer
    consume = agent_flow.consume
    armed = label == "A"

    def configured(config):
        return consumer({**config, "client.id": label, "session.timeout.ms": 6000,
                         "heartbeat.interval.ms": 1500, "group.protocol": "classic"})

    def traced(topic, group, handle, publisher, brokers):
        def accept(record):
            nonlocal armed
            handle(record)
            raw = record.value()
            evidence = {"pid": os.getpid(), "group": group, "topic": topic, "partition": record.partition(),
                        "offset": record.offset(), "sha256": hashlib.sha256(raw).hexdigest(),
                        "event_id": json.loads(raw)["event_id"]}
            with Path(trace).open("a") as target:
                print(json.dumps(evidence), file=target)
            if armed:
                armed = False
                os.kill(os.getpid(), signal.SIGSTOP)
        consume(topic, group, accept, publisher, brokers)

    with (patch.object(confluent_kafka, "Consumer", configured),
          patch.object(agent_flow, "consume", traced), patch.object(sys, "argv", ["agent_flow", role])):
        agent_flow.main()


if __name__ == "__main__":
    main()
