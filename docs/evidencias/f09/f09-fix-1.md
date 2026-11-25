# F09-A · Correção consolidada round1/5

Fonte973fe469dccbf4e1991dae198bdee820dd3c3e4a, mesma branch/worktree F09. Leia f09-review.md neste SDD raiz. Escopo apenas os dois achados documentais abaixo. Não alterar código/Compose/contratos/segredos/pins para contornar um problema do roteiro. Sem API IA, env/contareal, subagentes, merge/push.

P2: a alternativa Docker direto docs/f09.md95–105 dá precedência às variáveis do shell, ao contrário do wrapper. Ajustar a função documentada para sanitizar explicitamente as variáveis conflitantes do ambiente, mantendo as opções suportadas de portas e modo. Usar uma forma que preserve os valores do arquivo privado e as duas marcas seed; não imprimir segredos. Alternativamente limitar a alternativa a terminal limpo com instrução verificável inequívoca, mas a função equivalente é preferível para reprodução. Regressão dirigida com marcadores exportados e Compose configquiet deve confirmar equivalência. Sem rerodar stack/suites intactas.

P3: explicar que nome de projeto, checkout, arquivo privado e volumes pertencem ao mesmo conjunto, mesmo depois de down. Usar projectnames distintos ao alternar checkouts ou worktrees; não sugerir isolamento apenas para duas demos simultâneas. Ajustar docs e README somente onde necessário para consistência; não adicionar gerenciador de identidades/projetos ou apagar volumes.

Atualizar f09-report.md com apêndice de correção, comandos reais e resultado da prova de precedência/nomenclatura. Commitselecionado emportuguês; retorno curto comSHA. Re-review dirigida dos dois achados e links relacionados, não novaampla.
