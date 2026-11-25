disposition: fix

## persistence

UX02, base `1adc941`, HEAD `540f975`, branch `feat/estilo-cloudwalk`, worktree `.worktrees/ux02-cloudwalk`. As cinco capturas do HEAD mostram conteúdo carregado. O pacote contém estilos, fonte, licença e documentação. A estrutura de interação da UX01 permanece reconhecível nas cinco telas.

**SPEC — ajuste necessário.** A aba ativa da configuração perde legibilidade quando o ponteiro permanece sobre ela. **QUALITY — ajuste necessário.** O conflito entre duas regras de CSS é reproduzível pela especificidade dos seletores. Os três P3 da revisão dirigida ficam abaixo. O aceite do integrador registra a prévia em 1440 e 390 px. Os 34 testes e o build passaram segundo a execução registrada no commit.

## fidelity

- **TYPE.** Os títulos compactos e os pesos intermediários mantêm nome do caso, autor e texto da mensagem distinguíveis. Gabarito é a aproximação livre declarada da Cera Pro. O integrador confirmou a família CSS e os bytes da fonte servida. O navegador usado para a inspeção não identificou a face efetivamente desenhada.
- **MATERIAL.** O branco quente das ações “Entrar”, “Enviar mensagem” e “Criar fila” acompanha a referência. Campos têm contorno próprio. A tela de configuração mostra a aba “Filas” ativa em repouso e a caixa de atendimento mostra o visto do caso selecionado.
- **GROUND.** Navegação quase preta, canvas carvão e painéis grafite dão continuidade às cinco superfícies. O símbolo de três barras identifica o Help desk. O uso de âmbar e verde em estados acompanhados de texto preserva a leitura operacional.

## ceiling

A grade de desktop deixa lista, conversa e contexto simultaneamente visíveis. A 390 px, as mensagens são legíveis e o contexto fica ao alcance do botão “Ver contexto”. O seletor superior corta o fim de “Caixa de atendimento”, cujo título completo aparece logo abaixo. É uma limitação de espaço do cabeçalho existente. As capturas estáticas mostram os estados em repouso. O achado de hover abaixo resulta da leitura conjunta do componente e das folhas de estilo.

## material_fixes

- **P2 · Bloqueia o aceite.** `frontend/src/configuration/ConfigurationPanel.tsx:131` atribui a classe `primary` à aba ativa. Em hover, `frontend/src/style.css:84` tem maior especificidade que `frontend/src/configuration/configuration.css:10` e troca o fundo para branco. O texto e a faixa inferior continuam em `#f0efed`, a **1,15:1**. Em Configuração operacional, basta selecionar uma aba com o mouse e manter o ponteiro sobre ela. Manter o fundo grafite no hover da aba ativa com uma regra local, por exemplo `.configuration-tabs button[aria-pressed="true"]:hover`. Verificar o rótulo e a faixa antes e depois de mover o ponteiro.
- **P3 · Acessibilidade.** A faixa ativa em `frontend/src/staff/staff.css:8` e `frontend/src/configuration/configuration.css:10` depende de sombra interna, suprimida em cores forçadas. Adicionar um indicador de borda em cor de sistema nesse modo. Convém aproveitar o ajuste da aba para tratar ambos os indicadores.
- **P3 · Documentação.** O raio secundário e a cor do texto ativo em `DESIGN.md:69` e `DESIGN.md:81`, além dos pesos em `.impeccable/design.json:44` e `:60`, divergem do produto. Alinhar as amostras ao raio de 0,65 rem, ao branco da navegação ativa e aos pesos 550 e 650.
- **P3 · Amostra de seleção.** Em `.impeccable/design.json:51`, o exemplo de item atual aparece como item comum. Incluir `aria-current` e o visto que já aparece na caixa real.

## keep

Preservar a densidade da caixa, o alinhamento e os rótulos de autoria das mensagens, a distinção entre ações primárias e secundárias e o ícone próprio. O visto, a faixa da navegação e a aba em repouso são visíveis nas capturas. A revisão dirigida confirmou o hover distinto nas listas, o contraste da barra de rolagem e a limpeza da licença.
