# F08-B · Avaliação do classificador Jev

O ensaio chama `Classification::Jev::Classifier` diretamente com o catálogo
fixado. O modo offline usa o `DemoFixture` e controles com `FixtureClient` e
`HttpClient` com conexão simulada. O modo ao vivo usa o `HttpClient` do produto.
O relatório observa a decisão do adaptador antes de qualquer persistência,
retentativa de job ou encaminhamento do atendimento.

## Conjunto e rótulos

[Dataset](../script/f08/jev/dataset.json) e [catálogo](../script/f08/jev/catalog.json)
estão na versão 1.0.0. São 60 relatos novos e sintéticos em português, com 20
por máscara de omissão. Os três grupos se alternam na ordem do arquivo, e cada
relato tem ID, texto, campos recebidos, campos omitidos, rótulos esperados,
estrato e justificativa. O validador confere os códigos e as descrições do
snapshot contra o catálogo do produto. O snapshot usa as categorias das
marcas do seed e as prioridades do contrato v1.

Use o assunto em que o problema ocorreu ou sobre o qual o cliente pede
orientação. Uma venda aprovada com crédito ausente trata de repasse, uma
transação ou estorno instantâneo trata de Pix e um problema físico ou de
configuração do leitor trata de maquininha. Compare o impacto e o tempo para
agir. `basic` cobre orientação sem prejuízo atual, `intermediate` indica impacto
moderado com operação disponível, `advanced` indica impacto relevante sem ação
imediata e `urgent` exige intervenção imediata. Paralisação total em andamento,
perda continuada ou um compromisso iminente sem alternativa podem justificar
`urgent`.

Marque `informacao_insuficiente` para o campo que o relato não permite decidir.
Assunto desconhecido pode coexistir com urgência clara, como em `jev-027`.
Expressões de pressa, isoladamente, são evidência insuficiente de impacto.
`rotina` indica relatos determináveis sem urgência imediata, incluindo casos
`advanced`. `ambiguo` indica pelo menos um campo com abstenção esperada, mesmo
quando o outro campo é urgente. Há 35 relatos de rotina, 13 urgentes e 12
ambíguos. O recorte de prioridade urgente tem 10 relatos com prioridade omitida
e esperada como `urgent`, independentemente do estrato.

Os rótulos foram escritos antes do primeiro ensaio e seguem provisórios até a
revisão humana no chat central. Registre o SHA-256 exato da versão revisada.
A amostra tem distribuição de omissões planejada, poucas categorias, um
rótulo por campo e texto sintético. As proporções medem esse conjunto e têm
generalização limitada para atendimentos reais ou catálogos por marca.

## Como rodar

Execute da raiz desta worktree. O runner usa Ruby 3.3 ou superior e os módulos
do backend via `require_relative`. O teste usa Minitest. A versão do backend
está em `backend/.ruby-version`.

```sh
rtk proxy ruby script/f08/jev/run.rb --mode validate
rtk proxy env -u TYPESAFE_API_KEY ruby script/f08/jev/run.rb --mode offline > /tmp/cloudwalk-f08-jev-offline.json
rtk proxy ruby script/f08/jev/test_evaluation.rb
```

Depois da revisão e da definição do orçamento, injete `TYPESAFE_API_KEY` no
ambiente e rode o comando abaixo. Use o hash aprovado pela revisão central,
a referência registrada de orçamento e o modelo selecionado. Para uma
primeira amostra, `--limit 6` inclui dois casos de cada máscara. O limite
obrigatório conta relatos na ordem versionada, com máximo de uma requisição
por relato, até duas perguntas por requisição, concorrência 1, timeout de
5 s e zero retentativas. A referência registra a aprovação do orçamento e
o limite de casos controla o volume de chamadas.

```sh
rtk proxy ruby script/f08/jev/run.rb --mode live --limit 6 \
  --reviewed-sha256 "$F08_JEV_REVIEWED_SHA256" \
  --budget-reference "$F08_JEV_BUDGET_REFERENCE" \
  --model "$F08_JEV_MODEL" > /tmp/cloudwalk-f08-jev-live.json
```

Sem `--model`, o runner usa `CLOUDWALK_JEV_MODEL` ou `jev-latest`. Para
comparações, prefira uma versão fixa quando disponível e confira o modelo
retornado no relatório. Pré-condições inválidas saem com código 2 e JSON
`blocked` no stderr. Quebra de preservação, do contrato de perguntas ou de
controle offline gera `invariant_failed` e código 1. `completed` indica que o
procedimento terminou e suas invariantes passaram. Falhas do fornecedor
continuam registradas nas métricas por caso.

## Leitura do resultado

Cada taxa contém `count`, `denominator` e `fraction` de 0 a 1. Quando o
denominador é zero, `fraction` é `null`. Cada campo recebido válido entra só na
taxa de preservação. A comparação usa igualdade de códigos.

| Métrica por campo | Numerador e denominador |
| --- | --- |
| Acerto na resposta por campo | Escolhas válidas iguais ao código esperado / omissões com código esperado. |
| Acerto dado que houve escolha | As mesmas escolhas certas / escolhas válidas nos campos com código esperado. |
| Acerto aplicado | Códigos corretos com origem `jev` / omissões com código esperado. |
| Cobertura automática | Valores com origem `jev` / todas as omissões, inclusive com abstenção esperada. |
| Abstenção | Abstenções válidas / todas as omissões. |
| Abstenção correta e indevida | Abstenções válidas / campos cuja referência era abstenção ou código, respectivamente. |
| Aplicação em caso ambíguo | Valores aplicados / campos cuja referência era abstenção. |
| Resposta inválida, falha de transporte e campo sem resposta | Contagem de cada resultado / todas as omissões. |

A resposta por campo considera a validação Choice do adaptador. A classificação
aplicada pode ficar vazia mesmo quando uma escolha isolada está correta. Uma
abstenção ou erro em qualquer campo bloqueia o complemento inteiro. O relatório
preserva `issues`, o código observado quando disponível e o código aplicado; uma
escolha observada que falhou na validação não entra como acerto. As taxas de
urgência dividem as omissões rotuladas `urgent` em aplicação urgente,
aplicação não urgente, abstenção ou revisão, resposta inválida e falha de
transporte.

O manifesto registra revisão Git, indicador de mudanças locais, versões,
SHA-256 dos arquivos, configuração, modelo solicitado e modelos retornados.
As contagens de requisições são chamadas tentadas ao cliente e incluem
tentativas com erros. Os p50/p95 ao vivo usam a latência do adaptador em
milissegundos, incluindo rede e falhas com medição, pelo método do posto mais
próximo. O adaptador atual não fornece custo faturado ou unidade de cobrança.
O relatório ao vivo sinaliza custo indisponível e não estima preço. Offline
deixa latência e custo do fornecedor sem medição.

## Resultado de verificação offline

A [amostra de relatório](../script/f08/jev/sample-offline.json) é um extrato de
uma execução offline completa em Ruby 3.3.8. A fixture de demonstração processou
60 relatos com 80 perguntas, preservou 40 de 40 campos do canal e completou
automaticamente 9 de 60 casos. Os sete controles passaram. Nenhuma chamada
externa foi feita e os números descrevem a fixture e o avaliador.

| Campo | Acerto na resposta | Acerto aplicado | Cobertura automática | Abstenções |
| --- | --- | --- | --- | --- |
| Categoria | 18/34 | 8/34 | 8/40 | 22/40 |
| Prioridade | 2/33 | 2/33 | 2/40 | 37/40 |

As 10 omissões rotuladas como urgentes seguiram para revisão na fixture.
A execução ao vivo aguarda revisão humana e orçamento no chat central.

**Exercício.** Calcule o acerto de categoria entre as escolhas válidas da
fixture, depois compare com o acerto aplicado. Localize `jev-003` no relatório
completo e identifique qual resposta impediu a aplicação da categoria Pix.
