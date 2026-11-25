# Avaliação luna-r5-20d81be917a04b2ab0910b631b970ece

Modo real. Lote interrompido. Elegibilidade inconclusiva.
30 relatos e 0 controles.
Controles injetados pelo avaliador: 0.
Perfil `observed-total-luna-r5` · protocolo 1.5.0 · relatório 1.6.0 · IPC 1.1.0.

| Campo | Acerto bruto | Acerto aplicado | Cobertura automática |
| --- | --- | --- | --- |
| category | 3/18 | sem medição (n=0) | 0/16 |
| priority | 3/18 | 1/1 | 1/16 |

## by_mask

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 2/12 |
| category | applied_accuracy | sem medição (n=0) |
| category | correct_abstention | 2/12 |
| category | undue_abstention | 10/12 |
| category | invalid_output | 0/12 |
| category | operational_error | 0/12 |
| category | unapplied_choices | 0/12 |
| category | review | 12/12 |
| category | automatic_coverage | 0/10 |
| category | correct_completion_coverage | 0/10 |
| priority | raw_accuracy | 3/12 |
| priority | applied_accuracy | 1/1 |
| priority | correct_abstention | 2/12 |
| priority | undue_abstention | 9/12 |
| priority | invalid_output | 0/12 |
| priority | operational_error | 0/12 |
| priority | unapplied_choices | 0/12 |
| priority | review | 11/12 |
| priority | automatic_coverage | 1/10 |
| priority | correct_completion_coverage | 1/10 |
| category+priority | raw_accuracy | 1/12 |
| category+priority | applied_accuracy | sem medição (n=0) |
| category+priority | correct_abstention | 0/12 |
| category+priority | undue_abstention | 9/12 |
| category+priority | invalid_output | 0/12 |
| category+priority | operational_error | 2/12 |
| category+priority | unapplied_choices | 1/12 |
| category+priority | review | 6/6 |
| category+priority | automatic_coverage | 0/6 |
| category+priority | correct_completion_coverage | 0/6 |

## by_stratum

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| rotina | raw_accuracy | 2/27 |
| rotina | applied_accuracy | 1/1 |
| rotina | correct_abstention | 0/27 |
| rotina | undue_abstention | 23/27 |
| rotina | invalid_output | 0/27 |
| rotina | operational_error | 2/27 |
| rotina | unapplied_choices | 1/27 |
| rotina | review | 21/22 |
| rotina | automatic_coverage | 1/22 |
| rotina | correct_completion_coverage | 1/22 |
| urgente | raw_accuracy | 0/5 |
| urgente | applied_accuracy | sem medição (n=0) |
| urgente | correct_abstention | 0/5 |
| urgente | undue_abstention | 5/5 |
| urgente | invalid_output | 0/5 |
| urgente | operational_error | 0/5 |
| urgente | unapplied_choices | 0/5 |
| urgente | review | 4/4 |
| urgente | automatic_coverage | 0/4 |
| urgente | correct_completion_coverage | 0/4 |
| ambiguo | raw_accuracy | 4/4 |
| ambiguo | applied_accuracy | sem medição (n=0) |
| ambiguo | correct_abstention | 4/4 |
| ambiguo | undue_abstention | 0/4 |
| ambiguo | invalid_output | 0/4 |
| ambiguo | operational_error | 0/4 |
| ambiguo | unapplied_choices | 0/4 |
| ambiguo | review | 4/4 |
| ambiguo | automatic_coverage | sem medição (n=0) |
| ambiguo | correct_completion_coverage | sem medição (n=0) |

## by_field

| Fatia | Métrica | Contagem |
| --- | --- | --- |
| category | raw_accuracy | 3/18 |
| category | applied_accuracy | sem medição (n=0) |
| category | correct_abstention | 2/18 |
| category | undue_abstention | 14/18 |
| category | invalid_output | 0/18 |
| category | operational_error | 1/18 |
| category | unapplied_choices | 1/18 |
| category | review | 18/18 |
| category | automatic_coverage | 0/16 |
| category | correct_completion_coverage | 0/16 |
| priority | raw_accuracy | 3/18 |
| priority | applied_accuracy | 1/1 |
| priority | correct_abstention | 2/18 |
| priority | undue_abstention | 14/18 |
| priority | invalid_output | 0/18 |
| priority | operational_error | 1/18 |
| priority | unapplied_choices | 0/18 |
| priority | review | 17/18 |
| priority | automatic_coverage | 1/16 |
| priority | correct_completion_coverage | 1/16 |

## Urgentes com prioridade omitida

- applied_urgent · 0/4 (parcial)
- applied_lower · 0/4 (parcial)
- review · 4/4 (parcial)
- abstained · 4/4 (parcial)
- invalid · 0/4 (parcial)
- operational_error · 0/4 (parcial)

## Indicadores

- p50 · 2130.830 ms (n=30) (parcial)
- channel_field_preservation_ratio · 24/24
- complete_or_invalid_controls_model_calls · sem medição (n=0)
- partial_application_after_abstention_or_error · 0/29
- automatic_completion_on_expected_review_cases · 0/4 (parcial)
- automatic_non_urgent_applied_when_expected_urgent · 0/4 (parcial)
- automatic_coverage_on_fully_classifiable_cases_min · 1/26 (parcial)
- raw_urgent_recognition_min · 0/4 (parcial)
- observed_total_latency_p95_ms_max · 3269.135 ms (n=30) (parcial)
- applied_category_accuracy · sem medição (n=0)
- applied_priority_accuracy · 1/1

## Uso por tentativa e requisição

- attempts · 30 (30/30 amostras)
- requests · 30 (30/30 amostras)
- questions · 36 (30/30 amostras)
- input_tokens · 42999 (29/30 amostras)
- output_tokens · 1544 (29/30 amostras)
- observed_api_usd · 0.00765168 (29/30 amostras)
- estimated_api_usd · 0.0199788 (29/30 amostras)
