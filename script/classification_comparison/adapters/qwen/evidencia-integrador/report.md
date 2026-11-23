# Avaliação c02-6ee4179fa01f4c32a2406758c9195904

Modo fixture. Elegibilidade inconclusive.
24 relatos e 13 controles.
Controles injetados pelo avaliador: 1.

| Campo | Acerto bruto | Acerto aplicado | Cobertura automática |
| --- | --- | --- | --- |
| category | 11/16 | 4/4 | 4/11 |
| priority | 6/16 | 1/1 | 1/11 |

## by_mask

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 5/8 |
| category | applied_accuracy | 3/3 |
| category | correct_abstention | 2/8 |
| category | undue_abstention | 3/8 |
| category | invalid_output | 0/8 |
| category | operational_error | 0/8 |
| category | unapplied_choices | 0/8 |
| category | review | 5/8 |
| category | automatic_coverage | 3/6 |
| category | correct_completion_coverage | 3/6 |
| priority | raw_accuracy | 2/8 |
| priority | applied_accuracy | sem medição (n=0) |
| priority | correct_abstention | 2/8 |
| priority | undue_abstention | 6/8 |
| priority | invalid_output | 0/8 |
| priority | operational_error | 0/8 |
| priority | unapplied_choices | 0/8 |
| priority | review | 8/8 |
| priority | automatic_coverage | 0/6 |
| priority | correct_completion_coverage | 0/6 |
| category+priority | raw_accuracy | 10/16 |
| category+priority | applied_accuracy | 2/2 |
| category+priority | correct_abstention | 4/16 |
| category+priority | undue_abstention | 6/16 |
| category+priority | invalid_output | 0/16 |
| category+priority | operational_error | 0/16 |
| category+priority | unapplied_choices | 4/16 |
| category+priority | review | 7/8 |
| category+priority | automatic_coverage | 1/5 |
| category+priority | correct_completion_coverage | 1/5 |

## by_stratum

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| rotina | raw_accuracy | 4/14 |
| rotina | applied_accuracy | 3/3 |
| rotina | correct_abstention | 0/14 |
| rotina | undue_abstention | 10/14 |
| rotina | invalid_output | 0/14 |
| rotina | operational_error | 0/14 |
| rotina | unapplied_choices | 1/14 |
| rotina | review | 9/11 |
| rotina | automatic_coverage | 2/11 |
| rotina | correct_completion_coverage | 2/11 |
| urgente | raw_accuracy | 3/8 |
| urgente | applied_accuracy | 2/2 |
| urgente | correct_abstention | 0/8 |
| urgente | undue_abstention | 5/8 |
| urgente | invalid_output | 0/8 |
| urgente | operational_error | 0/8 |
| urgente | unapplied_choices | 1/8 |
| urgente | review | 4/6 |
| urgente | automatic_coverage | 2/6 |
| urgente | correct_completion_coverage | 2/6 |
| ambiguo | raw_accuracy | 10/10 |
| ambiguo | applied_accuracy | sem medição (n=0) |
| ambiguo | correct_abstention | 8/10 |
| ambiguo | undue_abstention | 0/10 |
| ambiguo | invalid_output | 0/10 |
| ambiguo | operational_error | 0/10 |
| ambiguo | unapplied_choices | 2/10 |
| ambiguo | review | 7/7 |
| ambiguo | automatic_coverage | sem medição (n=0) |
| ambiguo | correct_completion_coverage | sem medição (n=0) |

## by_field

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 11/16 |
| category | applied_accuracy | 4/4 |
| category | correct_abstention | 4/16 |
| category | undue_abstention | 5/16 |
| category | invalid_output | 0/16 |
| category | operational_error | 0/16 |
| category | unapplied_choices | 3/16 |
| category | review | 12/16 |
| category | automatic_coverage | 4/11 |
| category | correct_completion_coverage | 4/11 |
| priority | raw_accuracy | 6/16 |
| priority | applied_accuracy | 1/1 |
| priority | correct_abstention | 4/16 |
| priority | undue_abstention | 10/16 |
| priority | invalid_output | 0/16 |
| priority | operational_error | 0/16 |
| priority | unapplied_choices | 1/16 |
| priority | review | 15/16 |
| priority | automatic_coverage | 1/11 |
| priority | correct_completion_coverage | 1/11 |

## Urgentes com prioridade omitida

- applied_urgent · 0/4
- applied_lower · 0/4
- review · 4/4
- abstained · 4/4
- invalid · 0/4
- operational_error · 0/4

## Indicadores

- p50 · sem medição (n=24)
- channel_field_preservation_ratio · 25/25
- complete_or_invalid_controls_model_calls · 0/4
- partial_application_after_abstention_or_error · 0/25
- automatic_completion_on_expected_review_cases · 0/7
- automatic_non_urgent_applied_when_expected_urgent · 0/4
- automatic_coverage_on_fully_classifiable_cases_min · 4/17
- raw_urgent_recognition_min · 0/4
- warm_total_latency_p95_ms_max · sem medição (n=24)
- applied_category_accuracy · 4/4
- applied_priority_accuracy · 1/1

## Uso por tentativa e requisição

- attempts · 32 (32/32 amostras)
- requests · 32 (32/32 amostras)
- questions · 43 (32/32 amostras)
- input_tokens · sem medição (0/32 amostras)
- output_tokens · sem medição (0/32 amostras)
- observed_api_usd · sem medição (0/32 amostras)
- estimated_api_usd · sem medição (0/32 amostras)
