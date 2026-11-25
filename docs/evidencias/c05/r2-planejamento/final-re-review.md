# C05-R2 · Re-revisão dirigida da correção final

**SPEC aprovada. QUALITY aprovada. P2 e P3 encerrados.** Base `1e98c4583ed9dc073a502658125f0bcf810b7ba0`, HEAD `b19a59645342cde40c4939f4f21d05959ae7c39a`, branch `feat/r2-avaliador`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-avaliador`. O aceite cobre a preparação offline.

## P2 encerrado · Uma chamada para duas perguntas

Conferi o caminho `verify_run` → `verify_case` → `verify_observation`. Para o relatório 1.3, o verificador limita cada observação da candidata a uma requisição e exige pontuação ausente ou nula. O teste dirigido da implementação contempla erro anterior ao despacho com zero requisições. O código continua aplicando os contratos anteriores às respectivas versões de relatório.

Reapliquei em memória as observações originais de `1e98c45` ao verificador atual. `ctl-duplo` foi recusado com `r2_request_limit` e `ctl-politica` com `r2_score`. Validei o exemplo 1.3 completo pelo mesmo caminho do checker e contei os registros. São oito controles candidatos, todos com uma requisição, nenhum com pontuação e 11 perguntas no total. O controle duplo mantém as duas perguntas. O controle injetado é contabilizado separadamente.

## P3 encerrado · Origem da aprovação e do exemplo estático

Confrontei a partição e o protocolo corrigidos com a decisão de 24/11/2026. Agora ambos atribuem ao responsável a escolha da opção A para implementação offline. Os metadados de procedência correspondem aos 36 casos finais revisados por agentes, com zero aprovações humanas individuais. A autorização de gasto segue desabilitada. O relatório 1.3 identifica `1e98c45` como base de implementação do exemplo sintético estático. Conferi diretamente no Git a presença do schema 1.3 nessa revisão.

## Verificações e limites

- Inspecionei os oito arquivos do diff e o teste de contrato novo. O diff desta onda não alcança o executor, o serviço financeiro, a candidata, os casos, as revisões congeladas ou os exemplos anteriores. Os 28 hashes do lock foram verificados durante o carregamento do perfil R2 na contrachecagem acima. Não há alterações locais em arquivos rastreados.
- O relatório do implementador registra quatro testes de contrato R2, 11 testes históricos, oito de latência, nove contraprovas R2, os dois verificadores anteriores e 21 relatórios históricos com bytes idênticos. Considerei esses resultados como evidência anterior. Nesta re-revisão executei a contrachecagem dos dois registros antigos, validei o exemplo e conferi a revisão de origem. A revisão ampla anterior cobre o restante da entrega.
- Toda a conferência usou arquivos estáticos, sem fornecedor, credencial ou conta financeira real. A qualidade e a latência do Qwen na rodada permanecem sem medição e C06 segue bloqueada.
