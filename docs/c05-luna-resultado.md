# C05-R3 · Resultado real Luna

Em 24/11/2026 foram executadas exatamente seis chamadas reais de desenvolvimento
à Feita, uma por relato, sem sondagem ou repetição. A fonte executada foi
`e8434bb8ed7a01ec564f8bf3b02aa35d7bde1575`, na branch `feat/avaliador-luna`,
worktree `.worktrees/r3-luna-avaliador`. O modelo solicitado e retornado foi
`openai/gpt-5.6-luna`, com as instruções e critérios previamente congelados.

## Resultado do desenvolvimento

| Critério | Resultado | Exigência | Estado |
| --- | ---: | ---: | --- |
| Alvos corretos, incluindo abstenção | 7/8 | 8/8 | Reprovado |
| Campos recebidos preservados | 4/4 | 4/4 | Aprovado |
| Casos classificáveis concluídos corretamente | 3/3 | 3/3 | Aprovado |
| Casos de revisão integral | 2/3 | 3/3 | Reprovado |
| Urgente reconhecido | 1/1 | 1/1 | Aprovado |
| Erros técnicos ou saídas inválidas | 0 | 0 | Aprovado |
| p95 do tempo total | 2.635,459 ms | Até 3.000 ms | Aprovado |

A mediana foi 1.383,625 ms. Com seis amostras, o p95 por nearest-rank corresponde
ao maior tempo observado. Esses números descrevem apenas este desenvolvimento;
o lote final não foi medido.

No `jev-013`, o relato era «Onde vejo aquele dinheiro que passou pelo aparelho e
apareceu no aplicativo? É só para conferir.» A prioridade `basic` veio do canal
e foi preservada. A referência exige abstenção na categoria porque a operação
não está suficientemente identificada. A Luna escolheu `payouts` e a decisão
concluiu o caso. O erro é uma conclusão indevida segundo a política congelada.
Os demais cinco relatos foram consistentes com as referências.

O gate real ficou **`failed`**. As 44 chamadas finais condicionais não foram
executadas. O lote financeiro terminou normalmente e o relatório de
desenvolvimento conserva elegibilidade `inconclusive`; nenhum desses estados
significa aprovação da candidata. Não houve adoção ou integração C06.

## Custo e auditoria

Os seis recibos somaram **US$ 0,00181827**, calculados a partir de 0,181827 créditos
à conversão documentada de US$ 0,01 por crédito. O acumulado conservador passou
de US$ 0,02687405 para **US$ 0,02869232**, na mesma conta histórica com teto
cumulativo US$ 10. Há 56 reservas liquidadas e nenhuma pendência. Não houve
conciliação manual, reinicialização da conta ou consumo extra após a reprovação.

A auditoria independente refez as contagens, o tempo, os custos e os vínculos de
fontes, identidade, revisão e artefatos. Conferiu os seis recibos filtrados e
comprovou que a verificação real rejeita a prova reprovada antes de consultar
uma conta para o final. O parecer e os comandos executados estão na
[auditoria](evidencias/c05/luna-ensaio-real-01/auditoria.md).

As [evidências originais](evidencias/c05/luna-ensaio-real-01/development/report.json),
o [gate](evidencias/c05/luna-ensaio-real-01/development/development-gate.json),
os [recibos filtrados](evidencias/c05/luna-ensaio-real-01/financial-receipts.json)
e os manifestos foram preservados. Chaves e a conta SQLite privada não foram
copiadas para os relatórios. Os rótulos dos 36 finais continuam sem aprovação
humana direta e sem inferência da Luna; a revisão por IA permanece identificada.

## Continuidade

A demonstração publicada permanece em fixture. C05 real, C06 e o aceite final
C07 continuam pendentes. A autorização das 44 chamadas não foi liberada pelo
gate e não autoriza repetir a mesma candidata reprovada.

A [análise de alternativas](evidencias/c05/luna-ensaio-real-01/alternativas.md)
recomenda discutir uma única revisão semântica da instrução, mantendo a Luna e
uma chamada por caso. Antes da implementação, definir pares novos de
desenvolvimento e rótulos independentes que distingam operação afirmada,
negada e apenas mencionada, preservando consultas claras e os gabaritos
existentes. Isso é uma hipótese para decisão, sem garantia de aprovação.
Exigir evidência verificável na resposta é outra opção, com mudanças maiores
no contrato e na validação. Nenhuma alternativa foi implementada ou testada
por nova inferência.

Exercício: compare `jev-004` e `jev-013` nas entradas de desenvolvimento e
identifique o fato que liga o primeiro relato ao recebimento de vendas.
Confira por que preservar a prioridade do canal não basta para aprovar uma
categoria inferida incorretamente.
