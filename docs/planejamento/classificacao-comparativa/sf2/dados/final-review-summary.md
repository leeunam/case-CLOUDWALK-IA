# SF2-02 — revisão do conjunto final

O conjunto final foi selado em `sf2-ipc/1.0` após a revisão independente de
especificação, qualidade e novidade. A auditoria usou o conjunto público
aceito em `4e006a3a2937553e82bb7ca7022190980e56cdf5`, com 150 relatos de treino
e 90 de validação, e 112 relatos históricos únicos. O parecer de novidade
aprovou os 120 relatos, com zero colisões entre partições por ID, família
ou texto normalizado.

| Verificação | Resultado |
| --- | --- |
| Casos finais | 120, com 96 classificáveis, 24 de revisão e 17 urgentes-alvo |
| Quotas por máscara | 40 casos em cada uma, com 32 classificáveis e 8 de revisão |
| Campos solicitados | 80 alvos de categoria e 80 de prioridade |
| Anotações independentes | Duas por relato, 240 comparações de campo, zero divergências pendentes |
| Proveniência | Quatro lotes cegos, com 61, 14, 39 e 6 relatos da versão selada |
| Tokenização offline | 120 relatos, de 14 a 78 tokens incluindo especiais, zero truncamentos, limite de 128 |

A tokenização usou `tokenizers` 0.22.2 e a revisão
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42` do snapshot aprovado, com
`tokenizer.json` SHA-256
`2c3387be76557bd40970cec13153b3bbf80407865484b209e655e5e4729076b8`.
O recibo foi emitido por `sf2-02-revisor-independente-novidade-spec-quality`.
A autoria, as anotações cegas, a conciliação e a revisão foram feitas por IA.
Os relatos são sintéticos em português e seguem quotas fixas. A concordância
entre os anotadores descreve este lote. Medir qualidade em produção exigiria
validação humana e avaliação com tráfego real.

| Artefato | SHA-256 |
| --- | --- |
| Dados finais | `6eeb6fa76aa8e2a648ccad2e1ec89afc8c91ba1ec41b1578c4281041a08c0b51` |
| Anotações conciliadas | `027c175a0a22cbefcf237467be1c0b3dd036544b33159e265f6be555e80dc924` |
| Comprimentos tokenizados | `cb953d63fdcc4c540e7058d4cadd294ef4907435ef334d6343194eca19ba55f1` |
| Proveniência | `ddb21de423712844716b6c22740ded22cc0dd2ec0b9e41522b7b01142e077336` |
| Projeção pública usada na auditoria | `51770d4c896a011081c10e5aba168c4b834c1d7c77ce6ced7e2eb8886ca9296f` |
| Manifesto público integrado | `36cbb5dab996775391a0c59802892a2b30d558fbf35b13e2620f0e7950d01ec9` |
| Parecer privado de novidade | `564f65c29c908a0b6a91e1793dc55779825429716168b9d25d3bcee8f2e90c98` |
| Relatório privado de qualidade | `726001ab44ff4d7dfbd69c7a8c2074aa1c69aadc15004e48405a14631bd9b5a3` |
| Recibo independente | `58dcf3c81dce0ba28b539121d541209bf353a29878821e9c80940e035007f369` |

Os arquivos canônicos permanecem sob custódia em
`.superpowers/sdd/conclusao-projeto/sf2-final/accepted/`. A equipe que
desenvolve a candidata usa o [selo público](final-seal.json) para o
congelamento de pré-treino. Somente o executor independente da SF2-05 pode
abrir o pacote para o ensaio, após a validação cumprir os gates e o modelo,
o adaptador e a política serem congelados. Para conferir a entrega, compare
os totais e os hashes do selo com este resumo.
