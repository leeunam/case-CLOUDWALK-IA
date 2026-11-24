# UX01 · Correção consolidada da revisão ampla

Base `0da38974da1e6d20adaf0492643e5de63172f43d`. Commit `88d80bee4b0be35469377fa9bbea958ce97d666b`. Branch `feat/interface-operacional`, worktree `.worktrees/ux01-interface`, limpa após o commit.

| Achado | Correção |
| --- | --- |
| Seleção de canal e atendimento | O rádio nativo permanece visível ao lado do canal. A classe compartilhada das listas mostra um visto no caso selecionado. O traço mede 6,882:1 sobre o preenchimento da seleção. Em cores forçadas o visto usa a cor de texto de botão do sistema. |
| Recibo tardio | A navegação do simulador distingue seleção explícita, troca de painel e recibo de envio. O recibo atualiza o histórico, preserva o painel escolhido e só pode atualizar o identificador se o caso de origem continuar selecionado. |
| Foco em novo atendimento | O comando abre o formulário e, após a atualização do React, foca seu título. A seleção por histórico mantém a transferência de foco ao título da conversa quando o botão escolhido fica oculto. |
| Motivos de bloqueio | O contexto apresenta causas de classificação, integração, capacidade e atribuição em português. Revisão e falha de integração indicam o que a supervisão pode fazer. Códigos futuros têm orientação por estado. O diagnóstico bruto permanece dentro dos detalhes do registro. |

## Verificação

Na raiz da worktree, os seguintes comandos usaram a imagem construída com o Dockerfile fixado do frontend e o código e os testes atuais montados para leitura.

```sh
docker run --rm --network none \
  --mount "type=bind,source=$PWD/frontend/src,target=/app/src,readonly" \
  --mount "type=bind,source=$PWD/frontend/test,target=/app/test,readonly" \
  cloudwalk-ux01-web:accept npm test
docker run --rm --network none \
  --mount "type=bind,source=$PWD/frontend/src,target=/app/src,readonly" \
  --mount "type=bind,source=$PWD/frontend/test,target=/app/test,readonly" \
  cloudwalk-ux01-web:accept npm run build
git diff --cached --check
```

Os 34 testes passaram. Cinco novos testes cobrem chegada atrasada de recibo após abrir o histórico, troca de caso enquanto o envio aguarda confirmação, navegação ao formulário, decisão de transferência de foco e mensagens de bloqueio conhecidas e futuras. O teste de foco usa controles simulados. TypeScript e Vite 8.3.8 processaram 59 módulos. A verificação de whitespace passou antes do commit.

O cálculo de contraste usou a luminância relativa sRGB de `#155c49` e `#e7f2eb`. A inspeção visual do rádio e do visto, inclusive com cores forçadas, e a confirmação por teclado no navegador da web isolada ficam para o integrador após a reconstrução.

## Exercício

Abra um atendimento pelo histórico, acione “Novo atendimento” com Enter e confirme o foco no título do formulário. Selecione um canal e mova o foco para Mensagem. O rádio marcado deve continuar identificável. Na caixa de supervisão, abra um caso em revisão e confira a orientação no contexto e o código em “Registro do caso”.
