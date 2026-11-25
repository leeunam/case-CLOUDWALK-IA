# Avaliação c05-58e8f0b5c64547b98d6f5ca738bf2c6e

Modo real. Elegibilidade fail.
36 relatos e 13 controles.
Controles injetados pelo avaliador: 1.
Perfil `observed-total-1.1` · protocolo 1.1.0 · relatório 1.2.0 · IPC 1.1.0.

| Campo | Acerto bruto | Acerto aplicado | Cobertura automática |
| --- | --- | --- | --- |
| category | 21/24 | 19/22 | 19/19 |
| priority | 23/24 | 19/20 | 19/19 |

## by_mask

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 10/12 |
| category | applied_accuracy | 10/12 |
| category | correct_abstention | 0/12 |
| category | undue_abstention | 0/12 |
| category | invalid_output | 0/12 |
| category | operational_error | 0/12 |
| category | unapplied_choices | 0/12 |
| category | review | 0/12 |
| category | automatic_coverage | 10/10 |
| category | correct_completion_coverage | 10/10 |
| priority | raw_accuracy | 11/12 |
| priority | applied_accuracy | 9/10 |
| priority | correct_abstention | 2/12 |
| priority | undue_abstention | 0/12 |
| priority | invalid_output | 0/12 |
| priority | operational_error | 0/12 |
| priority | unapplied_choices | 0/12 |
| priority | review | 2/12 |
| priority | automatic_coverage | 10/10 |
| priority | correct_completion_coverage | 9/10 |
| category+priority | raw_accuracy | 23/24 |
| category+priority | applied_accuracy | 19/20 |
| category+priority | correct_abstention | 2/24 |
| category+priority | undue_abstention | 0/24 |
| category+priority | invalid_output | 0/24 |
| category+priority | operational_error | 0/24 |
| category+priority | unapplied_choices | 2/24 |
| category+priority | review | 2/12 |
| category+priority | automatic_coverage | 9/9 |
| category+priority | correct_completion_coverage | 9/9 |

## by_stratum

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| rotina | raw_accuracy | 28/29 |
| rotina | applied_accuracy | 28/29 |
| rotina | correct_abstention | 0/29 |
| rotina | undue_abstention | 0/29 |
| rotina | invalid_output | 0/29 |
| rotina | operational_error | 0/29 |
| rotina | unapplied_choices | 0/29 |
| rotina | review | 0/22 |
| rotina | automatic_coverage | 22/22 |
| rotina | correct_completion_coverage | 21/22 |
| urgente | raw_accuracy | 9/9 |
| urgente | applied_accuracy | 9/9 |
| urgente | correct_abstention | 0/9 |
| urgente | undue_abstention | 0/9 |
| urgente | invalid_output | 0/9 |
| urgente | operational_error | 0/9 |
| urgente | unapplied_choices | 0/9 |
| urgente | review | 0/7 |
| urgente | automatic_coverage | 7/7 |
| urgente | correct_completion_coverage | 7/7 |
| ambiguo | raw_accuracy | 7/10 |
| ambiguo | applied_accuracy | 1/4 |
| ambiguo | correct_abstention | 4/10 |
| ambiguo | undue_abstention | 0/10 |
| ambiguo | invalid_output | 0/10 |
| ambiguo | operational_error | 0/10 |
| ambiguo | unapplied_choices | 2/10 |
| ambiguo | review | 4/7 |
| ambiguo | automatic_coverage | sem medição (n=0) |
| ambiguo | correct_completion_coverage | sem medição (n=0) |

## by_field

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 21/24 |
| category | applied_accuracy | 19/22 |
| category | correct_abstention | 0/24 |
| category | undue_abstention | 0/24 |
| category | invalid_output | 0/24 |
| category | operational_error | 0/24 |
| category | unapplied_choices | 2/24 |
| category | review | 2/24 |
| category | automatic_coverage | 19/19 |
| category | correct_completion_coverage | 19/19 |
| priority | raw_accuracy | 23/24 |
| priority | applied_accuracy | 19/20 |
| priority | correct_abstention | 4/24 |
| priority | undue_abstention | 0/24 |
| priority | invalid_output | 0/24 |
| priority | operational_error | 0/24 |
| priority | unapplied_choices | 0/24 |
| priority | review | 4/24 |
| priority | automatic_coverage | 19/19 |
| priority | correct_completion_coverage | 18/19 |

## Urgentes com prioridade omitida

- applied_urgent · 6/6
- applied_lower · 0/6
- review · 0/6
- abstained · 0/6
- invalid · 0/6
- operational_error · 0/6

## Indicadores

- p50 · 1516.830 ms (n=36)
- channel_field_preservation_ratio · 33/33
- complete_or_invalid_controls_model_calls · 0/4
- partial_application_after_abstention_or_error · 0/9
- automatic_completion_on_expected_review_cases · 3/7
- automatic_non_urgent_applied_when_expected_urgent · 0/6
- automatic_coverage_on_fully_classifiable_cases_min · 29/29
- raw_urgent_recognition_min · 6/6
- observed_total_latency_p95_ms_max · 2493.510 ms (n=36)
- applied_category_accuracy · 19/22
- applied_priority_accuracy · 19/20

## Uso por tentativa e requisição

- attempts · 44 (44/44 amostras)
- requests · 44 (44/44 amostras)
- questions · 59 (44/44 amostras)
- input_tokens · 47557 (44/44 amostras)
- output_tokens · 690 (44/44 amostras)
- observed_api_usd · 0.02197127 (44/44 amostras)
- estimated_api_usd · 0.021971225 (44/44 amostras)
