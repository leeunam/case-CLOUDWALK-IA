# SF1-A — execução do piloto C05-SF1

- Base `bf6322df792283e20cec5c12ef4dcc462bb5b846`
- Entrega `bfa67b45a40afa09a9ff2eb29089b1841045e87a`
- Branch `feat/setfit-piloto`
- Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-setfit`
- Guia `docs/c05-setfit-piloto.md`
- Evidências `docs/evidencias/c05/setfit-piloto-01/{data.json,model.json,predictions.jsonl,run.json}`

## Resultado observado

A execução única das quatro divisões terminou às 15:52:01 UTC. O modelo
multilíngue de revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` acertou
15/16 decisões (93,75%). Foram 12/12 categorias classificáveis corretas
e 3/4 revisões reconhecidas. O único erro foi `jev-013`, previsto como
`terminal` quando a saída esperada era revisão. A cobertura de categoria
foi 13/16 e o F1 macro foi 0,9365.

O executor registrou 62,43 s de treino, 4,10 s de carregamento e 70,59 s
decorridos. O provisionamento verificado levou 415,71 s. A inferência em
CPU por texto teve p50 de 15,188 ms e p95 de 21,078 ms (n=16, posto mais
próximo, aquecimentos excluídos).

## Execução e verificações

- A instalação de wheels públicos em uma venv isolada começou na faixa
  das 12:43 BRT e terminou com o modelo verificado antes das 12:51 BRT.
  A primeira tentativa de pip recebeu erro de DNS. A mesma instalação
  prosseguiu com acesso de rede autorizado. A lista e a revisão do
  modelo foram fixadas antes de transferir os pesos. Os dez arquivos
  passaram pela verificação de origem e receberam SHA-256 no manifesto.
- O download do modelo e a instalação de pacotes ocorreram em processos
  separados. As versões foram registradas com `pip freeze --all`.
  `pip check` passou, assim como os imports de SetFit 1.2.0, PyTorch
  2.12.0+cpu, Transformers 5.8.1 e Sentence Transformers 6.3.0.
  O instalador agregado foi checado com `sh -n`. Uma tentativa de
  checar o lock com `pip --dry-run` foi interrompida porque o pip
  voltou a solicitar o wheel da URL direta. A instalação limpa pelo
  instalador agregado permaneceu pendente.
- Executado na raiz da worktree com
  `rtk proxy sh script/classification_comparison/setfit_pilot/run.sh --output docs/evidencias/c05/setfit-piloto-01`.
  A seleção e os hashes das fontes foram registrados antes do primeiro
  treino. A seleção contém 16 relatos de development com categoria
  ausente. Cada treino contém três relatos por rótulo. Cada validação
  contém um por rótulo. Cada ID ocorre uma vez em validação. Os
  comprimentos sem truncamento variaram de 18 a 45 tokens, limite 128.
- Recarreguei o mesmo checkpoint público no início de cada divisão.
  A checagem mostrou um hash inicial idêntico e mudança no parâmetro
  monitorado das quatro divisões após 15 passos cada. O SetFit treinou
  a partir de 120 pares amostrados por divisão. Fixou-se uma época,
  cinco iterações, batch oito, taxa `2e-5` e semente 42. As quatro
  regressões logísticas ajustaram as mesmas quatro saídas.
- O primeiro texto de treino de cada divisão foi seu aquecimento.
  As decisões de validação receberam apenas o texto. O argmax usa
  scores brutos, sem limiar ou calibração. O rótulo exploratório
  `informacao_insuficiente` gera a decisão de revisão.
- Em seguida executei
  `rtk proxy python3 -B script/classification_comparison/setfit_pilot/.cache/verify_evidence.py docs/evidencias/c05/setfit-piloto-01`.
  A checagem independente recalculou a matriz, precisão, revocação,
  F1, cobertura, revisão e ambos os percentis a partir das decisões.
  Também conferiu hashes, IDs, ausência de IDs finais, distribuição
  e separação entre as divisões, unicidade normalizada, tamanho de
  entrada, passos, evidência de ajuste e soma dos scores. Passou duas
  vezes, antes e depois do commit, em modo de leitura.
- `git diff HEAD^ HEAD --check` passou. A worktree está limpa.
  Arquivos de pesos, cache, venv e saída de treino constam nas
  exclusões de Git. O commit contém apenas runner, locks, guia e
  evidências pequenas.

## Reprodução e limites

O guia contém os dois comandos para instalação e execução em checkout novo,
além de um exercício sobre o caso `jev-013`. A execução registrada usou
Linux x86-64, Python 3.11.13 e Intel Core i5-1345U, em CPU com duas
threads configuradas. A inferência foi local, com 16 classificações
medidas e quatro aquecimentos. Credenciais HF/Feita/Typesafe
ficaram fora dos subprocessos do piloto.

A amostra é sintética, pequena e apoiada por rótulos exploratórios. O p95
corresponde ao maior valor na amostra de 16. A avaliação da latência total,
a adoção e a integração continuam em espera. A revisão independente é
SF1-R. O checkout principal e os arquivos reservados para ST1 ficaram com
o integrador.

## Correção após SF1-R

A correção parte de `bfa67b45a40afa09a9ff2eb29089b1841045e87a` e está em
`859c55ed7a883fda7e7660086ec602049d816ba0`, na mesma branch e worktree.
Cada tentativa de instalação grava `status.json` e `commands.log` em um
diretório próprio. O provisionador registra a fase e o arquivo atual para
distinguir download de verificação. A experiência anterior preserva seu
registro e manifesto.

O supervisor externo inicia o contador antes de autorizar cada chamada a
`trainer.train()`. A carga e as inferências ficam fora da contagem. No
vencimento ou cancelamento o supervisor encerra o grupo do executor e
marca a fase interrompida em `run.json`, mantendo o conteúdo das
divisões e previsões já gravadas. Os códigos observados foram preservados.
Os resultados arquivados continuam vinculados ao código `bfa67b4`.

Comandos executados na raiz da worktree, com os resultados registrados.

```text
$ rtk proxy python3 -B script/classification_comparison/setfit_pilot/test_supervise.py -v
test_download_error_keeps_curl_exit_code (__main__.ControlTests.test_download_error_keeps_curl_exit_code) ... ok
test_installation_cancellation (__main__.ControlTests.test_installation_cancellation) ... ok
test_installation_timeout (__main__.ControlTests.test_installation_timeout) ... ok
test_successful_provision_survives_later_dependency_error (__main__.ControlTests.test_successful_provision_survives_later_dependency_error) ... ok
test_training_budget_is_cumulative_and_preserves_completed_fold (__main__.ControlTests.test_training_budget_is_cumulative_and_preserves_completed_fold) ... ok
test_training_cancellation (__main__.ControlTests.test_training_cancellation) ... ok
test_training_does_not_charge_time_outside_fit (__main__.ControlTests.test_training_does_not_charge_time_outside_fit) ... ok
test_training_error_preserves_worker_diagnosis (__main__.ControlTests.test_training_error_preserves_worker_diagnosis) ... ok
test_training_timeout_interrupts_native_call (__main__.ControlTests.test_training_timeout_interrupts_native_call) ... ok
test_verification_error_has_its_own_phase (__main__.ControlTests.test_verification_error_has_its_own_phase) ... ok

----------------------------------------------------------------------
Ran 10 tests in 4.095s

OK

$ rtk proxy git diff bfa67b4 HEAD --check
$ rtk proxy git diff --exit-code bfa67b4 HEAD -- docs/evidencias/c05/setfit-piloto-01
$ rtk proxy git status --short --branch
## feat/setfit-piloto
```

A checagem `sh -n` de `install.sh` e `run.sh`, a leitura das árvores
sintáticas Python e `rtk proxy sh run.sh --help` também passaram a partir
de `script/classification_comparison/setfit_pilot`. A função de checagem
histórica reproduzida no guia imprimiu
`OK: 7 hashes históricos conferem`. Uma comparação de AST com o código
de `bfa67b4` para `PARAMETERS`, `SEED`, `LABELS`, `FOLD_COUNT` e para
as funções `observe`, `select_data` e `summarize` imprimiu
`OK: parâmetros, seleção, classificação e métricas preservados`.

Os testes usaram subprocessos e arquivos de bytes simulados, sem novo
treino, inferência, instalação ou download. A primeira tentativa da
suíte detectou um erro de sintaxe no treino simulado por escape
de nova linha. O fixture foi corrigido e a suíte passou. A instalação
limpa pelo script agregado continua pendente.
