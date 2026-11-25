# SF2-01 — novidade dos 240 relatos públicos

**Parecer: revisão necessária antes do treino.** A auditoria encontrou 123 pares que repetem evento-base e 73 cuja independência permanece incerta. Os 240 identificadores de família são distintos. Nenhum texto repetiu literalmente após normalização e nenhum par atingiu Jaccard de 0,80.

## Alcance e método

Base de contratos `c4fe01fa5d3b058d1ebf8ccb36a07a8b99b522a5`. Projeção pública do commit `50ee50a583c5c6e359ac075919fcb3a2944c805c`, SHA-256 `e893dd83b06e0bdba6e33a50a4cb7c9b8f66072a5c6efc43332b5a81a324f93b`. A projeção contém somente ID, família declarada, partição e texto.

Comparamos 150 relatos de treino e 90 de validação com a partição oposta e com 112 textos históricos distintos (172 registros, incluindo 60 duplicações históricas). Foram 53.880 comparações direcionadas, das quais 27.000 entre partições públicas e 26.880 entre público e histórico. Elas equivalem a 40.380 pares distintos.

A função aceita `novelty_candidates` ordenou o conjunto unido por Jaccard de tokens normalizados e ID. As três sugestões de cada registro deram 720 revisões direcionadas, correspondentes a 623 pares únicos após juntar os dois sentidos. O maior Jaccard foi 0,2973. Nenhum texto público tinha menos de cinco tokens. A checagem de duplicatas usou NFKC, casefold e redução de espaços.

A leitura dos relatos e a comparação dos fatos acrescentaram 134 pares, totalizando **757 pares únicos julgados**. Comparamos o objetivo e o que causa, contorna ou resolve o problema. Nome do estabelecimento, bem comprado, prazo e volume podem mudar mantendo o mesmo evento. Atribuições nos pares obrigatórios: independente 553, same_family 41, uncertain 29. No painel completo: independente 561, uncertain 73, same_family 123.

## Exemplos de julgamento

| Par | Juízo | Motivo |
|---|---|---|
| sf2-train-007 ↔ r2:r2-033 | same_family | O banco já creditou um único ponto, o portal continua indicando trânsito/pendência e a conciliação automática pula exatamente esse lote. A baixa manual fecha os dois relatos. |
| sf2-train-103 ↔ r2:r2-013 | same_family | Silenciar a máquina de demonstração para a aula, com o leitor real funcionando no balcão, é o mesmo pedido com mudança do local do curso. |
| sf2-validation-082 ↔ r2:r2-019 | same_family | A leitora solta fumaça persistente ao lado de clientes no balcão; cheiro de queimado e retirada do carregador detalham o mesmo incidente. |
| sf2-train-121 ↔ sf2-validation-024 | same_family | A identificação dos pagadores some de todo o extrato/exportação Pix de uma arrecadação e a prestação de contas exige reconstituir centenas de participantes. |
| sf2-train-034 ↔ sf2-validation-022 | independente | No estacionamento de treino os carros não conseguem pagar porque o terminal está apagado. Na validação o pagamento foi aprovado e a cancela física é que não abre. |
| sf2-train-060 ↔ sf2-validation-079 | uncertain | Nos dois falta confirmação sonora ao ler, mas só o primeiro identifica aproximação de cartão e no segundo nem o tipo de aparelho fica claro. |

Os pares classificados como mesma família formam 44 grupos conectados. O campo `same_family_groups` lista todos os integrantes de cada grupo. O vínculo direto de cada par está registrado em `pair_reviews`.

## Escopo de correção

Substituir todo relato público que reutilize histórico; nos pares apenas entre treino e validação, dar preferência à substituição da validação, preservando o treino quando o outro extremo já cobre o conflito. Trata-se de proposta de escopo específica a estes pares. Antes de fechar, adjudicar os pares uncertain remanescentes e auditar novamente cada novo relato. Nenhuma linha foi alterada.

**70 IDs propostos para substituição.** Os números abaixo são o sufixo do ID da respectiva partição.

- train: 002, 007, 011, 013, 020, 021, 026, 028, 030, 034, 037, 038, 039, 043, 048, 053, 057, 064, 080, 093, 103, 107, 108, 115, 119, 122, 127, 131, 132, 133, 136, 139, 141, 143, 144, 148, 149.
- validation: 003, 010, 011, 016, 020, 023, 024, 025, 026, 031, 033, 036, 037, 038, 045, 053, 056, 058, 062, 064, 066, 067, 068, 069, 070, 071, 072, 075, 078, 082, 083, 086, 090.

**45 pares incertos restam para adjudicação depois dessas substituições**, envolvendo 46 IDs públicos. Substituir um extremo quando a revisão confirmar reuso; enquanto o fato central permanecer ambíguo, manter pendente.

- train: 006, 009, 018, 019, 022, 031, 036, 046, 047, 049, 051, 054, 060, 061, 066, 067, 082, 084, 087, 089, 091, 092, 094, 104, 109, 117, 125, 135, 146.
- validation: 002, 004, 009, 014, 017, 021, 028, 039, 041, 055, 059, 063, 074, 079, 080, 087, 088.

No conjunto dos dois tipos de alerta, 140 relatos públicos participaram de ao menos um par. A lista completa de pares, inclusive os independentes, traz os IDs integrais, as pontuações, a origem da seleção e uma justificativa por par em `report.json`. O JSON identifica os aliases históricos e informa quais pares incertos a proposta já resolveria pela substituição de um extremo.

## Integridade das fontes

| Fonte | SHA-256 | Objeto Git |
|---|---|---|
| script/f08/jev/dataset.json | `0e7e4c342c2a39cefd89855d8c0513f447d7878303eb4091488ca8af78928880` | `b6d0b326fbde55025ef9be5e0b3d24aca2d0e4a4` |
| docs/planejamento/classificacao-comparativa/r2/dataset.json | `3f4e69af44f03c89d1767d54ba07264327d616f18b0548656cc00c7bb89e3845` | `5843e5c388e45c9db7d35e923a78f257ce900a58` |
| docs/planejamento/classificacao-comparativa/r2/final-cases.json | `17f5bae372983f90aa1956d0d583db25483a77a3ff35e4f1041ad4d51b897af9` | `1d723e0aedc0d0481ca76bbaf615d920b76d45db` |
| docs/planejamento/classificacao-comparativa/r4/diagnostico/inputs.jsonl | `07777cf652d481c8f3c98f5c825679fe65bcafdb27919dd62ca92338af9e101b` | `9f359b498dcc555b8ad786b5c696b04188613dfe` |
| script/classification_comparison/setfit_sf2/contracts/data.py | `e918a5b5606051d8ded78733d1a95b245a5559cd4c0dc8679556596b20d7cd4b` | `6bd7e9a3768cc79026e08ca735cad4402c846daa` |

## Reprodução e limites

Na base indicada, reagrupar os quatro históricos pelo texto normalizado e preservar a origem de cada ID. Para cada relato da projeção, executar o contrato sobre a união da outra partição com os históricos distintos. Os campos selection e jaccard do JSON permitem reproduzir a seleção; os resumos de fatos e os motivos explicitam o julgamento qualitativo.

Revisão textual por um agente de IA, sem validação humana. A triagem lexical cobre todas as comparações e a revisão semântica cobre os pares declarados. Não há prova de independência exaustiva dos pares omitidos, de autoria original ou de isolamento de conjuntos fora do escopo. Sem treino, chamadas externas, uso de gold, leitura de anotações ou acesso aos dados finais SF2.
