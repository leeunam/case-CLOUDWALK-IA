# F09/F10 · Re-revisão dirigida da recuperação

Branch `feat/publicacao-demo`, worktree `.worktrees/f10-publicacao`. Revisão `0aea8212b359b5f3257e23268afa9530c65c7d04` sobre `7999b974d68c13d0211b9ea82167ee96530e86c1`. A revisão ampla da aplicação continua registrada em `app-final-review.md` sobre `b056b12`.

## SPEC

**Aprovada.** O único arquivo alterado é `docs/f10.md`. O procedimento confere a existência e as duas etiquetas dos três volumes antes de parar a origem. Registra a revisão e o ID de um atendimento com handoff relido na origem. O destino exige checkout na mesma revisão, projeto distinto e livre, ausência de arquivo privado preexistente e cópia concluída com permissões privadas. As três extrações precedem a inicialização. O comando final exige o mesmo ID de atendimento no projeto restaurado.

## QUALITY

- **P2 encerrado.** A falha simulada na extração do PostgreSQL retornou 17 e interrompeu o bloco antes das demais extrações, da subida e da verificação da aplicação. Volume de origem ausente retornou 5 antes da parada da origem. Falhas na cópia do arquivo privado e no arquivamento retornaram 23 e 19. As cópias incompletas ficaram sem o marcador de conclusão. Destino ocupado, arquivo de backup ausente ou com permissão aberta e arquivo privado preexistente impediram a restauração. O sucesso simulado executou a verificação pelo mesmo UUID e preservou o modo `0600`. Conferido nas linhas 163–195 e 212–282 do guia.
- **P3 encerrado.** As linhas 16–19 explicam como executar os exemplos sem RTK. Na simulação válida, as duas formas chegaram ao mesmo projeto e UUID. Em uma verificação adicional com o RTK instalado, `rtk proxy cat` preservou byte a byte um fluxo gzip sintético de 384 bytes.

## Verificação e limite

Comparei o pacote com `git diff -U10 7999b97 0aea821` byte a byte e confirmei o pai do commit, o escopo de um arquivo, o resultado limpo de `git diff --check` e a worktree limpa. Revisei e reexecutei o verificador temporário do autor com ambiente vazio e PATH mínimo. Ele extraiu os blocos literais do guia, validou a sintaxe e executou os cenários acima com dados temporários e Docker simulado. Todos passaram.

A correção está aprovada para integração. A prova real de cópia e restauração em volumes isolados, seguida da releitura do atendimento, permanece com o integrador. As demais conclusões e limites da revisão ampla continuam válidos.
