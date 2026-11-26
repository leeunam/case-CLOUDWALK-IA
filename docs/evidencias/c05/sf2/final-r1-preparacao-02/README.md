# SF2-FINAL-R1 · preparação pública revisada

O [recibo revisado](final-fix-publico/release.json) é a referência atual
para uma eventual autorização. Seu SHA-256 é
`1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a`.
Ele substitui o [recibo da preparação 01](../final-r1-preparacao-01/README.md),
preservado como histórico.

A [revisão ampla](final-review.md) apontou três P1. A rodada de correções
protegeu o fechamento do lote sob SIGINT, fixou a raiz temporária em `/tmp`
e protegeu a abertura das fontes históricas e do pacote contra links.
O [relatório das correções](final-fix-report.md) registrou 32/32 testes em
7,736 s. A [revisão independente](final-fix-review.md) aceitou as três
correções e reproduziu o SHA-256 do recibo em 7,53 s.

A política candidata usa τ de 0,95 para categoria, τ de 0,70 para
prioridade e δ de zero para ambos os campos. Os tempos de
[paridade](final-fix-publico/paridade.json) são do replay histórico em
fixture. A latência de inferência requer o ensaio real. Os 120 relatos
finais permanecem fechados. O nome projetado do inventário e os nomes
dos quatro papéis aguardam confirmação. A execução exige autorização
expressa vinculada ao novo recibo. A adoção e C06/C07 continuam pendentes.

Para reproduzir o check público, use o
[comando da revisão](final-fix-review.md#check-independente-e-cópias-públicas)
na worktree congelada `.worktrees/sf2-final-ajustes` no commit
`486d55c76d6a2436826364f01057dc0436247216`. A
[configuração](final-fix-publico/config.json), o
[comando congelado](final-fix-publico/command.json) e o
[freeze](final-fix-publico/freeze.json) registram os insumos do recibo.
O [comando futuro projetado](final-fix-publico/comando-futuro-projetado.json)
depende da confirmação dos nomes e da autorização. As
[decisões da preparação](decisoes/README.md) registram o escopo das etapas.
