# F10-B · Registro de execução

Publicação de referência em 25/11/2026: `https://newbie-aqua-stem-reveal.trycloudflare.com`. Horários em UTC. Os itens de preparação abaixo independem dos IDs do manifesto.

| Hora (UTC) | Origem e método | Caso | Esperado | Observado |
| --- | --- | --- | --- | --- |
| 16:26–16:27 | Computador de origem, terminal restrito, `curl` HTTPS em `/analista` | — | Receber a página | Falha de resolução de nome, sem resposta HTTP. |
| 16:27–16:32 | Computador de origem, terminal restrito, GET de saúde em `127.0.0.1:18443` | — | Alcançar HTTPS local | A abertura do socket foi impedida. O acesso ao socket Docker para leitura também foi negado. |
| 16:27–16:32 | Computador de origem, navegador integrado, abertura de `/analista` na URL pública | — | Tela de login do frontend | Exibiu “Entrar na operação”, campos E-mail e Senha e botão Entrar. Sessão anônima. |
| 16:32–16:33 | Worktree F10-B, leitura do seed, controladores de casos e sessão, política de visibilidade, canal e consumidor do frontend na base `81d5bf1` | — | Bia vinculada a Aurora, Cris e Alex às duas marcas | Vínculos confirmados **no seed**. A visibilidade do analista deriva das filas das suas equipes. A conferência efetiva exige login. |
| 16:32–16:33 | Worktree F10-B, `node frontend/test/cable.test.mjs` com Node 26.13.0 | Socket simulado pelo teste | Assinatura do caso, reconexão e comportamento após recusa | 3 testes passaram. O Node 22 do sistema havia parado antes dos testes por falta de suporte a TypeScript. |
| 16:35 | Worktree F10-B, teste do paginador em memória | Coleção sintética de teste | Visitar a segunda página e detectar repetição de cursor | 2 controles passaram. |
| 16:36 | Worktree F10-B, observador de assinatura com socket simulado em memória | Identificador sintético | Distinguir confirmação, rejeição e erro de transporte, ignorando quadro de outro identificador | 3 controles passaram. |
| 16:37 | Worktree F10-B, `git bundle verify`, `git show` e execução do verificador com o commit `090f67bb23e141a1473310ee9954ea6e125215e7` | Aurora `ad4a4699-5d96-4cce-a248-96b3568447fc` e Horizonte `32ab943b-2bea-428f-adb7-a802fe53bfaf` | Identificar os casos e iniciar três sessões independentes | Manifesto e IDs conferidos. Chromium encerrou antes do primeiro login (`TargetClosedError`, diagnóstico local `setsockopt: Operation not permitted`). Zero sessões autenticadas e zero consultas de caso nesta tentativa. |

## Estado do aceite

A execução autenticada dos dois casos identificados requer um processo com acesso ao HTTPS e ao WebSocket da publicação. A tela anônima, o seed e os testes locais não fornecem resultados observados para a matriz de perfis. O registro por dados móveis anterior a esta tarefa cobre a abertura da página. Falta a comparação do mesmo caso Horizonte em sessões independentes de Bia e Cris por outra rede.

[Matriz e reprodução](../../../f10-isolamento-marcas.md)
