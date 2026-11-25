# F08-A — f08-reference-1795208792430-8b61b6-02

**Estado** — aprovado

Cenário `reference`, revisão `dfbcc79f4ced07e5460eb73d06e956d94799d453`.


| Indicador | Inicial | Segundo turno |
| --- | ---: | ---: |
| Planejados | 1500 | 300 |
| Emitidos | 1500 | 300 |
| HTTP 202 | 1500 | 300 |
| Timeouts HTTP | 0 | 0 |
| Aceite p50 (ms) | 72 | 70.57 |
| Aceite p95 (ms) | 121 | 143.90 |
| Resposta persistida p50 (ms) | 312.20 | 325.88 |
| Resposta persistida p95 (ms) | 31753.95 | 5187.04 |

Iterações descartadas pelo k6 — 0

## Vazão

| Indicador | Valor |
| --- | ---: |
| `offered_initial_per_s` | 5.00 |
| `accepted_initial_per_s` | 5.00 |

## Conclusões

| Indicador | Valor |
| --- | ---: |
| `ai_turns_in_window` | 1800 |
| `resolved_cases_in_window` | 300 |
| `ai_turns_per_s` | 4.29 |
| `resolved_cases_per_s` | 0.71 |

## Persistência

| Indicador | Valor |
| --- | ---: |
| `confirmed_losses` | 0 |
| `duplicated_effect_identities` | 0 |
| `not_reconciled_http_202` | 0 |

## Recursos

| Indicador | Valor |
| --- | ---: |
| `host_cpu_busy_percent_peak` | 65.07 |
| `host_ram_used_bytes_peak` | 8717524992 |

## Kafka

| Indicador | Valor |
| --- | ---: |
| `repeated_records_observed` | 0 |
| `dead_letter_records_observed` | 0 |

## Backlog

| Indicador | Valor |
| --- | ---: |
| `max_outbox_pending` | 218 |
| `max_outbox_failed` | 0 |
| `max_consumer_lag` | 47 |
| `max_cases_waiting_processing` | 218 |
| `pending_cases_at_snapshot` | 0 |

## Interrupção

| Indicador | Valor |
| --- | ---: |
| `process_down_ms` | 30410.75 |
| `outage_to_ready_ms` | 33793.41 |
| `drain_after_readiness_ms` | 36122 |

Consulte `report.json` para denominadores, metas e séries.
O manifesto inventaria o plano, amostras e evidências desta rodada.
