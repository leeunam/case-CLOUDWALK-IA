# C01 — Congelar protocolo, rótulos e critérios de escolha

Issue publicada: [#2](https://github.com/leeunam/case-CLOUDWALK-IA/issues/2). Consulte a issue para progresso e comentários atuais.

## Parent e especificação

[Quadro CLASS-001](../README.md) · [CLASS-SPEC-001](../especificacao.md).
Estado inicial: planejamento com participação humana; não libera ensaio pago.

Progresso de revisão em 2026-11-23: oito casos com aprovação dos campos
ausentes e 52 pendentes, conforme o [registro parcial](../revisao-de-rotulos.md).
C01 continua em andamento; o dataset completo permanece provisório.

## O que construir

Como responsável pelo projeto, conseguir aprovar um protocolo executável antes
de comparar modelos: entrada sintética, decisão por campo, aplicação ou revisão,
catálogos, dados revisados, métricas e critérios numéricos de escolha. O agente
prepara exemplos e explica as escolhas; o responsável aprova rótulos, limites
e orçamento. Esta tarefa não escolhe o vencedor.

## Critérios de aceite

- [ ] CLASS-SPEC-001, schema JSON e fixtures registram entradas completas,
  omissões simples/duplas, inválidos, abstenção, erro e aplicação tudo-ou-revisão.
- [ ] A origem válida do canal é preservada; entrada completa/inválida não
  solicita inferência; scores opcionais têm natureza explícita, sem falsa calibração.
- [ ] Os 60 relatos atuais continuam provisórios até revisão humana documentada.
  Registrar revisão por caso, dúvidas, alterações, versão e hashes finais.
- [ ] Separar dados de desenvolvimento/calibração dos de teste final. Fixar IDs,
  tamanhos, catálogos e contagem de urgentes com prioridade omitida no holdout;
  declarar se o resultado sustenta decisão inicial ou apenas estudo exploratório.
  Não ajustar prompts/limiares com o resultado do holdout.
- [ ] Congelar a mesma informação semântica para os dois candidatos: critérios de
  categoria/prioridade/urgência, abstenção e eventuais exemplos. Registrar o
  mapeamento para cada adaptador e qualquer diferença antes da execução final.
- [ ] Aprovar limites de erro de urgência, acerto/cobertura, abstenção, latência
  e custo antes da comparação. Distinguir urgente classificado abaixo de urgente,
  abstenção e falha. Aceitar formalmente a possibilidade de nenhum vencedor.
- [ ] Definir schema de relatório, estados de medição, denominadores e registros
  de modelo/política/ambiente. Evidência ausente não vira aprovação nem custo zero.
- [ ] Registrar teto e limites de execução real ou marcar autorização pendente.
  Sem autorização, o caminho de fixtures segue disponível e o real fica bloqueado.
- [ ] Integrador registra aprovação e commit do protocolo comum antes de liberar C02.

## Fora do escopo

Implementar modelos, executar chamadas pagas, treinar pesos ou mudar o fluxo Rails.

## Bloqueado por

Nenhum card técnico. Requer revisão e decisões do responsável neste chat central.

## Execução e retorno

Papel: chat central com o responsável. Antes de trabalhar, ler AGENTS.md e a
especificação vinculante; declarar tarefa, base e diretório. Só especificação e
fixtures contratuais, em ambiente isolado conforme AGENTS.md. Entregar diff,
hashes, validação dos exemplos e perguntas humanas ainda pendentes. Não marcar
como aprovado por conta própria nem interpretar saldo disponível como orçamento.

## Exercício de aprendizagem

Explicar por que um exemplo urgente sem contexto suficiente pode ir à revisão
e como isso difere de classificá-lo automaticamente como básico.
