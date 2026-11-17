# Plano de execução e verificação do MVP

Este backlog usa a [especificação](especificacao-mvp.md) como contrato de produto. O horizonte de quatro semanas segue a estimativa do TAPI. Datas e dedicação semanal serão ajustadas à agenda real. Os checkpoints semanais são internos. A primeira entrega apresentável inclui atendente simulado via broker, complemento pelo Jev, experimento e resultados documentados.

## 1. Ordem de trabalho

| Etapa | Entregas internas | Evidência para avançar |
| --- | --- | --- |
| Semana 1 | F01 e F02. Contratos de versão 1 e caminho mínimo de entrada até a resposta da IA. | Subir o ambiente, abrir caso por webhook, ver o evento no broker e ler a resposta persistida. Reentregar a mensagem de entrada sem criar cópia. |
| Semana 2 | F03, F04 e início de F05 em paralelo após F02. | Escalar um caso preservando contexto, distribuir e retomar. Passar entradas válidas, ausentes e inválidas pela classificação. |
| Semana 3 | Terminar F05, F06 e F07 e preparar F08. | Usar a interface para percorrer IA, handoff, espera e retomada em duas marcas. Alterar uma regra pela interface e conferir o efeito e a auditoria. |
| Semana 4 | F08 e F09. Reservar o fim para integração, verificação e apresentação. | Repetir roteiro do zero, rodar os experimentos, registrar resultados e revisar o README. |

Os marcos são sequenciais. Tarefas dentro de um marco podem avançar em paralelo conforme as dependências. O primeiro corte demonstra um fluxo real ponta a ponta e serve de base para a interface e as outras regras.

## 2. Tarefas prontas para virar issues

| ID | Tarefa e saída esperada | Depende de | Aceite local |
| --- | --- | --- | --- |
| F01 | Base do monorepo, Compose, PostgreSQL, RabbitMQ, Rails, React e contratos. Entregar `compose.yml`, `docs/contratos/`, fixtures versionadas, seeds mínimos e convenções de módulos. Fechar modelo de dados inicial, versões do runtime e ordem dos bloqueios com o responsável. | — | Ambiente sobe com um comando, API e broker respondem, contratos trazem exemplos de sucesso/erro e o seed instala sem duplicar. |
| F02 | Primeiro fluxo completo com webhook de canal, persistência, ponte, broker, mock, webhook de retorno e leitura da conversa. Incluir o backend mínimo de sessão e credenciais sintéticas para acessar as leituras protegidas. Cobrir também resposta, resolução e histórico em dois turnos. | F01 | Um caso válido via chat percorre o broker, recebe resposta, pode continuar e resolver. Sessão autenticada permite ler o histórico autorizado. IDs permitem seguir o caminho e reentrega preserva um único efeito. |
| F03 | Handoff e atendimento humano com perfil, carteira, menor carga, troca de marca, espera, retomada e transferências. Publicar operações de leitura e alteração do caso e serviços de elegibilidade. | F02 | Resumo e contexto chegam ao humano, capacidade e carteira continuam corretas em retomada e em disputa pela última vaga. |
| F04 | Classificador Jev, fila de revisão, falhas e correção. Entregar adaptador HTTP com modo fixture para execução local sem chave e teste do adaptador real com chave. | F02 | Apenas campos ausentes geram perguntas ao Jev. Campo válido permanece. Inválido, abstenção e timeout aparecem em revisão. Configuração de demonstração com credencial executa pelo menos um complemento real. |
| F05 | React para simulador, caixa e conversa, usando fixtures contratuais no início e API real no fim. Incluir chat com atualização e recuperação após reconectar, e histórico assíncrono de WhatsApp e e-mail. | F01 para UI com fixtures. F02–F04 para integração. | Cliente envia pelos três canais simulados. Analista consulta e responde caso escalado, muda para aguardar e resolve. Controles e erros refletem as permissões do servidor. |
| F06 | Configuração editável de marcas/equipes, filas, regras, catálogo e perfis. Incluir revisão de classificação, consulta de falhas e ações de recuperação para supervisor. | F03 e F04 para integrar. F01 para fixtures de UI. | Supervisão cria uma fila, vincula duas equipes autorizadas, muda regra e perfil, corrige um caso e verifica auditoria. Vínculo inválido é bloqueado. |
| F07 | Robustez e rastreamento ponta a ponta, incluindo autenticação de integrações, isolamento de marcas, reentregas, falhas e recuperação. | F02–F06 para prova completa. Harness pode começar em F01. | Desconectar broker, reentregar callback e tentar acesso cruzado em API e WebSocket. Verificar backlog recuperado, ausência de efeito duplicado e isolamento. |
| F08 | Experimento reproduzível, gerador e conjunto sintético. Coletar latência, vazão, backlog, erros, capacidade e indicadores do Jev. | F02 para ensaio da carga, F03/F04 para políticas e F07 para resultados. | Scripts e parâmetros permitem repetir o experimento. Relatório liga hipóteses a resultados e limitações. |
| F09 | README, roteiro da apresentação e verificação final em instalação limpa. | F01–F08 | Outra pessoa consegue rodar a demo e repetir o ensaio seguindo somente os arquivos do repositório. |
| F10 | Publicação em servidor, caso a entrega inclua uma URL acessível ao avaliador. Preparar configuração de implantação e acesso de demonstração. | F01 para preparar a configuração. F09 para validar a publicação. | Abrir a URL por outra rede, acessar com o perfil de demonstração, percorrer o fluxo com a IA e o handoff humano, reiniciar a aplicação e verificar que os casos persistem. |

No F01, congelar as rotas REST em OpenAPI e os envelopes em JSON Schema, incluindo nomes, estados, tipos, exemplos e semântica de reentrega. Cobrir exemplo de regra e perfil, erro de versão, caso que a IA resolve, handoff, campos ausentes e evento atrasado. Cada revisão de contrato atualiza as fixtures e identifica os consumidores antes de integrá-la. O seed demonstra duas marcas, três equipes, quatro filas, ao menos três analistas e um supervisor. Perfis do seed incluem o caso urgente exclusivo, a combinação mista e cobertura das categorias encaminhadas às filas de demonstração.

### Coordenação e aprendizagem

Manter especificação, decisões e contratos versionados no Git. Usar issues para responsável, dependência, progresso, pull request e evidência de aceite quando o remoto for usado. O Markdown local serve de backlog inicial e funciona em qualquer checkout. Um arquivo ignorado pelo Git pode guardar anotações pessoais. Seu conteúdo só influencia o trabalho compartilhado depois de entrar no contrato ou na issue correspondente.

- Começar com até dois trabalhos de implementação simultâneos e o responsável como integrador. Usar branches ou worktrees distintas. Após F01, a interface pode trabalhar com fixtures enquanto outro agente constrói o caminho F02. Após F02, F03 e F04 podem avançar em paralelo; dividir a interface em cliente/conversa e administração apenas se rotas e arquivos tiverem responsáveis claros.
- Integrar mudanças de schema, seed, Compose, contratos e transições compartilhadas sob um responsável por vez. Em F03 e F04, dividir o motor de elegibilidade e atendimento humano de um lado, e o adaptador Jev e revisão de classificação do outro. Ambos chamam as transições combinadas em F01. O integrador incorpora alterações comuns de estado e schema antes de unir as duas frentes.
- Entregar ao agente o ID da tarefa, o trecho do contrato, dados de exemplo, testes esperados e limites de edição. No retorno, exigir resumo da mudança, testes executados com resultado, uma forma de reproduzir e dúvidas pendentes. O integrador executa o aceite da fatia e ao menos uma passagem ponta a ponta quando as interfaces se encontram.
- Para estudar Rails durante a execução, o responsável implementa ou revisa com o agente a primeira passagem `rota → controller → regra de domínio → persistência`. Antes de integrar F03, explicar com um caso de exemplo como duas atribuições concorrentes disputam a última vaga. Na apresentação, traçar um evento real do webhook até o retorno do mock.

### Passagem de trabalho entre agentes

As instruções de entrada e isolamento estão no [AGENTS.md](../../AGENTS.md).
Na primeira mensagem a cada agente externo, pedir a leitura desse arquivo e
informar a tarefa e o commit-base. Na retomada da mesma tarefa, reutilizar a
worktree já associada a ela.

1. Criar um commit inicial com o planejamento antes de abrir branches ou worktrees. Em F01, integrar os contratos, as fixtures e o mapa de módulos numa base comum. Cada tarefa começa desse ponto ou do último marco integrado.
2. Depois de F01, uma frente assume Rails, ponte e mock para F02. Outra assume React para F05 com fixtures. A interface começa pelo simulador e a conversa. Integração com o atendimento humano entra quando a API correspondente estiver pronta.
3. Depois de F02, dividir o backend entre F03 e F04. F03 assume elegibilidade, carteira e ações humanas. F04 assume o cliente Jev, classificação e revisão. O integrador define e incorpora previamente as mudanças em schema, estados e serviços compartilhados. F06 pode preparar a interface com fixtures e integra as operações de configuração quando as regras estiverem disponíveis.
4. Em cada tarefa, registrar o que o responsável quer aprender. Em F02, acompanhar uma mensagem desde o controller até o broker. Em F03, prever o resultado de uma disputa de capacidade e conferir no teste. Em F04, simular campo válido, ausente e inválido antes de chamar a API externa. O agente entrega o comando de verificação e indica os arquivos a ler. O responsável roda o teste e modifica um exemplo ou fixture antes de integrar.

Para cada tarefa delegada, informar o ID, o commit de partida, os contratos e arquivos envolvidos, o cenário de aceite e o exercício de revisão. Se a tarefa precisar alterar um arquivo compartilhado, o integrador incorpora a alteração na base comum antes de as frentes consumirem a mudança.

## 3. Aceite da entrega

| Cenário | Resultado verificável |
| --- | --- |
| Caso válido em cada canal | Três entradas aparecem com origem correta. Zero chamadas ao Jev. O mock responde via broker. Chat mostra a atualização e o cliente assíncrono reencontra a resposta ao voltar. |
| Classificação parcial e vazia | Um campo ausente gera uma pergunta e preserva o outro. Dois ausentes geram duas perguntas. Valor inválido não chama Jev. Saída inválida, abstenção, falha e indisponibilidade aparecem em revisão. Uma correção encaminha uma vez. |
| Memória e handoff | Segundo turno recebe a mensagem anterior. Mock escala com resumo e referências. Humano vê o contexto e o histórico sem duplicar caso. Resposta do mock atrasada após handoff é rejeitada e auditada. |
| Configuração e acesso | Novo caso segue regra editada da própria marca. Duas equipes autorizadas podem atuar na mesma fila. Usuário sem acesso à marca não lista, abre, altera ou recebe dados de suas conversas. |
| Distribuição | Entre candidatos que cabem no perfil, vence quem tem menos ativos e depois quem está há mais tempo sem receber. Sem encaixe, o caso aguarda e o motor tenta o próximo elegível. Aguardar 15 minutos muda a precedência de seleção e conserva a prioridade de capacidade. |
| Combinações | Urgente Pix sozinho é permitido. Urgente Pix + básico é rejeitado. Urgente Maquininha + básico Maquininha cabe. Três básicos Pix + um intermediário Repasses cabem. Acrescentar uma quinta tarefa ou somar duas alternativas é rejeitado. |
| Carteira e marcas | Sete atribuições não cabem no teto seis. Se os seis clientes voltarem juntos, os mesmos seis casos permanecem na carteira e só os que encaixam ficam ativos. Troca de marca espera os ativos concluírem ou serem transferidos. Pendência de outra marca aguarda retomada. |
| Concorrência e alterações | Duas atribuições disputam uma vaga e somente uma entra. Perfil reduzido bloqueia novas atribuições enquanto houver excesso. Revogação remove acesso imediatamente. Transferência e reclassificação preservam auditoria. |
| Falha e reentrega | Broker fora do ar deixa envios persistidos. Recuperação entrega ou expõe erro com motivo. Repetir entrada e resultado mantém contagem de casos/mensagens. A mesma chave com conteúdo divergente é detectada. |
| Resolução e nova entrada | Resolver libera vaga. Novo relato após resolução abre novo caso vinculado, com histórico anterior preservado. |

Evidências mínimas incluem testes automatizados do domínio e integração, roteiro manual da interface, IDs de correlação usados na demo e relatório do experimento. Registrar saídas reproduzíveis e casos que falharam. O modo fixture valida o contrato do Jev localmente. A chamada real com credencial e a avaliação da qualidade são evidências próprias.

## 4. Experimento técnico

**Hipótese principal.** A entrega assíncrona permite que o Rails aceite solicitações durante interrupção temporária do broker e conclua o processamento depois da recuperação, sem perda nem duplicação de efeitos em casos aceitos.

1. Usar k6 com taxa de chegadas fixa e dados sintéticos em três canais e duas marcas. Fixar semente e versões, registrar CPU, memória, réplicas, conexões de banco e concorrência dos workers. O ensaio principal usa classificação válida, mock determinístico com latência fixa, e 20% dos casos com segundo turno. Exercitar handoff e carteira em cenário separado com analistas sintéticos e ações roteirizadas.
2. Comparar três rodadas de 5 minutos a **5 novos casos/s** com o broker disponível e três com o broker interrompido por 30 segundos após o primeiro minuto. Manter os outros parâmetros. Gerar os retornos de cliente em intervalo fixo. Aguardar até dois minutos após o fim da carga para observar o escoamento.
3. Medir p50/p95 de webhook até aceite e de webhook até primeira resposta persistida, vazão, taxa de erro e iterações descartadas pelo gerador, maior backlog, tempo de recuperação, CPU/RAM e contagem de efeitos duplicados/perdidos por ID. Critério inicial proposto para a carga de referência: p95 do aceite até 500 ms, pelo menos 99% de webhooks aceitos, zero efeitos duplicados ou perdidos entre os casos aceitos e escoamento até o fim da janela de observação. Publicar resultados mesmo quando a meta falhar. Reportar separadamente o tempo de resposta ao cliente durante a falha. [Modelos de carga do k6](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/)
4. Aumentar a taxa progressivamente para identificar o primeiro gargalo. Como ensaio exploratório separado, testar **100 → 1.000 → 10.000 conexões de chat** em patamares, com uma mensagem por sessão a cada 100 segundos em média, distribuída ao longo do intervalo. O último patamar equivale a cerca de **100 mensagens/s**. Informar se eram novas conversas ou mensagens de seguimento, quantas conexões ficaram abertas, o patamar efetivamente alcançado e se o gerador virou gargalo. Esse cenário mede conexões e tráfego, enquanto o principal mede novos casos e recuperação. O TAPI não fixa 10 mil conexões ou essa taxa. [Enunciado do TAPI](../../TAPI_Inteli_CloudWalk_HelpDesk_AgentesIA.pdf)

**Jev.** Avaliar uma amostra proposta de 60 relatos sintéticos rotulados em português, 20 com categoria omitida, 20 com prioridade omitida e 20 com ambas omitidas. Incluir relatos urgentes e ambíguos, registrar rótulo esperado antes da execução e versão do modelo. Reportar acerto por campo, urgentes não detectados, cobertura automática, abstenções, erros, latência p50/p95 e custo observado, quando disponível. A qualidade e a velocidade do Jev serão reportadas a partir das medições, com limitações do tamanho da amostra e do catálogo sintético.

## 5. Entrega final

- Código com Rails, React, ponte, mock, três canais simulados, seeds e Compose.
- Testes e roteiro da demonstração com os cenários de aceite.
- Scripts de carga, dados sintéticos, resultados, gráficos ou tabelas e metodologia para reproduzir.
- README com problema, escopo, arquitetura, instalação, execução, modelos e configuração, método experimental, resultados, limitações e evolução.

A versão do Jev e as credenciais necessárias ao ensaio ao vivo serão verificadas em F04. A aplicação local e o experimento de carga de referência rodam com os campos de entrada válidos ou o modo de teste, conforme a evidência desejada. Nenhum resultado de carga ou qualidade está medido nesta fase.

### Publicação da demonstração por URL

F09 comprova a entrega local reproduzível. Se a apresentação exigir acesso remoto, F10 entrega uma instância de demonstração com URL HTTPS, login e dados sintéticos. A proposta é executar o mesmo conjunto de serviços do Compose em um servidor. O provedor, o endereço, o orçamento e o período de disponibilidade são entradas da tarefa.

- Configurar os serviços de aplicação e a origem HTTPS para React, API e WebSocket. Manter PostgreSQL, RabbitMQ e a ponte na rede interna, com volumes persistentes e segredos no ambiente do servidor.
- Documentar inicialização, migrações, carga de dados, atualização, reinício, consulta de logs e restauração da demonstração. Verificar que a aplicação se recupera de um reinício com casos e histórico preservados.
- Entregar URL e acesso de demonstração ao responsável, com perfis de cliente e analista. Validar de outra rede a conversa com a IA, o handoff, o acesso por marca e a atualização do chat. Se o roteiro incluir Jev ao vivo, configurar a credencial no servidor e registrar o resultado do teste antes da apresentação.
