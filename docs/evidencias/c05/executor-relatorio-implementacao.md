# C05-E · Task 1 · Executor final com contabilidade persistente

**DONE**

- Branch `feat/executor-qwen-final`
- Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao`
- Base `10dbd6f2ec18f0fc44dd3b4cfe60d79f04fa9e48`
- Entrega `24da473a4a20775d495775b2ee578d7df3afede3`
- Verificação em arquivo temporário e transporte simulado. Zero chamadas
  reais, zero inferências GLiClass, zero acesso a arquivo .env ou chave e zero
  criação de conta real pela Task 1.

## Alterações

- `script/classification_comparison/c05/settings.py` valida entradas pelo
  pré-voo da C02, compara a projeção com os IDs e hash congelados e vincula
  manifesto a revisão, versões, hashes de fontes e executor, identidade,
  configuração, IDs ordenados e conta. A confirmação explícita vale junto
  da autorização habilitada. O modo real conserva o prompt e a política
  históricos e anuncia adaptador 1.1.0 sobre IPC 1.1.0.
- `script/classification_comparison/c05/execute.py` escreve plano e template
  desabilitado sem abrir conta ou iniciar adaptador no dry-run. O executor
  reaproveita o cronômetro, diário, decisão, verificação e relatórios da C02.
  `script/classification_comparison/run.py` recebeu somente dois callbacks
  opcionais no lote para reservar antes do IPC e conciliar depois da
  conclusão verificável. Chamadas históricas não passam callbacks.
- `script/classification_comparison/c05/budget.py` usa SQLite da biblioteca
  padrão com transações `BEGIN IMMEDIATE` e `synchronous = FULL`. A
  inicialização separada é exclusiva e recebe teto e gasto anterior.
  Cada reserva tem chave execução/caso. IDs e hashes de manifesto e
  vinculação são únicos. A ativação única evita duplicar o processo de
  adaptador. A reserva soma gasto anterior, custos conciliados e pendências
  atomicamente. A conta compartilhada resolve a disputa pelo último saldo.
- `script/classification_comparison/c05/final_adapter.py` reutiliza o
  adaptador e o transporte Qwen, pede `max_tokens=128` e
  `reasoning={"enabled": false}`. Confere a autorização e o corpo canônico
  no processo do adaptador. Cada caso requer reserva prévia e consumo único
  do despacho antes de chamar o transporte. O modo `fixture` identifica o
  simulador e usa seu próprio escopo de conta.
- O IPC permanece congelado. A conciliação lê a resposta bruta do transporte
  em Decimal e guarda o valor no SQLite. A unidade de `usage.cost` exige
  referência explícita. A conversão opcional de `usage.credits` exige taxa
  de US$ 0,01, referência e confirmação na configuração vinculada. Se fontes
  verificadas coexistirem, preserva valores de origem e usa o maior em USD.
  As duas opções estão desativadas no exemplo real. A estimativa tarifária
  do IPC não altera o saldo.
- O adaptador persiste a cobrança como evidência intermediária antes de
  responder. Após observação e decisão verificadas pelo diário, o lançador
  pode substituir a reserva pelo custo comprovado. Timeout, crash ou falta
  de USD verificável não liberam saldo. Uma violação de valor ou de tokens
  congela a conta. Recibo explícito posterior pode conciliar uma reserva
  atribuída, uma única vez, sem disparar inferência ou atualizar o relatório
  de qualidade. Em caso de atualização da evidência, a atribuição original
  do gateway continua registrada.
- `config-real-exemplo.json` mantém limites 1.024.000/131.072, tarifas do
  registro histórico e US$ 1,4004736 de pior custo declarado por chamada.
  `config-fixture.json` e `manifesto-final-exemplo.json` distinguem simulação
  do manifesto real. `docs/c05.md` contém reprodução, configuração,
  limitações e exercício.

## Comandos e resultados reais

Execute a partir da worktree, com `rtk` e Python disponível.

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest \
  discover -s script/classification_comparison/c05 -p 'test_*.py' -v
```

`Ran 23 tests in 15.596s — OK`. O lote simulado concluiu 36 relatos e 13
controles, com 44 reservas conciliadas. Verificou campos válidos,
abstenções, autoria fixture e elegibilidade inconclusiva. Testes cobriram
SQLite ausente ou corrompido, gasto anterior, moeda e teto inválidos,
rejeições pré-transporte, duas execuções concorrentes pela última reserva,
repetição/ativação, saldo após reinício, falta de unidade ou usage,
estimativa, conversão de créditos, recibo duplicado, timeout e queda do
adaptador. A violação na chamada 44 persistiu congelamento e publicou
prefixo inconclusivo, pois ainda faltava o controle injetado número 49.

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest \
  discover -s script/classification_comparison -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest \
  discover -s script/classification_comparison/adapters/qwen -p 'test_qwen.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B \
  script/check_classification_contracts.py
```

C02 `Ran 39 tests in 32.056s — OK`. C03 `Ran 30 tests in 6.818s — OK`.
O checker retornou `OK: 5 schemas; 13 inputs, 9 observations, 13 decisions;
1 fixture report; 64 expected rejections. No model calls.`

Execute os blocos de dry-run e simulação de `docs/c05.md` para reproduzir
o CLI. Na verificação após o commit, usei diretórios temporários e
removi do ambiente `FEITA_API_KEY` e `TYPESAFE_API_KEY`. Saída conferida:

```text
24da473a4a20775d495775b2ee578d7df3afede3 observed-total-1.1 1.4004736 36 13 44 1786f8cdc239f9a661ba413f7f8ee964a33c5d87be48450a62ea29fd5a4fed09
OK: observed-total-1.1 · [diretório temporário]/lote/report.json
"accounted_usd": "0.024587",
```

A primeira tentativa de smoke antes da suíte detectou a falta do import
de `Path` no adaptador. Corrigido e reexecutado com sucesso na suíte e no
CLI documentado. `git diff --check 10dbd6f..HEAD` passou. O diff de
planejamento congelado, dataset, piloto histórico e plano estático foi
vazio.

## Limites e decisões

- A conta é compartilhada por processos que usam o mesmo arquivo e
  identidade. Inicializações separadas geram contas distintas. Gasto
  anterior precisa ser consolidado pelo integrador antes da abertura da
  conta real. Valores são decimais exatos até 30 casas.
- A rota real continua condicionada a autorização, configuração financeira
  confirmada, conta válida e disponibilidade. Não existe medição real da
  C05 nem garantia de débito ou limite faturável a partir de
  `reasoning.enabled=false`. A solicitação tem limite de 128 tokens de
  geração e a reserva usa o teto faturável maior declarado.
- Na falta de custo conciliável, a execução para com um prefixo mesmo
  havendo saldo para outra reserva. A conciliação posterior é somente
  financeira. A autorização consumida e as tentativas registradas
  permanecem bloqueadas para replay.
- O cronômetro usado no modo real é o da C02. Como a reserva é feita antes
  do IPC e a evidência é persistida no adaptador antes da resposta, esse
  tempo local integra a espera observável do caso. O modo fixture não
  produz medição de elegibilidade real.
- O teste de concorrência disputa a reserva usando dois processos reais
  com SQLite temporário. O fornecedor, a conta real e a adequação de
  referências de cobrança permanecem verificações externas a esta tarefa.

## Exercício

Repita o bloco fixture de `docs/c05.md` com uma conta nova e gasto anterior
de `8.5993`. O primeiro caso, `jev-001`, usa US$ 0,000547 simulados. Em
`interruption.json`, `jev-016` deve ter entrega `not_sent`. O saldo após
a primeira conciliação fica em US$ 1,400153 e falta US$ 0,0003206 para
a reserva seguinte.


## Rodada de correção 1/5

- Status da implementação **DONE**, aguardando revisão do integrador.
- Base da rodada `24da473a4a20775d495775b2ee578d7df3afede3`.
- Commit `aee264c2d1b38344bc9b41c7d5b84f03c8941b80` na branch
  `feat/executor-qwen-final`, com worktree limpa.
- Os três achados do parecer foram tratados no mesmo commit.
  Configurações reais, IPC, protocolo, C02 e piloto histórico permaneceram
  fora do diff.

O adaptador preserva USD e créditos verificados sem depender dos contadores
de tokens ou de HTTP 200. O prefixo da C02 mantém o erro operacional de
HTTP 500 e a ausência de contadores. O SQLite registra a cobrança e
congela quando ela excede a reserva. Respostas sem cobrança validável e
timeouts mantêm a reserva.

Após liquidar uma reserva, um recibo independente com aumento comprovado
entra como correção do total daquele caso. O SQLite mantém o valor e recibo
originais e usa o maior valor para o saldo, sem agregar as duas cobranças.
A mesma transação congela o saldo se o novo valor ultrapassar a reserva ou se
o total, incluindo outras reservas, ultrapassar o teto. A correção pode ser
menor que a reserva original e ainda assim ultrapassar o teto, porque uma
parte da reserva já havia voltado ao saldo quando a cobrança original foi
conciliada. O relatório de classificação permanece preservado.

Referências são normalizadas antes de atribuir ou persistir recibos. A
verificação considera recibos atuais, anteriores e correções. Na abertura de
uma conta da versão 1, a atualização transacional conserva as reservas
originais e normaliza referências legadas. Uma atribuição legada duplicada
entre casos bloqueia a atualização.

### Verificações da rodada

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY \
  PYTHONPATH=script/classification_comparison/c05 python3 -B -m unittest -v \
  test_qwen_final.ExecutorTest.test_documented_usd_with_missing_token_counter_still_freezes_and_preserves_evidence \
  test_qwen_final.ExecutorTest.test_documented_credits_in_http_error_freeze_without_hiding_operational_error \
  test_qwen_final.AccountTest.test_late_receipt_above_reservation_is_recorded_without_second_settlement \
  test_qwen_final.AccountTest.test_late_increase_within_case_reservation_can_break_global_cap \
  test_qwen_final.AccountTest.test_reconcile_explicit_receipt_once_exactly \
  test_qwen_final.AccountTest.test_dashboard_receipt_preserves_original_gateway_attribution \
  test_qwen_final.AccountTest.test_v1_receipts_keep_attribution_and_normalize_on_upgrade

rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest \
  discover -s script/classification_comparison/c05 -p 'test_*.py' -v
rtk proxy git diff --check
rtk proxy git status --short --branch
```

Saída dos testes dirigidos `Feita jev-001: HTTP 500` no transporte
simulado, `Ran 7 tests in 1.803s` e `OK`. Saída da suíte C05
`Ran 28 tests in 15.657s` e `OK`. A verificação de espaços ficou vazia.
`git status` mostrou somente `## feat/executor-qwen-final`.

O cenário de recibo tardio de US$ 2,25 preservou os US$ 0,001 originais
no histórico, contabilizou US$ 10,25 e bloqueou o próximo despacho. Na
borda cumulativa, com US$ 8 anteriores, um caso corrigido para US$ 1,00
e outra reserva pendente de US$ 1,4004736, o total passou a
US$ 10,4004736 e a conta congelou. Os testes de normalização bloquearam a
reutilização de recibos com espaços, tabulação e espaço não separável,
inclusive contra a referência legada preservada.

As suítes C02 e C03 registradas na entrega inicial não foram reexecutadas
nesta rodada, pois só houve mudanças na C05. Todas as verificações da rodada
usaram SQLite temporário e simulação, sem chave, rede ou conta real.


## Correção final consolidada

- Status da implementação **DONE**, aguardando a revisão dirigida do integrador.
- Base da correção `511047d1a0a8ada5c1dffca2386f8f43739666fe`.
- Commit `20610ca3b431158767e3eaf6d136aca5e48087f3` na branch
  `feat/executor-qwen-final`, com worktree limpa.
- Arquivos `budget.py`, `execute.py`, `final_adapter.py` e `test_qwen_final.py`
  sob `script/classification_comparison/c05`, e o callback opcional em
  `script/classification_comparison/run.py`. Configurações reais versionadas
  continuam desabilitadas.

O adaptador registra a evidência financeira ao receber o corpo de uma
requisição despachada, antes de interpretá-lo como classificação. Tanto o
corpo entregue depois do prazo interno quanto o parse que expira mantiveram
`timeout` na observação verificada pela C02. Com custo observado de US$ 2,25
e US$ 7,10 de gasto prévio, o saldo contabilizado foi US$ 9,35 e a conta
congelou. Um custo de US$ 0,000547 sob timeout ficou registrado, com a
reserva de US$ 1,4004736 integral até conciliação explícita. O timeout
sem corpo também manteve a reserva integral. Para fazer essa distinção,
a C02 entrega ao callback a observação já verificada. O relógio, os
prazos, a decisão, os contratos e o comportamento do avaliador sem
callback seguem a mesma lógica.

A representação monetária remove zeros excedentes de escala quando o
valor continua exatamente igual. As fontes de USD e créditos são
avaliadas de forma independente. Uma fonte maior sem conversão exata
aceita permanece registrada como pendente e impede a liberação pela
fonte menor, mesmo quando o valor menor já era conhecido. Atribuir
recibo inferior à evidência pendente é recusado. O teste com créditos
equivalentes a pouco mais de US$ 0,20 demonstrou retenção da reserva e
conciliação posterior usando um recibo acima do valor pendente. A
precisão aceita continua em até 30 casas significativas após a vírgula
para a contabilidade exata de valores positivos.

A transação que registra a resposta aceita uma reserva que já recebeu
recibo manual. O estado mantém a liquidação original, a evidência
independente do gateway e correções manuais. O saldo usa o maior valor
comprovado do caso. Na interleavação simulada, o recibo manual de
US$ 0,001 chegou primeiro. O gateway informou depois US$ 2,25 e o saldo
total passou a US$ 10,25, com congelamento e prefixo inconclusivo.
Outra regressão preservou ambas as evidências quando o gateway cobrou
menos e bloqueou reutilização da referência para outro caso. A falha
do processo deixou o caso órfão disponível para conciliação manual
posterior sem reabrir inferência. A atualização SQLite é aditiva e
preserva contas antigas das versões 1 e 2.

A verificação de credencial no modo real consulta somente a presença
de valor não vazio no ambiente do processo. Ocorre após validar
configuração, manifesto, conta, saída e uso prévio, antes de persistir
o consumo da autorização ou reservas. Ausência deixa o manifesto
reutilizável. Os testes simulam presença/ausência sobre SQLite
`fixture` e interceptam a criação de qualquer adaptador de modo real.
Manifesto desabilitado, replay, dry-run e fixture são cobertos sem
consulta de credencial.

### Verificações da correção consolidada

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY \
  PYTHONPATH=script/classification_comparison/c05 python3 -B -m unittest -v \
  test_qwen_final.ExecutorTest.test_late_parse_and_late_body_preserve_timeout_and_freeze_known_excess \
  test_qwen_final.ExecutorTest.test_low_cost_received_with_timeout_holds_reserve_until_explicit_receipt \
  test_qwen_final.ExecutorTest.test_timeout_is_journaled_and_retains_reservation \
  test_qwen_final.ExecutorTest.test_zero_suffix_in_credit_scale_does_not_erase_higher_usd \
  test_qwen_final.ExecutorTest.test_larger_unrepresentable_credit_holds_reserve_without_erasing_usd \
  test_qwen_final.ExecutorTest.test_gateway_cost_after_in_flight_manual_receipt_combines_both_without_duplicate_charge \
  test_qwen_final.AccountTest.test_lower_gateway_receipt_arriving_after_manual_preserves_both_and_cannot_be_reused \
  test_qwen_final.ExecutorTest.test_crash_keeps_third_reservation_and_verified_prefix_after_restart \
  test_qwen_final.ExecutorTest.test_real_credential_check_obeys_gates_and_preserves_unclaimed_manifest \
  test_qwen_final.ExecutorTest.test_credential_presence_uses_only_non_blank_environment_value

rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest \
  discover -s script/classification_comparison/c05 -p 'test_*.py' -v
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest \
  discover -s script/classification_comparison -p 'test_*.py'
rtk proxy git diff --check
rtk proxy git status --short --branch
```

Resultados `Ran 10 tests in 9.247s` com `OK` nos casos dirigidos,
`Ran 36 tests in 23.162s` com `OK` na C05 e
`Ran 39 tests in 29.365s` com `OK` na C02. `git diff --check` não
produziu saída. `git status` mostrou somente
`## feat/executor-qwen-final`. O piloto histórico C03 não foi
reexecutado nesta correção e seu código está fora do diff.

Sem chamadas externas, chaves reais, arquivos de credencial ou contas
reais nesta correção. A revisão final deve considerar somente a
evidência offline e o estado pendente do lote pago.


## Adjudicação residual Task2

- Status da implementação **DONE**, aguardando validação estreita dos dois resíduos.
- Base `20610ca3b431158767e3eaf6d136aca5e48087f3`.
- Commit `e4ce14c95a4a59737b000bcc8dfa21009a1d566d` na branch
  `feat/executor-qwen-final`, com worktree limpa.

A C05 registra no SQLite a expiração de prazo financeiro antes de devolver
a observação para a C02. A marcação é monotônica. Uma observação com timeout
também pode registrar a marca, e um callback posterior sem timeout não a
apaga. O motivo canônico continua `version_mismatch` quando o modelo
retornado diverge. A regressão com o prazo normal registra US$ 0,000547
do caso `jev-001` e mantém a reserva de US$ 1,4004736. Com US$ 8,50 de gasto
anterior, o total fica em US$ 9,9004736. O prefixo conferido tem um único
despacho e a segunda entrada conserva o estado pendente.

A versão 4 é a primeira versão suportada da conta SQLite. Removi a
migração automática. As versões 1, 2, 3 e demais incompatíveis são
recusadas em verificação de leitura antes da abertura com escrita. O
teste verificou que validação, consulta, ativação, reserva, conciliação
e tentativa de inicialização mantêm intactos os bytes do arquivo
incompatível. `docs/c05.md` preserva a orientação de manter arquivos dos
protótipos para consolidação ou importação auditada do histórico. Contas
novas persistem entre processos, e a reserva órfã continua conciliável
sem replay.

### Verificação residual

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY \
  PYTHONPATH=script/classification_comparison/c05 python3 -B -m unittest -v \
  test_qwen_final.ExecutorTest.test_timeout_and_model_mismatch_retain_reserve_without_sending_next_case \
  test_qwen_final.AccountTest.test_incompatible_accounts_are_refused_without_modifying_bytes \
  test_qwen_final.ExecutorTest.test_crash_keeps_third_reservation_and_verified_prefix_after_restart
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest \
  discover -s script/classification_comparison/c05 -p 'test_*.py' -v
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B \
  .superpowers/sdd/executor-qwen-final/c05-executor-final-migration-probe.py
rtk proxy git diff --check
rtk proxy git status --short --branch
```

Resultado dos testes dirigidos `Ran 3 tests in 7.090s` e `OK`. Resultado
da suíte C05 `Ran 37 tests in 29.938s` e `OK`. A sonda independente da
conta v2 retornou código 1 no ponto esperado, antes de ativação ou
despacho, com `BudgetError: versão da conta incompatível: 2. Exigida: 4.`.
A verificação de espaços ficou vazia. O Git mostrou somente
`## feat/executor-qwen-final`. O callback da C02 e o IPC permaneceram
iguais. As regressões C02 registradas na correção consolidada não foram
reexecutadas nesta adjudicação.

Todas as verificações usaram transporte fixture e SQLite temporário,
sem chamada real, chave, arquivo de credencial ou conta financeira real.
