# Contratos do help desk v1

A F01 implementa `GET /api/v1/health`. O [OpenAPI](openapi.yaml) define também
a interface que Rails, ponte e React devem implementar nas fases F02–F06. Cada
operação indica a fase em `x-implementation-phase`. Os [schemas JSON 2020-12](schemas/v1.json)
são compartilhados pelo OpenAPI e pelas fixtures. Mudanças em um contrato exigem
atualização dos exemplos e coordenação com os consumidores.

## Entrada dos canais e integração

- O Rails usa o canal da rota e a credencial validada para determinar a marca.
  Os três IDs externos são strings opacas. A chave de entrada é
  `(channel_id, source_event_id)`. Depois da persistência, o Rails retorna
  `202` com os IDs do atendimento e da correlação. Reentrega com os mesmos bytes
  de corpo retorna os mesmos IDs. Reuso da chave com bytes diferentes retorna
  `409`.
- Ausência, `null` e string vazia em categoria ou prioridade representam campo
  faltante. Quando os valores presentes são válidos, o Rails encaminha apenas
  os campos faltantes ao Jev. Valor fora do catálogo ativo da marca ou tipo
  incorreto encaminha a entrada persistida para revisão. Em ambos os caminhos
  o envelope pode receber `202`. A ausência de um campo obrigatório, como
  `text`, recebe `422`.
- O seed usa as categorias `pix`, `payouts` e `terminal`. A precedência da
  demonstração é `urgent`, `advanced`, `intermediate`, `basic`. O Rails registra
  a origem de cada campo aplicado em separado. Um campo pode vir de `channel`,
  `jev` ou `supervisor`. A correção auditada altera a origem dos campos
  corrigidos e invalida o complemento que ainda estiver em voo.
- Os três webhooks exigem assinatura por credencial específica do canal ou da
  integração. `X-Webhook-Timestamp` é o epoch Unix em segundos decimais.
  `X-Webhook-Signature` contém 64 dígitos hexadecimais minúsculos do
  HMAC-SHA256 sobre o timestamp fornecido, um ponto ASCII e os bytes originais
  do corpo. O receptor verifica uma única ocorrência de cada header, formato,
  janela absoluta de 300 segundos e igualdade em tempo constante. Headers
  ausentes, malformados, fora da janela ou com assinatura divergente recebem
  `401`. Cada tentativa recalcula timestamp e assinatura e conserva a
  identidade e o corpo do evento.
- O Rails grava a rodada e o outbox junto à transição do atendimento. A ponte
  retorna `202` para `/webhooks/v1/agent/requests` após confirmação da publicação
  no tópico `agent.requests`. Kafka usa `acks=all`, idempotência de produtor e
  três partições por tópico na demo, com `case_id` como chave. Os tópicos
  `agent.requests`, `agent.events` e `agent.failures` usam retenção de sete dias
  (`KAFKA_RETENTION_MS`, padrão `604800000`) e `cleanup.policy=delete`; consumo
  não remove eventos. O mock consome com o grupo `mock-agent-v1`; a ponte consome
  retornos com `platform-agent-events-v1`. Auto commit fica desligado. Cada
  grupo avança por partição apenas até o próximo offset do último registro
  contíguo concluído. A ponte só conclui após o Rails confirmar aplicação ou
  descarte definitivo auditado; o mock conclui após publicar o retorno. Após
  tentativas limitadas, publica falha com identificação, motivo e origem em
  `agent.failures`, confirmando o offset só após publicação. Timeout ambíguo
  pode repetir o mesmo `event_id`, protegido pela deduplicação da aplicação.
  Replay é explícito, limitado aos dados retidos e sujeito à geração/rodada
  vigente. O PostgreSQL mantém o histórico e a auditoria do domínio.
- O Rails aceita uma rodada em voo por atendimento. O payload da solicitação
  contém classificação validada e histórico por `sequence` crescente. Toda
  proposta referencia `request_event_id`. O Rails verifica marca, atendimento,
  correlação, geração de atribuição, rodada, solicitação e estado vigentes
  antes de aplicar o efeito. Evento de retorno idêntico já processado mantém
  um único efeito. Reuso do ID com outros bytes recebe `409`. Resultado
  estruturalmente válido de rodada antiga recebe `200` com
  `disposition: discarded` após o registro de auditoria.
- Mensagens que chegam enquanto o mock responde são persistidas e entram na
  próxima rodada. Se a IA propõe resolver com mensagens novas pendentes, o Rails
  grava a resposta e dispara outra rodada antes de encerrar. No handoff, os
  IDs citados pertencem ao histórico do pedido e mostram quais mensagens
  entraram no resumo. O analista vê também as mensagens posteriores.
- `status` expressa a situação operacional do caso. `integration_status`
  expressa o envio/resultado da rodada, inclusive falhas durante `ai_active`.
  Uma nova rodada após expiração recebe nova identidade. Os prazos e as
  políticas de recuperação do MVP estão na
  [especificação](../planejamento/especificacao-mvp.md#4-contratos-e-recuperação).

## API para o navegador

Rails aplica autorização em toda leitura, mutação e assinatura de atualização.
React usa a mesma origem, cookie de sessão e token `X-CSRF-Token` para escritas.
A resposta de sessão também expõe a marca em operação, disponibilidade e
contagem de casos do analista. A F02 implementa a sessão no Rails para que as
leituras protegidas possam ser exercitadas. A F05 implementa a tela de login.
Consultas de caso e histórico usam cursor opaco ou sequência conforme a
operação. Após um sinal de atualização do Action Cable, o cliente consulta o
recurso novamente. Também recarrega na reconexão e pode intercalar consultas
periódicas enquanto a conversa estiver aberta.

O WebSocket usa `/cable` na mesma origem. O identificador de assinatura contém
`channel: "CaseUpdatesChannel"`, `case_id` e `audience: "simulator" | "staff"`.
A sessão do simulador só pode assinar conversas próprias e a sessão operacional
precisa de visibilidade vigente sobre o caso. O servidor verifica essa permissão
na assinatura e em cada aviso. Sessões revogadas ou expiradas perdem acesso.
O adapter PostgreSQL propaga entre API e workers, após commit, somente
`{ "type": "case.updated", "case_id": "<uuid>" }`. Os envelopes de controle são
do Action Cable. Os formatos estão em [assinatura](fixtures/case-update-subscription.json)
e [aviso](fixtures/case-updated.json).

Supervisores têm autorização explícita por marca. Analistas ganham visibilidade
pelo caminho equipe → autorização na marca → vínculo de responsabilidade da
fila. `GET /api/v1/case-filters` fornece nomes e IDs para os filtros dessa
visibilidade, inclusive em marcas em que o analista pode consultar sem atuar.
O Rails aplica o mesmo escopo quando a interface usa esses IDs na caixa.

O UUID em `session.user.id` identifica o usuário. Para analistas,
`session.user.attendant_id` identifica o atendente humano usado em
`case.assignee.id`. Supervisores e simuladores têm `attendant_id` nulo.
O React pode habilitar ações de resposta, espera e resolução quando o caso
está em `human_active`, o responsável é humano, o ID do atendente coincide
com o da sessão e o caso pertence à marca em operação. O Rails revalida a
autorização a cada comando. A supervisão encontra os analistas cujo perfil
ela pode editar em `GET /api/v1/analysts` e usa o `user_id` na rota de perfil.
Como o perfil vale em todas as marcas de atuação do analista, a edição
exige autorização explícita para cada uma delas.

O simulador usa uma identidade segregada e consulta apenas suas conversas.
`POST /api/v1/simulator/session` cria ou recupera essa identidade e devolve o
token CSRF vigente. Quando o mesmo navegador tem sessão operacional e sintética,
`GET /api/v1/session` mostra a operacional e `GET /api/v1/channels` usa a
identidade sintética para a seleção da simulação. O logout revoga as duas
identidades presentes no navegador. As APIs de cada audiência aplicam seu
próprio escopo.

O catálogo paginado retorna somente canais habilitados para a sessão. Cada
canal inclui `brand_id` e o `brand_name` atual da marca. A interface do
simulador deriva suas opções desse par no catálogo autorizado.
Após recarregar, a listagem e o detalhe recuperam `channel_id` para a rota
de envio e `external_conversation_id` para o corpo da continuação. O Rails
verifica se o canal e a conversa pertencem à sessão e se a conversa usa
esse canal. O recibo devolve os dois IDs. As leituras do simulador expõem
estados e mensagens públicas.

Nas mutações de atendimento, o Rails verifica `Idempotency-Key` e
`expected_version`. A chave é vinculada ao ator, operação e recurso. Repetir o
comando idêntico devolve o resultado original depois de conferir a autorização
atual. Versão defasada, ação incompatível com a situação ou chave reutilizada
com outro conteúdo retorna `409`. O React recarrega o caso em conflito de
versão. `403` indica ação proibida em um recurso visível. Recursos fora do
escopo de visibilidade podem receber `404`.

O Rails valida a fila padrão, os vínculos de equipes, as categorias habilitadas
e a versão de configurações. As regras de encaminhamento ativas são avaliadas
por posição única na marca, com a fila padrão como fallback. Editar uma regra
afeta encaminhamentos posteriores. Casos em andamento só mudam de fila por
transferência. Para um perfil, cada alternativa contém pares exatos e únicos de
categoria e prioridade com limites positivos. A carteira deve comportar a maior
alternativa. O conjunto ativo precisa caber inteiro em uma única alternativa.
O Rails valida os pares e o teto ao publicar a versão.

Supervisores consultam criação e edição de configurações em
`GET /api/v1/brands/{brand_id}/configuration-audit`, com filtros de tipo
e ID de recurso. O Rails grava a auditoria junto à mudança,
associa o evento às marcas afetadas e retorna apenas o escopo autorizado.
Cada evento informa ator, versão publicada e fotografias `before` e `after`
dos campos operacionais autorizados. Em criação, `before` é nulo.
O `resource_id` do catálogo identifica a marca. O do perfil identifica o
usuário analista, mantendo a identidade ao publicar outra versão.
As fotografias omitem credenciais e dados de marcas fora da consulta.

## Transições do atendimento

O módulo Atendimento do Rails aplica todas as transições. Classificação,
distribuição, ponte, mock, React e simuladores submetem entradas ou propostas.
O módulo revalida estado, versão, vínculos, permissão e elegibilidade conforme
a operação e grava o efeito com auditoria. As regras operacionais abaixo são o
contrato-alvo da demo nas fases F02–F04.

| Estado de origem | Ator e condição | Resultado |
| --- | --- | --- |
| Nova entrada ou conversa anterior resolvida | Canal autenticado envia mensagem inédita | Novo atendimento na fila padrão. Classificação válida inicia IA, campos faltantes ficam em `classification_pending`, campo inválido vai a `classification_review`. Conversa anterior resolvida fica vinculada. |
| `classification_pending` | Triagem aplica complemento válido e vigente | Encaminha para a fila aplicável, atribui IA e entra em `ai_active`. Falha ou abstenção segue para `classification_review`. |
| `classification_pending`, `classification_review` | Supervisor autorizado corrige a classificação inicial com motivo | Invalida eventual complemento pendente, define fila, atribui IA e entra em `ai_active`. |
| `classification_pending`, `classification_review`, `waiting_human`, `human_active` | Cliente envia mensagem | O Rails anexa a mensagem e conserva o estado. |
| `ai_active` | Cliente envia mensagem | Anexa ao histórico. Se a rodada está em voo, inclui no próximo pedido. |
| `ai_active` | Retorno da rodada vigente | Resposta mantém `ai_active`. Resolução sem novas mensagens pendentes muda para `resolved` e libera o responsável. Handoff guarda resumo e referências, libera IA e muda para `waiting_human`. |
| `ai_active` com integração em falha | Supervisor autorizado recupera com `retry_agent` ou escala com `force_handoff` e resumo | Retoma a entrega ou abre rodada após expiração, conforme o ponto de falha. Handoff de contingência segue para `waiting_human`. |
| `waiting_human` | Distribuição encontra analista elegível | Atribui o responsável principal e muda para `human_active`. Sem candidato, mantém o caso visível e registra bloqueio. |
| `human_active` | Analista responsável responde na marca em operação | Registra a mensagem e mantém `human_active`. A ação `wait_for_customer` registra a mensagem solicitando informação e muda para `waiting_customer`. A ação `resolve` muda para `resolved` e libera capacidade e carteira. |
| `waiting_customer` | Cliente responde | Caso com responsável muda para `waiting_resumption`. Caso sem responsável vai a `waiting_human`. |
| `waiting_resumption` | Distribuição encontra espaço ativo para o responsável elegível | Muda para `human_active` com o mesmo responsável. Mensagens recebidas enquanto aguarda são anexadas ao histórico. |
| Caso em fluxo humano | Supervisor autorizado transfere com motivo | Preserva a marca, registra fila e responsável anteriores e valida destino. Destino elegível assume em `human_active`, ou preserva `waiting_customer` se o caso estiver nesse estado. Transferência apenas de fila pode remover a atribuição e voltar a `waiting_human` ou continuar aguardando cliente. Destino explícito inelegível recebe `422`. |
| Caso classificado em andamento | Supervisor autorizado corrige a classificação com motivo | Preserva a fila. Mudança que excede a combinação em uso bloqueia novas entradas e retomadas do analista enquanto durar o excesso. |

A espera pelo cliente libera o espaço ativo e preserva a vaga da carteira quando
há responsável. A fila atual e o histórico permanecem no atendimento. Nova
atribuição, mudança de responsável e retomada usam as regras de elegibilidade
sob bloqueio descritas no [modelo conceitual](modelo-de-dados.md).

## Fixtures

Em cada arquivo, `schema` aponta para a definição e `data` contém o documento
enviado ou recebido. `valid: false` identifica um exemplo cuja estrutura deve
falhar na validação. Os IDs de marca coincidem com o seed. Os demais IDs são
determinísticos dentro dos exemplos e podem ser usados no mock da interface.

| Arquivo em `fixtures/` | Schema | Efeito esperado |
| --- | --- | --- |
| `health-200.json` | `HealthSuccess` | API e banco disponíveis. |
| `health-503.json` | `HealthUnavailable` | Falha de disponibilidade do banco. |
| `channel-entry.json` | `ChannelMessage` | Cria o atendimento do fluxo de dois turnos. Reentrega idêntica reutiliza o resultado. |
| `channel-handoff.json` | `ChannelMessage` | Preserva a categoria e pede ao Jev somente a prioridade. |
| `channel-list.json` | `ChannelList` | Oferece chat, WhatsApp e e-mail para o seletor de canais. |
| `channel-followup.json` | `ChannelMessage` | Anexa o retorno do cliente ao mesmo atendimento. |
| `channel-missing-fields.json` | `ChannelMessage` | Persiste, solicita ambos os campos ao Jev e aguarda classificação. |
| `channel-invalid-classification.json` | `ChannelMessage` | Persiste, encaminha para revisão de classificação e recebe `202`. |
| `channel-invalid-envelope.json` | `ChannelMessage` | Sem texto obrigatório. Falha estrutural com `422`. |
| `channel-accepted.json` | `ChannelReceipt` | Identifica caso e correlação do primeiro evento. |
| `agent-turn-1-request.json` | `AgentTurnRequested` | Envia relato original e classificação validada. |
| `agent-turn-1-reply.json` | `AgentReplyProposed` | Registra resposta e mantém o atendimento com a IA. |
| `agent-turn-2-request.json` | `AgentTurnRequested` | Envia relato, resposta da IA e retorno do cliente em ordem. |
| `agent-turn-2-resolve.json` | `AgentResolveProposed` | Registra a mensagem final e resolve o atendimento. |
| `agent-handoff-request.json` | `AgentTurnRequested` | Envia rodada de outro atendimento com classificação por canal e Jev. |
| `agent-handoff.json` | `AgentHandoffProposed` | Encaminha para humano com resumo e referência à mensagem analisada. |
| `agent-late-result.json` | `AgentReplyProposed` | Estrutura válida. A rodada terminou no handoff. O Rails descarta com auditoria. |
| `agent-late-discarded.json` | `AgentReceipt` | Confirma descarte definitivo de resultado atrasado. |
| `case-list.json` | `CaseList` | Página com casos em revisão, aguardando humano e resolvido. |
| `case-handoff.json` | `Case` | Detalhe com resumo, fila e bloqueio operacional. |
| `case-handoff-messages.json` | `MessageList` | Histórico inclui retorno do cliente que chegou após o disparo da rodada. |
| `case-resolved-messages.json` | `MessageList` | Histórico completo da conversa resolvida em dois turnos. |
| `case-correct-classification.json` | `CaseClassificationCorrection` | Supervisor corrige a classificação com motivo. |
| `analyst-session.json` | `Session` | Analista com acesso de consulta a duas marcas e operação em uma. |
| `supervisor-session.json` | `Session` | Supervisor autorizado nas duas marcas, sem identidade de atendente. |
| `case-human-owned.json` | `Case` | O atendente da sessão é responsável e pode agir na marca em operação. |
| `case-human-coworker.json` | `Case` | Caso visível na mesma marca, com outro responsável. |
| `case-filters.json` | `CaseFilters` | Nomes e IDs de duas marcas e suas filas visíveis ao analista. |
| `analyst-list.json` | `AnalystList` | A supervisão relaciona usuários a atendentes e obtém o ID para editar o perfil. |
| `simulator-accepted.json` | `SimulatorReceipt` | A abertura por WhatsApp devolve os identificadores da conversa. |
| `simulator-recovered-list.json` | `SimulatorCaseList` | A sessão reencontra a conversa no histórico após recarregar. |
| `simulator-recovered-case.json` | `SimulatorCase` | O detalhe recupera o canal da rota e a identidade externa para o envio. |
| `simulator-followup.json` | `SimulatorMessage` | O cliente envia outra mensagem à conversa recuperada. |
| `simulator-followup-accepted.json` | `SimulatorReceipt` | O Rails confirma o mesmo caso, conversa e correlação. |
| `case-wait-for-customer.json` | `CaseAction` | Responsável ativo solicita informação usando a versão do caso. |
| `routing-rule-brand.json` | `RoutingRule` | Encaminha a categoria para uma fila da mesma marca. |
| `configuration-audit.json` | `ConfigurationAuditList` | Criação e edição da regra são consultáveis por marca e recurso. |
| `capacity-profile.json` | `CapacityProfile` | Perfil com teto de carteira e alternativas de simultaneidade. |
| `error-403.json` | `Error` | Escrita negada a ator autenticado sem permissão. |
| `error-409.json` | `Error` | Versão defasada em uma ação. |
| `error-409-replay.json` | `Error` | Identidade de evento reutilizada com outro conteúdo. |
| `error-422.json` | `Error` | Entrada com envelope inválido. |
| `error-422-profile.json` | `Error` | Regra da edição de perfil rejeitada pelo Rails. |

A partir de `backend/`, com as dependências instaladas, execute
`bundle exec ruby ../script/check_contracts.rb`. O verificador confere a
estrutura OpenAPI 3.1, as referências locais, o JSON Schema 2020-12 e as
fixtures. Ele também confere se os dados dos exemplos permitem retomar uma
conversa, distinguir o responsável e acompanhar versões de configuração.
Autorização, persistência, concorrência e transições serão testadas nas
implementações seguintes.

Exercício curto. Abra o segundo pedido da IA, localize a resposta da primeira
rodada no histórico e confira quais campos ligam a proposta de resolução ao
segundo pedido. Depois compare a proposta atrasada com o pedido do handoff.
As identidades coincidem naquele par, mas a rodada já terminou.
