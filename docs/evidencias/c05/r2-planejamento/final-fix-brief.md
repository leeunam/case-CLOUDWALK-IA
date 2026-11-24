# Onda única de correção final — C05-R2

Mesma worktree .worktrees/r2-avaliador e branch feat/r2-avaliador, base atual 1e98c4583ed9dc073a502658125f0bcf810b7ba0. Leia o parecer completo final-review.md neste SDD raiz; os achados abaixo são todo o escopo. É uma única onda consolidada, seguida de re-review dirigida. Sem API/env/chave/conta real, sem subagentes, merge/push; preservar budget.py/schema4, catálogo/rubrica/históricos e candidata/casos/reviews congelados. Não reabrir P1/P2 anteriores já encerrados.

## P2 · Contrato concreto da candidata

Golden report1.3 ainda tem ctl-duplo com2requests e score ranking2.7, ctl-politica com outro ranking. Política R2 prevê uma chamada por caso apto e semscore; checker aceita os desvios. Aplicar as invariantes de no máximo uma requisição e ausência de pontuação somente ao perfil R2 (preservar erro antes de despacho com0requests). Corrigir positivos da1.3, reconstruir métricas/totais/pins e adicionar contraprovas negativas dos dois tipos. Não modificar golden/perfis genéricos históricos que cobrem outros adaptadores. A implementação CLI real do experimento simulado já respeitou44; não há cobrança duplicada observada.

## P3 · Procedência da rodada atual

split/protocol R2 copiaram approved_on/approval_evidence de23/11/2026/divisãoantiga, enquanto o responsável escolheu Aoffline em24/11/2026. Também conferir created_on copiados. Ruling do integrador: a autorização atribuída ao responsável é a escolha da abordagem/implementação offline em24/11; não é aprovação humana casoacaso dos36novos nem liberação de gasto. Rótulos novos permanecem referência exploratória porIA, com reviews já congelados. Atualizar só metadados R2 e pins dependentes, mantendo referência histórica separada.

Golden report1.3 aponta dcc3963 que não contém o perfil. Usar como git_revision uma base verificável que já contém R2 (pode1e98c4583ed9dc073a502658125f0bcf810b7ba0), explicando em campo existente compatível comschema/documento que representa a base de implementação do exemplo sintético; não é medição de modelo nem alegação de execução nesse commit. Não introduzir autorreferência impossível ao hash do futuro commit.

Atualizar as verificações R2 pertinentes de metadados/observação, exemplosnegativos e locks. Reexecutar somente as cobridoras afetadas, checkerR2 e regressão de interpretação dos perfis antigos/históricos após mudança ao checker; não rerodar suites do executor inalterado. Registrar sourceSHA, mudanças, comandos/resultados/limitações em final-fix-report.md neste SDD raiz, sem alterar relatórios históricos para ocultar achados. Commit selecionado emportuguês e retorno curto. Se qualquer incompatibilidade compartilhada exigir mudança fora desse escopo, comunique antes.
