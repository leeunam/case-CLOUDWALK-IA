# F08-A — f08-reference-1795208792430-8b61b6-04

**Estado** — reprovado

Cenário `reference`, revisão `dfbcc79f4ced07e5460eb73d06e956d94799d453`.

- metas do ensaio não atingidas: escoamento_na_janela, todos_segundos_turnos_enviados_e_concluidos

| Indicador | Inicial | Segundo turno |
| --- | ---: | ---: |
| Planejados | 1500 | 300 |
| Emitidos | 1500 | 60 |
| HTTP 202 | 1500 | 60 |
| Timeouts HTTP | 0 | 0 |
| Aceite p50 (ms) | 86 | 100.92 |
| Aceite p95 (ms) | 126 | 194.92 |
| Resposta persistida p50 (ms) | 335.53 | 382.56 |
| Resposta persistida p95 (ms) | 492.77 | 537.69 |

Iterações descartadas pelo k6 — 0

## Vazão

| Indicador | Valor |
| --- | ---: |
| `offered_initial_per_s` | 5.00 |
| `accepted_initial_per_s` | 5.00 |

## Conclusões

| Indicador | Valor |
| --- | ---: |
| `ai_turns_in_window` | 356 |
| `resolved_cases_in_window` | 55 |
| `ai_turns_per_s` | 0.85 |
| `resolved_cases_per_s` | 0.13 |

## Persistência

| Indicador | Valor |
| --- | ---: |
| `confirmed_losses` | 0 |
| `duplicated_effect_identities` | 0 |
| `not_reconciled_http_202` | 1204 |

## Recursos

| Indicador | Valor |
| --- | ---: |
| `host_cpu_busy_percent_peak` | 64.13 |
| `host_ram_used_bytes_peak` | 9112870912 |

## Kafka

| Indicador | Valor |
| --- | ---: |
| `repeated_records_observed` | 0 |
| `dead_letter_records_observed` | 0 |

## Backlog

| Indicador | Valor |
| --- | ---: |
| `max_outbox_pending` | 209 |
| `max_outbox_failed` | 0 |
| `max_consumer_lag` | 1206 |
| `max_cases_waiting_processing` | 503 |
| `pending_cases_at_snapshot` | 0 |

## Interrupção

| Indicador | Valor |
| --- | ---: |
| `process_down_ms` | 30523.16 |
| `outage_to_ready_ms` | 34843.38 |
| `drain_after_readiness_ms` | indisponível |

Consulte `report.json` para denominadores, metas e séries.
O manifesto inventaria o plano, amostras e evidências desta rodada.
