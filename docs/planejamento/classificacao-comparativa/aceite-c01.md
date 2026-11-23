# C01 — aceite local e passagem para C02

Estado: **aceita localmente em 2026-11-23**, com revisão ampla e re-revisão
aprovadas. C02 liberada somente para fixtures, após integração e indicação do
SHA pelo integrador. Orçamento de execução real permanece pendente.

## O que está fechado

- Os 60 casos têm revisão rastreável: oito aprovações diretas e 52 por IA
  delegada, como referência exploratória. Dataset/catálogo e histórico F08 preservados.
- Critérios e divisão foram aprovados pelo responsável: 24 relatos para
  desenvolvimento e 36 para teste, com seis urgentes de prioridade omitida.
- A rubrica comum, os dados, os IDs e as definições dos critérios estão
  versionados em `rubrica-comum.md`, `divisao-dados.json` e
  `protocolo-comparacao.json`, sem mudar os números aprovados.
- Contratos neutros v1.0.0 cobrem entrada, observação, decisão e relatório.
  O [guia](contratos/README.md) define estados, métricas, custo parcial,
  leitura JSONL e a fronteira entre Ruby/Python. C02 define a invocação concreta.

## Evidência local

A entrega dos contratos está em `d39d659`, com correções em `590a8b9` e
`98b2bc2`. A revisão ampla final aprovou a coerência das métricas e a
distinção entre metas aprovadas e orçamento pendente, com 43 contraprovas
dirigidas e um controle de manifesto interrompido.
A revisão independente encontrou cinco problemas e a re-revisão confirmou
a correção de todos: completude das fatias, custo parcial, zero comprovado
de chamadas, origem da divergência de versão e texto Unicode em JSONL.

Os comandos abaixo foram executados pelo integrador na branch da C01:

```sh
rtk proxy python3 script/check_classification_contracts.py
rtk proxy python3 docs/planejamento/classificacao-comparativa/contratos/test_regressions.py -v
```

Resultado: **5 schemas, 12 entradas, 8 observações, 12 decisões, 1 relatório
fixture e 34 rejeições esperadas** conferidos. As oito regressões passaram,
sem erros ou falhas. O relatório fixture é inconclusivo quanto à qualidade
dos candidatos; os valores sintéticos exercitam a representação.

## Limites da liberação

C02 pode implementar e executar somente o avaliador comum com fixtures.
Nenhum adaptador ou modelo real foi executado na C01. A autorização de
chamadas pagas continua falsa, sem teto definido. O integrador fornecerá o
SHA completo da main integrada ao despachar C02; não usar um SHA antigo de
um texto histórico. C03/C04 dependem do avaliador integrado e aceito.

O resultado da futura comparação é exploratório. A escolha do classificador
permanece com o responsável; não há vencedor nesta entrega. R01/R02 são
correções independentes e E01 continua posterior à conclusão/publicação.

## Exercício

Abra `ctl-sem-assunto` nas fixtures de entrada, observação e decisão. Localize
a escolha bruta `urgent`, a abstenção de categoria e a prioridade aplicada
nula. O campo correto fica auditável, mas o complemento completo vai à revisão.

## Emenda técnica 1.1.0 integrada

A revisão da C02 revelou a necessidade de distinguir controles injetados da inferência do candidato. A [decisão técnica](ajuste-de-proveniencia-c02.md) preservou os critérios aprovados, os dados, a divisão, a rubrica e o orçamento pendente. O contrato 1.1.0 foi integrado em `70f96d08538dcf5798b569ef718cd16171b6e14f` após revisão independente e correção dirigida.

A verificação integrada passou com cinco schemas, 13 entradas, nove observações, 13 decisões, 64 rejeições esperadas e 11 regressões. A política de controle possui caminho, versão e hash fixados no protocolo. O controle misto não depende do comportamento natural do candidato e fica excluído de seus totais de inferência. [Formato e reprodução](contratos/ajuste-1.1.md). C02 consome essa versão antes da liberação C03/C04.
