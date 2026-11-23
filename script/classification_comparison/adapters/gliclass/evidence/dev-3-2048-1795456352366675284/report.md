# Avaliação c02-7542ee31f5ee457ea606ee7d957a53cc

Modo real. Elegibilidade inconclusive.
3 relatos e 13 controles.
Controles injetados pelo avaliador: 1.

| Campo | Acerto bruto | Acerto aplicado | Cobertura automática |
| --- | --- | --- | --- |
| category | 0/3 | sem medição (n=0) | 0/3 |
| priority | sem medição (n=0) | sem medição (n=0) | sem medição (n=0) |

## by_mask

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 0/3 |
| category | applied_accuracy | sem medição (n=0) |
| category | correct_abstention | 0/3 |
| category | undue_abstention | 3/3 |
| category | invalid_output | 0/3 |
| category | operational_error | 0/3 |
| category | unapplied_choices | 0/3 |
| category | review | 3/3 |
| category | automatic_coverage | 0/3 |
| category | correct_completion_coverage | 0/3 |
| priority | raw_accuracy | sem medição (n=0) |
| priority | applied_accuracy | sem medição (n=0) |
| priority | correct_abstention | sem medição (n=0) |
| priority | undue_abstention | sem medição (n=0) |
| priority | invalid_output | sem medição (n=0) |
| priority | operational_error | sem medição (n=0) |
| priority | unapplied_choices | sem medição (n=0) |
| priority | review | sem medição (n=0) |
| priority | automatic_coverage | sem medição (n=0) |
| priority | correct_completion_coverage | sem medição (n=0) |
| category+priority | raw_accuracy | sem medição (n=0) |
| category+priority | applied_accuracy | sem medição (n=0) |
| category+priority | correct_abstention | sem medição (n=0) |
| category+priority | undue_abstention | sem medição (n=0) |
| category+priority | invalid_output | sem medição (n=0) |
| category+priority | operational_error | sem medição (n=0) |
| category+priority | unapplied_choices | sem medição (n=0) |
| category+priority | review | sem medição (n=0) |
| category+priority | automatic_coverage | sem medição (n=0) |
| category+priority | correct_completion_coverage | sem medição (n=0) |

## by_stratum

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| rotina | raw_accuracy | 0/2 |
| rotina | applied_accuracy | sem medição (n=0) |
| rotina | correct_abstention | 0/2 |
| rotina | undue_abstention | 2/2 |
| rotina | invalid_output | 0/2 |
| rotina | operational_error | 0/2 |
| rotina | unapplied_choices | 0/2 |
| rotina | review | 2/2 |
| rotina | automatic_coverage | 0/2 |
| rotina | correct_completion_coverage | 0/2 |
| urgente | raw_accuracy | 0/1 |
| urgente | applied_accuracy | sem medição (n=0) |
| urgente | correct_abstention | 0/1 |
| urgente | undue_abstention | 1/1 |
| urgente | invalid_output | 0/1 |
| urgente | operational_error | 0/1 |
| urgente | unapplied_choices | 0/1 |
| urgente | review | 1/1 |
| urgente | automatic_coverage | 0/1 |
| urgente | correct_completion_coverage | 0/1 |
| ambiguo | raw_accuracy | sem medição (n=0) |
| ambiguo | applied_accuracy | sem medição (n=0) |
| ambiguo | correct_abstention | sem medição (n=0) |
| ambiguo | undue_abstention | sem medição (n=0) |
| ambiguo | invalid_output | sem medição (n=0) |
| ambiguo | operational_error | sem medição (n=0) |
| ambiguo | unapplied_choices | sem medição (n=0) |
| ambiguo | review | sem medição (n=0) |
| ambiguo | automatic_coverage | sem medição (n=0) |
| ambiguo | correct_completion_coverage | sem medição (n=0) |

## by_field

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 0/3 |
| category | applied_accuracy | sem medição (n=0) |
| category | correct_abstention | 0/3 |
| category | undue_abstention | 3/3 |
| category | invalid_output | 0/3 |
| category | operational_error | 0/3 |
| category | unapplied_choices | 0/3 |
| category | review | 3/3 |
| category | automatic_coverage | 0/3 |
| category | correct_completion_coverage | 0/3 |
| priority | raw_accuracy | sem medição (n=0) |
| priority | applied_accuracy | sem medição (n=0) |
| priority | correct_abstention | sem medição (n=0) |
| priority | undue_abstention | sem medição (n=0) |
| priority | invalid_output | sem medição (n=0) |
| priority | operational_error | sem medição (n=0) |
| priority | unapplied_choices | sem medição (n=0) |
| priority | review | sem medição (n=0) |
| priority | automatic_coverage | sem medição (n=0) |
| priority | correct_completion_coverage | sem medição (n=0) |

## Urgentes com prioridade omitida

- applied_urgent · sem medição (n=0)
- applied_lower · sem medição (n=0)
- review · sem medição (n=0)
- abstained · sem medição (n=0)
- invalid · sem medição (n=0)
- operational_error · sem medição (n=0)

## Indicadores

- p50 · 3865.117 ms (n=3)
- channel_field_preservation_ratio · 12/12
- complete_or_invalid_controls_model_calls · 0/4
- partial_application_after_abstention_or_error · 0/12
- automatic_completion_on_expected_review_cases · sem medição (n=0)
- automatic_non_urgent_applied_when_expected_urgent · sem medição (n=0)
- automatic_coverage_on_fully_classifiable_cases_min · 0/3
- raw_urgent_recognition_min · sem medição (n=0)
- warm_total_latency_p95_ms_max · 4034.109 ms (n=3)
- applied_category_accuracy · sem medição (n=0)
- applied_priority_accuracy · sem medição (n=0)

## Uso por tentativa e requisição

- attempts · 11 (11/11 amostras)
- requests · 6 (11/11 amostras)
- questions · 6 (11/11 amostras)
- input_tokens · sem medição (0/6 amostras)
- output_tokens · sem medição (0/6 amostras)
- observed_api_usd · 0.0 (6/6 amostras)
- estimated_api_usd · sem medição (0/6 amostras)
