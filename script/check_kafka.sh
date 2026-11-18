#!/usr/bin/env bash
set -euo pipefail

bootstrap_servers="${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}"
check_id="$(date +%s)-$$-$RANDOM"
topic="f01.retention-check-$check_id"
first_group="f01-first-$check_id"
replay_group="f01-replay-$check_id"
event="f01-retained-event-$check_id"

cleanup() {
  /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server "$bootstrap_servers" \
    --delete --group "$first_group" --group "$replay_group" >/dev/null 2>&1 || true
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server "$bootstrap_servers" \
    --delete --topic "$topic" >/dev/null 2>&1 || true
}
trap cleanup EXIT

/opt/kafka/bin/kafka-topics.sh --bootstrap-server "$bootstrap_servers" \
  --create --topic "$topic" --partitions 1 --replication-factor 1 \
  --config cleanup.policy=delete --config retention.ms=604800000

printf '%s\n' "$event" | /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server "$bootstrap_servers" --topic "$topic" \
  --command-property acks=all --command-property enable.idempotence=true

first_read="$(/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server "$bootstrap_servers" --topic "$topic" \
  --group "$first_group" --from-beginning --max-messages 1 --timeout-ms 15000 \
  --command-property enable.auto.commit=false)"

/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server "$bootstrap_servers" \
  --group "$first_group" --topic "$topic" --reset-offsets --to-latest --execute

replay="$(/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server "$bootstrap_servers" --topic "$topic" \
  --group "$replay_group" --from-beginning --max-messages 1 --timeout-ms 15000 \
  --command-property enable.auto.commit=false)"

if [[ "$first_read" != "$event" || "$replay" != "$event" ]]; then
  echo "A leitura inicial e o replay precisam devolver o mesmo evento." >&2
  printf 'Esperado: %q\nPrimeira leitura: %q\nReplay: %q\n' "$event" "$first_read" "$replay" >&2
  exit 1
fi

echo "Evento consumido e relido por outro grupo após avançar a posição do primeiro."
