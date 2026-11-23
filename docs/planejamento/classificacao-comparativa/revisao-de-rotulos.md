# C01 — revisão humana parcial dos rótulos

Estado: em andamento. Oito casos possuem aprovação dos campos ausentes,
totalizando dez decisões de campo; os outros 52 casos aguardam revisão.
Este registro não conclui C01 nem libera C02.

Fonte: [dataset de 60 relatos](../../../script/f08/jev/dataset.json), versão
1.1.0, SHA-256
`0e7e4c342c2a39cefd89855d8c0513f447d7878303eb4091488ca8af78928880`.
O arquivo e seus metadados `review: provisional` permanecem inalterados.

## Aprovações registradas

| Caso | Campo ausente | Rótulo esperado aprovado | Justificativa | Origem da aprovação |
| --- | --- | --- | --- | --- |
| jev-001 | category | informacao_insuficiente | Pagamento por QR não identifica, sozinho, o meio de pagamento. | Aprovação anterior do responsável, já registrada na CLASS-SPEC-001. |
| jev-041 | priority | informacao_insuficiente | O relato de reembolso Pix não informa prazo nem impacto suficientes para decidir prioridade. | Aprovação anterior do responsável, já registrada na CLASS-SPEC-001. |
| jev-002 | priority | urgent | Toda a cobrança está interrompida durante a operação e não há alternativa. | Chat central, 2026-11-23: responsável concordou com o bloco 002/005/044. |
| jev-005 | priority | basic | Pedido de orientação para uso futuro, sem falha operacional atual relatada. | Chat central, 2026-11-23: responsável concordou com o bloco 002/005/044. |
| jev-044 | priority | informacao_insuficiente | Faltam prazo e impacto para determinar a prioridade da mudança na agenda. | Chat central, 2026-11-23: responsável concordou com o bloco 002/005/044. |
| jev-003 | category | pix | O relato identifica explicitamente transferências por Pix. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |
| jev-003 | priority | urgent | Há transferências não autorizadas em andamento e necessidade de intervenção imediata. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |
| jev-008 | priority | intermediate | O atraso afeta uma venda pequena e o cliente consegue manter a operação e pagar as despesas de hoje. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |
| jev-009 | category | payouts | A divergência está na agenda de recebimento das vendas a crédito. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |
| jev-009 | priority | advanced | A divergência abrange metade das vendas, mas há caixa para operar pelos próximos dias. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |

As aprovações se referem aos campos ausentes indicados. Campos válidos recebidos
do canal permanecem como contexto e não contam como predição do classificador.
A concordância com esses exemplos não aprova o conjunto completo, uma rubrica
geral nova, a separação dos dados ou os limites de execução.

## Pendências antes do protocolo final

- Revisar os 52 casos restantes e registrar eventuais mudanças e justificativas.
- Detalhar e aprovar as definições operacionais de prioridade e abstenção.
- Separar desenvolvimento/calibração e teste final antes de usar exemplos em prompts.
- Congelar versões, hashes, critérios de escolha e limites de execução conforme
  a [C01](cards/C01-protocolo.md).

Nenhum caso deste conjunto foi enviado a Qwen ou GLiClass nesta revisão.
