# C01 — Congelar protocolo, rótulos e critérios de escolha

Issue publicada: [#2](https://github.com/leeunam/case-CLOUDWALK-IA/issues/2). Consulte a issue para progresso e comentários atuais.

## Parent e especificação

[Quadro CLASS-001](../README.md) · [CLASS-SPEC-001](../especificacao.md).
Estado: **aceita localmente em 2026-11-23**, com revisão e re-revisão
aprovadas. C02 liberada somente para fixtures. [Evidências](../aceite-c01.md).

Progresso em 2026-11-23: revisão dos 60 casos concluída para referência
exploratória, com oito aprovações diretas e 52 pela IA sob delegação explícita,
conforme o [registro da revisão](../revisao-de-rotulos.md). Os critérios/divisão
foram aprovados e os contratos e exemplos passaram nas verificações locais.

Os [critérios e a divisão](../protocolo-comparacao.md) foram aprovados pelo
responsável em 2026-11-23. A aprovação não autoriza gasto de API nem escolhe modelo.

## O que construir

Como responsável pelo projeto, conseguir aprovar um protocolo executável antes
de comparar modelos: entrada sintética, decisão por campo, aplicação ou revisão,
catálogos, dados revisados, métricas e critérios numéricos de escolha. O agente
prepara exemplos e explica as escolhas; a revisão individual dos rótulos foi
delegada à IA. O responsável decide os limites e o orçamento. Esta tarefa não
escolhe o vencedor.

## Critérios de aceite

- [x] CLASS-SPEC-001, schema JSON e fixtures registram entradas completas,
  omissões simples/duplas, inválidos, abstenção, erro e aplicação tudo-ou-revisão.
- [x] A origem válida do canal é preservada; entrada completa/inválida não
  solicita inferência; scores opcionais têm natureza explícita, sem falsa calibração.
- [x] Revisão dos 60 relatos documentada por caso, com origem, justificativas,
  ressalvas e hash preservado: oito aprovações diretas e 52 pela IA delegada.
  A limitação de referência exploratória acompanha o protocolo.
- [x] Separar dados de desenvolvimento/calibração dos de teste final. Fixar IDs,
  tamanhos, catálogos e contagem de urgentes com prioridade omitida no holdout;
  declarar se o resultado sustenta decisão inicial ou apenas estudo exploratório.
  Não ajustar prompts/limiares com o resultado do holdout.
- [x] Congelar a mesma informação semântica para os dois candidatos: critérios de
  categoria/prioridade/urgência, abstenção e eventuais exemplos. Registrar o
  mapeamento para cada adaptador e qualquer diferença antes da execução final.
- [x] Aprovar metas de erro de urgência, acerto, cobertura, abstenção e latência
  antes da comparação. Distinguir urgente classificado abaixo de urgente,
  abstenção e falha. Aceitar formalmente a possibilidade de nenhum vencedor.
- [x] Definir schema de relatório, estados de medição, denominadores e registros
  de modelo/política/ambiente. Evidência ausente não vira aprovação nem custo zero.
- [x] Registrar teto e limites de execução real ou marcar autorização pendente.
  Sem autorização, o caminho de fixtures segue disponível e o real fica bloqueado.
- [x] Integrador registra aprovação e commit do protocolo comum antes de liberar C02.

## Fora do escopo

Implementar modelos, executar chamadas pagas, treinar pesos ou mudar o fluxo Rails.

## Bloqueado por

Nenhum card técnico. Requer revisão e decisões do responsável neste chat central.

## Execução e retorno

Papel: chat central com o responsável. Antes de trabalhar, ler AGENTS.md e a
especificação vinculante; declarar tarefa, base e diretório. Só especificação e
fixtures contratuais, em ambiente isolado conforme AGENTS.md. Entregar diff,
hashes, validação dos exemplos e perguntas humanas ainda pendentes. A delegação
registrada cobre os rótulos; não aprova a C01 inteira, o vencedor nem o orçamento.

## Exercício de aprendizagem

Explicar por que um exemplo urgente sem contexto suficiente pode ir à revisão
e como isso difere de classificá-lo automaticamente como básico.
