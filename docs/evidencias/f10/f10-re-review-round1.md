# F10-A · Re-revisão da primeira correção

- Base `7b30c4eb868a01d1b4d4d85a0b3e1126c51e6015`.
- Revisão `7999b974d68c13d0211b9ea82167ee96530e86c1`.
- Branch `feat/publicacao-demo`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/f10-publicacao`.

## SPEC

**Aprovada.** O commit altera apenas `docs/f10.md`. O guia oferece uma parada de emergência independente da configuração privada e explica como identificar, separar e retomar as instalações pelos respectivos projetos e volumes.

## QUALITY

1. **P2 fechado.** `docs/f10.md:108–143` pede o nome exato do projeto e mostra o ID completo, o nome e as duas etiquetas do contêiner. O trecho de parada exige que a consulta com ID, projeto e serviço `cloudflared` devolva exatamente o ID informado. A consulta e a parada usam o Docker diretamente. O procedimento conserva o ambiente local e os volumes, e a recuperação da configuração usa o arquivo original com modo `0600`.
2. **P3 fechado.** `docs/f10.md:22–44` orienta a escolher um projeto exclusivo, conferir também os volumes de instalações paradas e retomar cada instalação com seu checkout, nome e arquivo originais. Os comandos passam o projeto explicitamente. A cópia offline usa os volumes do projeto selecionado, e a restauração usa um projeto novo.

## Verificações desta re-revisão

- Confirmei commit, pai, escopo de um arquivo, igualdade com o pacote de patch, `git diff --check` e worktree limpa.
- Validei a sintaxe dos blocos shell com `sh -n`. Executei os blocos de emergência com Docker simulado em diretório temporário, primeiro sem arquivo privado e depois com um arquivo sintético `0644`. O ID completo do contêiner correto foi o único enviado a `docker stop`. ID vazio, ID abreviado, o serviço `api` do mesmo projeto e o serviço `cloudflared` de outro projeto foram recusados nos dois cenários. O [relatório do executor](f10-report.md) registra também o teste dos filtros e da parada com contêineres descartáveis sem rede.
- Com configuração sintética em memória, `docker compose config` retornou os mesmos três volumes ao repetir um nome de projeto e volumes disjuntos para outro nome. A revisão foi dirigida aos dois achados. Os testes gerais e a pilha permaneceram fora da rodada, e o aceite público segue com o integrador.
