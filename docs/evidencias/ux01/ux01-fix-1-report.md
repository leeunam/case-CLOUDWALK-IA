# UX01 · Correção de acessibilidade

Base `e0e2a0d01f6e5c7ff826a9f74fa2ed77c58ec842`, commit `0da38974da1e6d20adaf0492643e5de63172f43d`. Branch `feat/interface-operacional`, worktree `.worktrees/ux01-interface`, limpa após o commit.

Escolher um atendimento no histórico atualiza a seleção e a visibilidade do painel no mesmo evento. Quando o botão que iniciou a ação fica oculto, o título “Conversa” recebe foco. A decisão usa a visibilidade real do botão após a atualização do React. A rolagem das mensagens aceita foco por Tab e tem o nome acessível “Histórico da conversa”.

O token `--control` passou a `#748c7f`. O cálculo com luminância relativa sRGB a partir dos tokens do CSS deu 3,621:1 sobre `--paper` e 3,361:1 sobre `--canvas`. A tabela de tokens de DESIGN.md acompanha a alteração.

## Verificação executada

Os dois comandos abaixo foram executados na worktree com o código atual montado para leitura e o runtime da imagem da UX01 construída com o Dockerfile fixado do repositório.

```sh
docker run --rm --network none --mount "type=bind,source=$PWD/frontend/src,target=/app/src,readonly" cloudwalk-ux01-web:accept npm test
docker run --rm --network none --mount "type=bind,source=$PWD/frontend/src,target=/app/src,readonly" cloudwalk-ux01-web:accept npm run build
```

Os 29 testes passaram. TypeScript e Vite 8.3.8 concluíram o build de 57 módulos. `git diff --cached --check` passou.

## Exercício de teclado

Em 390 px, abra Histórico com o teclado, selecione um atendimento e pressione Enter. Confira o foco no título “Conversa”. Navegue com Tab até a região “Histórico da conversa” e use Page Down e Page Up quando houver mensagens suficientes para rolar. O controle “Ver atendimento anterior” pode entrar no percurso de Tab antes da região. Em desktop, ao abrir um caso com ambas as colunas visíveis, o botão escolhido mantém o foco. O aceite no navegador do ambiente 45199 fica com o integrador.
