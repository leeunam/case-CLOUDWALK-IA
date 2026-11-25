# C05-E · Reavaliação dirigida de 20610ca

**Especificação — não aprovada integralmente.** Os quatro vetores originais agora têm o resultado esperado. A condição de aceite do primeiro achado ainda falha quando a classificação expira e, simultaneamente, a versão retornada diverge. O lote pode enviar outra requisição após ter liberado automaticamente a primeira reserva.

**Qualidade — não aprovada integralmente.** Além do resíduo de timeout, a atualização de uma conta da versão 2 pode manter subcontabilizada uma cobrança comprovada que já consta da própria conta. O projeto informa que a conta real ainda não foi inicializada. A consequência demonstrada da migração é restrita a uma conta legada sintética.

Branch `feat/executor-qwen-final`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao`. Base `511047d1a0a8ada5c1dffca2386f8f43739666fe`, correção `20610ca3b431158767e3eaf6d136aca5e48087f3`. Os caminhos abaixo são relativos à worktree.

## Quatro achados anteriores

| Achado em 511047d | Estado em 20610ca | Resultado conferido |
|---|---|---|
| P1 — timeout descarta a cobrança | **NOT ADDRESSED integralmente** | O caso original de US$ 2,25 está corrigido. O corpo já recebido é persistido antes do parse, o prefixo registra timeout e USD, o total fica em US$ 9,35 e a conta recusa outro despacho. O caso de custo menor com timeout simples também retém a reserva. O resíduo descrito abaixo permite liquidar automaticamente um timeout de custo menor. |
| P1 — escala dos créditos anula USD independente | **ADDRESSED** para respostas processadas pelo novo executor | US$ 2,25 com créditos terminados em zeros resultaram em US$ 9,35 contabilizados e congelamento. Uma fonte maior com precisão irrepresentável segurou a reserva até recibo suficiente. A migração de evidência já gravada tem um problema separado, abaixo. |
| P1 — recibo manual anterior descarta a resposta financeira | **ADDRESSED** | Com US$ 8 anteriores, recibo manual de US$ 0,001 e gateway posterior de US$ 2,25, o saldo contabilizado ficou em US$ 10,25. As evidências foram preservadas, a C02 publicou prefixo válido e a conta recusou a próxima autorização. A reserva órfã após queda continuou conciliável. |
| P2 — credencial ausente consome o manifesto | **ADDRESSED** | O teste isolado de presença ausente preservou manifesto, conta e saída. Replay e manifesto desabilitado foram recusados antes da consulta. O dry-run termina antes da função de presença, e a condição de modo protege a fixture. Testes usaram mocks, SQLite com escopo fixture e interceptação do runner. |

## Resíduos para adjudicação

1. **P1 · Um timeout com divergência de versão libera a reserva e permite outro envio.** Em `script/classification_comparison/c05/execute.py:96`, o callback descobre a expiração exclusivamente pelo motivo que chegou na observação. O adaptador histórico captura o timeout em `adapters/qwen/adapter.py:180`, mas a validação de versão em `:205` substitui seu motivo por `version_mismatch`, como exige o contrato do IPC quando a identidade diverge. A contraprova conservou o prazo normal do adaptador, enviou uma resposta com cobrança atribuída de US$ 0,000547 e modelo divergente, e atrasou o parse até dois milissegundos depois do prazo interno. A observação chegou à C02 dentro de seu prazo exterior. A conta ficou com `jev-001=settled` e passou a `jev-016=dispatched`. O segundo transporte sintético foi interrompido propositalmente. Com US$ 8,50 anteriores, as duas reservas integrais somariam US$ 11,3009472 com o gasto anterior. O saldo registrado após o segundo despacho foi US$ 9,9010206. O vetor demonstra quebra da regra conservadora de parar e segurar a primeira reserva sob timeout. A cobrança de US$ 0,000547 permaneceu registrada e o ensaio não demonstra débito real acima do teto. É possível distinguir a expiração para fins financeiros preservando o motivo canônico de divergência da observação. O código alterado relevante está no callback e na consulta a `timed_out` em `c05/budget.py:370`; as referências ao adaptador histórico apenas explicam a interação.

2. **P2 · A migração v2→v3 aceita uma conta com evidência de excesso já gravada sem congelá-la.** Em `script/classification_comparison/c05/budget.py:164`, a migração adiciona três colunas nulas. O cálculo em `:192` e `:203` usa os campos monetários estruturados. A versão 2, sob o segundo vetor do parecer anterior, persistia `gateway_usage.cost_usd="2.25"` junto dos créditos com zeros finais, mas deixava `observed` nulo e o caso em `staged`. A prova criou um SQLite com a implementação efetiva de `511047d` e esse mesmo registro, encerrou a execução e abriu a conta usando `20610ca`. A validação aceitou US$ 8,5004736 com US$ 7,10 anteriores, em vez do total comprovado de US$ 9,35 que excederia a reserva individual. A conta não congelou e permitiu marcar outro despacho. Com a segunda reserva, a exposição decorrente da evidência já presente chegaria a US$ 10,7504736. O limite prático para a integração é explícito: contas novas da versão 3 passam neste vetor, e não se conhece conta real antiga neste projeto. Um tratamento restrito a registros legados inconsistentes pode bloquear uso até conciliação com atribuição suficiente.

## Verificações efetivas

- O pacote fornecido equivale byte a byte ao diff `-U10` dos dois commits. `git diff --check 511047d..20610ca` passou. A worktree estava limpa.
- A contraprova independente repetiu os três vetores financeiros originais, conferiu os congelamentos e identificou o caso combinado de timeout e versão. Os quatro prefixos passaram no verificador da C02. A contraprova de migração usou a implementação financeira anterior apenas para criar a conta temporária.
- Cinco testes dirigidos foram reexecutados para credencial ausente e em branco, timeout de custo menor, precisão insuficiente com recibo posterior e conciliação de órfão após queda. Todos passaram em 4,204 s. O relatório do implementador registra separadamente 10 testes dirigidos, 36 C05 e 39 C02 aprovados.
- As verificações usaram transporte e registros sintéticos, sem rede, modelo, chave ou conta real. Nenhum arquivo do repositório foi alterado. O parecer encerra esta reavaliação dirigida e deixa os dois resíduos para decisão do integrador.

### Reprodução

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B /tmp/c05-executor-final-rereview-probes.py
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B /tmp/c05-executor-final-migration-probe.py
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY PYTHONPATH=script/classification_comparison/c05 python3 -B -m unittest -v \
  test_qwen_final.ExecutorTest.test_real_credential_check_obeys_gates_and_preserves_unclaimed_manifest \
  test_qwen_final.ExecutorTest.test_credential_presence_uses_only_non_blank_environment_value \
  test_qwen_final.ExecutorTest.test_low_cost_received_with_timeout_holds_reserve_until_explicit_receipt \
  test_qwen_final.ExecutorTest.test_larger_unrepresentable_credit_holds_reserve_without_erasing_usd \
  test_qwen_final.ExecutorTest.test_crash_keeps_third_reservation_and_verified_prefix_after_restart
```
