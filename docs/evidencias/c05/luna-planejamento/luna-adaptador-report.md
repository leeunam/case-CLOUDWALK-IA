# C05-R3 Task 3-A · Adaptador Luna

Implementação offline na branch `feat/luna-feita`, na worktree
`/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r3-luna-adaptador`.
Base `eaca1c6b64f407e628929023145d5cf1479973d2`.
Commit `dc74cd321f769db49123b018c9e5c8e1ca264c83`.

A candidata fixa `openai/gpt-5.6-luna` e reaproveita o prompt, a política e a
rubrica da C05-R2 pelos hashes originais. O novo manifesto inclui `rubric`
explicitamente, no mesmo formato `{path, version, sha256}` de `prompt` e
`policy`. O formulário histórico do Qwen permanece com os mesmos bytes.
`operational.json` é uma fonte separada, versionada e apta a vinculação por SHA.
O único ponto compartilhado é a construção do corpo no adaptador Qwen.

## Interface para Task 3-B

```python
from adapters.luna.adapter import LunaAdapter
from adapters.luna.transport import LunaTransport

gateway = LunaTransport(api_key)
try:
    adapter = LunaAdapter(identity, run_id, instructions, gateway, budget, timeout_ms=5000)
    observation = adapter.classify(item)
finally:
    gateway.close()
```

- `LunaAdapter(identity, run_id, instructions, transport, budget=None, timeout_ms=5000)`
  valida identidade fixa antes de construir a sessão. Use a identidade de
  `candidate.json` no real. Para fixture, substitua somente `mode` por
  `fixture` e `provider` por `simulador-c05-luna`. Mantenha os dois campos de
  modelo com `openai/gpt-5.6-luna`. O real exige `budget`.
- `instructions` é a junção `"\n\n"` dos textos UTF-8 de `prompt` e `rubric`
  nesta ordem, resolvidos pelo verificador de fontes do executor. `policy`
  documenta a semântica e continua fora do corpo.
- `classify(item)` devolve a observação IPC 1.1.0 do adaptador comum. O
  executor mantém bypass de entrada completa/inválida e decisão integral com
  `common.decide`. A observação de falha técnica chega ao executor para
  registro e encerramento, inclusive quando algum campo foi predito mas outro
  teve saída inválida. Depois disso o adaptador rejeita novos despachos.
  Abstenção explícita ou recusa documentada pode seguir para o gate.
- `transport(body: bytes, deadline: float, dispatched)` devolve
  `(status: int, data: bytes)`. `deadline` é absoluto de `time.monotonic()`.
  O transporte chama `dispatched()` antes de tentar o POST. `LunaTransport`
  recebe a credencial por argumento. O parâmetro opcional
  `connection_factory=HTTPSConnection` serve para injetar o duplo offline.
  A função de captura do executor pode envolver o `gateway`, recebendo os
  bytes integrais de respostas HTTP de erro para registrar custo conhecido.
- `close()` é idempotente no adaptador e no transporte. Use `finally` na
  entrada IPC, inclusive em EOF/interrupção. O adaptador delega a `close()`
  se o transporte injetado expuser esse método. Se `capture` for uma função
  sem `close()`, feche também o `gateway` de que ela depende. Após HTTP
  não-200 ou falha de rede/prazo, `LunaTransport` fica encerrado.
- O objeto `budget` segue a interface histórica `reserve(id, body_size)`,
  `observe(usage)`, `tariff`, `cost_unit`, `max_tokens`, `reasoning`. Para a
  implementação compartilhada use `max_tokens=128` e `reasoning=None`.
  O corpo HTTP da Luna usa exclusivamente `max_completion_tokens=128` e
  `reasoning_effort="none"` mesmo se esses atributos auxiliares variarem.
  Com orçamento, forneça uma tarifa válida para o modo. Para uso real,
  `RequestBudget.cost_unit=None` mantém a conciliação decimal de bytes brutos
  no executor. Fixture isolada sem orçamento publica tokens conhecidos sem
  estimativa ou tarifa. Conciliação, reserva e interrupção financeira
  pertencem à Task 3-B.
- A resolução de imports segue a inicialização já usada por `c05/settings.py`,
  com `script/classification_comparison` e `adapters/qwen` em `sys.path`.

## Transporte e teste de encerramento

`transport.py` abre um processo local na primeira chamada. Nesse processo,
uma sessão HTTPS abre a conexão dentro do prazo do caso, atualiza o timeout
do socket a cada POST e preserva a conexão após a resposta completa. Se o
servidor declarar o fim da conexão, a próxima chamada permitida pode abrir
uma nova. O pai impõe um prazo monotônico para o canal local, inclusive
enquanto o processo estiver bloqueado em DNS, TLS ou leitura. O processo
só tenta POST depois da confirmação de despacho do pai. EOF na entrada IPC
aciona `close()` no executor. O transporte encerra e recolhe o trabalhador,
com encerramento forçado se a saída normal não vier em tempo. Um canal
separado monitora a morte do pai mesmo durante leitura bloqueada.

Os testes usaram apenas envelopes artificiais, arquivos temporários,
credencial artificial e duplo de conexão HTTPS. O duplo registrou uma
conexão e dois POSTs para duas chamadas válidas, nenhum POST com handshake
bloqueado além do prazo, nenhum reenvio após socket obsoleto/EOF/erro HTTP e
encerramento do trabalhador após EOF do canal de vida do pai com leitura
bloqueada. A resposta HTTP de erro preservou bytes de uso/custo. A leitura
da segunda chamada foi interrompida pelo relógio global mesmo com socket
reutilizado. O teste de abertura no caso seguinte cobre servidor fechando
explicitamente depois de resposta válida. Não houve sondagens.

## SHA-256 para revisão e congelamento

Os caminhos abaixo são relativos à raiz.

| Arquivo | SHA-256 |
| --- | --- |
| `script/classification_comparison/adapters/luna/candidate.json` | `1daac4749be2e8ac07989780ce5b4aae58f3f7f2bbbf460fdfb904a98295caf5` |
| `script/classification_comparison/adapters/luna/operational.json` | `0666cdd1c99f58c52512681563b72ddcaf4f97593071a1797104526d062678da` |
| `script/classification_comparison/adapters/luna/adapter.py` | `e0ce592d9dfd36f1aae4043ff339a69de932d2b657b320f8c15994588110c810` |
| `script/classification_comparison/adapters/luna/transport.py` | `60673dff9db3f3dd8e16db409843ec6d073397053a66e664a5b65e2b98d03ea0` |
| `script/classification_comparison/adapters/qwen/adapter.py` | `fefe1b4458d667bf9701e59ce2071d368a92169848ba14e6ccd516ab7d74c90f` |
| `script/classification_comparison/adapters/qwen/transport.py` | `a93f322b347efe69096aa4fa1483ae003b2ef06a2e1e1077ed09cbcab4f030f2` |
| `script/classification_comparison/adapters/qwen/pilot.py` | `5605c8cfc06af9acea2319aad2c9284c46ab381e3262362fbeda99e5e866c79b` |
| `script/classification_comparison/adapters/qwen/fixture.py` | `7d0d2d3a86971481664652488afb4eb83bcd961be693b03dfdc1c1904b1a5dbf` |
| `script/classification_comparison/adapters/qwen/tarifas-publicas.json` | `4494fc5d7d0f970521560697ae3facc16773fed8c38d7ef28df9b78686bf27cf` |
| `script/classification_comparison/adapters/qwen/r2/prompt.txt` | `c03848e1f9266ae2aadb5d28d8f82265034c0312067a5e3204aea723437cfa75` |
| `script/classification_comparison/adapters/qwen/r2/politica.txt` | `6893a119e6dc90aef81e10cc803dba8d66e3cf4c04cc4f3f2d333515c4b2a039` |
| `docs/planejamento/classificacao-comparativa/rubrica-comum.md` | `ac497f8d36af1aceb4eac39648ca7fe2c1e291d16cf512f27894b40e113ed4ac` |
| `script/classification_comparison/adapters/luna/test_adapter.py` | `5e3ac4deee3c437746198fbc15d91f3c6f3ecdbfb6da2765df9c7103f556a148` |
| `script/classification_comparison/adapters/luna/test_transport.py` | `1dc30bf2598014f89b741366d408b2660ee6c1ea63e1f585695a1f3ed003a866` |

O congelamento depende de revisão independente e do registro integrado
pelo responsável. As fontes R2 e os artefatos históricos de dados ficaram
intactos.

## Verificação executada

```sh
rtk proxy env PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen \
  python3 -B -m unittest -v adapters.luna.test_adapter adapters.luna.test_transport
rtk proxy git diff --cached --check
rtk proxy git diff HEAD^ HEAD --check
rtk proxy git status --short --branch
```

- 19 testes passaram em 4,905 s. O teste de rejeição do ACK passou a aceitar
  encerramento normal ou forçado do processo, pois ambos impedem POST. A
  versão anterior do teste falhou em uma execução por assumir que só o
  encerramento forçado seria observado no log.
- A projeção Qwen padrão foi conferida byte a byte em envelope artificial
  com `reasoning` histórico. Os casos sintéticos verificaram dois campos em
  uma chamada, schema de ausentes, preservação do fornecido, revisão
  integral, recusa, abstenção e procedência ausente/divergente.
- `sha256sum` conferiu manifesto, operação, arquivos de runtime da fatia e
  fontes originais. O commit inclui sete arquivos selecionados e o diff
  passou no `--check`. Worktree limpa depois do commit.
- A frente não abriu casos/gabaritos finais, seus outputs nem executou
  preflight, planos ou regressões que os carreguem. Não houve rede, API,
  leitura de `.env`, chave ou conta real. Isolamento e ausência de retentativa
  foram verificados offline. Compatibilidade, identificação e custo reais
  pela Feita continuam pendentes, assim como a avaliação da latência real
  e o aceite com o executor integrado.

## Fontes públicas registradas

`docs/planejamento/classificacao-comparativa/rodada-3-proposta.md` registra a
consulta pública do modelo na Feita e da documentação OpenAI. Os parâmetros
escolhidos seguem o formato Chat Completions e as capacidades documentadas
da Luna. A fase offline apenas utilizou as evidências locais e registrou as
referências no manifesto operacional.
[Catálogo Feita](https://feita.ai/models/openai/gpt-5.6-luna),
[Modelo OpenAI](https://developers.openai.com/api/docs/models/gpt-5.6-luna),
[Chat Completions](https://platform.openai.com/docs/api-reference/chat/create).

## Exercício

Execute `adapters.luna.test_adapter.LunaAdapterTests.test_dois_campos_em_uma_chamada_estrita`
com o mesmo prefixo da suíte acima. Localize `gateway.bodies[0]` e compare as
duas chaves de `required` com `requests == 1`. Em seguida, veja como o teste
de abstenção conserva os dois campos sem aplicação apesar de a categoria ter
sido prevista.

## Correção da primeira revisão

O commit `cda8fc83d82cfc9c8cf4b746732fb11088edf751` corrige os dois despachos
reproduzidos pela revisão em `dc74cd321f769db49123b018c9e5c8e1ca264c83`.
A branch é `feat/luna-feita` e a worktree é `.worktrees/r3-luna-adaptador`.

- A Luna valida a configuração de orçamento antes de cada classificação.
  O modo real exige orçamento. Em ambos os modos, um objeto fornecido deve
  ser verdadeiro, oferecer `reserve` e `observe` chamáveis e expor os
  atributos `max_tokens`, `reasoning`, `cost_unit` e `tariff`. O limite
  solicitado do orçamento deve ser o inteiro `128` e a unidade é `USD` ou
  `None`. `reasoning` continua como atributo da interface compartilhada.
  O corpo HTTP da Luna fixa `reasoning_effort="none"`.
- A função compartilhada `rates` confere unidade da tarifa, fonte não
  vazia, data e valores finitos não negativos para entrada, saída e cache.
  Uma tarifa inválida bloqueia antes de `reserve` e do gateway. A validação
  da fonte real correspondente à rota Luna cabe ao executor da Task 3-B.
- `budget=None` continua válido em fixture isolada, com tarifa e estimativa
  ausentes da observação publicada. O caso válido reservou antes do único
  despacho e registrou o uso de uma única resposta.
- A Task 3-B deve manter o timeout canônico externo e encerrar o adaptador
  em `finally`, inclusive em EOF. Uma função `capture` sem `close()` exige
  fechar também seu gateway. A inicialização local e os callbacks
  síncronos fazem parte da medição total. Internamente o prazo volta a ser
  conferido antes do POST, e operações síncronas locais bloqueadas dependem
  do timeout externo do executor para serem interrompidas.

### Verificações da correção

```sh
rtk proxy env PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen \
  python3 -B -m unittest \
  adapters.luna.test_adapter.LunaAdapterTests.test_orcamento_falso_ou_sem_interface_bloqueia_gateway \
  adapters.luna.test_adapter.LunaAdapterTests.test_tarifa_ausente_ou_invalida_bloqueia_gateway
rtk proxy env PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen \
  python3 -B -m unittest -v adapters.luna.test_adapter adapters.luna.test_transport
rtk proxy git diff --check
rtk proxy git diff --cached --check
rtk proxy git diff HEAD^ HEAD --check
rtk proxy git status --short --branch
```

Os dois testes dirigidos reproduziram a falha antes da correção. Depois,
23 testes sintéticos passaram em 10,176 s, incluindo os dois dirigidos, o
caso válido e a revalidação de tarifa em sessão reutilizada. O gateway
recebeu zero chamadas com `False`, objeto falso, atributos ausentes,
operações inválidas ou tarifa ausente/malformada. A verificação do diff
passou e a worktree ficou limpa. Nenhum dado final ou serviço real foi
acessado. A nova revisão independente e o congelamento seguem pendentes.

### SHA-256 atual

| Arquivo | SHA-256 |
| --- | --- |
| `script/classification_comparison/adapters/luna/candidate.json` | `1daac4749be2e8ac07989780ce5b4aae58f3f7f2bbbf460fdfb904a98295caf5` |
| `script/classification_comparison/adapters/luna/operational.json` | `0666cdd1c99f58c52512681563b72ddcaf4f97593071a1797104526d062678da` |
| `script/classification_comparison/adapters/luna/adapter.py` | `cf221d6d1f39f27bbc3d4388d6c14091fe869e0351ca8564c713284eca4b3845` |
| `script/classification_comparison/adapters/luna/transport.py` | `60673dff9db3f3dd8e16db409843ec6d073397053a66e664a5b65e2b98d03ea0` |
| `script/classification_comparison/adapters/luna/test_adapter.py` | `2716ed5e42271f2e26ed41974c067bb7abf6575ff7dae13a9f81d9f623df038a` |
| `script/classification_comparison/adapters/luna/test_transport.py` | `1dc30bf2598014f89b741366d408b2660ee6c1ea63e1f585695a1f3ed003a866` |
| `script/classification_comparison/adapters/qwen/adapter.py` | `fefe1b4458d667bf9701e59ce2071d368a92169848ba14e6ccd516ab7d74c90f` |
