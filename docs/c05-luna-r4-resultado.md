# C05-R4 · Resultado real Luna

Em 24/11/2026, no horário de São Paulo, foram executadas exatamente seis
chamadas reais de desenvolvimento, uma por relato. A fonte foi
`1c89c264ca7cba4e8cde72ec9098181435def74d`, branch
`feat/luna-executor-r4`, worktree `.worktrees/r4-luna-executor`.
O modelo solicitado e retornado foi `openai/gpt-5.6-luna` pela Feita.
Não houve sondagem, repetição ou envio dos 16 diagnósticos adicionais.

| Critério | Resultado | Exigência | Estado |
| --- | ---: | ---: | --- |
| Campos previstos corretos, incluindo abstenção | 7/8 | 8/8 | Reprovado |
| Campos recebidos preservados | 4/4 | 4/4 | Aprovado |
| Casos classificáveis concluídos corretamente | 3/3 | 3/3 | Aprovado |
| Casos de revisão integral | 2/3 | 3/3 | Reprovado |
| Urgente reconhecido | 1/1 | 1/1 | Aprovado |
| Erros técnicos ou saídas inválidas | 0 | 0 | Aprovado |
| p95 do tempo total | 1.762,223 ms | Até 3.000 ms | Aprovado |

A conexão, o formato da resposta e o tempo passaram. A qualidade ainda não:
no `jev-013`, a Luna escolheu `payouts` para «Onde vejo aquele dinheiro que
passou pelo aparelho e apareceu no aplicativo? É só para conferir.». O relato
não identifica suficientemente a operação, e a referência congelada exige
`informacao_insuficiente`. A prioridade `basic`, recebida do canal, permaneceu
preservada. Escolher a categoria produziu uma conclusão indevida.

O [gate](evidencias/c05/luna-r4-ensaio-real-01/development/development-gate.json)
ficou `failed`. As 44 chamadas finais condicionais não foram enviadas.
O relatório de desenvolvimento registra elegibilidade `inconclusive`, e o
lote financeiro está `finished`: nenhum desses estados aprova a candidata.
Com seis amostras, o p95 por nearest-rank é o maior tempo observado; não
representa uma medição do conjunto final ou da capacidade da aplicação.

## Custo e evidências

Os seis [recibos filtrados](evidencias/c05/luna-r4-ensaio-real-01/financial-receipts.json)
somam 0,224280 créditos, convertidos em **US$ 0,00224280** à taxa documentada
de US$ 0,01 por crédito. O acumulado conservador passou de US$ 0,02869232 para
**US$ 0,03093512**, na mesma conta histórica com teto cumulativo de US$ 10.
A [auditoria independente](evidencias/c05/luna-r4-ensaio-real-01/auditoria.md)
recalculou as métricas, conferiu os recibos e reproduziu o bloqueio do final.
São 62 reservas liquidadas e zero pendências. A conta não foi reiniciada, e
não houve conciliação manual ou inferência extra após a reprovação.

O [pré-voo](evidencias/c05/luna-r4-preflight-2026-11-24/autorizacao-continuacao.json)
registra a interpretação do pedido de conclusão como continuidade dentro do
orçamento existente. A aprovação anterior apenas offline foi preservada como
registro histórico. Os [dados originais](evidencias/c05/luna-r4-ensaio-real-01/development/report.json),
o manifesto, o gate e os resumos financeiros foram mantidos; chaves e a conta
SQLite privada não fazem parte das evidências versionadas.

## Continuidade

O responsável escolheu manter a Luna e acrescentar evidência verificável com
validação conservadora. Essa nova estratégia exige alteração do contrato
privado do modelo e da política de validação, com preparação e revisão antes
de novo ensaio. Ela ainda não está implementada ou qualificada. Uma citação
presente no relato comprova a origem do trecho, mas não prova sozinha que a
categoria escolhida está correta; o desenho deve distinguir essas duas coisas.

Os critérios e gabaritos permanecem. C05, C06 e C07/F09 final continuam
pendentes, e a demonstração pública permanece em fixture. O atendente
conversacional real E01 segue posterior e opcional.

Exercício: compare a escolha de categoria do `jev-013` com a prioridade que
veio do canal. Identifique qual campo a plataforma deve preservar e qual
deve deixar para revisão quando o relato não sustenta uma escolha.
