# R5-A · Revisão dirigida da política 2.1.0

**Veredicto — FIX.** Os quatro alvos publicados de desenvolvimento passaram. Um P1 da nova regra de interrupção total permite aplicar urgent mesmo quando os clientes declaram estar pagando normalmente por outro meio. O congelamento v2 deve aguardar a correção desse ramo.

Base `b474570dda7aa5bdeb7d609848d5e6b46b936d59`, commit `f2c205608f62b06e4479c247e8bc06a892bb9bac`, branch `feat/luna-evidencias-r5`, worktree `.worktrees/r5-luna-evidencias` limpa. Esta revisão abrange o delta da política, o bloqueio público de desenvolvimento e os contrastes diretamente afetados.

## Resultado nos quatro alvos

Usei as três entradas integrais do arquivo permitido de desenvolvimento e as quatro citações publicadas no pacote de bloqueio. O mesmo gateway local respondeu uma vez por caso. Verifiquei `R5Adapter.classify`, as posições literais, o replay com o digest da política e `common.decide`. Repeti os três com identificador substituído. Os resultados abaixo se mantiveram.

| Caso | Campo e código proposto | Política anterior | Política 2.1.0 e decisão comum |
| --- | --- | --- | --- |
| jev-004 | category · payouts | Veto | Aceitou. Preservou intermediate do canal |
| jev-002 | priority · urgent | Veto | Aceitou. Preservou terminal do canal |
| jev-006 | category · terminal | Veto | Aceitou terminal e basic em uma chamada |
| jev-006 | priority · basic | Veto | Aceitou com citação apenas do pedido de ajuste antes do uso |

Com textos sintéticos adicionais e IDs independentes, confirmei aceitação para venda no cartão ausente de repasse creditado e aquisição de leitora seguida de pergunta sobre o brilho antes da abertura. Citação só do depósito, destino sem crédito em conta, condição hipotética, citação só da ação sem o equipamento para a categoria, equipamento substituído por telefone e tela de outro aparelho foram vetados. A perda de vendas no restante do texto vetou a prioridade basic. Não encontrei decisão baseada nos identificadores. Esses exemplos demonstram a existência de citações admissíveis; a escolha espontânea de uma dessas citações pelo modelo permanece sem medição.

## P1 · Pagamento efetivo por outro meio não veta a urgência por interrupção total

No módulo `script/classification_comparison/adapters/luna/r5/evidence.py`, a linha 351 reconhece clientes que **conseguem** pagar. A linha 571 considera essa relação ao procurar alternativa e a linha 574 libera a urgência por ausência dela. Quando o cliente informa diretamente que os compradores **pagam**, a nova regra de `ninguém consegue pagar` ignora a ressalva. A citação e a primeira frase são idênticas nas três linhas comparadas abaixo.

Relato inicial “Ninguém consegue pagar e não temos outro meio de cobrança.” Campo ausente priority, categoria terminal recebida. Resposta sintética `urgent/immediate_harm` com citação “Ninguém consegue pagar”.

| Frase acrescentada | Base b474570 | Commit f2c2056 | Esperado pelo critério de paralisação total |
| --- | --- | --- | --- |
| Mas os compradores conseguem pagar em dinheiro. | Veto | Veto, revisão | Veto |
| Mas os compradores pagam em dinheiro normalmente. | Veto | **Aceitou urgent, complete** | Veto |
| Mas todos os clientes pagam por Pix normalmente. | Veto | **Aceitou urgent, complete** | Veto |

As duas últimas linhas falham mesmo após replay e decisão comum. A informação de que o pagamento funciona exclui a totalidade da interrupção e não há outra perda ou prazo relatado. Para reproduzir, use o helper de item de `test_evidence` com `requested=("priority",)`, devolva a escolha e a citação acima pelo `Gateway` e compare os resultados de `classify`, `replay_envelope` e `decide` entre os dois commits. Sem a ressalva de pagamento por outra via, a mesma entrada sustenta urgent na política nova. O reparo dirigido deve manter esse positivo e vetar a urgência nos pares de pagamento alternativo afirmado, conservando a distinção de pagamento negado ou hipotético.

## Integridade e limites

Os 32 métodos focais passaram. `git diff --check b474570 HEAD` passou. Recalculei os seis hashes do manifesto R5 e os 12/12 e 7/7 hashes de fontes dos congelamentos originais R3/R4 usando blobs do HEAD. O adaptador, o prompt e o schema do envelope continuam idênticos aos da base. A política se identifica como 2.1.0 na observação, o adaptador como 2.0.0, com envelope 1.0.0 e IPC 1.1.0. O congelamento histórico R5 v1 permanece um registro de sua própria versão.

Não executei varredura exaustiva de recortes, avaliação final, preflight, acesso a conta ou chamada externa. Os achados anteriores de rebaixamento, auditoria/replay e preservação de campos permanecem cobertos pela suíte focal. O único reparo solicitado nesta revisão é a contradição de disponibilidade documentada acima.
