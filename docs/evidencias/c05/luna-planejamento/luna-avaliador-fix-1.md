# Task3-B · Correção dirigida 1

Mesmo autor/worktree/branch, HEAD85803430f17d5f582b26890e621746412a85db66. Leia AGENTS/RTK e o relatório luna-avaliador-review.md nesta pasta. Requisitos originais do brief continuam. Sem rede, chaves, leitura da conta real ou finais para tuning. Sem subagentes/merge/push.

Único achado importante aceito: init-account cria conta fixture antes da guarda de caminho reservado quando a conta histórica está ausente. Corrigir a ordem para a guarda Luna de caminho e identidade atuar ANTES de qualquer criação/mutação de fixture, inclusive init-account. Rejeitar também alias resolvido/symlink de diretório para o caminho reservado (sem abrir conta real); manter fixture em caminho temporário permitido. Não modificar budget.py, fontes congeladas ou defaults Qwen/R2. Preserve a guarda de identidade e de caminho real já existente.

Faça regressão focal usando Gitcommonroot/contas TEMPORÁRIOS, cobrindo alvo ausente proibido sem arquivo criado, alias resolvido, alvo existente intacto e conta fixture válida. Reexecute somente testes novos/fluxo Luna afetado e um smoke de init-account fixture R2 que assegure compatibilidade se tocar o dispatcher compartilhado. Não repetir suítes amplas já aceitas sem motivo.

Commit português Conventional selecionado. Report breve em luna-avaliador-fix-1-report.md com novoSHA, mudança, comandos/resultados e limitações. Depois haverá re-review dirigida sobre o diff desta correção, não revisão completa duplicada.
