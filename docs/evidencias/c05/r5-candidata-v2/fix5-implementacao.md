# R5-A · Pagamento por outro meio e paralisação total

Na base `f2c205608f62b06e4479c247e8bc06a892bb9bac`, o relato de clientes pagando em dinheiro ou por Pix ainda permitia aplicar urgência por paralisação total. O commit `38ac4cb81abe9f84469e379cee30e6bb976e25dd` devolveu ambos para revisão com `veto/context_conflict` e prioridade aplicada nula. A única proposta partiu de um gateway simulado. O replay reproduziu o veredicto e a decisão comum preservou a categoria terminal recebida.

**Entrega para revisão dirigida.** Branch `feat/luna-evidencias-r5`, worktree `.worktrees/r5-luna-evidencias` limpa. A relação liga o pagador ao verbo e ao meio ou liga o meio ao funcionamento atual. Reutiliza escopo de afirmação, negação, hipótese e futuro e respeita a última restauração. Uma dúvida explícita quanto ao pagamento atual também impede confirmar a paralisação total. A justificativa de uma perda independente continua disponível quando a citação a identifica.

## Comparação direta

As 17 variantes usam a mesma proposta `urgent/immediate_harm` e a mesma citação “Ninguém consegue pagar”. O relato começa por “Ninguém consegue pagar e não temos outro meio de cobrança”. Cada variante foi avaliada com os mesmos bytes de entrada e a mesma resposta no adaptador, alternando a política da base e a corrigida. A tabela agrupa o desfecho de `common.decide`. Duas propostas adicionais verificam perda independente e veto a rotina.

| Continuação | Base f2c2056 | Correção 38ac4cb |
|---|---|---|
| “Mas os compradores pagam em dinheiro normalmente.” | complete · urgent | review |
| “Mas todos os clientes pagam por Pix normalmente.” | complete · urgent | review |
| “, e todos os compradores estão pagando com cartão.” | complete · urgent | review |
| “O pagamento por Pix continua funcionando.” | complete · urgent | review |
| “Não sei se os compradores estão pagando em dinheiro.”, “Talvez os clientes paguem em espécie.” e “Os clientes pagam por Pix?” | 3 complete · urgent | 3 review |
| “Mas os compradores conseguem pagar em dinheiro.” e “Os clientes continuam pagando pelo celular.” | 2 review | 2 review |
| Sem continuidade, duas negações de pagamento, dois pagamentos exclusivamente passados, dois futuros e uma condição de retorno da rede | 8 complete · urgent | 8 complete · urgent |
| Perda de vendas separada e citada, apesar do pagamento alternativo | complete · urgent | complete · urgent |
| Pedido de configuração citado para basic com interrupção e disponibilidade contraditórias | review | review |

No commit, as 19 propostas produziram 9 aceitações e 10 vetos esperados. Sete decisões mudaram, todas de urgência aplicada para revisão. A matriz da suíte verifica a posição da citação, o motivo, a decisão, a prioridade aplicada e uma chamada simulada por caso de paralisação. Cada classificação faz replay local vinculado ao digest da política.

## Regressões e integridade

- A suíte passou nos 33 métodos, os 32 anteriores mais o método desta correção. A matriz anterior de 52 propostas nos três métodos da fix4 continua incluída.
- Reexecutei as 14 propostas dos 12 cenários de `r5-independent-policy-checks.md` por classificação, replay e decisão comum. Foram 8 aceitações e 6 vetos. Conferi os valores fornecidos, a proposta e o trecho literais na auditoria, o corpo bruto e a abstenção no IPC. A suíte focal também cobre entrada completa e inválida sem despacho.
- No arquivo público de desenvolvimento, as quatro propostas do pacote de bloqueio receberam `accepted/supported_relation`. As três decisões foram `complete`. Em jev-004, payouts completou intermediate recebido. Em jev-002, urgent completou terminal recebido. Em jev-006, terminal e basic foram aplicados juntos. A troca do identificador preservou os quatro resultados. Uma chamada simulada por caso.
- A política continua em 2.1.0, adaptador e perfil operacional em 2.0.0, envelope em 1.0.0 e IPC em 1.1.0. Conferi os seis hashes do manifesto nos arquivos e blobs do commit, além dos 12 hashes originais da R3 e sete da R4. O SHA de `operational.json` confere sem alteração de bytes. O adaptador que constrói o corpo, o prompt e o schema do envelope são os da base. Compilei os três módulos Python R5 e conferi a leitura dos JSON. O diff local, o staged e o intervalo da base ao commit passaram em `git diff --check`. O congelamento R5 v1 tem diff vazio.

| Fonte | SHA-256 |
|---|---|
| evidence.py | `42dcd4fd4806a485606d359eb64b86bcb59e4e299892288ce4e3624cde971557` |
| candidate.json | `d95c4691cbd4babeb000be285b4bdbca632bf4d8ea4ffe3b83d818579ac9df99` |
| operational.json | `745fbc7eeef9abf17c7fb2e3a8a28619a40941362ea4a8e8c01e75b20b28f1f3` |
| test_evidence.py | `7ffcc2e31c75dd05a487b9d7c81b3868beef0c9081835d0f4387945b4bc1caa3` |

## Reprodução offline

Na raiz da worktree da candidata, execute

~~~sh
rtk proxy env PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen \
    python -m unittest adapters.luna.r5.test_evidence -v
rtk git diff --check f2c2056 38ac4cb
~~~

Para reproduzir a comparação, injete um gateway que devolva `{"priority":{"code":"urgent","criterion":"immediate_harm","quote":"Ninguém consegue pagar"}}` para cada continuação da tabela. Use o helper `item` com `requested=("priority",)`, execute `EvidenceTests.classify` em cada versão e passe a observação a `decide`. O método `test_pagamento_por_outro_meio_contradiz_paralisacao_total` contém a lista integral e os asserts da versão corrigida. Como exercício, compare o veredicto entre “os clientes pagam por Pix” e “os clientes pagavam em dinheiro antes da falha”, mantendo a mesma citação.

Os resultados dependem de construções reconhecidas em português. Vocabulário não coberto, elipses e marcadores temporais ou de negação fora de seu escopo usual podem alterar o resultado. Houve zero chamadas externas, acesso a dados reservados ou medição da escolha espontânea da Luna. O novo congelamento, a integração e a decisão sobre ensaio ficam com o integrador.
