# Contratos da pesquisa SF2

O [JSON Schema Draft 2020-12](sf2.schema.json) reúne os contratos no namespace `sf2-ipc/1.0`. Cada tipo está em `#/$defs/<tipo>`. O validador Python verifica também relações entre documentos, contagens e SHA-256 dos arquivos. Usa Python 3.11 com a dependência `jsonschema` já prevista em [requirements.txt](../../../../../script/classification_comparison/requirements.txt).

| Tipo principal | Uso |
| --- | --- |
| `record`, `annotationRecord` | Um relato por linha e um grupo de anotações por ID em JSONL UTF-8 |
| `publicManifest`, `finalSeal` | Inventário dos dados públicos e selo reservado. O selo público contém somente hashes, contagens, nomes fixos e versão |
| `tokenLengths`, `reviewReceipt` | Evidências conferidas pelo custodiante antes de emitir um aceite |
| `input`, `decision` | Entrada projetada e resultado do adaptador |
| `scorePackage`, `policy` | Scores com ordem original das classes, inventário de erros por alvo, cortes da grade aprovada |
| `trainingFreeze`, `modelManifest`, `freeze` | Congelamento pré-treino, pacote do modelo e congelamento anterior à abertura do final |
| `report` | Qualidade, denominadores, recursos e latência por partição |

## Dados e anotação

O [exemplo de relato](fixtures/record.json) e as anotações [inicial](fixtures/annotation-draft.json) e [conciliada](fixtures/annotation-accepted.json) usam texto exclusivamente de controle. Cada relato tem `author` e `gold` dos dois campos. No treino a linha termina nesses metadados e no texto, identidade, família e partição. Na validação e no final, `received` contém somente os campos do canal, e `missing_fields` precisa corresponder aos campos omitidos, nulos ou em branco.

Cada anotador fornece os dois rótulos, motivo e trechos literais por campo. Uma insuficiência pode ter lista vazia de trechos quando a justificativa descreve qual informação falta. A origem declarada é `ai` ou `human`. O hash da anotação é SHA-256 dos bytes UTF-8 do texto exato, sem quebra de linha adicional. O leitor verifica o vínculo, IDs, trechos e referências à rubrica e ao catálogo congelados.

- Em `draft`, há exatamente uma anotação do autor, gold igual à sua leitura e conciliação nula. O validador verifica as quotas completas do lote e retorna `accepted: false` com as pendências.
- Em `accepted`, são obrigatórias duas identidades distintas, uma conciliação que justifique o gold e os recibos de revisão e tokenização. O responsável pela coleta cega assegura a independência das leituras. A verificação de IDs distintos por si só não demonstra cegamento.
- `reviewReceipt.files` reproduz os hashes de dados e anotações, indexados pelos papéis do manifesto. O recibo registra revisor, limitações, revisão semântica concluída e zero desacordos pendentes.
- `tokenLengths.files` vincula as partições tokenizadas pelos hashes dos JSONL. `revision` identifica o snapshot aprovado e `lengths` mapeia cada ID ao número inteiro de tokens incluindo os especiais. O produtor usa o tokenizer do snapshot, sem truncar. O contrato confere cobertura, revisão e limite de 128. Não realiza a tokenização.
- O validador compara famílias, IDs e textos normalizados entre as partições fornecidas. O custodiante usa `validate_isolation` com as partições autorizadas e `novelty_candidates` com registros de outras partições e históricos para obter os três vizinhos lexicais, todos os pares com Jaccard ≥ 0,80 e o sinal de texto curto. Ele revisa semanticamente esses casos e guarda a trilha detalhada na área correspondente antes de atestar o recibo.

O manifesto usa objetos `{path, sha256}` em `files`. Os basenames públicos são `train.jsonl`, `validation.jsonl` e `annotations-public.jsonl`. No final são `final.jsonl` e `annotations-final.jsonl`. Os argumentos da CLI vinculam cada papel a um caminho explícito. O autor do modelo só precisa do selo público emitido pelo custodiante para conferir o congelamento.

## Entrada e decisão

`project(record, catalog)` copia ID, texto, campos recebidos e catálogo ativo, calcula a máscara e remove os metadados de anotação. O catálogo segue a estrutura de `script/f08/jev/catalog.json` e pode restringir os códigos ativos. O adaptador passa **somente o texto** ao especialista do campo ausente. `calls` contabiliza as invocações por campo. `received` é o objeto original, inclusive com omissões, tipos inválidos, nulos ou espaços. `applied` contém exclusivamente os complementos aplicados. Um caso completo do canal tem zero chamadas e `applied: {}`.

`validate_decision(input, decision, policy, class_order, identities)` audita o resultado recebido, incluindo a ordem do vetor, soma, argmax, margem, cortes, decisão, hash e atomicidade. Em empate prevalece o primeiro índice para a escolha bruta e ocorre revisão. O erro/timeout de um alvo invalida o complemento do caso inteiro. Apenas uma falha observada pelo supervisor permite usar `interruption="error"|"timeout"` para registrar o alvo interrompido antes de chamar seu especialista. O sinal `interruption="too_long"` vem do tokenizador e exige revisão sem chamadas. O parâmetro `identities` vem do pacote e da política conferidos pelo executor. Os valores ilustrativos das fixtures exercitam apenas a interface.

`validate_scores` exige uma linha por ID recebido, exatamente um vetor ou um erro por alvo e classes idênticas à ordem congelada no manifesto. `class_order` corresponde a `classes_` de cada cabeça. Os scores são não calibrados. Uma falha de inferência tem motivo em `errors` e zero scores fabricados.

## Artefatos, congelamento e relatório

Todos os SHA-256 identificam os **bytes gravados**. O código confere os bytes indicados pelo chamador antes de aceitar um manifesto. As chaves de `files` nos congelamentos são papéis lógicos.

1. `trainingFreeze` repete o aceite dos dados públicos a partir dos relatos, anotações conciliadas e dos caminhos explícitos `--file review_receipt=...` e `--file token_lengths=...`. Vincula fontes aprovadas, contrato, código do treino e selo público do final. O arquivo `arguments` reproduz a seção `training` do protocolo. O validador confere os parâmetros da receita e os bytes congelados. As frentes 03/05 registrarão os argumentos efetivamente usados durante a execução.
2. `modelManifest` registra versões, classes e inventário dos arquivos. Para cada especialista, o arquivo do papel `<campo>.manifest` é um objeto JSON com os hashes `base_encoder`, `encoder`, `head`, `tokenizer` e `training_evidence`. Esses mesmos cinco papéis têm prefixo do campo no inventário de arquivos. O hash do descritor individual é `model_sha256[campo]`. O hash do manifesto geral é `package_sha256`. Cada um dos cinco hashes identifica um índice JSON `componentIndex`, inclusive para um arquivo único. Em cada índice, `files` associa o nome relativo do membro ao SHA-256 dos seus bytes. O inventário geral e os caminhos explícitos usam o papel `<campo>.<componente>/<nome>`, por exemplo `category.tokenizer/tokenizer.json`. A verificação compara o inventário com o índice e lê os bytes individuais antes da desserialização local.
3. `freeze` vincula política, relatório elegível, scores, previsões da validação, pesos, dados, comandos e versões. O papel `validation_predictions` exige o arquivo de decisões seladas da validação. O congelamento verifica os bytes no caminho explícito e compara o digest ao `predictions_sha256` do relatório. O JSONL precisa conter uma `decision` por ID da validação. O hash do final vem do selo público. O comando de verificação de `freeze` dispensa e rejeita um caminho de dados finais. O executor confere o pacote reservado ao abri-lo após o congelamento.
4. Em `report.metrics`, `confusion` é a matriz da **escolha bruta**, por classe gold nas linhas, por escolha/erro nas colunas. `by_class` usa essa matriz. As métricas aplicadas contam apenas complementos. Em um relatório conclusivo, a preservação usa todos os campos fornecidos pelo canal, 60 na validação ou 80 no final. `wilson95` é um par de limites, ou nulo para denominador zero. `latency_ms` conta durações observadas. Um relatório conclusivo exige os totais prescritos e hash das previsões seladas. A validação de contrato confere denominadores, gates, matriz e consistência do resumo. A avaliação SF2-04 calcula as métricas a partir das decisões, verifica a cronologia e escolhe a política entre as 225 possibilidades.

## Reprodução

Execute da raiz da worktree. O comando `schema` verifica apenas a forma de um documento. Os comandos `record`, `ipc`, `manifest` e `report` e as funções acima verificam as relações pertinentes.

```sh
rtk proxy python3 -B -m unittest discover -s script/classification_comparison/setfit_sf2/contracts -t . -v
sf2=script.classification_comparison.setfit_sf2.contracts
fx=docs/planejamento/classificacao-comparativa/sf2/contratos/fixtures
rtk proxy python3 -B -m "$sf2" ipc "$fx/complete-channel.json"
rtk proxy python3 -B -m "$sf2" ipc "$fx/invalid-partial.json"
```

Exemplo de aceite público, com os caminhos reais definidos pelo operador:

```sh
rtk proxy python3 -B -m "$sf2" manifest publicManifest "$dados/manifest-public.json" \
  --file "train=$dados/train.jsonl" --file "validation=$dados/validation.jsonl" \
  --file "annotations=$dados/annotations-public.jsonl" \
  --file "review_receipt=$recibo" --file "token_lengths=$comprimentos"
```

O estágio inicial pode omitir os dois últimos argumentos quando os hashes correspondentes forem nulos. Para verificar apenas uma anotação de trabalho antes de completar as quotas, use `validate_annotation(record, entry, stage)`.

**Exercício.** Execute `record` com `fixtures/record.json` e depois com `fixtures/invalid-mask.json`. A segunda fixture muda somente `missing_fields`: declara prioridade ausente mesmo tendo recebido prioridade válida. O validador retorna código 1 com a mensagem `missing_fields diverge do canal`.
