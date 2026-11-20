# Modelo de dados e ordem de bloqueios

Os IDs de domínio são UUIDs. A base da F01 cria estruturas de operação. F02
acrescenta atendimentos, mensagens, trilha e integração. F03 usa o mesmo modelo
de marca, equipe, fila e responsável para distribuição e retomada.

## Operação

| Entidade | Vínculos e invariantes |
| --- | --- |
| Marca e equipe | `brand_teams` tem uma autorização única por `(brand_id, team_id)`. Uma equipe pode atuar em múltiplas marcas. |
| Fila de atendimento | `support_queues` pertence à marca. A fila padrão é ativa e única na marca. A operação garante uma fila padrão e ao menos uma equipe por fila ativa. |
| Equipe responsável pela fila | `queue_teams` referencia `support_queues(id, brand_id)` e `brand_teams(id, brand_id)` por chaves compostas, mantendo a mesma marca nos dois vínculos. |
| Canal e catálogo | Canal tem uma marca e um tipo. Uma categoria tem uma chave por marca. O campo de prioridade usa o catálogo comum da demo. A identidade da marca chega da credencial do canal. |
| Pessoas e acesso | `team_memberships` vincula analistas a equipes. `supervisor_brands` autoriza supervisores em marcas explícitas. Atendente humano referencia o usuário. O mock tem identidade de atendente própria. |
| Capacidade | Uma versão ativa de perfil por analista. A versão guarda limite de carteira e alternativas, cada qual um conjunto de pares de prioridade e categoria com limites inteiros. |
| Encaminhamento F06 | Regra versionada tem `brand_id`, posição, filtros opcionais e fila de destino na mesma marca por vínculo composto. O Rails registra a regra e versão aplicadas ao caso. |
| Auditoria de configuração F06 | Evento administrativo é persistido na transação da mudança e indexado por marca, tipo, ID do recurso e data. Registra ator, versão e fotografias autorizadas antes e depois. Pode existir antes da abertura de qualquer atendimento. |

## Atendimento e integração previstos para F02–F04

- O atendimento possui uma marca imutável, um canal de origem, uma fila
  operacional atual e um responsável principal opcional. Referências compostas
  apontam para `channels(id, brand_id)` e `support_queues(id, brand_id)`. Caso
  anterior precisa compartilhar marca, canal e identidade da conversa externa.
  O Rails mantém as transferências anteriores na trilha.
- A conversa é localizada pelo canal e ID externo de conversa. A entrada
  referencia também o cliente externo e guarda a chave
  `(channel_id, source_event_id)`, SHA-256 do corpo arquivado e o resultado original. A
  entrada do simulador também guarda o SHA-256 do pedido normalizado do navegador. Uma
  restrição única serializa deduplicação. Um vínculo à conversa serializa
  entrada simultânea e criação de novo caso após resolução.
- Mensagens identificam autor, caso e ordem única `(case_id, sequence)).
  Corpos de eventos da IA e mensagens externas preservam seus IDs de origem.
  O atendimento guarda versão da classificação, versão pública do caso e
  geração de atribuição. Troca do responsável invalida a geração usada pelo
  responsável anterior.
- Rodada referencia atendimento, geração e o pedido do mock. Apenas uma
  rodada pode ficar em voo por caso. O outbox armazena o evento com ID único
  e próxima data de tentativa. A integração publica em `agent.requests` e
  consome `agent.events` por grupos Kafka independentes. Os tópicos retêm os
  registros por prazo finito; offsets não removem eventos e não substituem o
  histórico/auditoria no PostgreSQL. A confirmação do callback registra o
  `event_id` do retorno para aplicar ou descartar uma única vez. A aplicação
  deduplica reenvios e não presume exatamente-uma-vez na cadeia HTTP + banco.
- Auditoria persiste junto à mudança e associa caso, ator, horário, motivo,
  estado anterior e novo, vínculos aplicados e IDs de correlação. Índices
  cobrem fila/estado/ordem de espera, carteira por responsável e estado,
  mensagem por caso e ordem e outbox por próxima tentativa.

## Ordem proposta para F03

Adotar a mesma ordem de aquisição entre distribuição, retomada, transferência,
edição de configuração, mudança de marca e revogação de acesso. Quando uma
operação usa mais de uma linha do mesmo tipo, adquire por UUID crescente.

1. Bloquear as marcas afetadas e depois as configurações usadas pela operação,
   nesta ordem de tipos. Filas, vínculos marca/equipe, vínculos fila/equipe,
   permissões e regras.
2. Bloquear todos os analistas afetados, incluindo origem e destino em
   transferências. Usar o registro do analista para coordenar alterações ou
   leituras de seu perfil ativo, disponibilidade e carteira.
3. Bloquear conversas quando a operação cria ou seleciona o atendimento atual,
   depois bloquear os atendimentos e suas rodadas. Registrar mensagens,
   efeitos de idempotência, auditoria e outbox na mesma transação.

As transações podem consultar candidatos antes dos bloqueios. Depois de
adquiri-los, o Rails revalida versão, fila, estado, marca ativa, permissões,
carteira e combinação. Se a revalidação exigir novos bloqueios que precedam
os já adquiridos, reinicia dentro do mesmo protocolo. Chamadas ao broker e ao
Jev ocorrem depois do commit. O teste da última vaga em F03 deve disputar
duas atribuições e observar apenas uma aceita.

### Aplicação na F03

- `users` guarda a marca de destino, se houver troca em preparação, e o horário
  da última atribuição nova. Retomadas conservam esse horário. A auditoria da
  operação do analista fica em `analyst_operation_audits`.
- `case_command_receipts` registra o conteúdo por hash e a resposta original
  das mutações do caso, com chave única por caso, usuário, operação e chave
  de idempotência. O recibo e a mudança do caso compartilham a transação.
- A marca serve de bloqueio de coordenação para o atendimento. O PostgreSQL usa
  `FOR NO KEY UPDATE` nessa linha para permitir verificações de chave estrangeira
  quando uma troca altera a marca em operação. A distribuição bloqueia os
  analistas por UUID antes de revalidar o caso. O ajuste da própria operação
  bloqueia as marcas por UUID antes de bloquear o analista, pois pode preparar,
  cancelar ou concluir uma troca.
- O distribuidor recebe sinais após o commit de handoff, retorno do cliente,
  espera, resolução, transferência e ajuste da operação. O worker também
  reavalia as filas a cada minuto e identifica casos cujo responsável perdeu
  acesso. Alterações de configuração em F06 devem seguir a mesma ordem de
  bloqueios e solicitar reavaliação após publicar.

### Aplicação na F06

- A mutação administrativa adquire as marcas por UUID antes de publicar
  vínculos, regras ou perfis. Isso serializa a seleção inicial da fila e
  mantém estável o escopo das equipes compartilhadas. A remoção de acesso
  adquire usuários e atendimentos em ordem de UUID para reconciliar a carteira
  antes do commit.
- A fila e a equipe têm versão própria. A criação de equipe incrementa
  a versão de cada marca que recebe a autorização. Revogar o último vínculo
  deixa a equipe consultável pela marca que a desvinculou para edição e
  reativação administrativa.
- O perfil de capacidade mantém as versões anteriores. A trilha administrativa
  tem uma entrada por marca afetada, com a mesma correlação. Cada entrada de
  perfil contém apenas os pares de categorias presentes no catálogo daquela
  marca. A trilha do caso registra a fila, o ID e a versão da regra inicial.
