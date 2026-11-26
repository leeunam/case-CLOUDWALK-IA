# Decisões de preparação da SF2-FINAL-R1

Registro das três decisões tomadas durante a preparação pública.

Ruling: preparar o supervisor da proposta recomendada, com o worker original intacto, é uma etapa necessária do pedido de conclusão. A exposição final só será proposta com recibo concreto revisado. Custo se errado: código reversível por fixtures, sem gasto de API nem uso do teste reservado.

Ruling: as duas implementações podem começar em paralelo, atendendo ao pedido do usuário por agentes paralelos: possuem pastas e worktrees disjuntas e interface congelada no protocolo. Nenhuma consome código não integrado da outra; ligação real espera revisão e Task3. Custo se errado: retrabalho de interface identificado no QA conjunto, sem risco de vazamento do final.

Ruling: a correção2 pode acrescentar -S a -I -B antes da liberação congelada, preservando a invocação lexical do venv e atestando fontes/dependências antes de qualquer import de terceiro/.pth. Motivo: revisãoidentificou origem de import não garantida pelos RECORDs. Custo se errado: incompatibilidade debootstrap identificada nasfixtures echeckpúblico; nenhum modelo/finaléaberto.
