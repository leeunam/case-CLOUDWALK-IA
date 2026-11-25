# C05-R2 · Correção da revisão ampla final

- Revisão de origem `1e98c4583ed9dc073a502658125f0bcf810b7ba0`.
- Commit `b19a59645342cde40c4939f4f21d05959ae7c39a`.
- Branch `feat/r2-avaliador` e worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-avaliador`, limpa após o commit.

## Correções

**P2 · Contrato da candidata.** O verificador R2 exige até uma requisição por observação candidata e rejeita pontuação. O contrato continua aceitando zero requisições em erros antes do despacho. No exemplo 1.3, `ctl-duplo` tem duas perguntas em uma requisição e as pontuações de `ctl-duplo` e `ctl-politica` foram removidas. As métricas canônicas do exemplo registram oito tentativas, oito requisições e 11 perguntas. As duas novas contraprovas exigem as rejeições `r2_request_limit` e `r2_score`.

**P3 · Procedência.** O split e o protocolo R2 registram criação e aprovação em 24/11/2026. A evidência identifica a escolha da opção A pelo responsável para implementação offline. Os 36 rótulos finais têm revisão exploratória por agentes, com zero aprovações humanas de casos e autorização de gasto separada. O verificador confronta esses metadados com a referência congelada. O dataset composto contém apenas `version`, `review`, `language` e `cases`. Seus 60 objetos e bytes permaneceram íntegros.

O `git_revision` do golden 1.3 aponta para a revisão `1e98c4583ed9dc073a502658125f0bcf810b7ba0`, que contém o perfil e o schema R2. O campo `environment.runtime` explica que essa revisão identifica a base de implementação do exemplo sintético estático. A revisão documenta essa origem. Medições de modelo seguem pendentes.

## Verificações executadas

Comandos na raiz da worktree R2:

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s docs/planejamento/classificacao-comparativa/contratos/relatorio-1.3 -p 'test_*.py' -v
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s docs/planejamento/classificacao-comparativa/contratos -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B -m unittest discover -s docs/planejamento/classificacao-comparativa/contratos/relatorio-1.2 -p 'test_*.py'
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B script/check_classification_contracts.py --profile observed-total-r2
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B script/check_classification_contracts.py --profile observed-total-1.1
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B script/check_classification_contracts.py --profile warm-1.0
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B script/check_classification_contracts.py --profile observed-total-r2 --report docs/planejamento/classificacao-comparativa/contratos/relatorio-1.3/report.json
rtk proxy git cat-file -e 1e98c4583ed9dc073a502658125f0bcf810b7ba0:docs/planejamento/classificacao-comparativa/contratos/relatorio-1.3/report.schema.json
rtk git diff --check 1e98c45 HEAD
```

| Verificação | Resultado |
| --- | --- |
| Contrato R2 | 4 testes passaram em 0,128 s. Cobre a contagem do golden, erro com zero requisições, data e autorização de gasto, e atribuição dos rótulos finais. |
| Contrato histórico | 11 testes passaram em 0,592 s. |
| Contrato de latência total 1.1 | 8 testes passaram em 1,547 s. |
| Checker R2 | 5 schemas, 13 entradas, 9 observações, 13 decisões, 1 golden e 9 rejeições esperadas. |
| Checkers históricos | 7 rejeições esperadas em `observed-total-1.1` e 64 em `warm-1.0`. |
| Golden R2 por `--report` | `OK: observed-total-r2`. |
| Git | Schema R2 localizado na revisão declarada. `git diff --check` retornou código zero. |

Conferi os 21 relatórios históricos com `verify_report` e a igualdade byte a byte com a revisão de origem. A verificação enumerou os arquivos com `rtk proxy git ls-tree -r --name-only 1e98c4583ed9dc073a502658125f0bcf810b7ba0 -- script/classification_comparison docs/planejamento/classificacao-comparativa/contratos` e leu cada versão com `rtk proxy git show BASE:CAMINHO`. Também conferiu os 28 pins do lock por `source_path` e a presença de `R2 = "observed-total-r2"` no checker da revisão declarada. Saída:

```text
{'warm-1.0': 18, 'observed-total-1.1': 3} bytes históricos idênticos à base; 28 pins válidos; revisão do golden contém R2
```

O diff protegido retornou código zero:

```sh
rtk git diff --exit-code 1e98c45 -- script/classification_comparison \
  docs/planejamento/classificacao-comparativa/r2/{dataset,final-cases,final-freeze,data-authorship,data-review,similarity-review}.json \
  docs/planejamento/classificacao-comparativa/contratos/{fixtures,relatorio-1.2}
```

| Fonte R2 alterada | SHA-256 |
| --- | --- |
| `split.json` | `054f0d572e5cb35e15bcc8b1e96df992bc9bf443edf1d4cd512c61e74b017e62` |
| `protocol.json` | `4e89f10dcb15b4a9593532aa52d05917b68df4771972d570dd646a7ce11163d1` |
| `observations.jsonl` | `5d67a4627a3fbce31eeab59da156fa3e27a1b0a2c89e4115a9c9a0fe94c88147` |
| `report.json` | `dd909f778f814cfde6889fd6889d556c4871b38ec84a6bbddb476141f207010e` |
| `negative.json` | `26db0b97ae91ef70b139f8edc4ce7d089ac967168040d142784bd16d62758eff` |
| `sources.lock.json` | `f91f9325870cde169eba795195052908035af2c179de610a0a432f1eaa344df1` |

Exercício. Localize `ctl-duplo` no golden 1.3 e compare `questions`, `requests` e o tamanho de `request_usage`. Relacione as duas escolhas com a única chamada contabilizada. A contraprova `duas-requisicoes-em-caso-duplo` demonstra o erro de contar cada pergunta como requisição.

As evidências anteriores do executor, do selo e da conta continuam vinculadas às respectivas revisões. As suítes do executor permaneceram como evidência da ronda anterior. Esta correção fez zero chamadas ao fornecedor e usou apenas arquivos estáticos. A re-revisão dirigida e eventual execução real seguem pendentes.
