# SF2-01 — revisão independente dos dados públicos

**SPEC aprovada. QUALITY aprovada.** O parecer se aplica à candidata de conciliação identificada abaixo. A worktree pública `.worktrees/sf2-dados-publicos`, na branch `feat/sf2-dados-publicos`, estava limpa em `e68577d84b3b9aa29b93d0e155f9d289a65f6cc8`. Os contratos usados têm base `c4fe01fa5d3b058d1ebf8ccb36a07a8b99b522a5`. O checkout mantém o rascunho com uma leitura A por relato. A promoção da candidata cabe ao responsável pela integração.

## SPEC

Conferi os bytes da worktree contra os objetos do commit dos dados. O conjunto contém 150 relatos de treino e 90 de validação. O contrato validou o rascunho autoral e validou separadamente as duas partições com as anotações conciliadas, incluindo estrutura, unicidade, separação das famílias e referências de texto.

- O treino contém dez exemplos de cada um dos 12 pares claros. Há 44 por categoria clara, 33 por prioridade clara e 18 insuficientes por campo, com seis de dupla insuficiência.
- Cada máscara de validação contém 30 relatos, com 24 classificáveis e seis de revisão. As três categorias dividem os classificáveis em 8/8/8. As máscaras com prioridade ausente têm seis exemplos classificáveis por nível. São 13 urgentes-alvo, seis em cada uma dessas duas máscaras e um adicional com categoria insuficiente na máscara de dois campos.
- Conferi os 60 alvos de cada campo e os 60 campos presentes no canal. Todos os valores presentes são válidos e coincidem com o gold da linha.
- Conferi os pins do catálogo, rubrica, lock do modelo e requisitos contra o protocolo. As 240 linhas de anotação têm as versões e assinaturas previstas para catálogo e rubrica.
- Retokenizei offline com `tokenizers==0.22.2` e o arquivo local de SHA-256 `2c3387be76557bd40970cec13153b3bbf80407865484b209e655e5e4729076b8`, revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. A contagem inclui tokens especiais, sem preenchimento ou truncamento. Os 240 resultados coincidem por ID com o recibo ligado aos hashes das partições. Treino de 14 a 72 tokens, validação de 22 a 78, limite de 128.

## QUALITY

Comparei a anotação A integral de cada linha com o objeto original no commit dos dados. Para B conferi as entradas cegas dos três lotes com os respectivos commits e os hashes das saídas seladas. Reconstituí a seleção pela correspondência do ID e dos bytes UTF-8 atuais com a entrada cega mais recente que continha aquele texto. O inventário coincide por linha com a seleção independente e com os dois hashes do lote. Para cada linha, o objeto B da candidata reproduz os campos do registro selado cujo ID está no nível externo da candidata.

| Origem B | Anotações selecionadas | SHA-256 da saída cega |
|---|---:|---|
| Original | 158 | `f17c8515f903706191ec45c34a5b7c07db02423f83c015da6accc33c110059a8` |
| Primeira revisão | 78 | `6738f3da0be182851f0affc1cdcd2162143d4e4461304baf6137bb573d1f7fcd` |
| Segunda revisão | 4 | `7afcc411c16014c5d0b0ca9d160ecfa8e6a4c90668fd7f5239f381fb420bacbc` |

Cada relato tem duas identidades distintas e origem IA explícita, justificativas por campo e conciliação atribuída. As duas leituras, a conciliação e o gold concordam nos 480 campos. Os 1.028 trechos citados aparecem literalmente nos textos. A nova leitura dirigida das fronteiras confirmou, por exemplo, que `sf2-train-122` identifica o terminal sem descrever o impacto, que `sf2-train-110` usa “urgente” por orientação de preenchimento e que `sf2-train-051` descreve retrabalho em vinte aparelhos após o plantão, com quinze dias até a próxima escala. A concordância entre IAs não mede a precisão frente a clientes reais.

A auditoria de novidade aprovada foi conferida contra ID, família, partição e texto vigentes em todas as linhas. Ela contém 622 pares obrigatórios, 170 complementares e sete comparações intrapartição, sem conflito remanescente. Seu SHA-256 é `153d1ea1923d4f9fd64a231026500e4afaf0255ff7228378376a9090ebefe884`. Os dados são sintéticos e balanceados por desenho. A limitação da revisão semântica por IA consta no recibo. A revisão abrange somente o conjunto público.

## Recibo e reprodução

O arquivo `public-acceptance-candidate/review_receipt.json` passou no schema `reviewReceipt` com zero desacordos não resolvidos e revisão semântica concluída. SHA-256 do recibo **`11b65d96576176808d7262a2ed917f52a1bb4f8b55e453a48dc42ec778005ef4`**.

| Papel | SHA-256 dos bytes |
|---|---|
| Treino | `d10ebb37c4a00bbbe466d01558ff67eef0ed6002db65793f0bc97d50eed91e83` |
| Validação | `b7d78a8adca44b1165cbadb804cbd879a3573a5c73d6311a592887d70ef68fc9` |
| Anotações conciliadas | `2cde06b88e8993aad3d7a2e761cf0933896e7db2d20e63ff9b2c2858436b3005` |
| Comprimentos por ID | `98ef16ed8f9f8428302cc2bd5a20a7d4fbd4b72b729fef7ca2c3ea7b6b3d197c` |
| Inventário da conciliação | `408c4a7c254c1eedb15936ee3c9d1c834927cc5a77d8c5efb80575b0ba30b55f` |

A chamada `validate_dataset(partitions, annotations, "accepted")` passou como verificação estrutural. Para reproduzir a checagem do pacote completo, montar em memória o manifesto da candidata com o estágio de aceite e o hash do recibo acima e executar `validate_manifest("publicManifest", manifesto, paths)` com treino, validação, anotações conciliadas, recibo e comprimentos. Esse ensaio passou com 150/90. O manifesto em disco continua provisório, e esta revisão não fez commit.
