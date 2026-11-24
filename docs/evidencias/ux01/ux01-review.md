# Revisão UX01

## SPEC

**Ajustes necessários.** Ao abrir um atendimento pelo histórico do simulador no móvel, o botão focado desaparece da tela sem transferir o foco à conversa. O novo contorno de controles tem contraste inferior a 3:1 sobre as superfícies claras. Os dois pontos afetam o aceite de acessibilidade.

Tarefa UX01, branch `feat/interface-operacional`, worktree `.worktrees/ux01-interface`. Base `3e59f4ad80536b5586e91c89a2ea157bebbcb442`, commit revisado `e0e2a0d01f6e5c7ff826a9f74fa2ed77c58ec842`.

## Pontos conferidos

- A navegação por perfil usa os filtros reais da lista e mantém marca, fila, categoria e prioridade ao trocar de área. O catálogo informa as opções e `next_cursor` controla a paginação. `frontend/src/staff/StaffNavigation.tsx:15`, `frontend/src/staff/navigation.ts:10`, `frontend/src/staff/CaseList.tsx:13`.
- Selecionar um caso na operação foca o cabeçalho da conversa. Alternar os painéis do mesmo caso mantém o componente montado. A referência do resumo revela a conversa e foca a mensagem. `frontend/src/staff/StaffPage.tsx:98`, `frontend/src/staff/StaffConversation.tsx:112`, `frontend/src/staff/staff.css:110`.
- O compositor continua exigindo `canHandle`, texto nas ações que o requerem e versão atual no comando. O mesmo controle de tentativas governa conflito, erro e confirmação. A correção e a transferência passam a montar os formulários ao abrir a seção, preservando as condições de cada ação e o bloqueio por versão. `frontend/src/staff/StaffConversation.tsx:55`, `frontend/src/staff/StaffConversation.tsx:68`, `frontend/src/staff/StaffConversation.tsx:81`, `frontend/src/staff/SupervisorActions.tsx:19`, `frontend/src/staff/SupervisorActions.tsx:147`.

## Achados

### Importantes

1. **Abrir uma conversa pelo histórico móvel perde o foco do teclado.** Em 390 px, abra “Histórico” por teclado, navegue até um atendimento e pressione Enter. O manipulador esconde a lista e não dá foco à conversa recém-aberta. Mova o foco ao cabeçalho da conversa após a troca, como a caixa do analista já faz. `frontend/src/simulator/Simulator.tsx:119`, `frontend/src/simulator/simulator.css:41`, `frontend/src/staff/StaffPage.tsx:98`.
2. **O contorno dos campos comuns fica abaixo de 3:1.** Os campos em que o contorno delimita a área de interação usam `#99ada2`. O cálculo deu 2,37:1 sobre `#fff` e 2,20:1 sobre `#f5f7f4`. Escureça o token de contorno e conserve a distinção entre borda, divisória e foco. `frontend/src/style.css:10`, `frontend/src/style.css:49`.

### Menores

- O simulador ganhou rolagem própria no histórico de mensagens, mas o contêiner ainda é um `div` genérico. O acesso por teclado depende de o navegador colocar contêineres roláveis no percurso de Tab. Use uma região nomeada e foco equivalente ao da conversa do analista e verifique Tab, Page Up e Page Down em conversas longas. `frontend/src/simulator/simulator.css:32`, `frontend/src/simulator/Conversation.tsx:57`, `frontend/src/staff/StaffConversation.tsx:156`.

## QUALITY

**Requer os ajustes de acessibilidade acima.** A divisão da caixa em navegação, filtros, lista, conversa e contexto concentra responsabilidades. Os dois novos testes exercitam os filtros de navegação. A preservação de foco e de rascunho em interação móvel depende do aceite no navegador.

O relatório do autor registra 29 testes e build aprovados com a imagem Node fixada pelo projeto. O ambiente local do autor retornou `ERR_NO_TYPESCRIPT` ao iniciar parte da suíte. A revisão não repetiu a suíte. Para conferir os trechos fora do diff, foram examinados os guardas de comando em `StaffConversation.tsx`, o bloqueio de versão em `SupervisorActions.tsx` e a semântica do contêiner em `simulator/Conversation.tsx`. A caixa autenticada, a configuração e a supervisão pela API isolada permanecem no aceite do integrador.
