# C05-R2 · Task 3 · Perfil, contrato e executor offline

- Base integrada `b299fdd1a9bc52d45bd46cd87a4a7a9583a6d115`.
- Branch `feat/r2-avaliador` e worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-avaliador`.
- Commit `e6fe31cbe4dd2c96493bf455016163c6c68ff7dc`. Worktree limpa após o commit.
- Chamadas externas nesta entrega: zero. Os testes utilizaram contas SQLite v4 temporárias no modo fixture e credenciais removidas do ambiente de execução.

## O que foi implementado

- O pacote R2 concatena os 24 objetos históricos de desenvolvimento aos 36 finais aceitos. Conferi a igualdade literal dos objetos delimitados pelas chaves nos arquivos de origem e no pacote. O protocolo registra seis referências com revisão humana direta e 54 com origem em agentes, sendo 0/36 humanas no final. O checker valida o congelamento e os pareceres, a partição, a ordem, as quotas, a projeção de entradas e as fontes da candidata.
- `observed-total-r2` usa protocolo 1.2.0, relatório 1.3.0 e IPC 1.1.0. O golden cobre os 13 controles e sete contraprovas. O cálculo de latência seleciona a família observada pelo indicador do perfil. O runner genérico C02 recusa o perfil R2. O checker e o executor dedicado continuam aceitando o perfil.
- O CLI R2 fixa seis casos em desenvolvimento e 36 casos mais 13 controles no final. As 44 candidaturas do final usam uma tentativa por caso. O adaptador Qwen usa corpo JSON com 128 tokens máximos, reasoning desabilitado e somente os campos ausentes. O reuso de `run_batch`, `Journal` e `decide` preserva o relógio total, o diário e a revisão integral da C02.
- A configuração passa `expected_scope="c05-qwen-r2"` a `Settings.load`. O parâmetro usa o scope C05 histórico como padrão. A conta continua usando scope `fixture` ou `real`. A reserva, o despacho, a captura de custo bruto, a conciliação e o bloqueio reutilizam o serviço C05 v4. Desconhecido e timeout conservam a reserva, interrompem o lote e produzem o prefixo. Custo conhecido é registrado ainda que a classificação esteja incorreta. O CLI R2 inicializa contas apenas no modo fixture.
- O manifesto vincula etapa, identidade, candidata, fontes, config, revisão e hashes de código, ordem e hash dos envelopes, conta, teto e reserva. O ID é determinístico por conta, candidata, final e etapa. A unicidade transacional no ledger impede repetir a mesma etapa mesmo com outro conteúdo de manifesto, inclusive depois de uma interrupção. Para o final, o manifesto fixa o caminho e o hash da prova, que por sua vez fixa os hashes dos sete artefatos de desenvolvimento.
- O gate recalcula resultados do relatório, dos streams, do diário completo e dos custos conciliados da mesma execução no ledger. A etapa final confronta a prova com a conta, candidata, protocolo, configuração financeira e revisão de código antes da credencial ou do adaptador. Um prefixo, prova com custo adulterado, status reprovado ou modo divergente impede o final. A prova fixture informa `fixture_ready` e latência sem medição. O `pass` real exige as seis durações observadas e p95 de até 3.000 ms. O relatório C02 de desenvolvimento continua `inconclusive` para a elegibilidade.

## Fontes e hashes confirmados

| Arquivo | SHA-256 |
| --- | --- |
| Candidata Qwen `candidate.json` | `db8005776018a1c94abaffe4ea0f5d6cdcf5a67836e19931bac747e68e1628f3` |
| Final aceito `final-cases.json` | `17f5bae372983f90aa1956d0d583db25483a77a3ff35e4f1041ad4d51b897af9` |
| Pacote composto `dataset.json` | `3f4e69af44f03c89d1767d54ba07264327d616f18b0548656cc00c7bb89e3845` |
| `split.json` | `84afa9b03f218e731aeae4e1c5906894103a9886fe76109e9e0ccf15dc0ef7f8` |
| `protocol.json` | `8b65cd24c08162fea3ba4ed281aa38598d58a16219251c8184d2d6c5cd4d034c` |
| Lock do relatório 1.3 | `b2ad29171936ca41c0fa99ac79886563cad041ee8009c9beebc6b21c156d056c` |

## Verificações realizadas

Comandos executados na worktree R2. Todos os comandos de suíte abaixo retornaram código zero.

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison/r2 -p 'test_*.py' -v
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison/c05 -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison/adapters/qwen -p 'test_qwen.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s docs/planejamento/classificacao-comparativa/contratos -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s docs/planejamento/classificacao-comparativa/contratos/relatorio-1.2 -p 'test_*.py'
```

| Suíte | Resultado |
| --- | --- |
| R2 | 9 passaram em 17,063 s |
| C02 | 39 passaram em 36,632 s |
| C05 | 37 passaram em 35,800 s |
| Qwen | 30 passaram em 8,938 s |
| C01 | 11 passaram em 0,764 s |
| C01-L | 8 passaram em 1,703 s |

```sh
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-r2
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-1.1
rtk proxy python3 -B script/check_classification_contracts.py --profile warm-1.0
rtk git diff --check b299fdd HEAD
```

- Os três checkers passaram com cinco schemas, 13 entradas, nove observações e 13 decisões. As contraprovas foram 7 R2, 7 de tempo total 1.1 e 64 do perfil histórico.
- A suíte R2 exerceu o CLI real do programa em transporte fixture. Development concluiu seis relatos e seis chamadas, com 8/8 alvos, 4/4 fornecidos, três completos corretos, três revisões, 1/1 urgente e US$ 0,003282 simulados. O gate resultou `fixture_ready`, com zero amostras de latência e p95 sem medição. Final concluiu 36 relatos, 13 controles e 44 chamadas. O ledger reaberto mostrou duas etapas `finished`, 50 reservas `settled` e US$ 0,027350 simulados. Ambos os relatórios foram verificados pelo checker.
- Os cenários dirigidos cobriram erro de classificação com custo conhecido, reexecução com outra configuração, falsificação do ID, prova adulterada, prefixo, prova fixture em modo real antes de acessar a conta, custo desconhecido, timeout e conservação da reserva. O teste unitário de latência confirmou 3.000 ms inclusivos em seis amostras e rejeitou amostra faltante ou acima do limite.
- Validei os 21 relatórios históricos disponíveis no checkout, com comparação byte a byte contra `git show b299fdd:CAMINHO`. Total confirmado de 18 `warm-1.0` e três `observed-total-1.1`, incluindo os dois pilotos e o primeiro final C05. A primeira contagem usava 17 warm do inventário original e terminou com uma asserção incorreta após validar todos os relatórios. A conferência seguinte incluiu explicitamente o reteste C03-P2 e retornou código zero. `git diff --exit-code b299fdd --` nos caminhos congelados e em `c05/budget.py` também retornou zero.
- A primeira reprodução manual do CLI detectou uma soma que passava texto ao serviço Decimal. Corrigi a conversão e a suíte posterior confirmou as duas etapas e os valores exatos. A chamada `run.py --profile observed-total-r2 --dry-run` foi recusada pelo seletor genérico com código 2, como esperado.

## Reprodução fixture

Executar na raiz da worktree. O caminho do ledger fica em diretório temporário. A saída, que integra o inventário local do checker, fica abaixo da worktree.

```bash
r2_cli() {
  rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B script/classification_comparison/r2/execute.py "$@"
}

r2_finance=$(rtk proxy mktemp -d)
r2_evidence=$(rtk proxy mktemp -d "$PWD/r2-fixture.XXXXXX")
r2_account="$r2_finance/account.sqlite"
r2_cli init-account --mode fixture --account "$r2_account" --cap-usd 10 \
  --previous-spend-usd 0 > "$r2_finance/identity.json"
r2_id=$(rtk proxy python3 -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["account_id"])' "$r2_finance/identity.json")
r2_common=(--mode fixture --config script/classification_comparison/r2/config-fixture.json \
  --account "$r2_account" --account-id "$r2_id" --cap-usd 10)

fixture_manifest() {
  rtk proxy python3 -B -c 'import json,sys; p=json.load(open(sys.argv[1])); p["enabled"]=True; json.dump(p,sys.stdout)' "$1"
}

r2_cli run --stage development "${r2_common[@]}" --dry-run --output "$r2_evidence/dev-plan"
fixture_manifest "$r2_evidence/dev-plan/manifest-template.json" > "$r2_evidence/dev-manifest.json"
r2_cli run --stage development "${r2_common[@]}" --manifest "$r2_evidence/dev-manifest.json" \
  --confirm-execution --output "$r2_evidence/dev"

r2_gate="$r2_evidence/dev/development-gate.json"
r2_cli run --stage final "${r2_common[@]}" --development-gate "$r2_gate" --dry-run --output "$r2_evidence/final-plan"
fixture_manifest "$r2_evidence/final-plan/manifest-template.json" > "$r2_evidence/final-manifest.json"
r2_cli run --stage final "${r2_common[@]}" --development-gate "$r2_gate" \
  --manifest "$r2_evidence/final-manifest.json" --confirm-execution --output "$r2_evidence/final"
r2_cli status --mode fixture --account "$r2_account" --account-id "$r2_id"
```

Exercício. No `dev/decisions.jsonl`, localize `jev-039`. Confira que a decisão ficou em revisão e que os dois campos ausentes mantiveram `applied: null`. Compare a observação com as três revisões integrais do `development-gate.json`. Depois encontre o controle injetado do final e verifique como uma previsão válida acompanhada de abstenção também leva à revisão integral.

## Pendências

A revisão independente e a integração pertencem ao integrador. A execução real depende de manifesto habilitado próprio, verificação futura de tarifas e limites faturáveis e autorização específica. Medidas reais de qualidade, latência e custo da R2 seguem pendentes. Os exemplos real e de manifesto foram entregues com verificações e habilitação desativadas.

## Correção consolidada 1

Revisão original `e6fe31cbe4dd2c96493bf455016163c6c68ff7dc`, base sincronizada `ef840a1f40f2e5da2ca439dc5bf359f7e6770504` e correção `9dfbc0d0fe1a981946e2e05e41395b6146b77d05`, na mesma worktree e branch `feat/r2-avaliador`. Worktree limpa após o commit.

- **P1.** Depois de publicar o desenvolvimento original e registrar `finished` na conta, o executor grava um selo local que inclui a identidade da conta, execução, etapa, manifesto, binding, configuração e candidata, mais os hashes do gate e dos sete arquivos da execução. O nome do selo é derivado do manifesto determinístico de desenvolvimento. O arquivo `.<manifest_id>.development-seal.json` fica ao lado do SQLite, é criado com `O_EXCL` e modo privado, e é sincronizado junto com o diretório. O executor sela resultados `failed` e resultados liberatórios. A verificação do final resolve esse local pela conta e exige o selo original antes de despachar. `collect` permanece uma recomputação sem escrita do selo. O teste substituiu observação e decisão, regenerou relatório, gate e manifesto, obteve 8/8 no recálculo e confirmou a rejeição com ledger e selo originais.
- **P2.** O checker R2 compartilha o cálculo canônico com a C02 e compara gates, fatias, urgências, p50 e uso com o que reconstrói dos streams. A elegibilidade é verificada a partir dessas métricas e da completude da evidência. O relatório sintético com uma conclusão indevida continuou validando como `fail`. Com os três streams intactos, zerar o numerador e trocar o veredito por `pass` passou a ser rejeitado com `r2_metrics: gates`.
- **Metadados.** O split identifica o pacote composto 2.0.0 e separa o contexto HTTP da projeção IPC, que é onde o ID permanece. Recalculei somente o golden R2 afetado e seus pins. Novos SHA-256 do split, protocolo e lock, respectivamente: `0a1deb39189fc059f3dcf4ea4261f5175afce874eda11ff3dc065e0b6faf6b14`, `4dac44b9fcd378ec12df5b6e0b3243c9b05300710560fc579368899632954466` e `9b83e6c85fcf25a061e93e28ad4c9682cb505e6f830c6dbc5ef08c37fc2159a6`.

Comandos offline executados na worktree da Task 3:

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison/r2 -p 'test_*.py' -v
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison/c05 -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison/adapters/qwen -p 'test_qwen.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s docs/planejamento/classificacao-comparativa/contratos -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s docs/planejamento/classificacao-comparativa/contratos/relatorio-1.2 -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B script/check_classification_contracts.py --profile observed-total-r2
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B script/check_classification_contracts.py --profile observed-total-1.1
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B script/check_classification_contracts.py --profile warm-1.0
rtk git diff --check ef840a1 HEAD
```

| Verificação | Resultado |
| --- | --- |
| R2 | 12 passaram em 16,335 s |
| C02 | 39 passaram em 36,001 s |
| C05 | 37 passaram em 33,867 s |
| Qwen | 30 passaram em 7,991 s |
| C01 | 11 passaram em 0,877 s |
| C01-L | 8 passaram em 1,328 s |
| Checkers | R2 7 rejeições esperadas, observado 1.1 7, histórico 64 |
| Históricos | 18 warm e três observados válidos, bytes iguais à base `b299fdd` |
| Diff | Código zero na checagem de espaços |

A primeira execução da suíte R2 teve 11 casos aprovados e uma asserção textual desatualizada para a mensagem de adulteração. Ajustei o teste para esperar a rejeição pelo selo e repeti apenas R2. A suíte de 12 passou, incluindo retorno do CLI fixture com as duas etapas, execução reprovada com saídas regeneradas, selo removido e corrompido, relatório final forjado, modo divergente e replay.

A verificação histórica enumerou `report.json` de contratos 1.1/1.2 com `rtk proxy git ls-tree -r --name-only b299fdd -- script/classification_comparison docs/planejamento/classificacao-comparativa/contratos`, conferiu cada conteúdo com `rtk proxy git show b299fdd:CAMINHO` e executou `verify_report`. A saída foi `{'warm-1.0': 18, 'observed-total-1.1': 3} 21 relatórios, bytes conferidos contra b299fdd`. A comparação protegida abaixo retornou código zero:

```sh
rtk git diff --exit-code ef840a1 -- script/classification_comparison/c05/budget.py \
  script/classification_comparison/adapters/qwen/r2 \
  docs/planejamento/classificacao-comparativa/r2/{dataset,final-cases,final-freeze,data-authorship,data-review,similarity-review}.json
```

Exercício fixture. Após executar o desenvolvimento, compare os hashes em `development-gate.json` e no selo privado do diretório financeiro temporário. A regressão `test_regenerated_proof_from_failed_development_cannot_replace_original_outputs` mostra por que atualizar um manifesto com um novo gate é insuficiente quando as saídas divergem das registradas na conclusão.

O selo depende da integridade da pasta privada da conta e do programa. Preserve-o com o SQLite. Se o processo cair após o encerramento financeiro e antes da criação do selo, a etapa continua consumida e o final permanece bloqueado. A re-revisão é dirigida ao diff da correção. Houve zero chamadas externas e todas as contas usadas foram temporárias em modo fixture.

## Correção dirigida 2

Base `9dfbc0d0fe1a981946e2e05e41395b6146b77d05` e commit `3f66bec2e6ac89c03ffd298fbfb9d5fcc5e428e5`, na branch `feat/r2-avaliador` e worktree original da Task 3. A worktree ficou limpa.

O executor mantém em memória os hashes das sete saídas, obtidos na produção. A projeção IPC já tem hash dos bytes que o plano escreve. Os escritores de JSON devolvem o hash da própria serialização. Durante development, o diário atualiza incrementalmente o hash de cada stream com as linhas originais sincronizadas. Depois do fechamento financeiro, o coletor confronta a publicação com os sete hashes e usa exatamente os bytes validados para montar o gate. Também confronta o gate publicado com o hash retornado pelo escritor antes de criar o selo. A autorização do final continua exigindo o selo privado junto da conta.

A regressão dirigida encaixou um escritor imediatamente após a chamada original de `close_run(finished=True)` e antes da coleta. A execução produziu uma categoria incorreta. O escritor substituiu as observações e decisões públicas e regenerou o relatório correspondente. O executor detectou a diferença e parou antes de escrever o gate ou o selo. O ledger permaneceu `finished` com as seis reservas conciliadas. Uma prova recalculada a partir das saídas substituídas pôde descrever `fixture_ready`, mas o final a recusou por ausência de selo e o replay do desenvolvimento foi bloqueado. O gancho controla a ordem para reproduzir a condição e não mede uma corrida entre processos. Outra regressão alterou os bytes do gate logo após a gravação e verificou a rejeição antes de selar.

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison/r2 -p 'test_*.py' -v
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison/c05 -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s script/classification_comparison/adapters/qwen -p 'test_qwen.py'
rtk git diff --check 9dfbc0d HEAD
```

| Verificação afetada | Resultado |
| --- | --- |
| R2 | 14 passaram em 23,671 s |
| C02 | 39 passaram em 34,932 s |
| C05 | 37 passaram em 33,825 s |
| Qwen | 30 passaram em 7,283 s |
| Diff | Checagem de espaços retornou código zero |

```sh
rtk git diff --exit-code 9dfbc0d -- docs/planejamento/classificacao-comparativa \
  script/check_classification_contracts.py script/classification_comparison/c05/budget.py \
  script/classification_comparison/adapters/qwen/r2
```

A comparação dos caminhos de fontes, contratos, perfis, candidata e orçamento retornou código zero. P2 e metadados mantêm as verificações da rodada anterior. As contas usadas foram temporárias em modo fixture e houve zero chamadas externas.

O selo se apoia na integridade do programa, da conta e do armazenamento privado. Escrita posterior nas saídas públicas pode impedir a validação do final mesmo se o selo original tiver sido criado. Uma divergência detectada na conclusão mantém o desenvolvimento consumido e bloqueia o final. O repro e a revisão desta rodada cobrem a origem do selo, com avaliação real ainda pendente.
