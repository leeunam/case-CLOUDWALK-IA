# F08-A — f08-reference-1795207088594-f6c560-02

**Estado** — aprovado

Cenário `reference`, revisão `10125a57a8d72abd69a646dea0970cca59cf3ce2`.


| Indicador | Inicial | Segundo turno |
| --- | ---: | ---: |
| Planejados | 1500 | 300 |
| Emitidos | 1500 | 300 |
| HTTP 202 | 1500 | 300 |
| Timeouts HTTP | 0 | 0 |
| Aceite p50 (ms) | 66 | 66.21 |
| Aceite p95 (ms) | 112 | 134.47 |
| Resposta persistida p50 (ms) | 302.10 | 309.73 |
| Resposta persistida p95 (ms) | 28090.74 | 3622.82 |

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
| `host_cpu_busy_percent_peak` | 52.55 |
| `host_ram_used_bytes_peak` | 10058428416 |

## Kafka

| Indicador | Valor |
| --- | ---: |
| `repeated_records_observed` | 0 |
| `dead_letter_records_observed` | 0 |

## Backlog

| Indicador | Valor |
| --- | ---: |
| `max_outbox_pending` | 177 |
| `max_outbox_failed` | 0 |
| `max_consumer_lag` | 140 |
| `max_cases_waiting_processing` | 197 |
| `pending_cases_at_snapshot` | 0 |

## Interrupção

| Indicador | Valor |
| --- | ---: |
| `process_down_ms` | 30321.07 |
| `outage_to_ready_ms` | 34358.79 |
| `drain_after_readiness_ms` | 33737 |

Consulte `report.json` para denominadores, metas e séries.
O manifesto inventaria o plano, amostras e evidências desta rodada.
