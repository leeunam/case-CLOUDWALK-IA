# CLASS-001 · Contratos do experimento 1.0.0

Um relato sintético produz uma decisão mesmo quando o classificador recebe zero
chamadas. A chave de uma decisão é o par `(run_id, id)`. A observação da
tentativa acrescenta `attempt`. O [protocolo aprovado](../protocolo-comparacao.json)
fixa uma tentativa por relato e concorrência 1. Cada candidato tem seu próprio
`run_id`. A [rubrica comum](../rubrica-comum.md) acompanha o catálogo nos dois
adaptadores, com zero exemplos na linha de base.

| Arquivo do lote | Unidade | Exemplo estático |
| --- | --- | --- |
| [input.schema.json](input.schema.json) | Uma entrada por relato | [inputs.jsonl](fixtures/inputs.jsonl) |
| [observation.schema.json](observation.schema.json) | Uma observação por tentativa, inclusive falhas | [observations.jsonl](fixtures/observations.jsonl) |
| [decision.schema.json](decision.schema.json) | Uma decisão por relato, inclusive controles | [decisions.jsonl](fixtures/decisions.jsonl) |
| [report.schema.json](report.schema.json) | Um manifesto/relatório JSON por execução | [report.json](fixtures/report.json) |

[common.schema.json](common.schema.json) contém tipos compartilhados. Todos os
schemas usam JSON Schema 2020-12. Os identificadores HTTPS com domínio
`.invalid` são nomes de recursos resolvidos localmente. Versão incompatível
do contrato ou envelope malformado interrompe a leitura antes de invocar o
adaptador.

## Entrada e lote Ruby/Python

JSONL usa UTF-8, um objeto JSON completo por linha, sem cabeçalho, linhas
vazias, chaves repetidas ou valores não finitos. Mensagens de diagnóstico
ficam fora desse fluxo. Ruby e Python podem trocar arquivos ou usar streams.
C02 define a linha de comando e como ligar os processos. Um único processo
local carrega os pesos uma vez por lote e responde na ordem de entrada. Cada
processo registra tempo de inicialização/carregamento separado. Processar os
dois campos de um relato pode envolver uma ou duas perguntas dentro da mesma
tentativa. Uma falha gera uma observação identificada, inclusive quando não
houve resposta do fornecedor. Nunca inferir o ID de uma resposta por sua posição.

O avaliador projeta `id`, `text`, `received` e `missing` do dataset, acrescenta
`contract_version`, a marca fixa `marca-sintetica` e o objeto do catálogo
versionado. O experimento usa uma marca fictícia com o catálogo congelado da
C01. A validação compara códigos, descrições e versão com a fonte congelada
antes da inferência. O corpo `received` conserva os valores originais para
diagnosticar tipos e códigos inválidos. Chaves aceitas em seus dois níveis
são fechadas pelo schema. `expected`, justificativas, estrato, revisão,
saídas anteriores e métricas ficam no avaliador. O adaptador recebe somente
entradas aptas à inferência e inclui no contexto do modelo apenas texto,
marca, ID, valores válidos do canal, campos ausentes e definições comuns.

`missing` lista as ausências reais na ordem `category`, `priority`. Omissão,
`null`, texto vazio ou só espaços indicam ausência. Um código válido precisa
coincidir exatamente com o catálogo. Outro valor presente, inclusive um
objeto ou número, é inválido. Máscara inconsistente é erro de contrato.
Catálogo de versão ou conteúdo incompatível e campo presente inválido são
controles com zero tentativas e decisão de revisão. Em controle de catálogo,
os códigos recebidos reconhecidos no catálogo congelado da marca são preservados
para revisão. Dois campos válidos encerram a classificação com zero tentativas.

## Observação e aplicação

A observação identifica modo, fornecedor, modelo solicitado e retornado, revisão
dos pesos, versões do adaptador e da política. Um identificador de modelo
pode ser um alias. Quando houver versão esperada, fixar
`identity.expected_returned_model` e/ou `identity.expected_weights_revision`
antes do lote. Uma divergência verificada na resposta gera `version_mismatch`
e revisão. Um timeout pode deixar modelo retornado e revisão `null`.
`version_error_raw` aceita diagnóstico sintético de uma resposta de versão
recusada. Não incluir credenciais ou cabeçalhos. Registrar no material de
política como cada adaptador constrói a entrada comum, a versão dos pesos,
os limiares aplicáveis e qualquer limitação conhecida antes do teste final.

A observação tem exatamente uma entrada em `choices` por campo solicitado.
Ela mantém o valor bruto mesmo diante de recusa pela política. O avaliador
junta entrada, observação e decisão pelo ID para reconstruir valor recebido,
pergunta, resposta bruta e aplicação.

| Estado do campo | Interpretação | Valor efetivamente aplicado |
| --- | --- | --- |
| `provided` | Campo válido fornecido pelo canal | Sempre o valor recebido |
| `predicted` | Escolha bruta com código válido | Código escolhido se todos os campos foram resolvidos |
| `abstained` | Razão `explicit` para `informacao_insuficiente` ou `policy` para recusa pela política congelada | `null` |
| `invalid` | Valor recebido inválido, saída inválida ou campo de resposta ausente | `null` |
| `error` | Timeout, transporte, revisão de modelo incompatível ou falha do adaptador | `null` |
| `not_requested` | Ausência que não gerou pergunta porque a validação bloqueou o relato | `null` |

Uma saída que omitiu uma escolha é normalizada como `invalid`, com
`reason: "missing_output"` e `raw: null`. Em erro operacional de um dos campos,
registrar o erro nele e conservar quaisquer respostas já obtidas nos demais.
Uma tentativa totalmente sem resposta registra erro em todos os campos
solicitados. `requests` conta invocações ao fornecedor/motor local.
`questions` conta campos efetivamente perguntados. Uma falha antes do envio
pode registrar zero para ambos. O protocolo conta uma tentativa nesse caso.

Na decisão, `complete` requer os dois códigos válidos. Um bloqueio ou qualquer
escolha recusada, ausente, inválida ou com erro leva a `review` e mantém
`applied: null` em **todos** os campos que faltavam. Em `ctl-sem-assunto`, a
escolha bruta `urgent` coincide com a urgência descrita no exemplo. A abstenção
na categoria impede aplicar até essa prioridade. O campo ainda é contabilizável
pelo futuro avaliador para reconhecimento bruto de urgência.

`score` omitido ou `null` significa ausência de score. Quando existe, sua
natureza é `provider_probability` (0 a 1), `ranking` (número da escala do
modelo) ou `self_report` (texto do fornecedor). O relatório v1.0.0 registra calibração **não avaliada**
em `score_calibration`. Preservar a escala original. A fixture inclui um ranking
de 2,7 que não pode ser interpretado como probabilidade.

## Medições e manifesto

- `elapsed_ms` usa relógio monotônico para o relato completo, da validação ao
  término da decisão incluindo perguntas, interpretação e erros. O avaliador
  pode finalizar esse valor ao persistir a observação. `inference_ms` e
  `load_ms` separam inferência e carga quando mensuráveis. `cold_start_ms`
  no ambiente registra a inicialização do lote. Identificar se a tentativa
  ocorreu com processo aquecido, frio ou desconhecido. No teste, aquecer antes
  do primeiro relato medido e incluir tempos de falhas e timeouts.
- Tokens e custo desconhecidos usam `null`. `observed_api_usd` guarda
  cobrança informada. `estimated_api_usd` exige tarifa com fonte, data e taxa
  (unidade e valor). Uma chamada local pode ter custo de API conhecido de zero.
  O custo de infraestrutura tem registro próprio. CPU/GPU ficam em `hardware`,
  memória de pico em bytes, runtime em `runtime`. O manifesto identifica a
  semente, ou a representa como indisponível com `null`.
- `sources` identifica versão, caminho e SHA-256 dos **bytes do arquivo** para
  dataset, catálogo, divisão, rubrica, protocolo, prompt e política.
  `artifacts` identifica os três fluxos JSONL por caminho e SHA-256. Todos os
  caminhos são relativos à raiz do checkout. O relatório é a raiz do inventário.
  Na fixture, a revisão Git identifica a base congelada e os dois textos com
  sufixo `fixture` documentam material ilustrativo.
- `planned_ids` guarda o plano ordenado de desenvolvimento ou teste.
  `completed_ids` é a subsequência com decisão registrada, inclusive erros.
  Teste final planeja exatamente os 36 IDs congelados. Os `control_ids` são
  sintéticos e disjuntos dos 60 IDs do dataset. Os fluxos contêm os casos
  concluídos nessa ordem e depois os controles na ordem declarada.
  Observações seguem a mesma ordem, omitindo casos com zero tentativas.
  Lote exclusivo de controles usa `split: "control"` e listas de dados vazias.

### Unidades e denominadores

Cada métrica inclui `state`, `numerator`, `denominator` e `value`.
`measured` descreve a amostra completa da métrica. `partial` contém valor sobre
as unidades efetivamente observadas e seu denominador. `unmeasured` indica
ausência de medição e `unavailable`, medição impedida. Nos dois últimos,
numerador e valor são nulos. O denominador pode ser conhecido (inclusive zero)
ou nulo. Quando uma fatia descritiva está vazia usar `unmeasured` com
denominador zero. Uma taxa medida requer denominador positivo.

| Grupo | Unidade e leitura |
| --- | --- |
| `gates` | Mesmas chaves e metas do protocolo. `applied_category_accuracy` e `applied_priority_accuracy` instanciam a meta por campo. Para taxas, valor é a divisão. Para limites de contagem zero, valor é o numerador e denominador é o tamanho da população controlada. |
| `by_field`, `by_mask`, `by_stratum` | Fatias por campo-alvo, máscara de omissão e estrato do gabarito. Cada taxa conserva seus próprios numerador e denominador. |
| `urgent_outcomes` | Denominador dos seis urgentes com prioridade omitida no teste. `applied_urgent`, `applied_lower` e `review` descrevem o caso. `abstained`, `invalid` e `operational_error` descrevem o campo prioridade e podem coincidir com revisão. |
| `latency_p50_ms` e gate p95 | Valor em ms, numerador nulo e denominador igual ao número de relatos aquecidos com tempo observado, inclusive falhas. Usar posto mais próximo do protocolo. |
| `usage` | Totais de tentativas, requisições, perguntas, tokens e custo observado/estimado com estado, valor, número de tentativas com medição e total de tentativas observadas no lote. Cobrança ausente conserva valor nulo. |

Nas fatias, `raw_accuracy` conta escolhas brutas que coincidem com o gabarito
sobre todos os campos-alvo da fatia, incluindo abstenção explícita ou por
política quando o gabarito pede insuficiência. `applied_accuracy` usa somente
campos-alvo aplicados. `correct_abstention`, `undue_abstention`,
`invalid_output`, `operational_error` e `unapplied_choices` usam todos os
campos-alvo da fatia. A última mede escolhas preditas válidas retidas pela
decisão de revisão. Campos fornecidos pelo canal ficam fora desses acertos.
`review` usa todos os relatos da fatia. As duas coberturas usam os relatos
inteiramente classificáveis da fatia. A automática conta conclusões completas
mesmo com erro de código. A correta exige também os códigos esperados.
Contar cada relato uma vez na respectiva fatia. Um relato com dois campos
omitidos pode pertencer a ambas as fatias por campo.

Os gates têm populações explícitas no [protocolo](../protocolo-comparacao.md).
Preservação usa os campos válidos recebidos. Chamadas proibidas usam os controles
completos/inválidos. Aplicação parcial usa como população os relatos examinados
para detectar aplicação indevida depois de falha ou abstenção. Os controles
devem provocar esses caminhos inclusive se o candidato sempre responder com
códigos válidos. Separar controles das métricas calculadas sobre o teste.
A escolha bruta urgente conta mesmo quando o relato segue para revisão.
O relatório preserva a separação entre taxa de reconhecimento e contagem de
rebaixamentos aplicados.

`eligibility` admite `pass`, `fail` ou `inconclusive`. Fixture, piloto, teste
incompleto, gate com denominador zero, ausência de medição necessária ou
indisponibilidade total produzem `inconclusive`. Uma vez completa a evidência
real do teste, qualquer violação dos gates produz `fail`. `pass` requer todos
os gates aprovados. A origem dos 60 rótulos e os limites da conclusão ficam
no [registro de revisão](../revisao-de-rotulos.md). A escolha de um candidato
cabe ao responsável depois da comparação.

## Verificação offline

Na raiz do checkout, com Python 3.9+ e `jsonschema` 4.18+ (com
`referencing`), execute o comando abaixo. O verificador usa os arquivos
versionados, valida os schemas e as referências locais, confere a estrutura
das quatro mensagens e cruza IDs, máscara, valores, aplicação, fontes e
consistência do manifesto. A agregação das linhas e o comando de avaliação
pertencem a C02.

```sh
rtk proxy python3 script/check_classification_contracts.py
```

Cada exemplo em [negative.json](fixtures/negative.json) é uma mutação declarativa
de uma cópia do lote positivo. O caminho usa nomes de propriedades e índices
de linha a partir de zero. O verificador exige a rejeição declarada, incluindo
a localização e a regra para erros de schema. Os exemplos positivos são
fabricados para exercitar os contratos. Os custos, tempos e resultados de
qualidade de modelos reais continuam sem medição.
