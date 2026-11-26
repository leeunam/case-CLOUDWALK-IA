# SF2-FINAL-R1 · preparação pública

Em 26/11/2026, a revisão independente aceitou a preparação pública da Task 3.
A candidata fixa τ = 0,95 para categoria, τ = 0,70 para prioridade e δ = 0
para ambos. O SHA-256 de [release.json](release.json) é
`5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b`.

O [QA original](task-3-report.md) registrou 5/5 testes aprovados.
A [revisão independente](task-3-review.md) reproduziu o `check` público em
7,38 s e obteve o mesmo SHA-256. Os tempos do replay medem o transporte da
fixture e o cálculo da decisão. A latência de inferência ainda precisa ser
medida no ensaio real.

O conjunto final de 120 relatos permanece fechado, os modelos seguem como
candidatos e C06/C07 continuam bloqueadas. Para a abertura, ainda faltam a
confirmação do nome exato do inventário e dos quatro papéis previstos no
protocolo e a autorização específica para a execução única.

## Reprodução do check público

Use a worktree original
`/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao`
no commit congelado `31a055bcdae0c89c2bdb626ce4084e405a07be4e`.
O recibo original está em
`script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/release/release.json`
nessa worktree. A configuração original está em `config.json` ao lado do
diretório `release`. Execute o [comando da revisão independente](task-3-review.md#comandos-executados-e-resultados)
a partir dessa worktree, com os caminhos originais e o SHA esperado.

Este arquivo reúne as cópias exatas da [configuração](config.json), do
[comando congelado](command.json), do [freeze](freeze.json) e da
[paridade](paridade.json). O
[comando futuro projetado](comando-futuro-projetado.json) é um registro para
revisão e depende das confirmações e da autorização acima.
