# Parecer SF1-A — piloto SetFit

## Conformidade com a especificação

- **Ajustes necessários.** As evidências sustentam o desenho e o resultado da execução registrada. Os dois achados importantes tratam do comportamento do executor em caso de falha e do teto operacional de treino.
- **Verificação pendente.** A instalação do zero pelo `install.sh` segue pendente. Conferi os 69 itens fixados contra os metadados da venv existente, incluindo a URL do wheel CPU. O relatório de implementação registra que `pip check` e os imports passaram, que houve uma falha de DNS recuperada e que o `pip --dry-run` foi interrompido quando o pip voltou a solicitar o wheel. `.superpowers/sdd/setfit-piloto/sf1-report.md:29`.
- Tarefa `C05-SF1` / `SF1-A`. Base `bf6322df792283e20cec5c12ef4dcc462bb5b846`, entrega `bfa67b45a40afa09a9ff2eb29089b1841045e87a`, branch `feat/setfit-piloto`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-setfit`.

## Verificações

- A seleção usa apenas desenvolvimento R2 2.0.0 com `category` ausente. Recalculei os dois hashes das fontes e conferi os 16 IDs, quatro por rótulo e sem textos duplicados após normalização. `script/classification_comparison/setfit_pilot/protocol.py:32`.
- Reproduzi com o scikit-learn instalado as quatro divisões estratificadas com seed 42, 12 relatos de treino e quatro de validação, com três e um por rótulo, respectivamente. Cada previsão corresponde ao fold em que seu ID ficou na validação. `script/classification_comparison/setfit_pilot/protocol.py:65`.
- Cada divisão carrega um encoder CPU do snapshot verificado e cria uma cabeça de regressão logística nova. O relatório traz uma época, cinco iterações de amostragem, batch oito, taxa `2e-5`, 120 pares e 15 passos por divisão. Os hashes iniciais do parâmetro monitorado coincidem e os quatro hashes finais demonstram ajuste. A checagem de tokens usa `truncation=False` e aborta acima do limite. Nos registros, os relatos têm de 18 a 45 tokens para limite de 128. `script/classification_comparison/setfit_pilot/run.py:99`, `script/classification_comparison/setfit_pilot/run.py:112`, `script/classification_comparison/setfit_pilot/run.py:137` e `docs/evidencias/c05/setfit-piloto-01/run.json:93`.
- A inferência recebe texto, usa o maior score não calibrado e representa revisão com categoria nula. Conferi os rótulos com a fonte e a escolha do maior score nas 16 linhas. Os quatro aquecimentos são textos do próprio treino. `script/classification_comparison/setfit_pilot/run.py:42` e `script/classification_comparison/setfit_pilot/run.py:176`.
- Os hashes dos sete arquivos do executor no diff correspondem à execução registrada. Conferi o tamanho e o SHA-256 dos dez arquivos em cache com o manifesto salvo. O carregamento fixa `trust_remote_code=False`, `local_files_only=True` e Safetensors. A execução isola cache e restringe credenciais e acesso externo. Os diretórios de pesos e venv estão nas exclusões do Git. `docs/evidencias/c05/setfit-piloto-01/run.json:84`, `script/classification_comparison/setfit_pilot/run.py:101`, `script/classification_comparison/setfit_pilot/run.sh:6` e `script/classification_comparison/setfit_pilot/.gitignore:1`.
- Recalculei matriz, precisão, revocação, F1, cobertura e percentis a partir das decisões. Conferem 15/16 decisões, 12/12 categorias classificáveis, 3/4 revisões e 13/16 atribuições de categoria. `jev-013` foi a única decisão divergente. A latência por texto teve p50 de 15,188 ms e p95 de 21,078 ms por posto mais próximo, com n=16. Conferi a soma por divisão de 4,095 s de carga e 62,433 s de treino. O manifesto registra separadamente 415,707 s de provisionamento do snapshot. `docs/evidencias/c05/setfit-piloto-01/predictions.jsonl:7`, `docs/evidencias/c05/setfit-piloto-01/run.json:220` e `docs/evidencias/c05/setfit-piloto-01/model.json:46`.
- O diff contém apenas o piloto, suas evidências e seu guia. O guia descreve amostra sintética, rótulos exploratórios e adoção, calibração, comparação e integração em espera. `docs/c05-setfit-piloto.md:3` e `docs/c05-setfit-piloto.md:65`.

## Achados

### Critical

Nenhum.

### Important

- **Falhas do instalador ficam sem registro parcial persistente.** O `exec timeout` entrega o código da primeira falha ou do prazo expirado e encerra o instalador. O provisionador só grava seu manifesto quando termina toda a verificação. Em diretório temporário, injetei a saída `124` de `timeout` e o instalador saiu sem stdout, stderr ou arquivo de estado. Grave a etapa e seu resultado final, distinguindo falha de instalação, download, verificação e expiração. Preserve o código de saída e a evidência bem-sucedida de uma execução anterior. `script/classification_comparison/setfit_pilot/install.sh:11` e `script/classification_comparison/setfit_pilot/provision.py:69`.
- **O teto de treino depende de o controle voltar ao Python.** O temporizador entrega `SIGALRM` ao próprio processo em treino. O tratamento em Python pode aguardar o fim de operações nativas. Num teste leve com `zlib` local, o alarme de 5 ms foi tratado depois de 34,8 ms. Uma operação bloqueada por tempo indefinido pode deixar a divisão como `training` indefinidamente. Para cumprir o teto mesmo nesse cenário, um supervisor externo ao treino deve poder interrompê-lo e marcar a execução como interrompida. O treino observado terminou em 62,43 s. `script/classification_comparison/setfit_pilot/run.py:151` e `docs/c05-setfit-piloto.md:90`.

### Minor

Nenhum.

## Qualidade da tarefa

**Requer ajustes.** A separação entre seleção, provisionamento e execução permite auditar a amostra e os resultados. Os achados afetam tratamento de falha e limite operacional em reprodução. Preserve os hashes e artefatos históricos ao corrigir o executor. Os checks foram locais e leves, sem instalação, download, inferência ou treino adicional.

## Revisão da correção `859c55e`

**Conformidade da SF1-A — aprovada.** A revisão focal cobre `bfa67b45a40afa09a9ff2eb29089b1841045e87a` a `859c55ed7a883fda7e7660086ec602049d816ba0` na mesma branch e worktree. Os dois achados da primeira revisão estão resolvidos.

- **ADDRESSED — registro da instalação.** Cada tentativa recebe um diretório próprio e grava a etapa antes de executar o comando. O provisionador registra download e verificação em separado. O supervisor preserva o código do processo, grava a conclusão ou interrupção em `status.json` e guarda a saída dos comandos em `commands.log`. Os testes relatados cobrem erro de dependência, download e verificação, além de cancelamento, prazo e preservação do manifesto anterior. `script/classification_comparison/setfit_pilot/supervise.py:90`, `script/classification_comparison/setfit_pilot/supervise.py:112` e `script/classification_comparison/setfit_pilot/provision.py:82`.
- **ADDRESSED — teto acumulado de treino.** Um processo separado arma o prazo antes de autorizar `trainer.train()` e desconta o tempo a cada término. No vencimento, encerra o grupo do executor e grava a interrupção a partir do último relatório disponível, preservando as previsões gravadas. Os testes relatados incluem uma chamada nativa bloqueada, soma entre divisões e espera fora do treino. `script/classification_comparison/setfit_pilot/run.py:142`, `script/classification_comparison/setfit_pilot/supervise.py:52`, `script/classification_comparison/setfit_pilot/supervise.py:139` e `script/classification_comparison/setfit_pilot/supervise.py:192`.
- **Evidências preservadas.** O diff da correção mantém os quatro artefatos da execução original e os argumentos do experimento. O guia vincula os hashes ao commit histórico e documenta a conferência sem reexecutar inferência. Os tempos medidos pertencem ao executor de `bfa67b4`. `script/classification_comparison/setfit_pilot/run.py:19` e `docs/c05-setfit-piloto.md:119`.

**Qualidade da SF1-A — aprovada.** A revisão do diff e dos dez testes locais registrados, concluídos em 4,095 s, sustenta a correção dos dois caminhos de falha. Nenhum novo achado Critical, Important ou Minor. A instalação limpa pelo fluxo agregado segue pendente. Esta revisão não executou novamente a suíte, a instalação, o download, o treino ou a inferência. `docs/c05-setfit-piloto.md:107`.
