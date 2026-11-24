# Task2 · F09-A · Demonstração local reproduzível

Leia primeiro AGENTS.md e CONTEXT.md. Base53c60a844006b47a97276e3f6b560d8920bb9c93, branch feat/demo-reproduzivel, worktree /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/f09-demo, já preparada. Read-only auditoria em /tmp/cloudwalk-fechamento-preflight.md. Requisitos F09/especificação/plano/conclusao-projeto.md já autorizados pelo responsável para conclusão; não pedir nova aprovação para esse escopo.

## Escopo e propriedade

Consolidar o fluxo local já existente em uma entrada de demonstração completa, preservando o Compose de desenvolvimento. Propriedade: novo compose.demo.yml, novo script/demo.py (ou script/demo com auxiliares mínimos), integration/Dockerfile e requisitos/lock Python se necessário para pinagem, docs/f09.md e README.md. Não alterar backend/frontend/contratos/SQL/classificador/runners C05/F08/R01/R02 nem compose.yml base. Se outra interface compartilhada for indispensável, informar antes. Documentação do resultado C05 atual pertence ao integrador, não a esta frente; referenciar o relatório vigente sem inventar resultado de qualidade.

O comando de demonstração deve subir DB, Kafka, setup, API, worker, frontend, outbox, ponte requests/events e mock. Reusar código/contratos existentes e rede interna, callback assinado e persistência. Portas somente loopback. Classificador explicitamente fixture (modo desabilitado também documentado), zero fornecedor real e nenhuma leitura de .env.feita.local. A UI não entra implicitamente em fixture=demo; deve conectar ao Rails real. Campo recebido válido continua bypass. Não desenvolver atendente IA real.

Segredos locais de demo em arquivo ignorado .env.demo.local, criado uma vez com permissões privadas; nunca sobrescrever um existente ou usar as chaves do usuário. Gerar segredo Rails, assinatura dos canais/ponte e credenciais sintéticas coerentes com o seed. Segredos não aparecem em logs/config imprimidos/Git. O responsável precisa de uma forma local explícita de obter o login demo. Não gravar credencial pública fixa que depois seja reutilizada no servidor. Preferir wrapper com up/status/down/logs/check, projeto próprio configurável e caminho relativo robusto. down preserva volumes; nenhuma exclusão -v automática. Manter Docker puro disponível e instruções claras. Não conectar demo à conta de fornecedor.

Congelar imagem Python usada na integração por digest verificável de fonte oficial e requisitos transitivos de forma reproduzível, preservando versões compatíveis existentes. Não fazer atualização geral de bibliotecas. Registrar origem do digest e comando de instalação validado. Bloqueio de registry ou Docker deve ser registrado, nunca chamado de aceite.

## Aceite

1. Wrapper/Compose validam configuração sem imprimir segredos e iniciam a pilha completa em projeto F09 isolado, com portas que não conflitam e volumes próprios vazios. Não tocar projetos/volumes de outras tarefas.
2. Um caso de classificação completa passa por entrada→outbox→Kafka→mock→resposta persistida e pode ter segundo turno, sem duplicação. Exercitar três canais/duas marcas quando possível; pode reutilizar verificadores canônicos, sem copiar toda a lógica.
3. Complemento fixture e revisão/correção auditada, handoff com histórico, resposta humana/espera/retomada/resolução têm roteiro executável. Persistência de um caso após reiniciar deve ser verificada com dados sintéticos do projeto isolado.
4. README deixa problema, escopo/arquitetura, pré-requisitos/comando completo, login, configuração, roteiro, testes, resultados/limites e evolução fáceis de achar; reduzir cronologia repetitiva e remeter aos relatórios históricos imutáveis. Não alegar C06/C07 ou publicação concluídas. R01/R02 corrigiram recuperação, mas a F08 antiga continua5/6.
5. Explicar em português e propor exercício simples para seguir correlation_id. Testes apropriados da entrada e pinagem; não rerodar matriz longa de carga. Usar runtime/lockfiles existentes. Registrar verificações reais e pendências.

Sem API externa de IA, .env/chaves do usuário, conta financeira, alteração de critérios ou subagentes. Pode consultar documentação/registry oficiais para pinagem. Pode usar Docker para o próprio projeto de teste, sem alterar redes/volumes existentes. O ensaio pago do integrador terminou, então não há mais janela de latência a preservar. Sem merge/push. Commit selecionado em português, Conventional Commits.

Relatório completo em /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.superpowers/sdd/conclusao-projeto/f09-report.md: base/branch/worktree/commits, implementação, comandos/saídas realmente observados, limites e reprodução/exercício. Retorne só status/SHAs/resumo de testes e preocupações. Revisão independente e integração ficam com o chat central.
