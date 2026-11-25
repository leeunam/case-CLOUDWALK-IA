# SF2-01 — revisão de novidade pública da primeira correção

**Ainda há 4 pares da mesma família. A menor correção cobre os quatro com 4 substituições e preserva os 158 textos retidos.** Os IDs propostos são `sf2-train-048`, `sf2-validation-002`, `sf2-validation-037`, `sf2-validation-075`.

| Pares a corrigir | Seleção | Motivo |
|---|---|---|
| sf2-train-037 ↔ sf2-validation-037 | Leitura complementar | Uma configuração do terminal aprova a compra em modalidade diferente da devida e onera o cliente pela fonte de pagamento errada. Carteira de benefício lançada como comum e débito lançado como crédito financiado substituem as modalidades na mesma falha de roteamento. Juros, estágio do plantão e momento da correção mudam o impacto, mas não separam o evento-base de maneira suficiente. |
| sf2-train-048 ↔ sf2-validation-029 | Vizinhos contratuais | Os dois solicitantes querem baixar um demonstrativo-modelo de liquidação de vendas para treinar pessoas, enquanto a liquidação real está regular. Indicar que o exemplo deve mostrar a divisão das taxas especifica o conteúdo do mesmo documento solicitado. Os dois textos continuam descrevendo a mesma ação e a mesma circunstância. |
| sf2-train-062 ↔ sf2-validation-002 | Vizinhos contratuais | A data de um conjunto localizado de créditos diverge entre controle de liquidação e banco. Os valores já entraram corretamente e o lojista resolve pela mesma correção manual da data no fechamento. A validação atribui a discrepância ao feriado municipal, mas conserva a evidência, o encadeamento e o ajuste do relato de treino. |
| sf2-train-119 ↔ sf2-validation-075 | Vizinhos contratuais | A operação corrente do leitor desfaz a autorização de outra compra já paga e o erro se propaga pelas próximas operações. Em um terminal isso ocorre ao cancelar o item atual; no outro, um botão lateral preso aciona a desautorização ao aprovar a venda seguinte. O defeito funcional característico é a reversão cruzada de compras alheias, com o mesmo pedido de interrompê-la. |

## Cobertura e conciliação

A projeção do commit `bce33eeadd262b91a7f85883ce50df86b8eebcd2` tem SHA-256 `d4e7df89b52ac09db2ca9e9161e1efb3d61da57c173a8b0ad9b13e272377b0bb`. Os 82 IDs modificados são exatamente os 70 da auditoria original mais os 12 da adjudicação. Os demais 158 preservam os quatro campos projetados. Os 123 pares originais da mesma família tiveram ao menos um extremo reescrito. Entre os 45 pares posteriormente adjudicados, 15 foram superados pela mudança dos textos e 30 conservam os dois textos e sua decisão anterior de independência.

O contrato de `c4fe01fa5d3b058d1ebf8ccb36a07a8b99b522a5` comparou 150 relatos de treino, 90 de validação e 112 textos históricos distintos obtidos de 172 registros. Foram 53.880 comparações direcionadas (40.380 pares). Cada registro público recebeu seus três vizinhos. Não houve duplicata normalizada, identificador de família cruzado, texto público abaixo de cinco tokens ou Jaccard ≥ 0,80. Maior Jaccard: 0.2857.

Os 720 vínculos direcionados formam **620 pares obrigatórios**. Foram reaproveitados 318 julgamentos cujos dois textos conservaram os bytes e julgados novamente 302 pares. Os 82 novos textos também foram examinados por seus fatos, inclusive contra históricos e textos retidos com poucas palavras em comum. As 124 comparações suplementares levam o painel a 744 pares únicos: 740 independentes e 4 da mesma família. O JSON registra os IDs, origem, posição e pontuação, fatos, motivo por par e hashes individuais e por par.

Por exemplo, o depósito de terceiros apreendido em bloqueio judicial difere de uma compensação automática da dívida de um vendedor com saldo de outros, embora ambas prejudiquem terceiros. A conferência também separou o leitor que exibe cartões inteiros para pessoas que filmam do aparelho fisicamente adulterado que levanta suspeita de cópia.

## Fontes e reprodução

| Fonte | SHA-256 |
|---|---|
| script/f08/jev/dataset.json | `0e7e4c342c2a39cefd89855d8c0513f447d7878303eb4091488ca8af78928880` |
| docs/planejamento/classificacao-comparativa/r2/dataset.json | `3f4e69af44f03c89d1767d54ba07264327d616f18b0548656cc00c7bb89e3845` |
| docs/planejamento/classificacao-comparativa/r2/final-cases.json | `17f5bae372983f90aa1956d0d583db25483a77a3ff35e4f1041ad4d51b897af9` |
| docs/planejamento/classificacao-comparativa/r4/diagnostico/inputs.jsonl | `07777cf652d481c8f3c98f5c825679fe65bcafdb27919dd62ca92338af9e101b` |
| script/classification_comparison/setfit_sf2/contracts/data.py | `e918a5b5606051d8ded78733d1a95b245a5559cd4c0dc8679556596b20d7cd4b` |

Aplicar `novelty_candidates` à outra partição pública e aos históricos normalizados, desempatar por ID, manter os três vizinhos e todos a partir de 0,80. Conferir SHA-256 do texto em UTF-8 de ambos os extremos antes de reaproveitar uma decisão. O JSON inclui o recibo individual dos 45 pares anteriores e a regra exata de hash do par.

## Limite do parecer

Julgamento textual por uma instância de IA. Todos os pares contratuais estão registrados, além dos suplementares selecionados pela leitura dos fatos; não houve revisão semântica exaustiva de todas as combinações. Esta revisão não lê anotações, gold ou dados finais SF2, não treina modelo, não verifica quotas e não aceita o conjunto em nome do validador.

Os quatro novos textos de substituição ainda precisam ser escritos e revisados antes do treino.
