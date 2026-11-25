# Plano de execução e verificação do MVP

Este backlog usa a [especificação](especificacao-mvp.md) como contrato de produto. O horizonte de quatro semanas segue a estimativa do TAPI. Datas e dedicação semanal serão ajustadas à agenda real. Os checkpoints semanais são internos. A demonstração inclui atendente simulado via broker, complemento da classificação em fixture, experimento e resultados documentados.

F01–F03 estão integradas e verificadas localmente. A rodada de conclusão
F04/F05 integra jobs persistidos, correção auditada, sessão e catálogo do
simulador e interface conectada ao Rails e ao Action Cable. A suíte conjunta
passou com 74 testes e 881 asserções, sem falhas nem erros. O único teste
pulado foi a chamada TypeSafe real, pois falta `TYPESAFE_API_KEY`.

A F05 passou no navegador com três canais, duas marcas, handoff, resposta
humana, espera, retomada, resolução, reentrega após resposta perdida, conflito
de versão e recuperação após reiniciar a API. A
[integração F04/F05](../integracao-f04-f05.md) registra evidências e limites.
A F04 concluiu a implementação e verificação local. A chamada ao vivo com
Jev ficou pendente naquela etapa. A qualificação real passou ao CLASS-001.

A F06 está implementada e verificada localmente, incluindo configuração,
supervisão, migração e duas corridas de configuração no PostgreSQL. A base
conjunta passou com 86 testes Rails e 1.065 asserções (uma omissão TypeSafe),
27 testes frontend e build pelo lockfile. A F07-A fornece cinco cenários reais
de robustez dos fluxos F02–F05. A [integração F06/F07-A](../integracao-f06-f07.md)
registra os resultados e a complementação administrativa da F07, incluindo
revogação com uma sessão WebSocket já aberta. F06 e F07 têm aceite local
concluído. A F08 executou a referência de carga: cinco rodadas aprovadas e
uma reprovada por encerramento dos consumidores após a retomada do Kafka.
O [relatório F08](../f08.md) conserva os resultados e o diagnóstico.
A R02 resolveu dois casos limite do analisador, o carimbo ausente com
publicação tardia e a atribuição SQL de escrita de chat após timeout HTTP.
Seu aceite local registrou 49 testes e preservação dos sete históricos e
das 12.600 linhas. [Relatório R02](../r02.md) · [Issue #9](https://github.com/leeunam/case-CLOUDWALK-IA/issues/9).
A R01 foi aceita e integrada localmente após revisão e ensaio real controlado:
os dois consumidores retomaram em cerca de 12 segundos, com lag zero e
recuperação canônica aprovada. O [relatório R01](../r01.md) conserva as evidências.
O ensaio controlado é posterior à referência. A matriz histórica preserva
a reprovação e segue sem repetição após a correção.

A [passagem da F08](passagem-f08.md) separa o gerador/observador de carga
do dataset/avaliador Jev, com arquivos próprios e a mesma base Git. A execução
comparável e a coordenação da revisão dos rótulos ficam no chat central.

### Frente de classificação — CLASS-001

Em 2026-11-23, o responsável escolheu comparar Qwen pela Feita com GLiClass
local antes de selecionar o classificador. O [quadro SDD](classificacao-comparativa/README.md)
contém sete cards de protocolo/avaliador/adaptadores/comparação/integração/demo
e duas correções independentes de robustez. A especificação é CLASS-SPEC-001;
a decisão está em D017. SDD aqui significa Specification Driven Development.
A divisão foi aprovada e publicada no [épico CLASS-001](https://github.com/leeunam/case-CLOUDWALK-IA/issues/1),
com nove issues vinculadas. A aprovação dos cards não aprova ainda dados,
orçamento de inferência ou vencedor.

Os itens F04/F08 abaixo registram a implementação e o experimento anteriores
com Jev. A nova frente preserva as regras de negócio, prepara o comparativo e,
após decisão humana, atualiza o aceite real para o classificador selecionado.
Os 60 rótulos foram revisados para referência exploratória: oito casos
diretamente pelo responsável e 52 pela IA sob delegação explícita, conforme o
[registro da C01](classificacao-comparativa/revisao-de-rotulos.md). Critérios e
divisão 24/36 foram aprovados no [protocolo](classificacao-comparativa/protocolo-comparacao.md).
Os contratos v1.1.0 passaram na verificação local, conforme o
[aceite C01](classificacao-comparativa/aceite-c01.md). A revisão final da C01 foi aprovada. A revisão da C02 levou à emenda técnica
1.1.0 de proveniência dos controles. O avaliador está aceito com 31 testes
após a manutenção de integração e reprodução fixture do código aprovado.
A C03 foi integrada com 30 testes e piloto real mínimo aceito: uma requisição
completou `pix` e `urgent` em 1,826 s, com cobrança exibida de aproximadamente
US$ 0,000518. Naquele momento, o comparativo final ainda estava pendente.
A C04 teve código revisado e dez lotes reais adicionais de
desenvolvimento, incluindo falhas por prazo e um rebaixamento de urgência.
Sua configuração não foi aprovada para C05. A [passagem da frente](classificacao-comparativa/passagem-autonoma.md)
registra as evidências e decisões daquela etapa. O teto de US$ 10 foi aprovado
para o piloto Qwen, com mínimo de requisições; uma chamada foi suficiente.
Depois da investigação, o responsável aprovou focar na avaliação do Qwen e
encerrar novos ajustes do GLiClass nesta entrega. C04 deixa de bloquear C05;
a qualificação usa os mesmos critérios e os 36 casos finais, sem comparação
pareada final. Naquele momento, faltavam configurar a execução e decidir
pela adoção. [Plano da qualificação Qwen](classificacao-comparativa/qualificacao-qwen.md).
O reteste C03-P2 autorizado usou uma chamada adicional no mesmo caso e foi
confirmado em recibo separado; não avalia o conjunto final. C05-E adiciona
o executor final e a contabilidade cumulativa, aceitos em `e4ce14c` com 37 testes
offline e revisão independente aprovada. A primeira conta suportada é a versão 4,
preservando as regressões anteriores e o teto total de US$ 10. O lote real
ficou condicionado ao manifesto e à decisão próprios.
Criar os cards não equivale a autorizar inferência paga nem escolher o fornecedor.

A atualização C01-L/C02-L foi aceita e integrada em `933836e`. As próximas
avaliações usam explicitamente `observed-total-1.1`: p95 do tempo total da
classificação até 3.000 ms, incluindo falhas e timeouts observados, sem depender
de aquecimento comprovado. Protocolo de qualidade 1.1, relatório 1.2 e IPC 1.1;
39 testes do avaliador passaram, sem novas chamadas externas. Os 17 relatórios
históricos conservaram seus hashes. [Plano e aceite](classificacao-comparativa/plano-latencia-total.md).

Em 24/11/2026, o primeiro lote final autorizado da C05 foi concluído:
36 relatos + 13 controles, 44 chamadas, custo US$ 0,02197127 e total conservador
com pilotos US$ 0,02300927. Resultado técnico **não elegível**: 3/7 conclusões
onde era obrigatória revisão e 19/22 categorias aplicadas corretas (86,36%).
O p95 de 2.493,510 ms e o reconhecimento de 6/6 urgentes passaram. As auditorias
independentes conferiram qualidade e finanças. O resultado bloqueou a adoção
na C06. A autorização do lote foi consumida.
[Resultado e verificações sem API](../c05-resultado.md).

O responsável escolheu a opção A da **C05-R2**: instruções mais conservadoras
de uma chamada, com novo final independente e preservação dos limites.
A [implementação offline](classificacao-comparativa/rodada-2-implementacao.md)
partiu da base comum `c00ac54`, com frentes de instruções e dados em worktrees
separadas. A candidata foi congelada antes de o integrador abrir os novos
textos; os 36 novos finais passaram por revisão de rótulos e semelhança,
com referência exploratória por IA. O executor `3f66bec` passou no aceite
offline e no roteiro CLI fixture do integrador. O [guia R2](../c05-r2.md)
registra verificações, limites e revisão ampla final aprovada no código `b19a596`,
sem achados residuais e com nova reprodução CLI fixture.
O responsável autorizou até seis chamadas de desenvolvimento e, somente se
aprovadas, até 44 do final/controles. As seis foram executadas em 24/11/2026:
5/8 alvos corretos, uma conclusão indevida em três revisões esperadas,
p95 de 4.995,002 ms e um timeout. O development foi interrompido e o final
ficou bloqueado, sem repetição. O custo conservador da R2 é US$ 0,00386478,
com acumulado US$ 0,02687405 e nenhuma reserva pendente após conciliação
tardia. Isso não representa saldo do fornecedor. C06/C07 ficaram bloqueadas
naquela etapa. [Resultado e auditoria R2](../c05-r2-resultado.md).

#### Estado em 25/11/2026

A R4 acertou 7/8 campos e reprovou o gate. A preparação R5 A+B passou nas
revisões e foi seguida por seis chamadas reais de desenvolvimento: 8/8 alvos,
p95 de 2.886,371 ms, gate aprovado. O final da R5 parou na tentativa 30 de
até 44 por erro de transporte sem custo conciliável, sem repetição. O
prefixo permanece inconclusivo e mostrou 1/26 conclusões automáticas em
casos classificáveis, 0/4 urgentes reconhecidos após a política e p95 de
3.269,135 ms. A candidata não está apta para adoção. Os 35 recibos R5 somam
US$ 0,00992557 e há reserva pendente de US$ 1,239, sem cobrança confirmada
para a última tentativa. Novas chamadas estão suspensas.
[Resultado R4](../c05-luna-r4-resultado.md) ·
[Resultado real R5](../c05-luna-r5-resultado.md) ·
[Candidata R5](../c05-luna-r5-candidata.md).

A sequência da qualificação é C01 → C02 → C03 → C05 → C06 → C07. Os ajustes
da C04 foram encerrados nesta entrega, e R01 e R02 tiveram aceite independente.
O responsável autorizou o piloto local SetFit (C05-SF1) e propôs adiar a
categorização para avançar nas outras frentes. O piloto concluiu a avaliação
exploratória de categoria. A escolha e a calibração do classificador (C05),
a integração (C06) e o complemento real em instalação limpa (C07/F09 final)
ficam em espera até retomada explícita. O requisito de classificação real
continua no plano. A preparação F09-A já foi verificada com fixture, e o
aceite externo da demonstração F10 pode avançar nesse modo.
[Piloto SetFit](classificacao-comparativa/setfit-piloto.md) ·
[Estado da entrega](../estado-entrega.md) · [Plano de conclusão](conclusao-projeto.md).
O [guia dos chats](classificacao-comparativa/guia-dos-chats.md) explica base Git,
isolamento, propriedade, modelos sugeridos, revisão e exercícios de aprendizagem.

### Evolução futura depois da publicação — E01

Em 2026-11-23, o responsável pediu registrar o [E01 — atendente experimental
com IA real](https://github.com/leeunam/case-CLOUDWALK-IA/issues/11). Retomar
**somente depois de concluir a F09 e publicar e verificar a F10, caso sobre
tempo**. A ordem é concluir o projeto, publicar a demonstração e então explorar
essa evolução. Manter o card no backlog futuro durante o fluxo atual.

O objetivo é conversar com um modelo real usando histórico e dados fictícios,
integrado pelos contratos Kafka existentes, com respostas e encaminhamento
humano demonstráveis. Essa função é distinta do classificador do CLASS-001.
Modelo, provedor, desenho, critérios de aceite e limites de uso/custo serão
definidos na retomada; o mock determinístico permanece disponível para testes.

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
| F01 | Base do monorepo, Compose, PostgreSQL, Kafka, Rails, React e contratos. Entregar `compose.yml`, `docs/contratos/`, fixtures versionadas, seeds mínimos e convenções de módulos. Fechar modelo de dados inicial, versões do runtime e ordem dos bloqueios com o responsável. | — | Ambiente sobe com um comando, API e Kafka respondem, contratos trazem exemplos de sucesso/erro e o seed instala sem duplicar. |
| F02 | Primeiro fluxo completo com webhook de canal, persistência, ponte, broker, mock, webhook de retorno e leitura da conversa. Incluir o backend mínimo de sessão e credenciais sintéticas para acessar as leituras protegidas. Cobrir também resposta, resolução e histórico em dois turnos. | F01 | Um caso válido via chat percorre o broker, recebe resposta, pode continuar e resolver. Sessão autenticada permite ler o histórico autorizado. IDs permitem seguir o caminho e reentrega preserva um único efeito. |
| F03 | Handoff e atendimento humano com perfil, carteira, menor carga, troca de marca, espera, retomada e transferências. Publicar operações de leitura e alteração do caso e serviços de elegibilidade. | F02 | Resumo e contexto chegam ao humano, capacidade e carteira continuam corretas em retomada e em disputa pela última vaga. |
| F04 | Classificador Jev, fila de revisão, falhas e correção. Entregar adaptador HTTP com modo fixture para execução local sem chave e teste do adaptador real com chave. | F02 | Apenas campos ausentes geram perguntas ao Jev. Campo válido permanece. Inválido, abstenção e timeout aparecem em revisão. Configuração de demonstração com credencial executa pelo menos um complemento real. |
| F05 | React para simulador, caixa e conversa, usando fixtures contratuais no início e API real no fim. Incluir chat com atualização e recuperação após reconectar, e histórico assíncrono de WhatsApp e e-mail. | F01 para UI com fixtures. F02–F04 para integração. | Cliente envia pelos três canais simulados. Analista consulta e responde caso escalado, muda para aguardar e resolve. Controles e erros refletem as permissões do servidor. |
| F06 | Configuração editável de marcas/equipes, filas, regras, catálogo e perfis. Incluir revisão de classificação, consulta de falhas e ações de recuperação para supervisor. | F03 e F04 para integrar. F01 para fixtures de UI. | Supervisão cria uma fila, vincula duas equipes autorizadas, muda regra e perfil, corrige um caso e verifica auditoria. Vínculo inválido é bloqueado. |
| F07 | Robustez e rastreamento ponta a ponta, incluindo autenticação de integrações, isolamento de marcas, reentregas, falhas e recuperação. | F02–F06 para prova completa. Harness pode começar em F01. | Interromper Kafka, reentregar callback e tentar acesso cruzado em API e WebSocket. Verificar backlog recuperado, offsets sem lacunas, publicação em `agent.failures`, ausência de efeito duplicado e isolamento. |
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
| Falha e reentrega | Kafka fora do ar deixa envios persistidos no outbox. Recuperação publica ou expõe erro com motivo. Repetir entrada e resultado mantém contagem de casos/mensagens. A mesma chave com conteúdo divergente é detectada. Offset só avança depois da aplicação ou descarte auditado no Rails; lacunas pendentes não são ultrapassadas. |
| Resolução e nova entrada | Resolver libera vaga. Novo relato após resolução abre novo caso vinculado, com histórico anterior preservado. |

Evidências mínimas incluem testes automatizados do domínio e integração, roteiro manual da interface, IDs de correlação usados na demo e relatório do experimento. Registrar saídas reproduzíveis e casos que falharam. O modo fixture valida o contrato do Jev localmente. A chamada real com credencial e a avaliação da qualidade são evidências próprias.

## 4. Experimento técnico

**Hipótese principal.** O outbox permite que o Rails mantenha solicitações pendentes durante interrupção temporária do Kafka e conclua o processamento depois da recuperação, sem perda nem duplicação de efeitos em casos aceitos.

1. Usar k6 com taxa de chegadas fixa e dados sintéticos em três canais e duas marcas. Fixar semente e versões, registrar CPU, memória, réplicas, conexões de banco e concorrência dos workers. O ensaio principal usa classificação válida, mock determinístico sem atraso artificial injetado, e 20% dos casos com segundo turno. O tempo real do processamento continua medido. Exercitar handoff e carteira em cenário separado com analistas sintéticos e ações roteirizadas.
2. Comparar três rodadas de 5 minutos a **5 novos casos/s** com Kafka disponível e três com Kafka interrompido por 30 segundos após o primeiro minuto. Manter os outros parâmetros. Gerar os retornos de cliente em intervalo fixo. Aguardar até dois minutos após o fim da carga para observar o escoamento.
3. Medir p50/p95 de webhook até aceite e de webhook até primeira resposta persistida, vazão, taxa de erro e iterações descartadas pelo gerador, maior backlog, tempo de recuperação, CPU/RAM e contagem de efeitos duplicados/perdidos por ID. Critério inicial proposto para a carga de referência: p95 do aceite até 500 ms, pelo menos 99% de webhooks aceitos, zero efeitos duplicados ou perdidos entre os casos aceitos e escoamento até o fim da janela de observação. Publicar resultados mesmo quando a meta falhar. Reportar separadamente o tempo de resposta ao cliente durante a falha. [Modelos de carga do k6](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/)
4. Aumentar a taxa progressivamente para identificar o primeiro gargalo. Como ensaio exploratório separado, testar **100 → 1.000 → 10.000 conexões de chat** em patamares, com uma mensagem por sessão a cada 100 segundos em média, distribuída ao longo do intervalo. O último patamar equivale a cerca de **100 mensagens/s**. Informar se eram novas conversas ou mensagens de seguimento, quantas conexões ficaram abertas, o patamar efetivamente alcançado e se o gerador virou gargalo. Esse cenário mede conexões e tráfego, enquanto o principal mede novos casos e recuperação. O TAPI não fixa 10 mil conexões ou essa taxa. [Enunciado do TAPI](../../TAPI_Inteli_CloudWalk_HelpDesk_AgentesIA.pdf)

**Jev.** Avaliar uma amostra proposta de 60 relatos sintéticos rotulados em português, 20 com categoria omitida, 20 com prioridade omitida e 20 com ambas omitidas. Incluir relatos urgentes e ambíguos, registrar rótulo esperado antes da execução e versão do modelo. Reportar acerto por campo, urgentes não detectados, cobertura automática, abstenções, erros, latência p50/p95 e custo observado, quando disponível. A qualidade e a velocidade do Jev serão reportadas a partir das medições, com limitações do tamanho da amostra e do catálogo sintético.

## 5. Entrega final

- Código com Rails, React, ponte, mock, três canais simulados, seeds e Compose.
- Testes e roteiro da demonstração com os cenários de aceite.
- Scripts de carga, dados sintéticos, resultados, gráficos ou tabelas e metodologia para reproduzir.
- README com problema, escopo, arquitetura, instalação, execução, modelos e configuração, método experimental, resultados, limitações e evolução.

A aplicação local admite o complemento em fixture. O ensaio de carga de
referência usou campos válidos na entrada e atendente simulado. Os cenários
exploratórios de aumento de taxa, atendimento humano e dez mil conexões
continuam sem medição. A avaliação com Jev na F08 foi offline. A qualificação
real seguiu para CLASS-001. [Resultados de carga](../f08.md) · [Plano de conclusão](conclusao-projeto.md).

### Publicação da demonstração por URL

A preparação F09-A comprovou a reprodução local com fixture. A F10 publicou
a demonstração com login e dados sintéticos sobre um túnel HTTPS temporário
do computador local. O reinício e a restauração foram verificados. O
integrador comprovou uma conversa de dois turnos na publicação da UX02. Na
primeira URL da F10, o responsável abriu a página por dados móveis e confirmou
que marcas e canais estavam visíveis. A renovação de 25/11/2026 verificou a
saúde da API em HTTPS no novo endereço. O fluxo completo por outra rede
segue pendente.
[F09-A](../f09.md) · [Resultado F10](../f10-resultado.md) · [UX02](../ux02.md).

O plano de aceite da publicação prevê os seguintes passos.

- Configurar os serviços de aplicação e a origem HTTPS para React, API e WebSocket. Manter PostgreSQL, Kafka e a ponte na rede interna, com volumes persistentes e segredos no ambiente do servidor.
- Documentar inicialização, migrações, carga de dados, atualização, reinício, consulta de logs e restauração da demonstração. Verificar que a aplicação se recupera de um reinício com casos e histórico preservados.
- Entregar URL e acesso de demonstração ao responsável, com perfis de cliente e analista. Validar de outra rede a conversa com a IA, o handoff, o acesso por marca e a atualização do chat. Se o roteiro incluir o classificador real, validar sua configuração após a adoção em C06 e registrar o resultado antes da apresentação.
