# F09-A · Re-revisão dirigida

- Base da correção `973fe469dccbf4e1991dae198bdee820dd3c3e4a`.
- Commit revisado `aa3911e5d8d25c288b6a92920583c7c531c75939`.
- Branch `feat/demo-reproduzivel`, worktree `.worktrees/f09-demo`.

## SPEC

**Aprovado.** A via Docker direto lê as credenciais de `.env.demo.local`
mesmo quando o terminal contém variáveis conflitantes. As três opções
documentadas continuam funcionando. O README e o roteiro orientam a
reservar um nome de projeto por checkout ou worktree, inclusive após
`down`, e conservar o mesmo checkout, arquivo privado e projeto na
retomada.

O commit alterou apenas `README.md` e `docs/f09.md`. As demais evidências
da F09-A continuam nas referências da [revisão original](f09-review.md)
e do [relatório de execução](f09-report.md).

## QUALITY

**Aprovado. P2 e P3 encerrados.** A função documentada limpa as variáveis
do terminal em um subshell e recebe explicitamente o nome do projeto.
O roteiro explica o vínculo dos volumes PostgreSQL e Kafka com esse
nome e passa o mesmo nome no cenário de reinício.

## Verificações desta revisão

- Extraí a função do Markdown e rodei `config --quiet` em Bash e Zsh,
  nos modos fixture e desabilitado e em dois diretórios temporários.
  Os oito ensaios terminaram com código zero e saída vazia.
- Comparei, em memória, a configuração completa da função e do wrapper
  com marcadores no ambiente e um arquivo privado sintético. Os modelos
  renderizados coincidiram. A configuração carregou a credencial do
  arquivo, preservou Aurora e Horizonte e manteve as portas padrão e
  alternativas testadas.
- Com o mesmo nome de projeto, os dois diretórios renderizaram os mesmos
  nomes de volumes. Com nomes de projeto distintos, os conjuntos de
  volumes ficaram disjuntos.
- Conferi os 19 links locais do README e os sete de `docs/f09.md`,
  incluindo a âncora da imagem e das dependências Python.
  `git diff --check 973fe46..aa3911e` passou. A worktree estava limpa.

Usei configuração estática do Compose 5.1.0, com diretório e ambiente
sintéticos. A re-revisão dispensou daemon, subida de serviços e repetição
das suítes originais.
