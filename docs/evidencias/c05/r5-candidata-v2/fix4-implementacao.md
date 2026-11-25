# R5-A · Quarta correção da cobertura em desenvolvimento

A política 2.1.0 aceitou os quatro alvos publicados por R5-B. Com as propostas fornecidas e um gateway local simulado, a decisão comum concluiu os três casos afetados, preservou os dois valores oferecidos pelo canal e fez um despacho simulado por caso. A prova mede o comportamento determinístico da política diante de uma resposta conhecida. A escolha espontânea de código e citação pela Luna continua sem medição nesta rodada.

**Entrega.** Base `b474570dda7aa5bdeb7d609848d5e6b46b936d59`, commit `f2c205608f62b06e4479c247e8bc06a892bb9bac`, branch `feat/luna-evidencias-r5`, worktree `.worktrees/r5-luna-evidencias`. O diretório do congelamento inicial permaneceu idêntico à base. A reabertura usou o pacote `r5-b-development-blocker.md`, o arquivo permitido de entradas de desenvolvimento e controles sintéticos. Zero chamadas externas. A revisão dirigida e o novo congelamento ficam com o integrador.

## Citações e decisões reproduzidas

Cada posição inicial e final formou um recorte literal contínuo, de 1 a 160 caracteres, avaliado por `field_data` e `verdict` sobre o texto integral. As contagens referem-se às posições examinadas. Não são probabilidades de acerto.

| Caso e campo | Exemplo de citação aceita | Aceitas na política 2.0 | Aceitas na 2.1 |
|---|---|---:|---:|
| jev-004, categoria | Uma venda no crédito de terça ainda não entrou no lote que caiu na minha conta. | 0/6.555 | 111/6.555 |
| jev-002, prioridade | ninguém consegue pagar e não temos outro meio de cobrança. | 0/10.011 | 3.108/10.011 |
| jev-006, categoria | Ganhei uma segunda maquininha. Onde encontro a opção de aumentar a letra da tela antes de pôr no balcão? | 0/5.460 | 500/5.460 |
| jev-006, prioridade | Onde encontro a opção de aumentar a letra da tela antes de pôr no balcão? | 0/5.460 | 64/5.460 |

As quatro propostas receberam `accepted/supported_relation`. Repeti cada caso por `R5Adapter.classify`, `replay_envelope` e `common.decide`. Repeti também com identificador trocado e conferi igualdade dos campos auditados, do desfecho e dos valores aplicados.

| Caso | Categoria na decisão | Prioridade na decisão | Desfecho |
|---|---|---|---|
| jev-004 | payouts, predita | intermediate, fornecida | complete |
| jev-002 | terminal, fornecida | urgent, predita | complete |
| jev-006 | terminal, predita | basic, predita | complete |

## Famílias e controles adicionais

| Propostas verificadas nos três novos métodos | Aceitações esperadas e observadas | Vetos esperados e observados |
|---|---:|---:|
| Venda ausente de lote com crédito em conta | 2/2 | 8/8 |
| Paralisação dos pagadores e disponibilidade de alternativa | 2/2 | 12/12 |
| Ajuste de exibição de um equipamento em preparação, categoria | 8/8 | 7/7 |
| Orientação durante esse preparo, prioridade | 5/5 | 8/8 |
| Total | 17/17 | 35/35 |

A venda precisa ser o sujeito e o lote precisa ter evidência do recebimento. As paráfrases cobrem débito, cartão, data, crédito em conta e entrada no saldo. Cupom incidental, lote de notas fiscais, recebimento hipotético e citação só do depósito receberam veto. Para urgência, a citação sustenta que os clientes não conseguem pagar. A ausência de alternativa pode estar em outra oração. Negação, pergunta, hipótese, dívida específica, falha restrita a cartão e meio de cobrança em funcionamento impediram a aceitação. A falta de outro transporte também recebeu veto.

O par “aquisição de terminal + pedido de ajuste antes do uso” exige orações adjacentes e objeto reconhecido. Para categoria a citação cobre o nome do terminal e a ação sobre a tela. Para prioridade pode cobrir só o pedido de orientação, com o contexto completo disponível para a análise de impacto. Testei outra tela, aparelho genérico, aquisição negada, menção incidental, prejuízo atual e sua negação. A política mantém limites de vocabulário, elipse, pontuação e resolução de referências. Uma citação literal verifica a origem textual, mas a suficiência semântica continua falível.

## Regressão e integridade

- A suíte focal passou nos 32 métodos, incluindo os 29 anteriores. Continuam cobertos falha afirmada versus negação, orientação após dano, recusa, tempo excedido, orçamento, procedência, replay adulterado, erro de formato e revisão sem aplicação parcial.
- Reexecutei as 14 propostas dos 12 cenários em `r5-independent-policy-checks.md` com a decisão comum e replay. Houve oito aceitações e seis vetos esperados. Nos vetos, conferi a abstenção no IPC, a proposta e a citação originais na auditoria. A suíte focal também confere o conteúdo bruto original e a distinção para erro técnico.
- Compilei `adapter.py`, `evidence.py` e `test_evidence.py` e li todos os JSON de R5. Os seis pins do manifesto conferem com os bytes. Os hashes do checkout e dos blobs de HEAD coincidem com os 12 pins originais de R3 e os sete de R4. O diff no diretório de congelamento histórico está vazio. O diff local, o preparado para commit e o intervalo da base até o commit passaram em `git diff --check`.
- A identidade da fábrica, da instância, do manifesto e do perfil identifica política 2.1.0. O conteúdo de `adapter.py`, o corpo da requisição e o prompt continuam em 2.0.0. O envelope segue em 1.0.0, o IPC em 1.1.0 e o schema privado em 1.0.0. A assinatura de `identity_for(mode)` e a de `replay_envelope(item, envelope, *, policy_sha256=None)` permanecem idênticas à base.
- Durante a implementação, um ensaio intermediário detectou uma expressão sem compilação no caminho de rotina. Após correção, repeti a suíte, a matriz, a varredura de citações e a reprodução dos três casos na versão entregue.

| Fonte | SHA-256 no commit entregue |
|---|---|
| evidence.py, política 2.1.0 | `8f2e0f9de8c5eade87eee9328f9951ea3fce1484a77e4c736be0f0ea8658b4bc` |
| candidate.json | `55b16817795ab030a2ac37a98e32d4c499fdc9a810bb0186860427f18adb2d61` |
| operational.json, perfil 2.0.0 | `745fbc7eeef9abf17c7fb2e3a8a28619a40941362ea4a8e8c01e75b20b28f1f3` |
| test_evidence.py | `b944669f9b4ffe7db8be0c8ff2c4285a365e983a2ccdec2527514e933306d86f` |
| adapter.py, adaptador 2.0.0 | `8ac5c50ace54a58293bd63c4147a262a6dfbfcb566a2f5be2aac3f3eb5dfeecf` |
| prompt.txt, prompt 2.0.0 | `fb4437c677a6b6eea2fb55d6fdebd7143b22c9738f273a561f4601cac38e1610` |
| rubrica comum 1.0.0 | `ac497f8d36af1aceb4eac39648ca7fe2c1e291d16cf512f27894b40e113ed4ac` |
| evidence-envelope.schema.json, envelope 1.0.0 | `c788f313a1c002f4c6e78b400a91120a2373d744184006b50725f91f7239f579` |

## Reprodução offline

Na worktree da candidata:

~~~sh
rtk proxy env PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen \
    python -m unittest adapters.luna.r5.test_evidence -v
rtk git diff --check b474570 f2c2056
~~~

Para reproduzir os três casos, selecione apenas os IDs da tabela no arquivo `docs/evidencias/c05/luna-r4-ensaio-real-01/development/inputs.jsonl`. Passe a `EvidenceTests.classify` o item intacto e um objeto por campo ausente com a citação acima, o código e o critério respectivos (`sales_settlement`, `immediate_harm`, `terminal_operation`, `routine`). O helper injeta o gateway e reproduz a auditoria. Use `decide(item, envelope["observation"], item["catalog"], RUN_ID)` para conferir o resultado aplicado.

**Exercício.** No teste de paralisação, compare a saída ao acrescentar “Mas os clientes já conseguem pagar por Pix.” e manter a mesma citação. A posição conserva a origem do trecho e o campo de veredicto registra a mudança provocada pela alternativa.

