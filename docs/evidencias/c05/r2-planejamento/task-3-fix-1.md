# Task3 — correção consolidada round1/5

Fonte revisada e6fe31cbe4dd2c96493bf455016163c6c68ff7dc. Mesmo implementador e worktree. Revisão de especificação e qualidade reprovou pelos dois achados abaixo; o menor ponto de metadados relacionado pode ser corrigido junto, sem rodada separada. O report original contém comandos de contraprova executados. Preserve prompt/política/dados/reviews congelados, orçamento, perfis antigos e budget.py/schema4. SemAPI/env/conta real; semsubagentes/merge/push.

## Achados originais

### P1 · Vincular a prova do gate às saídas originais do desenvolvimento

`script/classification_comparison/r2/execute.py:119`, `script/classification_comparison/r2/gate.py:73` e `:107` e `:125`.

A conta conserva a identidade do lote, o manifesto, a configuração e o custo por caso. O diário vincula o plano e os eventos de despacho e conclusão. Os dados persistidos nesses pontos deixam sem compromisso independente os bytes das observações, decisões e relatório. Durante o pré-voo do final, `collect` calcula os hashes dos arquivos então apresentados e `verify` compara a prova com esse recálculo. Basta regenerar a prova e vincular seu novo hash no manifesto. A mesma verificação aceita um conteúdo de classificação diferente com os custos originais.

Reproduzi em uma conta fixture, com seis reservas conciliadas. O desenvolvimento concluiu com `failed` e 7/8 alvos. Substituí a categoria observada de `jev-004` de `pix` por `payouts`, derivei a decisão correspondente e regenerei o relatório e a prova. A prova passou a `fixture_ready` com 8/8 e o pré-voo do final a autorizou. Conta, diário, entradas, plano e invocação permaneceram originais. A verificação usa o mesmo mecanismo de vinculação para observações e durações reais.

Fixar o compromisso com as saídas no momento da conclusão, fora dos próprios artefatos oferecidos para validação. Fazer o final exigir esse compromisso da execução correspondente antes de abrir o adaptador. A escolha do armazenamento pertence ao integrador, pois a tarefa preserva a proteção financeira e a schema v4. Incluir regressão que regenere prova, relatório e manifesto depois de alterar uma observação, preservando a conta, e exija a rejeição.

### P2 · Reconstruir as métricas de aprovação do final a partir dos registros

`script/check_classification_contracts.py:349` e `:624`.

O checker comprova decisões por caso, a latência e a ausência de aplicação parcial. Para os outros gates, aceita numeradores compatíveis com a aritmética e aplica o limiar ao valor declarado no relatório. Em uma contraprova inteiramente sintética com formato de relatório completo real, o cálculo canônico indicou `fail` junto de uma conclusão automática em `r2-011`, caso de revisão obrigatória. Alterei somente o numerador e o valor de `automatic_completion_on_expected_review_cases` para zero e o veredito para `pass`. O checker aceitou, com os três streams originais. A lacuna é herdada na verificação de métricas e compromete a conferência do novo relatório R2.

Conferir os numeradores e demais valores de aprovação do perfil R2 contra entradas, observações, decisões e referências congeladas. Preservar a interpretação dos perfis históricos. Cobrir a alteração do numerador e do veredito com os streams intactos.

### Minor · Corrigir a origem declarada da partição nova

`docs/planejamento/classificacao-comparativa/r2/split.json:2`, `docs/planejamento/classificacao-comparativa/r2/protocol.json:6` e `script/check_classification_contracts.py:655`.

A partição R2 declara o dataset histórico 1.1.0 como seu dataset fonte, mas lista 36 casos que só existem no pacote composto 2.0.0. O protocolo aponta para o composto e os pins atuais protegem o conteúdo. O checker verifica os objetos do pacote e a partição sem verificar os campos de origem declarados no split. Usar a versão e o SHA do composto nesses campos, mantendo a referência histórica em `protocol.r2.historical_dataset`. A mesma partição descreve `id` como visível ao modelo, enquanto a projeção IPC inclui ID e o corpo Qwen o retira. A nomenclatura pode refletir a fronteira correta. Nenhuma dessas correções exige editar os casos, os pareceres ou as instruções congeladas.


## Ruling do integrador para P1 (armazenamento)

Adicionar selo NÃO FINANCEIRO junto da conta, fora do diretório de saídas/gate fornecido, em caminho determinado por identidade da conta e manifest_id de development. Formato JSON pequeno com hashes das sete saídas originais, hash da prova, conta/run/stage/manifest/binding/config/candidata necessários. Criação exclusiva O_EXCL/permissões privadas/fsync; original imutável pelo programa. Sem SQLite/tabela/schema nova ou alteração de budget.py.

Somente execute.run_evaluation na conclusão original de development, depois dos arquivos canônicos e encerramento financeiro finished, cria o selo — tanto para gate failed quanto ready/pass. `gate.collect` é cálculo sem autoridade de escrita; `verify` exige compromisso já criado. Não criar/reparar/migrar selo ausente durante coleta/verificação/final. Ausência, corrupção ou divergência bloqueiam antes da chave e despacho. Uma queda antes de selar deixa final bloqueado, preservando gastos/arquivos; não autoriza repetir estágio nem recriar conta. O conteúdo público e seu hash regenerados não bastam para reabrir um resultado failed. Preservar selo+conta juntos; não prometer proteção contra usuário que edita o próprio programa ou selo privado. Incluir novo módulo no inventário de código do binding. O final nunca aceita caminho de selo arbitrário do arquivo apresentado.

Regressões necessárias: development wrong/failed + ledger original + observação/decisão/report/gate regenerados deve ser recusado mesmo com manifesto final novo; selo removido/corrompido não reconstitui a autorização; fixture_ready/realpass e replay permanecem distintos e parentconclusão atual deve continuar funcionando. Se precisar de outra interface, pergunte antes de alterar.

## P2 e metadados

Para R2, recomputar todos os dados/gates que determinam aprovação contra inputs/observations/decisions/referência congelada (pode reusar cálculo canônico para evitar duplicar lógica), incluindo numeradores, estados, denominadores e veredito. Preservar interpretação dos perfis legados. Cobrir as duas contraprovas do report; não basta verificar numéricamente o valor declarado. Corrigir também source_dataset_version/hash do split para composto2.0 e separar model_visible_fields da projeção IPC (ID não vai a HTTP), conferindo isso no checker novo. Regerar só pins/artefatos R2 afetados, sem editar qualquer caso ou instrução congelada. Esse metadado era Minor e não cria loop próprio.

Apêndice no task-3-report.md: mudanças, comandos exatos/saídas, testes novos cobrindo achados e regressões afetadas. Não reexecutar suites se nada novo as afeta; uma rodada das cobridoras+checkers e históricos depois do fix basta. Commitselecionado emportuguês e retorno curto com fixcommit/testes/pendências. A re-review será dirigida ao fixdiff e aos achados.
