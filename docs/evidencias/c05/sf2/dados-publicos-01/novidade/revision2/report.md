# SF2-01 — novidade pública após a segunda correção

**Parecer favorável para a novidade pública dos quatro substitutos.** Os quatro conflitos da revisão anterior foram resolvidos. Os 622 pares obrigatórios, os 170 pares complementares com a outra partição ou os históricos e os sete controles adicionais intrapartição receberam parecer de independência. Nenhuma substituição adicional ficou pendente nesta etapa.

| Substituto | Conflito anterior | Comparação operacional |
|---|---|---|
| sf2-train-048 | sf2-validation-029 pedia um demonstrativo-modelo | O regulamento futuro fracionaria cada repasse real para alimentar um fundo de manutenção. Uma amostra de relatório não movimenta valores. A simulação tributária de sf2-validation-066 calcula um saldo hipotético, e a troca de conta de jev-031 redireciona o crédito integral. |
| sf2-validation-002 | sf2-train-062 corrigia a data de um crédito no livro | A baixa do bar identifica o funcionário errado como responsável pela conferência. O comprovante assinado documenta quem conferiu o lote. O caso também difere do lote em trânsito de r2-033, em que o status impede que a conciliação automática aconteça. |
| sf2-validation-037 | sf2-train-037 roteava cobranças à carteira incorreta | O encaixe da leitora arranca fisicamente o chip dos cartões. A falha de leitura de jev-007 e a necessidade de reinserção em sf2-train-086 prejudicam a aceitação. Nenhum dos dois descreve destruição da placa do chip. |
| sf2-validation-075 | sf2-train-119 cancelava a autorização de outra compra | O terminal offline emite recibo e apaga a captura da própria venda antes da transmissão. Os clientes retiram produtos que ficaram sem cobrança. Em sf2-train-108, a perda depende de reapresentar o mesmo comprovante Pix. No histórico R4-D-006, há compras aprovadas e atraso no crédito bancário, sem descrição de perda da captura. |

## Cobertura e rastreabilidade

O compromisso público informado para esta rodada é `e68577d84b3b9aa29b93d0e155f9d289a65f6cc8`. A projeção, com SHA-256 `51770d4c896a011081c10e5aba168c4b834c1d7c77ce6ced7e2eb8886ca9296f`, contém 150 textos de treino e 90 de validação. Quatro IDs tiveram o texto alterado. Os quatro campos projetados dos outros 236 foram preservados. Os quatro arquivos históricos canônicos mantiveram as assinaturas da revisão anterior e forneceram 112 textos normalizados distintos a partir de 172 registros.

A regra do contrato `c4fe01fa5d3b058d1ebf8ccb36a07a8b99b522a5` gerou 53.880 comparações direcionadas e 40.380 pares únicos. Os três primeiros vizinhos de cada um dos 240 relatos públicos resultaram em 720 vínculos direcionados e 622 pares obrigatórios. O maior Jaccard foi 0,2857. Não houve par no limiar de 0,80, texto público com menos de cinco tokens, duplicata normalizada ou identificador de família compartilhado entre treino e validação.

Dos 740 pareceres anteriores de independência, **723** preservaram os hashes de ambos os textos e puderam ser reaproveitados. Os 17 restantes e os quatro conflitos anteriores receberam nova leitura. Os 48 pares que passaram a compor o painel completam **69 leituras novas**. Dos 622 obrigatórios atuais, 593 conservaram decisão e 29 exigiram leitura nova. O painel principal tem 792 pares únicos. Os sete controles adicionais dentro da mesma partição aparecem em lista separada no JSON.

O JSON registra as assinaturas de entrada, relatórios anteriores, adjudicação, fontes históricas e textos de cada par. Para reproduzir os vínculos, deduplicar os históricos por texto normalizado, aplicar Jaccard à união da outra partição e dos históricos e ordenar por escore decrescente e ID crescente. Preservar os três primeiros vizinhos de cada texto e todo candidato com escore a partir de 0,80.

O parecer semântico foi feito por IA, com leitura dirigida aos substitutos, aos vizinhos alterados e aos casos de mecanismos próximos. Ele cobre esta rodada de novidade pública. A validação integral da tarefa e o conjunto final privado ficam fora de seu escopo.
