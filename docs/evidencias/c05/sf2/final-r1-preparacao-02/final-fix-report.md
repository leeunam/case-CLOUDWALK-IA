# SF2-FINAL-R1 · correção da revisão final

O `freeze` e o `check` públicos do autor produziram o mesmo SHA-256, `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a`. Os 32 testes de regressão passaram. A próxima decisão depende da revisão limitada e de um `check` independente no checkout congelado.

| Identificação | Valor |
| --- | --- |
| Tarefa | SF2-FINAL-R1, rodada consolidada dos três P1 |
| Base | `e1df85ee737d77a5698e9f4735f1a9aaf908cfed` |
| HEAD aceito pela CLI | `486d55c76d6a2436826364f01057dc0436247216` |
| Branch | `feat/sf2-final-ajustes` |
| Worktree e cwd | `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-ajustes` |
| Intérprete | Python 3.11.13 em `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python` |
| Escopo do commit | Oito módulos e quatro arquivos de testes em `qualification_r1/`. As 17 fontes do adaptador conservaram os hashes atestados. |

O Git informou árvore limpa antes de gerar o template e após o congelamento. A evidência adicional ficou no diretório SDD do checkout principal. O recibo histórico `5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b` identifica a preparação anterior.

## P1 · conclusão durável sob SIGINT

O supervisor instala o registro de SIGINT antes de preparar o lote. A coleta retoma o comportamento preemptivo durante o diálogo com o worker. Ao sair desse trecho, o registro continua ativo durante o tratamento da tentativa, a limpeza do subprocesso, a sincronização do diretório de unidades, a materialização dos JSONL, a publicação do selo e a sincronização do pai. Um sinal recebido depois de serializar o selo chega ao recibo externo, que identifica os bytes já duráveis do selo. Isso permite ao auditor reconstruir o prefixo confirmado também quando a coleta já havia falhado por outro motivo.

Em `test_sigint_through_cleanup_link_and_fsync_closes_one_durable_run`, a fixture entrega SIGINT com `os.kill` em seis pontos distintos. Usa dois relatos e os cinco controles, monitora a criação do subprocesso e tenta reservar novamente o mesmo selo fictício.

| Momento da entrega | Resultado em cada ensaio |
| --- | --- |
| Limpeza do worker, durante o fsync do stderr | Sete tempos válidos, duas decisões de relato e cinco controles auditados |
| Materialização, durante o fsync de timings.jsonl | Mesmo prefixo confirmado |
| Imediatamente antes do link do selo | Mesmo prefixo confirmado |
| Imediatamente após o link do selo | Mesmo prefixo confirmado |
| Fsync do diretório do selo | Mesmo prefixo confirmado |
| Fsync do diretório pai depois da publicação | Mesmo prefixo confirmado |

Nas seis execuções, o recibo vinculou o SHA exato do selo e a auditoria retornou `inconclusive`. Houve um lançamento do worker por ensaio e a segunda reserva foi recusada. `test_closing_interrupt_also_preserves_primary_collection_failure` simulou uma falha no segundo relato e um SIGINT durante a materialização. O auditor recuperou o primeiro relato, a causa primária `ValueError` e a interrupção do fechamento. As regressões anteriores também passaram, inclusive a interrupção antes e depois da publicação de uma unidade individual.

## P1 · primeiro temporário em raiz pública

A CLI fixa a raiz de `tempfile` em `/tmp` antes de processar os argumentos e direciona para essa raiz as variáveis `TMPDIR`, `TEMP` e `TMP` presentes no ambiente. Os snapshots de fontes, dependências, pacote e proveniência especificam a raiz. O snapshot temporário da futura leitura autorizada segue a mesma regra.

`test_first_temporary_lookup_and_snapshots_ignore_all_environment_candidates` começa com o cache de `tempfile` vazio e as três variáveis apontando para a mesma pasta restrita fictícia. Exercita o ponto de entrada da CLI, a primeira criação implícita de arquivo e diretório temporários e a criação de snapshots de fontes e pacote sintético. O monitor registrou zero operações no destino fictício e a pasta permaneceu vazia. Os arquivos criados ficaram em `/tmp`.

## P1 · origens históricas e pacote

O inicializador abre a worktree por descritor e obtém o bootstrap do objeto Git. A conferência do arquivo atual, dos membros e dos pais usa aberturas por descritor com recusa de links no kernel. O auditor histórico recebe duas cópias temporárias, construídas a partir dos bytes regulares dos papéis conhecidos de replay e captura. Ele confere as âncoras e os vínculos originais nesses mesmos bytes. O inventário físico do pacote enumera os diretórios por descritor e classifica as entradas com seguimento de links desativado. A cópia e o SHA de cada membro usam o mesmo fluxo aberto com os pais protegidos. O verificador de pacote original recebe o snapshot completo.

| Teste | Resultado observado |
| --- | --- |
| `test_historical_role_and_parent_links_are_rejected_before_target_lookup` | Papel histórico e pai redirecionados recusados por `ELOOP` ou `ENOTDIR`. Zero operações no alvo fictício |
| `test_extra_package_file_directory_and_parent_links_never_query_targets` | Links extras para arquivo, diretório e pai de membros recusados. O monitor inclui classificação de entradas de `scandir` |
| `test_package_parent_swapped_after_enumeration_and_detached_bytes` | Troca do pai entre enumeração e cópia recusada. Ao alterar uma origem regular depois da cópia, o consumidor encontrou o conteúdo original e seu digest |
| `test_historical_verifier_consumes_the_detached_role` | Alterar o catálogo fictício depois da cópia preservou os bytes e o SHA lidos pelo verificador histórico |
| `test_real_public_historical_roles_without_package_or_private_io` | O auditor histórico confirmou 28 papéis, 19 vínculos da captura, 17 membros do adaptador e 29 buffers, preservando as duas versões históricas de selection.py |

## Reprodução em fixtures

A partir da worktree identificada acima, os comandos são:

```sh
PY_SF2='/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python'
Q='script.classification_comparison.setfit_sf2.qualification_r1'
rtk proxy "$PY_SF2" -B -m unittest -v "$Q.test_public_io" \
  "$Q.test_corrections.Fixes.test_sigint_through_cleanup_link_and_fsync_closes_one_durable_run"
rtk proxy "$PY_SF2" -B -m unittest -v "$Q.test_runner" "$Q.test_corrections" \
  "$Q.test_preflight" "$Q.test_release_bootstrap" "$Q.test_integracao_publica" "$Q.test_public_io"
rtk git diff --cached --check
```

```text
Rodada focal inicial: Ran 6 tests in 0.880s — OK
Rodada de regressão final: Ran 32 tests in 7.736s — OK
Subprocesso isolado de atestação de dependências: OK
git diff --cached --check: código 0, sem diagnóstico
```

O replay integrado com 90 relatos públicos e cinco controles exerceu o runtime, o verificador e o auditor com um subprocesso de frames fixos. Os testes de interrupção, custódia e reserva usaram fixtures.

## Liberação candidata

Configuração e arquivos originais estão em `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-ajustes/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01`. Os comandos abaixo documentam a geração já concluída. Para a reprodução independente, execute somente o último comando no checkout congelado, fornecendo o SHA recebido externamente.

```sh
WT='/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-ajustes'
PY_SF2='/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python'
CLI="$WT/script/classification_comparison/setfit_sf2/qualification_r1/cli.py"
CACHE="$WT/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01"
rtk mkdir -p "$CACHE"
rtk proxy /usr/bin/time -f 'elapsed_s=%e maxrss_KiB=%M' "$PY_SF2" -I -B -S "$CLI" template \
  --release "$CACHE/release" --run "$CACHE/final-run" > "$CACHE/config.json"
rtk proxy /usr/bin/time -f 'elapsed_s=%e maxrss_KiB=%M' "$PY_SF2" -I -B -S "$CLI" freeze \
  --config "$CACHE/config.json" --out "$CACHE/release"
rtk proxy /usr/bin/time -f 'elapsed_s=%e maxrss_KiB=%M' "$PY_SF2" -I -B -S "$CLI" check \
  --release "$CACHE/release" --expect 1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a
```

| Etapa | Saída | Tempo de parede | RSS máximo |
| --- | --- | --- | --- |
| Template | Configuração JSON, código 0 | 4,86 s | 57.228 KiB |
| Freeze | `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a`, código 0 | 7,33 s | 517.036 KiB |
| Check do autor | `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a`, código 0 | 7,77 s | 517.548 KiB |

O recibo confere 84 fontes e recursos atuais, 74 campos de versão, 75 distribuições, 27.357 membros de RECORD e três arquivos .pth. A leitura do pacote verificou o manifesto `224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872` e os 36 membros por bytes, incluindo pesos, cabeças e tokenizadores. O selo público usado como compromisso tem SHA-256 `71bea26395321246ef00c4374465c6cd8bd3320252a7729429cfad5e3c2263a4`.

| Documento | SHA-256 dos bytes |
| --- | --- |
| [config.json](final-fix-publico/config.json) | `fb6613573c5fa02322cf14ce1b8b576c0daa30138cd6bcf46215b443b7929dac` |
| [command.json](final-fix-publico/command.json) | `5b81d96adcca66e2920fadcb5361fcf65dbf743c60d6d6463289dbf2388e4a8c` |
| [freeze.json](final-fix-publico/freeze.json) | `41c25a53b46f9928fd92252caf6249a545336c9b4d1e5da49787b35a906fff5a` |
| [release.json](final-fix-publico/release.json) | `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a` |
| [Paridade](final-fix-publico/paridade.json) | `8ec7806557bd0e8b4f841bed818671f4a22639804706ce502b16e9455f95001f` |
| [Comando futuro projetado](final-fix-publico/comando-futuro-projetado.json) | `cb198d9cb42a5c4c961f33ce955ff8e6ccd25a774bcf38d522788b1faf555edb` |

As quatro cópias arquivadas foram comparadas byte a byte com os originais. O recibo referencia os três digests de configuração, comando e freeze. O anexo de paridade é uma cópia histórica da Task 3. A política e o digest integral das métricas foram reconferidos no novo freeze, `86825eebee11a7815c337f99b96b841de32da4f2c45bdfe85a879adb09d157e4`. Os tempos e recursos de replay nesse anexo pertencem à medição anterior. Na validação, a grade original teve 0/225 elegíveis e a extensão teve 9/45. A candidata registrou 51/72 classificáveis com cobertura correta, 39/90 revisões e 12/13 urgentes brutos.

## Limites e exercício

A execução desta rodada consultou somente insumos públicos e fixtures. Contagem de processos de inferência, desserializações de modelo e exposições do final real nesta rodada: **zero**. O tempo de 913.684,54 ms de treinamento é histórico. A custódia, as autorizações e os marcadores reais permaneceram fechados. A inferência final, seus gates e a adoção seguem pendentes. O basename `private-inventory.json` continua projetado. A confirmação do inventário e dos quatro papéis compete ao responsável pela custódia. Uma eventual exposição exige autorização expressa para a liberação revisada.

**Exercício.** Rode a fixture de SIGINT do primeiro comando e acompanhe o caso `after-link` no teste. Compare o SHA calculado sobre o selo com o campo `seal_sha256` do recibo. Observe como a auditoria conta os sete tempos válidos e conserva o estado inconclusivo.
