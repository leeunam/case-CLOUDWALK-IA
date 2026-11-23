# Avaliação c04-targeted-060c97465807497ca3726fe6a2cfef88

Modo real. Elegibilidade inconclusive.
1 relatos e 13 controles.
Controles injetados pelo avaliador: 1.

| Campo | Acerto bruto | Acerto aplicado | Cobertura automática |
| --- | --- | --- | --- |
| category | sem medição (n=0) | sem medição (n=0) | sem medição (n=0) |
| priority | 0/1 | 0/1 | 1/1 |

## by_mask

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | sem medição (n=0) |
| category | applied_accuracy | sem medição (n=0) |
| category | correct_abstention | sem medição (n=0) |
| category | undue_abstention | sem medição (n=0) |
| category | invalid_output | sem medição (n=0) |
| category | operational_error | sem medição (n=0) |
| category | unapplied_choices | sem medição (n=0) |
| category | review | sem medição (n=0) |
| category | automatic_coverage | sem medição (n=0) |
| category | correct_completion_coverage | sem medição (n=0) |
| priority | raw_accuracy | 0/1 |
| priority | applied_accuracy | 0/1 |
| priority | correct_abstention | 0/1 |
| priority | undue_abstention | 0/1 |
| priority | invalid_output | 0/1 |
| priority | operational_error | 0/1 |
| priority | unapplied_choices | 0/1 |
| priority | review | 0/1 |
| priority | automatic_coverage | 1/1 |
| priority | correct_completion_coverage | 0/1 |
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
| rotina | raw_accuracy | sem medição (n=0) |
| rotina | applied_accuracy | sem medição (n=0) |
| rotina | correct_abstention | sem medição (n=0) |
| rotina | undue_abstention | sem medição (n=0) |
| rotina | invalid_output | sem medição (n=0) |
| rotina | operational_error | sem medição (n=0) |
| rotina | unapplied_choices | sem medição (n=0) |
| rotina | review | sem medição (n=0) |
| rotina | automatic_coverage | sem medição (n=0) |
| rotina | correct_completion_coverage | sem medição (n=0) |
| urgente | raw_accuracy | 0/1 |
| urgente | applied_accuracy | 0/1 |
| urgente | correct_abstention | 0/1 |
| urgente | undue_abstention | 0/1 |
| urgente | invalid_output | 0/1 |
| urgente | operational_error | 0/1 |
| urgente | unapplied_choices | 0/1 |
| urgente | review | 0/1 |
| urgente | automatic_coverage | 1/1 |
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
| category | raw_accuracy | sem medição (n=0) |
| category | applied_accuracy | sem medição (n=0) |
| category | correct_abstention | sem medição (n=0) |
| category | undue_abstention | sem medição (n=0) |
| category | invalid_output | sem medição (n=0) |
| category | operational_error | sem medição (n=0) |
| category | unapplied_choices | sem medição (n=0) |
| category | review | sem medição (n=0) |
| category | automatic_coverage | sem medição (n=0) |
| category | correct_completion_coverage | sem medição (n=0) |
| priority | raw_accuracy | 0/1 |
| priority | applied_accuracy | 0/1 |
| priority | correct_abstention | 0/1 |
| priority | undue_abstention | 0/1 |
| priority | invalid_output | 0/1 |
| priority | operational_error | 0/1 |
| priority | unapplied_choices | 0/1 |
| priority | review | 0/1 |
| priority | automatic_coverage | 1/1 |
| priority | correct_completion_coverage | 0/1 |

## Urgentes com prioridade omitida

- applied_urgent · 0/1
- applied_lower · 1/1
- review · 0/1
- abstained · 0/1
- invalid · 0/1
- operational_error · 0/1

## Indicadores

- p50 · 4061.104 ms (n=1)
- channel_field_preservation_ratio · 10/10
- complete_or_invalid_controls_model_calls · 0/4
- partial_application_after_abstention_or_error · 0/4
- automatic_completion_on_expected_review_cases · sem medição (n=0)
- automatic_non_urgent_applied_when_expected_urgent · 1/1
- automatic_coverage_on_fully_classifiable_cases_min · 1/1
- raw_urgent_recognition_min · 0/1
- warm_total_latency_p95_ms_max · 4061.104 ms (n=1)
- applied_category_accuracy · sem medição (n=0)
- applied_priority_accuracy · 0/1

## Uso por tentativa e requisição

- attempts · 9 (9/9 amostras)
- requests · 7 (9/9 amostras)
- questions · 10 (9/9 amostras)
- input_tokens · sem medição (0/7 amostras)
- output_tokens · sem medição (0/7 amostras)
- observed_api_usd · 0.0 (7/7 amostras)
- estimated_api_usd · sem medição (0/7 amostras)
