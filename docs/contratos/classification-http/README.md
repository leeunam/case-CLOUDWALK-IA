# C06-A · contrato privado Rails ↔ SetFit R1

Contrato normativo de C06 para o complemento local. A fase A publica `v1.json`, `pins.json` e `fixtures/` neste diretório antes da implementação dos dois lados. O Rails e o serviço privado leem a mesma revisão em `CLASSIFICATION_CONTRACT_DIR` (padrão na raiz do projeto: `docs/contratos/classification-http`). C06-C fornece a montagem no ambiente local. [Adoção](../../planejamento/classificacao-comparativa/sf2/decisao-adocao-r1.md) · [Plano de integração](../../planejamento/classificacao-comparativa/c06-setfit-integracao.md)

## Regras herdadas

- O Rails só chama o serviço para complementar uma entrada válida com um ou dois campos ausentes. Chave omitida, `null` e `""` são ausência na entrada do canal. Espaços, tipo incorreto e código fora do catálogo ativo são inválidos. Entrada completa segue o fluxo direto e entrada inválida vai à revisão, ambas com zero chamadas HTTP e zero inferências.
- Para o complemento, usar o snapshot inteiro do catálogo ativo projetado por `Classification::Catalog`, com os dois mapas. A compatibilidade SF2 exige que cada par código–descrição corresponda exatamente ao [catálogo canônico](../../../script/f08/jev/catalog.json). Subconjuntos canônicos são representáveis. O Rails envia as prioridades operacionais do snapshot. Código extra ou descrição divergente leva a `unsupported_catalog` antes da inferência. Entrada já completa é validada no catálogo operacional.
- O serviço privado tem um único worker JSONL residente e admite uma tentativa por vez. O Rails conserva os valores do canal e decide revisão, autorização, estado, fila e publicação. A aplicação é atômica e depende de tentativa vigente, lease, estado, versão da classificação, snapshot de catálogo e valores do canal ainda válidos na liquidação. Os scores são saídas brutas das cabeças, sem calibração como probabilidade de acerto.

## Envelope HTTP

`POST /internal/classification/v1/complete`, `application/json` UTF-8. `contract_version` é a string literal `classification-http/1.0` em pedidos e respostas. Todos os objetos têm chaves fechadas e obrigatórias conforme as listas abaixo. As exceções são os mapas de códigos de `catalog` e as chaves opcionais de `applied`. Recusar chaves repetidas, JSON inválido e números não finitos.

| Chave do pedido | Tipo e regra |
| --- | --- |
| `contract_version` | String `classification-http/1.0`. |
| `id` | String UUID em formato canônico minúsculo, com hífens. É o ID de `Classification::Attempt`. |
| `text` | String não vazia com conteúdo além de espaços. Mensagem inicial íntegra, sem `strip`, normalização ou truncamento. |
| `received` | Objeto com `category` e `priority`. Cada valor é `null` para ausência ou uma string que consta no mapa correspondente. Pelo menos um `null`. |
| `catalog` | Objeto com mapas `category` e `priority`. Chaves de código seguem `^[a-z][a-z0-9_]*$` com correspondência integral e valores são strings não vazias com conteúdo além de espaços. Compatibilidade canônica é uma validação adicional. |
| `catalog_version` | Inteiro JSON literal de `1` a `2147483647`, da versão da marca no claim. |

O sidecar repete as validações de admissão antes de escrever no pipe. Projeta `id`, `text` e `received` para `sf2-ipc/1.0`, inclui `catalog.version` literal `1.0.0` junto dos mesmos mapas e deriva `missing_fields` na ordem `category`, `priority`. Só o texto chega às cabeças solicitadas. A versão operacional da marca fica no HTTP. [Protocolo SF2](../../../docs/planejamento/classificacao-comparativa/sf2/protocolo.json) · [Projeção IPC](../../../script/classification_comparison/setfit_sf2/contracts/ipc.py)

| Chave da resposta `200` | Tipo e regra |
| --- | --- |
| `contract_version`, `id`, `catalog_version` | Mesmos tipos e valores do pedido. |
| `catalog_sha256` | String hexadecimal minúscula de 64 caracteres, SHA-256 do catálogo HTTP segundo a serialização abaixo. |
| `outcome` | String `complete`, `review` ou `error` produzida pelo runtime R1. |
| `applied` | Objeto com zero, uma ou duas chaves entre `category` e `priority`. Valores são códigos do snapshot. |
| `fields` | Objeto fechado com `category` e `priority`. Cada valor contém `vector`, `raw`, `margin`, `cut`, `decision`, `reason` conforme o schema R1. |
| `calls` | Objeto fechado com `category` e `priority`, cada valor inteiro JSON literal `0` ou `1`. |
| `package_sha256`, `capture_policy_sha256`, `decision_policy_sha256`, `raw_frame_sha256` | Strings hexadecimais minúsculas de exatamente 64 caracteres. |
| `model_sha256` | Objeto fechado com `category` e `priority`, um SHA-256 por especialista. |
| `elapsed_ms` | Número finito de `0` a `5000`, duração monotônica no sidecar desde antes da projeção até depois da verificação R1. |

O sidecar verifica contexto, frame e decisão com `runtime_r1.load_context`, `derive` e `verify` antes do `200`. Os nomes HTTP `decision_policy_sha256` e `raw_frame_sha256` projetam respectivamente `selected_policy_sha256` e `raw_sha256` da decisão R1. `raw_frame_sha256` cobre os bytes recebidos de uma linha JSONL UTF-8, inclusive o `LF` terminal, sem recodificação. `elapsed_ms` do HTTP mede o trecho verificado inteiro. O campo homônimo no frame mede apenas o processamento no worker. `received` fica no snapshot Rails e na decisão interna R1. [Runtime R1](../../../script/classification_comparison/setfit_sf2/runtime_r1/decision.py) · [Schema de decisão](../../../docs/planejamento/classificacao-comparativa/sf2/sf2-final-r1.schema.json)

| Status | Corpo fechado de erro e efeito no Rails |
| --- | --- |
| `422` | `{contract_version, error}` com `error` igual a `invalid_request`, `unsupported_catalog` ou `text_out_of_scope`. O último código exige comprimento acima de 128 tokens comprovado antes da admissão, segundo a regra abaixo. Revisão sem repetição. |
| `503` | `{contract_version, error}` com `error` igual a `not_ready` ou `busy`. Apenas antes da admissão. Permite repetição no teto vigente de duas tentativas quando o Rails recebe e valida essa recusa. |
| `502` | `{contract_version, error}` com `error` igual a `invalid_worker_frame` ou `worker_failure`. Falha após admissão. Revisão sem repetição. |
| `504` | `{contract_version, error}` com `error` igual a `processing_timeout`. Prazo monotônico de 5.000 ms excedido após admissão. Revisão sem repetição. |

Prazo absoluto do cliente Rails de 6.000 ms, abaixo do lease vigente de 30 s. Prazo vencido, interrupção de transporte e resposta inesperada seguem para revisão quando o Rails carece de prova de recusa. O limite operacional é de 65.536 bytes de corpo HTTP de entrada (medidos nos bytes UTF-8 antes do parse) e 65.536 bytes por frame JSONL do worker, incluindo o LF. Excesso no pedido produz `422 invalid_request` sem admissão; no frame produz `502 invalid_worker_frame`. Esses dois limites pertencem ao serviço HTTP. O transporte original lê blocos de 65.536 bytes sem limitar o tamanho total da linha por esse número. O IPC qualificado limita o texto a 128 tokens pelos tokenizadores solicitados. O prazo de processamento inclui projeção, leitura, derivação e validação do retorno. Se a validação terminar fora do prazo, aplicar `504`, mesmo que a linha já tenha chegado. [Limites SF2](../../../docs/planejamento/classificacao-comparativa/sf2/protocolo.json) · [Transporte de qualificação](../../../script/classification_comparison/setfit_sf2/evaluation/runner.py)

**Texto fora da janela.** Antes de admitir a inferência, C06-C usa somente os tokenizadores das cabeças solicitadas, com bytes e configuração conferidos contra o inventário do pacote aprovado. Reproduzir a tokenização do adaptador com tokens especiais, sem truncamento, preservando o texto e medindo o maior comprimento. Se exceder 128 tokens, devolver `422 text_out_of_scope`, com zero escritas no pipe, chamadas às cabeças ou reinícios. Isso não exige carregar encoders extra. O Rails encaminha à revisão sem aplicação nem repetição. Exatamente 128 tokens seguem o caminho normal. Só emitir essa recusa se a mesma tokenização congelada comprovar o excesso.

Se faltar essa comprovação prévia e chegar ao supervisor um frame `review/too_long` com zero chamadas, `runtime_r1.decision._observed` o recusa porque a validação IPC exige `interruption="too_long"`. Nesse caso, responder `502 invalid_worker_frame` e seguir a recuperação de sessão prevista. Preservar a validação R1 para todo `200`. [Adaptador](../../../script/classification_comparison/setfit_sf2/adapter/decide.py) · [Validador IPC](../../../script/classification_comparison/setfit_sf2/contracts/ipc.py) · [Runtime R1](../../../script/classification_comparison/setfit_sf2/runtime_r1/decision.py)

## Operação e configuração

`CLASSIFICATION_PROVIDER=jev|setfit` seleciona um provedor. O padrão é `jev`, respeitando seus modos históricos. No modo real local o Rails usa `SETFIT_URL=http://setfit:8080`. Apenas o worker Rails e o serviço compartilham a rede privada de inferência. O serviço inicia um único subprocesso residente, sem porta publicada no host, fila interna ou pesos baixados ao receber pedidos. O job SetFit usa a fila Solid Queue `classification_setfit` com um slot dedicado. Concorrência além de um pedido admitido recebe `503 busy` imediatamente. Até validar as identidades e o `READY`, usar `503 not_ready`; limite de partida de 60.000 ms. Liveness indica que o supervisor vive; readiness exige pacote e ciclo de worker íntegros. EOF, erro de frame ou prazo vencido invalidam a sessão. Descartar seus bytes, encerrar e colher o filho antes do reinício limitado.

Os pesos, manifestos e políticas são provisionados somente para leitura. Os pins vêm da decisão versionada e das fontes qualificadas. Validar inventário e digest antes de desserializar os pesos. A versão HTTP é independente das versões de REST, Kafka, IPC e decisão. A correlação de tentativa e o hash de catálogo vinculam o pedido a um snapshot de marca; o serviço não decide fila, acesso, estado ou envio ao broker.

## Hash e identidades

`catalog_sha256` é SHA-256 do objeto `catalog` inteiro em JSON compacto UTF-8, com chaves de cada objeto em ordem ASCII crescente, separadores `,` e `:`, sem espaço estrutural, BOM ou LF final. Preservar descrições literalmente, sem normalização Unicode. Só escapar aspas, barras invertidas e controles U+0000–U+001F conforme JSON, com hex minúsculo quando aplicável. A versão operacional `catalog_version` é comparada separadamente. A versão semântica IPC e o hash do arquivo canônico também são identidades próprias.

- Ruby stdlib com `JSON.generate(catalog.sort.to_h.transform_values { |items| items.sort.to_h }).encode(Encoding::UTF_8)` e `Digest::SHA256.hexdigest(bytes)`.
- Python stdlib com `json.dumps(catalog, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")` e `hashlib.sha256(data).hexdigest()`.

Vetor em ordem canônica abaixo, obtido do catálogo público retirando `version` e `category.terminal`. Alimentar ambos os serializadores com ordem invertida de mapas e códigos. Resultado de 449 bytes, SHA-256 `0cadca6fc5e2291b3e471df649d098123bf01cb8b422803c45b6cb9f22d63807`.

```json
{"category":{"payouts":"Repasse, recebimento ou liquidação de valores de vendas.","pix":"Transferência ou pagamento por Pix, prazo, estorno ou falha."},"priority":{"advanced":"Impacto relevante sem necessidade de ação imediata.","basic":"Orientação de rotina, sem operação prejudicada.","intermediate":"Impacto moderado com operação ainda disponível.","urgent":"Necessidade de ação imediata, como operação totalmente interrompida."}}
```

| Identidade aprovada | SHA-256 |
| --- | --- |
| Recibo público revisado de preparação | `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a` |
| Manifesto do pacote `package_sha256` | `224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872` |
| `model_sha256.category` | `b989492b3623dc6015e97c5d8af975950a48ce72f489d467062e07fe6996a6c5` |
| `model_sha256.priority` | `8a0224ad38fa45a902a58bc25c8dbcc4c9e9aff96ec50024dfe4a01c304bcab1` |
| `capture_policy_sha256` | `09de8c13fa56bcddb8006982b0016e3452bb15de89a72a6eae6c42847cedc21f` |
| `decision_policy_sha256` | `127eb227ac174384700a60390272a48abdca9a81592086dde5bc132727338473` |

A coleta carrega `sf2-ipc/1.0`, τ `0.5` para as duas cabeças e δ `0.0`. A decisão R1 usa política `sf2-r1-offline/1.0`, τ `0.95` em categoria, `0.70` em prioridade e δ `0.0`. O namespace da decisão derivada é `sf2-final-r1/1.0`. As identidades de execução vêm da configuração aprovada, verificadas antes de `READY` e comparadas no Rails. O recibo referencia o preparo público. [Recibo](../../../docs/evidencias/c05/sf2/final-r1-preparacao-02/final-fix-publico/release.json) · [Freeze](../../../docs/evidencias/c05/sf2/final-r1-preparacao-02/final-fix-publico/freeze.json) · [Protocolo R1](../../../docs/planejamento/classificacao-comparativa/sf2/sf2-final-r1-protocolo.json)

## Validação de retorno e consumidores

- No Rails, validar o envelope inteiro contra a tentativa e o snapshot. Para campo recebido, exigir `calls=0`, `decision=reason=provided` e `vector`, `raw`, `margin` e `cut` nulos. Para cada ausente enviado ao worker, exigir `calls=1`, o corte R1 da cabeça e uma observação válida ou erro de cabeça permitido. `vector` é nulo quando `decision=error`, junto de `raw` e `margin`, com `reason` em `error`, `timeout`, `invalid_score`. Nos outros retornos dos ausentes exigir `accept/accepted` ou `review` com `raw_review`, `inactive_label`, `below_tau` ou `low_margin`. O schema R1 contém também motivos de controles IPC, fora da admissão HTTP deste contrato.
- `vector` tem apenas os arrays `classes` e `scores`. Ordem fixa de categoria `[informacao_insuficiente, payouts, pix, terminal]` e de prioridade `[advanced, basic, informacao_insuficiente, intermediate, urgent]`. Exigir um score numérico finito em `[0,1]` por classe, soma a `1` com tolerância absoluta `1e-6`, `raw` string igual ao argmax estável e `margin` número finito em `[0,1]` igual à diferença entre os dois maiores scores com tolerância absoluta `1e-15`. A margem publicada é a observada. O objeto `cut` tem as duas chaves numéricas `tau` e `delta` com os valores R1 da cabeça. Conferir a decisão contra os mesmos valores em ordem: rótulo `informacao_insuficiente` gera `raw_review`, rótulo inativo gera `inactive_label`, score do vencedor abaixo de τ gera `below_tau`, margem menor ou igual a δ gera `low_margin`; nos demais casos, `accept/accepted`. Calcular com a semântica decimal do IPC e desempate pelo primeiro índice. O runtime R1 verifica os cortes e a decisão.
- `complete` requer o conjunto exato de ausentes em `applied`, aceites correspondentes e códigos iguais aos `raw` presentes no catálogo. `error` exige um erro de cabeça. `review` exige ao menos uma abstenção/recusa e nenhum erro de cabeça. Ambos exigem `applied={}`. Resposta inválida vai à revisão sem aplicação. Guardar na evidência interna por tentativa as identidades, hashes, duração e metadados validados; referenciar a tentativa na auditoria. Logs, respostas e trilhas de auditoria usam códigos controlados sem reproduzir texto, frame, payload inválido ou detalhes de exceções. `raw` é um rótulo bruto da cabeça.
- Em REST staff, `setfit` integra as origens por campo em OpenAPI `info.version: 1.1.0`, sob as rotas `/api/v1`. Preservar a leitura de `channel`, `jev`, `supervisor` e a nulidade por campo prevista no schema.
- Em Kafka, ponte e mock aceitam `AgentTurnRequested` com `schema_version` `1.0` ou `1.1`. O enum de `1.0` rejeita `setfit`; o de `1.1` o inclui. `QueueTurn` emite `1.1` quando qualquer origem do caso é `setfit`, inclusive em rodadas seguintes, e `1.0` nos demais casos. Reentrega usa o corpo persistido e o mesmo ID. O mock sobrescreve `schema_version` para `1.0` após `**request`, conserva `payload.request_event_id` e o ID derivado do resultado. `AgentReceipt` conserva a forma do contrato `1.0`, em que inexiste a chave `schema_version`. Manter chave por caso, assinatura HMAC, offsets e regras de recibo. Disponibilizar ambos os consumidores antes da emissão `1.1` e conservá-los durante uma reversão enquanto houver casos ou mensagens aptos a gerar ou carregar essa versão. [Schema atual](../../../docs/contratos/schemas/v1.json) · [Ponte e mock](../../../integration/agent_flow.py) · [Emissão Rails](../../../backend/app/services/agent_integration/queue_turn.rb)

## Três testes de contrato mínimos

1. **Hash Ruby/Python.** Verificar igualdade dos bytes e do digest do vetor acima com ordem invertida, e mudança do digest ao mudar um caractere de uma descrição. Variar `catalog_version` e confirmar que a versão diverge enquanto o hash do catálogo se mantém.
2. **HTTP com worker falso.** `received={"category":"pix","priority":null}`, versão `7` e catálogo do vetor. Emitir frame sintético válido com `calls={"category":0,"priority":1}`, vetor de prioridade `[0.01,0.05,0.01,0.03,0.9]` na ordem congelada, `raw=urgent` e margem `0.85`. Esperar `200` com `applied={"priority":"urgent"}`, identidades exatas e SHA-256 do frame incluindo `LF`. Mutações de ID, versão, hash, chamada no campo fornecido ou complemento parcial devem falhar. Incluir controles de entrada completa, inválida e catálogo incompatível com zero chamadas, além de 128 tokens admitidos, 129 tokens comprovados com `422 text_out_of_scope` sem escrita/inferência/reinício, e frame `too_long` sem prova prévia recusado pelo R1 com `502 invalid_worker_frame` sem aplicação.
3. **Kafka.** Enviar fixtures request `1.0` histórica e `1.1` de origem mista pela ponte e mock. Confirmar rejeição de `setfit` sob `1.0`, retorno explícito `1.0` referenciando cada request e os mesmos bytes/IDs em reentrega. Repetir `QueueTurn` em rodada posterior do caso misto e conferir `1.1`.
