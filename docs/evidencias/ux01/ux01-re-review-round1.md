# Revisão dirigida UX01 · rodada 1

## SPEC

**Aprovado.** O patch resolve os dois achados de acessibilidade e torna a região de mensagens do simulador navegável por teclado.

- A seleção pelo histórico aplica a troca de painel e de caso antes de inspecionar o botão. Se a lista ficou oculta, o título “Conversa” recebe foco. Com a lista visível, o botão conserva o foco. O código corre apenas no evento de abrir pelo histórico. A seleção continua usando o estado que atualiza o parâmetro `case` da URL. `frontend/src/simulator/Simulator.tsx:70`, `frontend/src/simulator/Simulator.tsx:129`, `frontend/src/simulator/Conversation.tsx:49`, `frontend/src/useOpenCase.ts:6`.
- O contêiner rolável pode receber foco por Tab e tem nome acessível “Histórico da conversa”. `frontend/src/simulator/Conversation.tsx:58`.
- Recalculei o contraste do contorno `#748c7f`. O resultado foi 3,621:1 sobre branco e 3,361:1 sobre o canvas. O guia visual registra o token novo. `frontend/src/style.css:10`, `DESIGN.md:25`.

## QUALITY

**Aprovado.** O patch é restrito à seleção do histórico, à semântica da região de mensagens e ao token de contorno. A revisão estática não encontrou achados residuais. O autor reportou 29 testes e build aprovados com a imagem Node fixada pelo projeto. A conferência do foco e da rolagem em navegador, junto com a API isolada, segue com o integrador.

Base `e0e2a0d01f6e5c7ff826a9f74fa2ed77c58ec842`, commit `0da38974da1e6d20adaf0492643e5de63172f43d`, branch `feat/interface-operacional`, worktree `.worktrees/ux01-interface`.
