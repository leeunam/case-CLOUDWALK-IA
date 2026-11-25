# F10 · Correção final do roteiro de recuperação

- Revisão integrada `b056b120a4d4878ad398248c6207e44b653b683e`.
- Base autoral `7999b974d68c13d0211b9ea82167ee96530e86c1`, commit `0aea8212b359b5f3257e23268afa9530c65c7d04`, branch `feat/publicacao-demo`.
- Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/f10-publicacao`.
- Alteração exclusiva em `docs/f10.md`.

## Pontos atendidos

- P2. Cópia e restauração rodam em subshells que interrompem a sequência em caso de erro. A cópia confirma previamente existência e etiquetas dos três volumes, relê o atendimento pelo ID, para a pilha e copia para uma pasta privada exclusiva. Registra projeto, revisão e ID, com marcador de conclusão criado após as três cópias.
- P2. A restauração confere proprietário e permissões dos arquivos, marcador de conclusão, revisão, ID e disponibilidade de checkout/projeto/volumes de destino. Copia o arquivo original sob `umask 077` com proteção contra sobrescrita. Inicializa o destino somente depois das três extrações. `script/check_publish.py --case-id` exige o atendimento original. O guia explica como encerrar e limpar apenas o ensaio.
- P3. O guia informa que RTK é opcional e descreve a equivalência para execução direta.

## Verificação executada

- `rtk proxy python3 -B /tmp/cloudwalk-f10-final-check.py` extraiu os dois blocos literais do Markdown, executou `sh -n` e simulou Docker/Git/aplicação em diretórios descartáveis. O pré-requisito Python da restauração, as cópias, os modos e os arquivos de controle foram executados de fato sobre fixtures locais.
- O terceiro volume de origem ausente devolveu 5 antes de verificar ou parar a aplicação de origem, criar uma pasta de backup ou executar tar. A cópia do arquivo privado falhou com 23 e o tar da origem falhou com 19, ambos sem seguir para arquivamentos posteriores, marcador ou confirmação de conclusão.
- A extração PostgreSQL no destino falhou com 17, após criar apenas o primeiro volume, sem extrações posteriores, `up` ou verificação. Volume de destino ocupado impediu todas as criações. Arquivo ausente ou com modo `0644` no backup impediu operações Docker. Arquivo privado preexistente no checkout de destino permaneceu intacto.
- A simulação válida criou os três destinos, copiou o arquivo privado para modo `0600` e chamou `up` seguido de `check_publish.py --case-id` com o mesmo UUID salvo. Repeti a restauração válida com a tradução documentada dos prefixos RTK.
- `rtk proxy docker volume inspect --format` confirmou as etiquetas no trio isolado `cloudwalk_publish_f10`. `rtk proxy docker volume ls --filter name=^cloudwalk_publish_f10_postgres_data$ --format` confirmou o filtro de nome exato. Essas consultas foram somente leitura. `rtk git diff HEAD^ HEAD --check` passou e a worktree ficou limpa.

## Limites

A prova de falhas e da sequência válida usou simulação. A cópia e restauração reais, com releitura do atendimento no projeto novo, ficam com o integrador. O projeto `cloudwalk_publish_integrator` permaneceu intocado. A verificação desta rodada foi dirigida ao roteiro e não iniciou túnel nem suíte de aplicação.
