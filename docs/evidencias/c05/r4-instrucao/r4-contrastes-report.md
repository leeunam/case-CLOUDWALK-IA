# Task3-D2 — Pares de diagnóstico R4

- Base Git `3e59f4ad80536b5586e91c89a2ea157bebbcb442`
- Branch `feat/luna-contrastes-r4`
- Worktree `.worktrees/r4-luna-contrastes`
- Commit `a8c0519224a60d76039785dd9a962957c96b219f`
- Entrega em `docs/planejamento/classificacao-comparativa/r4/diagnostico/`

## Entrega

O conjunto v1.0.0 traz 16 relatos de desenvolvimento em pt-BR. São oito
pares com duas paráfrases que preservam a categoria, duas mudanças entre
categorias e quatro mudanças de categoria identificável para abstenção.
Os rótulos esperados se distribuem em quatro `payouts`, quatro `pix`,
quatro `terminal` e quatro `informacao_insuficiente`. Em 14 entradas,
a prioridade válida já vem do canal. As duas restantes pedem ambos os
campos e mantêm o mesmo fato que justifica urgência.

A separação em dois arquivos permite rotulação cega por ID. O arquivo
`inputs.jsonl` contém apenas o envelope IPC e IDs sem associação visível
a pares. As expectativas, justificativas e relações entre os pares ficam
no `annotations.json`, com contagens e versões/hashes da rubrica e do catálogo.
O README descreve como devolver e conferir os rótulos cegos.

## Verificação

- Um verificador Python descartável leu os dois arquivos e validou
  sintaxe JSON, chaves exatas do envelope IPC 1.1.0, 16 textos e IDs únicos,
  correspondência por ID, oito pares de dois relatos, relações declaradas,
  cobertura dos campos ausentes, preservação e validade dos campos do canal,
  rótulos do catálogo ou abstenção, catálogo idêntico por entrada e hashes
  dos dois arquivos de referência. Todos os testes estruturais passaram.
- `rtk git diff HEAD^ HEAD --check` passou. A diferença para o commit-base
  lista apenas os três arquivos da entrega. A worktree terminou limpa.
- A rotulação cega está pendente. A redação dos relatos e anotações foi
  feita por IA. A validação desta frente foi local, sem chamadas de inferência.

## Reprodução e revisão cega

Na worktree, confira a diferença e os arquivos usados como referência.

```sh
rtk git diff a8c0519^ a8c0519 --check
rtk git diff a8c0519^ a8c0519 --name-only
rtk sha256sum docs/planejamento/classificacao-comparativa/rubrica-comum.md script/f08/jev/catalog.json
rtk sha256sum docs/planejamento/classificacao-comparativa/r4/diagnostico/inputs.jsonl
```

O SHA-256 das entradas é
`07777cf652d481c8f3c98f5c825679fe65bcafdb27919dd62ca92338af9e101b`.
Para reproduzir a verificação estrutural, carregue cada linha de
`inputs.jsonl` e o objeto de `annotations.json` em um leitor JSON.
Confira 16 IDs distintos nos dois arquivos e oito grupos com dois casos.
Em cada entrada, confira que `received` e `missing` são disjuntos e que
`expected` cobre exatamente `missing`. Compare rótulos, valores recebidos e
catálogo com o arquivo fixado e os hashes com `metadata`.

Para a revisão cega, use apenas `inputs.jsonl` e a rubrica comum. Registre
os rótulos por ID e a justificativa antes de abrir as anotações. Depois
da comparação, exercício de aprendizagem: escolha um par e aponte qual
trecho sustenta a mudança ou a preservação da categoria.
