# F08-A — f08-reference-1795208792430-8b61b6-01

**Estado** — aprovado

Cenário `reference`, revisão `dfbcc79f4ced07e5460eb73d06e956d94799d453`.


| Indicador | Inicial | Segundo turno |
| --- | ---: | ---: |
| Planejados | 1500 | 300 |
| Emitidos | 1500 | 300 |
| HTTP 202 | 1500 | 300 |
| Timeouts HTTP | 0 | 0 |
| Aceite p50 (ms) | 80 | 81.36 |
| Aceite p95 (ms) | 142 | 159.67 |
| Resposta persistida p50 (ms) | 312.59 | 337.95 |
| Resposta persistida p95 (ms) | 433.06 | 477.94 |

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
| `host_cpu_busy_percent_peak` | 65.47 |
| `host_ram_used_bytes_peak` | 8964915200 |

## Kafka

| Indicador | Valor |
| --- | ---: |
| `repeated_records_observed` | 0 |
| `dead_letter_records_observed` | 0 |

## Backlog

| Indicador | Valor |
| --- | ---: |
| `max_outbox_pending` | 3 |
| `max_outbox_failed` | 0 |
| `max_consumer_lag` | 2 |
| `max_cases_waiting_processing` | 4 |
| `pending_cases_at_snapshot` | 0 |

Consulte `report.json` para denominadores, metas e séries.
O manifesto inventaria o plano, amostras e evidências desta rodada.
