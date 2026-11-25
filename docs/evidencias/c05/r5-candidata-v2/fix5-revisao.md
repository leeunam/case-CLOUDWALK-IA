# R5-A · Revisão focal da quinta correção

**Veredicto — SHIP para congelamento v2.** O P1 de pagamentos efetivos em dinheiro ou por Pix está corrigido em `38ac4cb81abe9f84469e379cee30e6bb976e25dd`. Não há pendência bloqueante na revisão dirigida. A base da verificação foi `f2c205608f62b06e4479c247e8bc06a892bb9bac`, na branch `feat/luna-evidencias-r5` e worktree limpa `.worktrees/r5-luna-evidencias`.

## Resultado por achado

| Achado acompanhado | Resultado observado |
| --- | --- |
| P1 · urgent por interrupção total apesar de pagamento atual em dinheiro/Pix | **Corrigido.** A proposta recebe `veto/context_conflict`; a decisão comum envia o caso para revisão, com prioridade nula e categoria recebida preservada. |
| Risco de regressão · pagamento negado, passado, futuro ou condicional anular a interrupção atual | **Controles preservados.** Com interrupção total e ausência de alternativa afirmadas, esses relatos continuaram aceitando urgent. A dúvida explícita quanto à disponibilidade presente encaminhou para revisão. |
| Risco de regressão · a alternativa esconder outra perda em andamento ou liberar rotina | **Controles preservados.** A citação de perda de vendas em andamento sustentou urgent mesmo com alternativa mencionada. O pedido de configuração ao final de um relato contraditório permaneceu insuficiente para aplicar basic. |
| Bloqueio anterior · quatro alvos públicos de desenvolvimento sem citação aceita | **Permanece resolvido.** Os quatro campos propostos completaram as três entradas e preservaram os valores recebidos. A troca dos identificadores manteve os resultados. |

## Reprodução independente

Usei a citação “Ninguém consegue pagar” e o texto inicial “Ninguém consegue pagar e não temos outro meio de cobrança”. Na base, acrescentar “Mas os compradores pagam em dinheiro normalmente.” ou “Mas todos os clientes pagam por Pix normalmente.” permitia aplicar urgent. Com o mesmo insumo na versão corrigida, o motor comum vetou a urgência nas duas situações. A auditoria conservou proposta, citação e posição.

Conferi 19 propostas artificiais contra a política executável da base e o `R5Adapter` do commit. Em cada caso houve um único despacho pelo gateway simulado, replay com a política congelável e verificação do valor aplicado por `common.decide`. **As 19 propostas produziram o resultado esperado.** Sete passaram de urgência aplicada para revisão e as outras 12 conservaram o resultado anterior. A matriz inclui declaração de pagamento por meio alternativo, indicação de funcionamento, dúvida atual, negação, passado, futuro, condição e perda independente.

Reexecutei os quatro alvos de desenvolvimento sobre as três entradas públicas permitidas e repeti com IDs trocados. O caso de lote creditado completou payouts e preservou intermediate. O caso de interrupção completou urgent e preservou terminal. O ajuste do equipamento completou terminal e basic em uma única chamada simulada. A suíte focal teve 33 métodos aprovados e o diff `f2c2056..38ac4cb` passou na checagem de formatação.

Nos blobs de HEAD verifiquei os 12 hashes originais R3, os sete R4 e as seis referências do manifesto R5. O SHA-256 da política 2.1.0 é `42dcd4fd4806a485606d359eb64b86bcb59e4e299892288ce4e3624cde971557`. O adaptador, o prompt, o schema do envelope e o perfil operacional conservaram os bytes da base da correção. A revisão não mudou critérios, gabaritos nem contrato IPC.

**Limite da liberação.** As verificações demonstram o comportamento determinístico diante das respostas simuladas e das construções de português examinadas. Elipses, escopo temporal e expressões fora dessas construções continuam limitando a política. A escolha espontânea de códigos e citações pela Luna depende da avaliação posterior. A revisão foi offline, sem abertura de casos finais, chamada de modelo ou acesso à conta. O congelamento e a integração com B ficam com o integrador.
