# Avaliação luna-r5-8ff7998ec1654eea8328825b154dac09

Modo real. Elegibilidade inconclusive.
6 relatos e 0 controles.
Controles injetados pelo avaliador: 0.
Perfil `observed-total-luna-r5` · protocolo 1.5.0 · relatório 1.6.0 · IPC 1.1.0.

| Campo | Acerto bruto | Acerto aplicado | Cobertura automática |
| --- | --- | --- | --- |
| category | 4/4 | 2/2 | 2/2 |
| priority | 4/4 | 2/2 | 2/2 |

## by_mask

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 2/2 |
| category | applied_accuracy | 1/1 |
| category | correct_abstention | 1/2 |
| category | undue_abstention | 0/2 |
| category | invalid_output | 0/2 |
| category | operational_error | 0/2 |
| category | unapplied_choices | 0/2 |
| category | review | 1/2 |
| category | automatic_coverage | 1/1 |
| category | correct_completion_coverage | 1/1 |
| priority | raw_accuracy | 2/2 |
| priority | applied_accuracy | 1/1 |
| priority | correct_abstention | 1/2 |
| priority | undue_abstention | 0/2 |
| priority | invalid_output | 0/2 |
| priority | operational_error | 0/2 |
| priority | unapplied_choices | 0/2 |
| priority | review | 1/2 |
| priority | automatic_coverage | 1/1 |
| priority | correct_completion_coverage | 1/1 |
| category+priority | raw_accuracy | 4/4 |
| category+priority | applied_accuracy | 2/2 |
| category+priority | correct_abstention | 2/4 |
| category+priority | undue_abstention | 0/4 |
| category+priority | invalid_output | 0/4 |
| category+priority | operational_error | 0/4 |
| category+priority | unapplied_choices | 0/4 |
| category+priority | review | 1/2 |
| category+priority | automatic_coverage | 1/1 |
| category+priority | correct_completion_coverage | 1/1 |

## by_stratum

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| rotina | raw_accuracy | 3/3 |
| rotina | applied_accuracy | 3/3 |
| rotina | correct_abstention | 0/3 |
| rotina | undue_abstention | 0/3 |
| rotina | invalid_output | 0/3 |
| rotina | operational_error | 0/3 |
| rotina | unapplied_choices | 0/3 |
| rotina | review | 0/2 |
| rotina | automatic_coverage | 2/2 |
| rotina | correct_completion_coverage | 2/2 |
| urgente | raw_accuracy | 1/1 |
| urgente | applied_accuracy | 1/1 |
| urgente | correct_abstention | 0/1 |
| urgente | undue_abstention | 0/1 |
| urgente | invalid_output | 0/1 |
| urgente | operational_error | 0/1 |
| urgente | unapplied_choices | 0/1 |
| urgente | review | 0/1 |
| urgente | automatic_coverage | 1/1 |
| urgente | correct_completion_coverage | 1/1 |
| ambiguo | raw_accuracy | 4/4 |
| ambiguo | applied_accuracy | sem medição (n=0) |
| ambiguo | correct_abstention | 4/4 |
| ambiguo | undue_abstention | 0/4 |
| ambiguo | invalid_output | 0/4 |
| ambiguo | operational_error | 0/4 |
| ambiguo | unapplied_choices | 0/4 |
| ambiguo | review | 3/3 |
| ambiguo | automatic_coverage | sem medição (n=0) |
| ambiguo | correct_completion_coverage | sem medição (n=0) |

## by_field

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 4/4 |
| category | applied_accuracy | 2/2 |
| category | correct_abstention | 2/4 |
| category | undue_abstention | 0/4 |
| category | invalid_output | 0/4 |
| category | operational_error | 0/4 |
| category | unapplied_choices | 0/4 |
| category | review | 2/4 |
| category | automatic_coverage | 2/2 |
| category | correct_completion_coverage | 2/2 |
| priority | raw_accuracy | 4/4 |
| priority | applied_accuracy | 2/2 |
| priority | correct_abstention | 2/4 |
| priority | undue_abstention | 0/4 |
| priority | invalid_output | 0/4 |
| priority | operational_error | 0/4 |
| priority | unapplied_choices | 0/4 |
| priority | review | 2/4 |
| priority | automatic_coverage | 2/2 |
| priority | correct_completion_coverage | 2/2 |

## Urgentes com prioridade omitida

- applied_urgent · 1/1
- applied_lower · 0/1
- review · 0/1
- abstained · 0/1
- invalid · 0/1
- operational_error · 0/1

## Indicadores

- p50 · 1944.617 ms (n=6)
- channel_field_preservation_ratio · 4/4
- complete_or_invalid_controls_model_calls · sem medição (n=0)
- partial_application_after_abstention_or_error · 0/3
- automatic_completion_on_expected_review_cases · 0/3
- automatic_non_urgent_applied_when_expected_urgent · 0/1
- automatic_coverage_on_fully_classifiable_cases_min · 3/3
- raw_urgent_recognition_min · 1/1
- observed_total_latency_p95_ms_max · 2886.371 ms (n=6)
- applied_category_accuracy · 2/2
- applied_priority_accuracy · 2/2

## Uso por tentativa e requisição

- attempts · 6 (6/6 amostras)
- requests · 6 (6/6 amostras)
- questions · 8 (6/6 amostras)
- input_tokens · 8808 (6/6 amostras)
- output_tokens · 312 (6/6 amostras)
- observed_api_usd · 0.00227389 (6/6 amostras)
- estimated_api_usd · 0.0040847999999999995 (6/6 amostras)
