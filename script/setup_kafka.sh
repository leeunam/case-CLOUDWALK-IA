#!/usr/bin/env bash
set -euo pipefail

bootstrap_servers="${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"
retention_ms="${KAFKA_RETENTION_MS:-604800000}"

if [[ ! "$retention_ms" =~ ^(-1|[0-9]+)$ ]]; then
  echo "KAFKA_RETENTION_MS deve ser -1 ou um inteiro não negativo em milissegundos." >&2
  exit 1
fi

for topic in agent.requests agent.events agent.failures; do
  /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server "$bootstrap_servers" \
    --create --if-not-exists \
    --topic "$topic" \
    --partitions 3 --replication-factor 1 \
    --config cleanup.policy=delete \
    --config "retention.ms=$retention_ms"

  /opt/kafka/bin/kafka-configs.sh \
    --bootstrap-server "$bootstrap_servers" \
    --entity-type topics --entity-name "$topic" \
    --alter --add-config "cleanup.policy=delete,retention.ms=$retention_ms"
done

echo "Tópicos Kafka preparados com retenção de $retention_ms ms."
