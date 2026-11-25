# SF2-03 · Entrega de implementação

**Status** DONE. Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento`, branch `feat/sf2-treinamento`.

- Base `1f55d316f29afe7a749317ce136ebde28c2991be`.
- Entrega `d5819f7d47d16ed5394a224fa25fdeecf13e56d1` · `feat: implementar treino local e adaptador SetFit da SF2`.
- Interface da coleta esclarecida no commit `05d879924891a089e3af5deac23bd206d2cd3dfb` da integração. A branch usa a base indicada e a implementação segue esse esclarecimento.
- Worktree limpa após o commit. A integração e o aceite independente ficam com o integrador.

## Alterações

Todos os arquivos abaixo ficam em `script/classification_comparison/setfit_sf2/`.

| Arquivos | Resultado |
| --- | --- |
| `.gitignore` | Ignora cache, venv e bytecode neste módulo. |
| `training/requirements.txt`, `environment.py`, `supervise.py` | Mantêm os pins SF1 e verificam os pins dos contratos. Conferem snapshot, origem e hash declarado do wheel Torch, imports e CPU com duas threads intra/inter-op. Supervisor externo limita a instalação a 30 minutos e acumula até 30 minutos para os dois ajustes completos. Timeout ou cancelamento terminam o grupo do processo e geram status. |
| `training/fit.py`, `package.py`, `training/__main__.py` | Validam o congelamento, conferem hashes, repetem a tokenização antes do ajuste e projetam apenas texto e rótulo próprio para o Trainer. Instanciam dois encoders no mesmo snapshot com os parâmetros do protocolo. Exportam Safetensors e cabeça logística local, salvam ordem de classes e evidência efetiva e validam reload antes de publicar o pacote. |
| `training/scores.py` | Extrai os vetores brutos das decisões originais seladas da coleta SF2-04 com a política fixa mínima, verifica hashes, IDs, decisões e cobertura e publica um JSON novo sem chamar nenhum especialista. |
| `adapter/__main__.py`, `decide.py` | Worker com sinal READY seguido de uma decisão por linha. Carrega os artefatos já verificados antes de sinalizar, processa somente campos ausentes, preserva o canal e aplica os complementos em conjunto. Invalidez e texto longo bloqueiam inferência. Revisão ou erro em qualquer alvo bloqueiam complementos e preservam as escolhas brutas observadas. |
| `adapter/_fixture_worker.py`, `adapter/test_decide.py`, `training/test_package.py`, `training/test_supervise.py` | Controles de política, projeção, transporte, extração, integridade, receita e supervisão. |
| `adapter/README.md`, `training/README.md` | Comandos, layout, identidades de fixture e exercício. |

O pacote armazena um recibo indexado dos SHA-256 do snapshot base, os pesos
ajustados e tokenizer de cada campo, a cabeça e a evidência por especialista.
O reload usa o digest confiável do pacote como entrada, valida todos os membros
do inventário antes da desserialização e confere novamente os bytes individuais
da cabeça efetivamente lida. O teste de reload usa um microencoder BERT
inicializado localmente e cabeças com parâmetros determinísticos de fixture.

## Verificações executadas

Comandos a partir da raiz da worktree. O Python usado para as verificações foi
um venv separado em `.cache/verification/.venv`, referenciando em leitura o
site-packages SF1 e adicionando no próprio venv os quatro pacotes fixados dos
contratos. O ambiente original e o snapshot SF1 foram usados em leitura. Os
arquivos do snapshot foram conferidos na origem, copiados para `.cache`
da frente e conferidos novamente. Os comandos abaixo reproduzem as provas
com essa instalação ou com um ambiente provisionado pelo README.

```sh
sf2=script.classification_comparison.setfit_sf2
cache=script/classification_comparison/setfit_sf2/.cache/verification
python="$cache/.venv/bin/python"
snapshot_sf1=../c05-setfit/script/classification_comparison/setfit_pilot/.cache/model

rtk proxy "$python" -B -m pip check
rtk proxy "$python" -B -m "$sf2.training" check \
  --snapshot "$snapshot_sf1" --copy-to "$cache/model" --output "$cache/environment.json"
rtk proxy "$python" -B -m "$sf2.training" code-manifest --output "$cache/training-code.json"
rtk proxy "$python" -B -m unittest -v \
  "$sf2.adapter.test_decide" "$sf2.training.test_supervise" "$sf2.training.test_package"
rtk proxy "$python" -B -m unittest discover -s script/classification_comparison/setfit_sf2/contracts -t . -v
rtk proxy git show --format= --check HEAD
```

| Verificação | Resultado |
| --- | --- |
| `pip check` | `No broken requirements found.` |
| `training check` com cópia e imports | `73 pins conferidos; 10 arquivos do snapshot conferidos`. Conferidos os hashes aprovados das fontes e a origem do wheel Torch com SHA-256 declarado. |
| Carga do snapshot em CPU com `load_body`, leitura do parâmetro monitorado e `length(model.tokenizer, "Texto de controle SF2-03")` | Limite 128, texto de controle com 9 tokens, SHA-256 do parâmetro disponível. Sem forward. |
| `code-manifest` | Arquivo de inventário produzido na área ignorada. |
| Suíte SF2-03 | 21 testes em 15,716 s, OK. Inclui subprocesso real do worker com pacote sintético, `READY` e JSONL, preflight, desserialização bloqueada por digest errado/adulteração, tolerância de reload, configuração efetiva do Trainer sem ajustar, aviso de convergência de fixture, timeout acumulado e cancelamento. |
| Contratos SF2-00 | 16 testes em 1,903 s, OK. Os testes do manifesto criaram dados e arquivos sintéticos em diretório temporário. |
| Harness de integração em subprocesso | `{"type":"ready"}`, caso completo com `category=0, priority=0` e mesmo texto sem prioridade com `category=0, priority=1`. Decisões auditadas por `validate_decision`. |
| Autorrevisão | `git show --format= --check HEAD` sem saída. A lista explícita do commit contém 16 arquivos da frente. |

A primeira execução da suíte identificou que o registro sintético da extração
precisava declarar `missing_fields`. A fixture passou a declarar a máscara e a
suíte completa passou. Bibliotecas do ambiente emitiram avisos de depreciação
de Swig e `cache_dir`. A instalação limpa baixando novamente os wheels não foi
executada. O aceite desta onda usa o ambiente local verificado.

## Harness e exercício

O processo de controle a seguir reutiliza o loop e a política reais, com duas
cabeças de fixture. A saída tem os mesmos frames do worker de produção.

```sh
rtk proxy python3 -B -m "$sf2.adapter._fixture_worker" --policy "$collection_policy"
```

No executor, use a identidade do pacote `"2" * 64`, o hash `"3" * 64` para os
dois modelos, o SHA-256 real do arquivo da política e a ordem de
`labels.category` e `labels.priority` do protocolo. As escolhas brutas de
controle são `pix` e `urgent` quando o campo correspondente é solicitado.

Para reproduzir o exercício, execute o teste abaixo. Ele mantém texto e
categoria, retira prioridade da segunda chamada e verifica que o especialista
recebeu somente texto, que só prioridade foi invocada e que a categoria do
canal foi preservada.

```sh
rtk proxy "$python" -B -m unittest -v \
  "$sf2.adapter.test_decide.AdapterTests.test_exercicio_retirar_prioridade_sem_chamar_categoria"
```

## Limites e pendências

Foram usados exclusivamente controles sintéticos para resultados de execução.
A verificação do snapshot real se limitou a hashes, carga e tokenização de
fixture. Nenhum encoder foi ajustado, nenhum score dos 90 relatos foi extraído,
nenhum arquivo de texto, gold ou anotação do final reservado foi acessado e
nenhuma API de inferência foi chamada. Pesos reais após ajuste, convergência,
scores, consumo e latência do ensaio permanecem como evidência da SF2-05.
A verificação combinada entre SF2-03 e SF2-04 permanece com o integrador
após os aceites individuais.

## Correção 1 · Publicação e congelamento pré-treino

- Base da correção `d5819f7d47d16ed5394a224fa25fdeecf13e56d1`.
- Commit `420db5d3d618f6a43a43053161efa8ebb08ddff6` em `feat/sf2-treinamento`, na mesma worktree.
- Arquivos alterados em `training/` do módulo SF2. `supervise.py` finaliza o recibo e reverte artefatos. `environment.py` e `fit.py` resolvem os arquivos de requisitos e congelam suas fontes executadas. `test_supervise.py` e `test_package.py` contêm as regressões.

O resultado só é elegível com `status.json` em `complete`. A checagem do sinal
registrado ou pendente é feita imediatamente antes da troca atômica do
recibo, com SIGINT e SIGTERM bloqueados nessa etapa. Até esse compromisso,
qualquer cancelamento recebido encerra com recibo `cancelled` e remove os
destinos de pacote e evidência, inclusive se um deles já foi movido. Um
sinal posterior mantém o pacote e o recibo aceitos. Falhas de operação
gravam recibo terminal com código não zero. Exceções inesperadas preservam
seu tipo na mensagem e são propagadas depois da gravação.

O inventário pré-treino passou a incluir `__init__.py`, `artifacts.py`,
`core.py`, `data.py` e `ipc.py` dos contratos e todos os arquivos lidos pelo
resolvedor de `-r`, incluindo os pins compartilhados e os do SF1. O mesmo
resolvedor fornece as versões para `check`. As regressões alteram, uma a
uma, cópias temporárias dos oito arquivos efetivos de contrato e requisitos
e verificam que a conferência rejeita cada inventário divergente.

### Verificações da correção

Comandos executados na worktree com o ambiente de verificação já descrito.

```sh
rtk proxy "$python" -B -m unittest -v \
  "$sf2.training.test_supervise" "$sf2.training.test_package"
rtk proxy "$python" -B -m "$sf2.training" code-manifest \
  --output "$cache/training-code-fix1.json"
rtk proxy "$python" -B -m "$sf2.training" check \
  --snapshot "$cache/model" --output "$cache/environment-fix1.json"
rtk proxy git show --format= --check HEAD
```

Antes do reparo, os três pontos de cancelamento testados retornavam zero,
a exceção inesperada deixava `running/0` e a verificação acusava fontes
ausentes. A execução após o reparo retornou `Ran 17 tests in 13.557s` e
`OK`. As regressões confirmaram código `143` e ausência de artefatos
para sinais antes das duas movimentações e na preparação do recibo
terminal, inclusive sinal pendente bloqueado. Confirmaram também
`complete/0` e identidades iguais com sinal posterior, e `failed/1` com
propagação de `KeyError` em recibo de artefato incompleto.

A geração do inventário terminou com código zero. `check` conferiu os
mesmos 73 pins e 10 arquivos do snapshot. A autorrevisão encontrou cinco
arquivos da frente, sem erros em `git show --format= --check HEAD`. A
worktree ficou limpa. Os testes dos contratos e da avaliação SF2-04
permaneceram fora desta rodada focal. Não houve treino real, execução
sobre os dados do estudo, acesso ao final reservado ou chamada de API.
