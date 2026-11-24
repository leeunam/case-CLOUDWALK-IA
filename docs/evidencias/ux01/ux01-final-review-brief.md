# Revisão ampla única UX01

Leia primeiro este brief, AGENTS/RTK; pacote integral review-3e59f4a..0da3897.diff, ux01-brief.md, ux01-report.md, ux01-fix-1-report.md, ux01-review.md, ux01-re-review-round1.md e ux01-integrator-acceptance.md. Tudo na pasta deste brief. Apenas leitura, sem subagentes, sem nova suíte ou Docker/browser. Use evidências já produzidas, consulte código dependente pontualmente. Modelo Astra high conforme SDD final. Root manterá aplicação pública até seu aceite.

Base3e59f4ad80536b5586e91c89a2ea157bebbcb442, head0da38974da1e6d20adaf0492643e5de63172f43d, branch feat/interface-operacional, worktree /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/ux01-interface. Root main tem mudanças R4 independentes, não usar main como fonte do novo frontend.

Restrições vinculantes: usuário aprovou reorganização completa da interface operacional com identidade verde existente e referências Chatwoot/Zammad/Sidekiq; conservar funções, APIv1/Kafka/autenticação/CSRF/permissões/idempotência/expected_version/reconexão/rascunhos. Sem novos endpoints, dependências, métricas falsas ou labels de marcas hardcoded. Não adicionar Sidekiq. Sidebar por perfil, lista filtros reais/paginação, conversa central/contexto, login/simulador/configuração legíveis, mobile390 e desktop1440/1024/768. Focus/teclado/contraste/reducedmotion e estados de erro devem funcionar. Nenhum acesso a .env/chaves/conta financeira, nenhuma rede de IA paga. Sem merge/push.

Task-review e re-review aceitaram foco móvel e bordas corrigidos em0da. Root validou GUI/API real conforme acceptance. Observação para sua triagem: código bruto invalid_input apareceu no contexto em vez de mensagem em português; avaliar junto aos demais textos. Não pré-julgar gravidade. Reveja escopo inteiro apenas uma vez para consolidar achados.

Escreva ux01-final-review.md nesta pasta com SPEC e QUALITY separados; achados priorizados, linhas/trigger/efeito/correção mínima; triagem de observações/limitações. Retorne apenas status, contagem e caminho. Não implementar correções.
