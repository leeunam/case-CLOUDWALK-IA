# SF2-FINAL-R1/3 — revisão independente

**SPEC aprovado · QUALITY aprovado.** Aprovados a integração em fixture e o recibo público `5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b`. A exposição continua bloqueada pela confirmação dos nomes da custódia e pela autorização específica.

| Item | Identificação |
| --- | --- |
| Tarefa | SF2-FINAL-R1/3 |
| Base | `9b8f5127ae5e44c5287b824f2e46fb789f11f45b` |
| HEAD aceito | `31a055bcdae0c89c2bdb626ce4084e405a07be4e` |
| Branch | `feat/sf2-final-integracao` |
| Worktree | `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao` |

## SPEC

- O pacote de revisão coincide byte a byte com o diff Git. O intervalo acrescenta somente `test_integracao_publica.py`, com 131 linhas. Os commits aceitos de Task 1 `b97d2f8` e Task 2 `c111110` são ancestrais do HEAD congelado.
- O teste integrado usa o contexto carregado das duas políticas e do manifesto, a CLI existente de fixture JSON e o supervisor com `derive` e `verify` aceitos. Confere contagem, ordem, ID, SHA e motivos dos 90 frames e cinco controles, chamadas e aplicação dos controles, igualdade integral de métricas e gates, e reconstrução pelo auditor. A inconclusão sobre a fixture de 90 relatos é esperada para um protocolo de 120. `qualification_r1/test_integracao_publica.py:22`, `:44`, `:55`.
- Os ensaios injetam atraso depois das funções reais, cobram aborto no orçamento por item e conferem uma observação inválida e zero decisões auditáveis. O SIGINT é entregue antes e depois da publicação da segunda unidade, com um ou dois relatos auditáveis conforme o ponto de interrupção. `qualification_r1/test_integracao_publica.py:90`, `:111`.
- Os testes já aceitos complementam o integrado. A paridade individual confronta o replay da única política sobre os scores públicos por ID. A corrida envolve dois processos com recibos e destinos distintos e o mesmo selo fictício, com uma única leitura registrada em área temporária. `runtime_r1/test_public.py:17`, `qualification_r1/test_exposure.py:66`.
- Conferi estaticamente a linha selecionada e todos os marcos de `validation_reference` contra o resultado público arquivado e ancorado. `paridade.json` contém exatamente o objeto da linha arquivada, com matrizes, denominadores, Wilson e gates. O SHA das métricas `86825eebee11a7815c337f99b96b841de32da4f2c45bdfe85a879adb09d157e4` coincide com o pré-voo e com os bytes canônicos das métricas arquivadas.

## QUALITY

Sem achado bloqueante no diff, na junção das frentes ou no recibo. O teste reaproveita o worker, as funções de derivação e auditoria e os insumos públicos aceitos. O prazo de 150 ms em `qualification_r1/test_integracao_publica.py:102` é de relógio real e pressupõe que transporte e callable alcancem a espera injetada nesse intervalo. A janela de 140 a 900 ms discrimina a interrupção de uma espera completa de 1 s no ambiente pinado. Os tempos do replay medem IPC e cálculo de decisão. O p95 de inferência depende da eventual execução real.

## Comandos executados e resultados

A partir da worktree congelada, `rtk git status --short --branch` mostrou `feat/sf2-final-integracao` e árvore limpa antes e depois do check. `rtk git rev-parse HEAD HEAD^` devolveu os SHAs da tabela. `rtk git diff --check 9b8f5127ae5e44c5287b824f2e46fb789f11f45b..31a055bcdae0c89c2bdb626ce4084e405a07be4e` e `rtk proxy git merge-base --is-ancestor` para cada commit aceito saíram com código 0. A comparação com `rtk proxy git diff --no-ext-diff` em um script de biblioteca padrão confirmou o corpo do pacote de revisão.

Reexecutei uma vez somente o comando público de aceite abaixo, com o SHA fornecido externamente.

```sh
rtk proxy /usr/bin/time -f 'elapsed_s=%e maxrss_KiB=%M' /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python -I -B -S /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/qualification_r1/cli.py check --release /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/release --expect 5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b
```

```text
5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b
elapsed_s=7.38 maxrss_KiB=517336
```

Código de saída 0. O caminho de `check` reconstruiu a pré-inspeção pública e validou as origens históricas, as dependências e o pacote físico de 36 membros mais o manifesto. Os hashes dos encoders, cabeças e tokenizadores são conferidos por leitura de bytes em `qualification_r1/package.py:28`. O `check` retorna antes do despacho de execução em `qualification_r1/cli.py:138`. A evidência de cinco testes executados consta do relatório original, que registrou cinco sucessos em 4,133 s. Nesta revisão os testes e a grade foram examinados pelas fontes e evidências arquivadas.

Executei também `rtk proxy python3 -I -B -S -` no checkout principal, com `hashlib`, `json`, `gzip` e `pathlib` da biblioteca padrão. O script leu apenas os arquivos públicos nomeados, comparou o original e a cópia de cada documento byte a byte e verificou os três vínculos SHA-256 do recibo.

| Documento | SHA-256 verificado nas duas cópias |
| --- | --- |
| `release.json` | `5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b` |
| `config.json` | `449a2207d5e75ff56418ced863c83ff9d340b4978d073d8ba6bc4f9834a92837` |
| `command.json` | `6d880923414fa6d6a8c7ee793872fb6740adf8ff5d3f5f4d270ba042f425bafd` |
| `freeze.json` | `7c311d9b9cb2ec48db3733a02e4885c78ca0b53f695c368157d0d53d6f77465c` |

O mesmo script, com saída 0, confirmou a igualdade de `command.json` com o comando interno em `config.json`, o commit e o diretório efetivos e as âncoras públicas do pacote, dos modelos, do selo e do resultado offline. Conferiu também o SHA da cópia de `paridade.json` e a igualdade do array de `comando-futuro-projetado.json` com o publicado no relatório, incluindo os caminhos públicos, as flags e o SHA esperado.

O recibo original está em `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/release/release.json`. A cópia pública e as evidências estão em `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.superpowers/sdd/sf2-final-r1-plano/task-3-publico`.

## Pendências de exposição

`private-inventory.json` é um basename projetado que a revisão tratou apenas como texto. A raiz da custódia e os nomes `final.jsonl` e `annotations-final.jsonl` têm evidência pública. A entrega ainda requer os nomes exatos do inventário e dos quatro papéis indicados pelo protocolo, confirmados pelo responsável ou por handoff autorizado. A futura autorização deve vincular esses nomes, a ação `execute_once`, o SHA da liberação e o selo do conjunto final. A aprovação desta Task cobre a preparação pública. A exposição e a execução real continuam bloqueadas, e o conjunto final permanece fechado. Todo o trabalho desta revisão se restringiu a código e artefatos públicos, sem consulta de metadados de custódia e sem carregamento de modelo.

**Exercício.** Calcule o SHA-256 da cópia pública de `freeze.json` e compare com `freeze_sha256` em `release.json`. Confira em seguida como a mudança de um único byte alteraria o digest referenciado.

