# UX01 — aceite do integrador

24/11/2026. Corte frontend 3e59f4a..0da3897, .worktrees/ux01-interface. Docker isolado cloudwalk_demo_ux01_integrator, API 43129 e web 45199; volumes próprios. Apenas fixture de IA, nenhuma chamada paga. Credenciais sintéticas de teste configuradas antes do primeiro boot no .env ignorado; credenciais públicas preservadas.

CLI demo up/check passou: caso 52c2f65c-f580-40ab-9ff5-779650e45a20, correlation f45d6494-ee5f-4b51-bba3-e25a16b265db, dois turnos, quatro mensagens, resolução, recibos e Kafka reconciliados.

CUA observou pela API real: login Bia; histórico persistido; supervisor corrige categoria inválida para pix com motivo e origem Supervisão; transfere caso 6a7eb4ae-b339-4d51-b732-61eec638df39 de Alex para Bia; outro responsável não pode responder; Bia envia mensagem e resolve; carteira retorna a zero. Supervisor cria fila de teste em Horizonte Negócios com equipe compartilhada e lê auditoria administrativa versão 1. Dados sintéticos somente no projeto isolado.

Layout observado em 1440x900, 1024x768, 768x1024 e 390x844. Largura do documento não excedeu a viewport em 1024/768/390. Alternar conversa/contexto mantém rascunho; referência do handoff abre a mensagem e transfere foco para message-546ce8a8-98c0-427f-a8e0-050358a001fb. Lista/conversa do simulador mantém rascunho.

Primeira checagem da correção de foco usou inadvertidamente a imagem e0e2, pois Compose web não monta fontes nem faz HMR. Não foi atribuída falha à correção. Web foi reconstruída explicitamente em 0da3897, imagem sha256:f9d787e66d3616163dde07c700783590ae1d1ddcbb5e4539e6b6416bbab643da. Nova prova CUA no simulador 390x844: Histórico > Tab > Tab > Enter seleciona caso e foco fica conversation-heading; próximo Tab chega à região Histórico da conversa; --control = #748c7f. Viewport restaurada e aba de teste fechada. CUA concluída.

Observação para triagem da revisão ampla: contexto do caso com entrada inválida exibiu código bruto invalid_input. Avaliar texto compreensível em português dentro do escopo de UX. Não há proposta de alterar backend ou regras.

29 testes e build com lock/runtime fixados constam do relatório do autor e da correção. Este aceite não mede qualidade do classificador real, desempenho de 10 mil conexões ou certificação completa de acessibilidade.

## Correção ampla e publicação

Corte final88d80be aceito pela re-review4/4sem novos achados. Web isolada reconstruída sha256:1167b24b355f387037edf9fb6b5ddf8c6dae4b253b94fe0ab3b66349a1568c9a. CUA confirmou Novo atendimento recebe foco em new-heading; rádio nativo marcado persiste; 390px sem overflow. Captura desktop final analista.jpg contém dados sintéticos do projeto isolado. Recibo tardio testado por redutor; forcedcolors inspecionado estaticamente, sem simulação de navegador.

Merge local3c00691. Publicação: build estático passou, imagem74df75f9fdbbdbc979753d8c30ef531061e4833be32961912a0047444382161d, API permaneceu Running e somente web foi recriada. HTTPS e banco verificados pelo wrapper; mesma URL mirrors-labour-crafts-characteristic.trycloudflare.com. CUA confirmou novo simulador público com caso5f81ffdd-016b-487a-af16-a8d9e258fee0 preservado com4mensagens, resolvido. Sem novas chamadas/modelos/credenciais públicas modificadas.
