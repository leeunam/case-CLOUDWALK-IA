# UX01 · Revisão final da interface operacional

Base `3e59f4ad80536b5586e91c89a2ea157bebbcb442`, versão `0da38974da1e6d20adaf0492643e5de63172f43d`, branch `feat/interface-operacional`, worktree `.worktrees/ux01-interface`. Os caminhos de código abaixo são relativos a essa worktree.

## SPEC

**Ajustes necessários.** O aceite confirma login, atribuição, autorização para responder, resolução, correção, transferência, configuração de fila, auditoria e referências ao histórico. A mudança preserva o texto ao alternar os painéis do caso aberto. Restam indicações de seleção pouco perceptíveis e uma ação de teclado sem destino de foco no simulador.

## QUALITY

**Ajustes necessários.** Os componentes reutilizam o cliente da API, a paginação e os controles de versão e de tentativas idempotentes. O pacote de 26 arquivos concentra as mudanças no frontend, nos testes de navegação e na documentação. Há também uma disputa entre a navegação e um envio em andamento, além de códigos de bloqueio expostos como mensagem operacional.

## Achados priorizados

1. **P2 · A seleção de canal e de caso depende de diferenças sutis de cor.** No simulador, escolha um canal e mova o foco para a mensagem. O rádio nativo fica transparente, e a seleção aparece somente por cores de texto, preenchimento e borda. Os contornos selecionado e comum têm contraste de 2,18:1 entre si. Na lista da operação e no histórico, abra um caso e desloque o foco. A borda selecionada `#a9c7b5` tem 1,74:1 sobre a lista `#f9faf8`, e o preenchimento selecionado tem 1,10:1 sobre a mesma superfície. Quem tem dificuldade para distinguir essas variações perde a referência visual do canal ou caso atual. Preserve um indicador marcado no canal, como o rádio nativo, e acrescente uma barra ou marca contrastante ao item atual da lista. Confira a seleção com o foco em outro controle e com cores forçadas. `frontend/src/simulator/simulator.css:22`, `frontend/src/simulator/simulator.css:23`, `frontend/src/style.css:105`, `frontend/src/staff/staff.css:32`, `frontend/src/simulator/simulator.css:8`.

2. **P3 · Um recibo atrasado fecha o histórico móvel.** Em 390 px, envie uma continuação e abra Histórico antes da resposta do envio. O recibo chama `onOpen` mesmo quando pertence ao caso já aberto. `showCase` chama `setShowHistory(false)` incondicionalmente, ocultando a lista recém-escolhida. Atualize o histórico e o identificador a partir do recibo, e reserve a troca explícita de painel para os comandos de navegação. Verifique com um envio cuja resposta chegue depois do clique em Histórico. `frontend/src/simulator/Conversation.tsx:39`, `frontend/src/simulator/Simulator.tsx:64`, `frontend/src/simulator/Simulator.tsx:95`.

3. **P3 · “Novo atendimento” remove o botão focado.** Com uma conversa aberta, acione o botão do cabeçalho por teclado. O novo formulário aparece, o botão é desmontado e nenhum elemento do formulário recebe foco. Em desktop, o histórico inteiro precede o formulário na ordem do documento. Mova o foco ao título “Novo atendimento” ou ao primeiro campo após a troca. A correção já aceita para selecionar uma conversa pelo histórico cobre outro manipulador. `frontend/src/simulator/Simulator.tsx:88`, `frontend/src/simulator/Simulator.tsx:149`.

4. **P3 · O aviso de bloqueio pode mostrar apenas um código interno.** O integrador viu `invalid_input` ao abrir um caso em revisão. A mesma expressão exibe motivos conhecidos como `agent_result_timeout` e `classifier_disabled` sem explicação. A ação de corrigir ou recuperar segue disponível, mas o operador precisa interpretar o código para entender o motivo. Apresente orientações em português para revisão e falha de integração, com uma mensagem compreensível de reserva para causas futuras. O código pode permanecer nos detalhes técnicos. `frontend/src/staff/CaseContext.tsx:48`, `backend/app/services/attendances/receive_channel_message.rb:99`, `backend/app/services/agent_integration/deliver_outbox.rb:99`, `backend/app/services/classification/configured_jev.rb:7`.

## Evidências e limites

- `ux01-integrator-acceptance.md` registra o fluxo com a API real e o Kafka isolados, a inspeção em 1440, 1024, 768 e 390 px, os rascunhos e o foco da referência do encaminhamento. Na imagem reconstruída em `0da3897`, o título da conversa recebeu foco ao abrir pelo histórico móvel, e Tab alcançou a região rolável. O contraste dos campos comuns já foi corrigido. O primeiro achado acima trata dos indicadores de seleção.
- `ux01-fix-1-report.md` registra 29 testes aprovados e build concluído com a versão de Node fixada no Dockerfile. Nesta revisão, as razões de contraste foram recalculadas com as cores do CSS. Os fluxos temporais e de foco dos achados 2 e 3 foram identificados no código. O aceite existente não exercitou essas sequências. A revisão não repetiu a execução da aplicação, da API ou da suíte.
