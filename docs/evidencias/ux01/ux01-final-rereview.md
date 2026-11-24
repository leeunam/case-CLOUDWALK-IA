# UX01 · Re-revisão das quatro correções

**SPEC aprovado. QUALITY aprovado.** Os quatro achados estão atendidos. A inspeção do patch não identificou regressões nos fluxos alterados.

Base `0da38974da1e6d20adaf0492643e5de63172f43d`, commit `88d80bee4b0be35469377fa9bbea958ce97d666b`, branch `feat/interface-operacional`, worktree `.worktrees/ux01-interface`.

| Achado | Situação | Evidência no commit |
| --- | --- | --- |
| Seleção de canal e atendimento | ADDRESSED | O canal exibe o rádio nativo marcado. O item atual ganha um visto nos dois históricos, com `ButtonText` em cores forçadas. As duas listas aplicam `aria-current` apenas ao caso selecionado. `frontend/src/simulator/simulator.css:23`, `frontend/src/style.css:106`, `frontend/src/staff/CaseList.tsx:28`, `frontend/src/simulator/Simulator.tsx:129`. |
| Recibo tardio | ADDRESSED | O retorno do envio atualiza o histórico. O redutor preserva o painel escolhido, inclusive ao receber o ID de um atendimento novo, e ignora a troca de ID se a seleção já mudou. A abertura explícita de caso continua levando à conversa. `frontend/src/simulator/Conversation.tsx:42`, `frontend/src/simulator/Simulator.tsx:67`, `frontend/src/simulator/navigation.ts:7`. |
| Foco em “Novo atendimento” | ADDRESSED | O botão abre o formulário, o React conclui a atualização e o título com `tabIndex={-1}` recebe foco quando o botão sai da tela. A seleção pelo histórico conserva a mesma regra para o título da conversa. `frontend/src/simulator/Simulator.tsx:72`, `frontend/src/simulator/Simulator.tsx:87`, `frontend/src/simulator/Simulator.tsx:150`, `frontend/src/simulator/navigation.ts:19`. |
| Motivos de bloqueio | ADDRESSED | O aviso traduz `invalid_input`, `classifier_disabled` e `agent_result_timeout`. Falhas de entrega e códigos futuros recebem uma orientação em português de acordo com o estado. O código de diagnóstico fica em “Registro do caso”. `frontend/src/staff/blockingReason.ts:13`, `frontend/src/staff/blockingReason.ts:31`, `frontend/src/staff/CaseContext.tsx:39`, `frontend/src/staff/CaseContext.tsx:51`. |

O relatório da correção registra 34 testes aprovados e build concluído com a imagem fixada. Os novos testes cobrem a ordem de chegada do recibo, a seleção posterior, a decisão de mover o foco e os textos de bloqueio. O teste de foco usa controles simulados. Esta revisão foi estática. A inspeção dirigida no navegador pertence ao aceite do integrador.
