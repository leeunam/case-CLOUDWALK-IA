# Revisão crítica e alternativas do MVP

**Registro histórico:** esta revisão precede a escolha da V2 ajustada em D011.
O responsável posteriormente adotou a V2 e substituiu pesos por combinações
configuráveis. A versão atual está no [fluxo operacional](fluxo-operacional.md)
e em [perfis de capacidade](perfis-de-capacidade.md). As referências a V1 vigente
abaixo descrevem o momento original da análise.

## Estado e alcance

Análise de desenho solicitada pelo responsável antes de prosseguir com as
perguntas de planejamento. A versão vigente está no [registro de decisões](decisoes.md)
e no [fluxo operacional](fluxo-operacional.md). O desempate por maior tempo sem
receber caso está confirmado em D010.

Os exemplos abaixo são contraprovas numéricas e hipóteses de comportamento,
não medições de um sistema implementado. Não houve teste de carga. Banco,
broker, ambiente, volume de mensagens e várias políticas ainda não foram
definidos; não há evidência de capacidade para dez mil usuários simultâneos.

V1 é a proposta vigente. V1.1 reúne melhorias recomendadas compatíveis com suas
políticas. V2 é uma alternativa operacional que altera D008 e D009 e a definição
de carga contabilizada em D010; requer escolha explícita antes de substituir
qualquer parte da versão vigente.

## Avaliação principal

O modelo é coerente: há marca do atendimento, uma fila atual e um responsável
principal; várias equipes elegíveis podem atender a fila; atribuições humanas
respeitam capacidade e contexto de marca. Rails API, React e um monólito modular
são compatíveis com esse domínio.

O maior limite operacional vem da combinação de peso integral na espera,
atuação em uma marca e obrigação de concluir ou transferir todos os casos antes
de trocar. Essa combinação protege continuidade, mas reduz a possibilidade de
usar capacidade disponível entre marcas. A escolha de microserviços não altera
essa regra de operação.

O maior risco de entrega é construir um motor de distribuição e um configurador
genérico antes de demonstrar o ciclo completo de mensagem, integração, resposta
e handoff. As fronteiras, contratos e evidências desse ciclo precisam fazer parte
da definição de escopo.

## Limites operacionais da V1

### Espera pelo cliente pode prender a troca de marca

Ana tem capacidade de 5 pontos e um caso de peso 1 da marca A aguardando cliente.
Tem 4 pontos livres. Um caso de peso 3 aguarda na marca B, para a qual Ana também
tem autorização. D009 impede a troca enquanto o caso de A continuar com ela.

Se ninguém elegível puder receber o caso de A, a transferência também não
desbloqueia a situação. Há capacidade numérica livre, mas não há elegibilidade
operacional para B. A espera pode durar bastante, dependendo de resposta do
cliente ou intervenção da operação; não é uma falha que mais servidores resolvam.

**Tradeoff:** continuidade e menor mistura de marcas versus menor flexibilidade
para responder a demanda desigual entre marcas.

### Capacidade livre pode estar fragmentada

Três analistas com capacidade 4 e carga 3 têm 3 pontos livres no total. Um caso
de peso 2 não cabe em nenhum deles, mesmo que todos sejam elegíveis para a fila.
O caso tem um único responsável principal; a capacidade livre das pessoas não
pode ser somada para atribuí-lo.

**Tradeoff:** impedir sobrecarga individual pode deixar capacidade total
temporariamente sem uso. Atribuição manual não cria a capacidade que falta.

### Casos pesados podem esperar indefinidamente

Se um caso pesado não cabe, mas novos casos leves ocupam continuamente as
pequenas vagas que surgem, a vaga necessária pode nunca se formar. Escolher o
melhor analista não resolve a ordem de escolha dos casos.

Prioridade, ordem de chegada e tratamento de casos que não cabem precisam de
política própria. Parar toda a fila no primeiro caso pesado protege sua vez, mas
pode impedir trabalho que caberia. Permitir ultrapassagens melhora ocupação em
alguns cenários, mas exige limite de espera, alerta ou reserva de capacidade.
Nenhuma dessas políticas está aprovada ainda.

### Menor carga absoluta tem uma consequência deliberada

Ana, capacidade 5 e carga 3, recebe um caso de peso 1 antes de Bruno, capacidade
10 e carga 4. Depois disso, ambos têm 4 pontos, mas ocupações de 80% e 40%.
Isso cumpre D010: equilibra pontos ocupados, sem tentar igualar porcentagens.

Não é um erro do algoritmo. O painel e o experimento devem permitir interpretar
essa diferença. Esta revisão preserva a escolha por carga absoluta; a alternativa
proposta abaixo também a preserva para o trabalho ativo.

### Pesos não comprovam esforço humano real

Um caso rotulado como simples pode exigir investigação longa. Se os pesos
estiverem mal calibrados, pontos equilibrados podem coexistir com esforço real
desigual. O protótipo pode comprovar respeito aos pesos configurados; não pode
comprovar produtividade de uma operação humana a partir de dados sintéticos.

Alterar o peso ou reduzir a capacidade enquanto há casos atribuídos também pode
produzir uma carga acima do limite novo. É necessário definir se configurações
afetam apenas casos futuros e como ocorre uma reclassificação explícita.

### Equipe compartilhada não garante pessoas disponíveis

Uma fila pode ter várias equipes e ainda não ter nenhum analista disponível,
operando na marca correta e com capacidade suficiente. Offline, pausa, preparação
de troca e revogação de autorização precisam de comportamento explícito para
novas atribuições e casos já existentes.

Trocar o nome de uma equipe ou aumentar workers não resolve ausência de
candidato. A interface deve informar o motivo do bloqueio.

## Limites técnicos a tratar no desenho

| Situação | Falha possível | Proteção proposta |
| --- | --- | --- |
| Duas atribuições usam a mesma capacidade livre | Ultrapassar o limite ou registrar dois responsáveis | Reservar capacidade e atribuir o caso numa operação consistente; revalidar candidato. |
| Transferência ocorre junto com troca de marca | Novos casos da marca anterior ou mudança com casos pendentes | Preparação que suspende novas atribuições e verificação conjunta antes da troca. |
| Mensagem é gravada, mas o processo para antes de emitir o webhook | Agente nunca recebe o caso | Registrar também o envio pendente na mesma transação e despachá-lo depois. |
| Evento é reentregue após uma falha | Resposta, atribuição ou reserva duplicada | Identificador do evento e processamento idempotente. |
| IA termina de responder após handoff | Resposta antiga aparece durante atendimento humano | Verificar estado e versão da responsabilidade na publicação; registrar resposta obsoleta sem publicá-la como atual. |
| Muitas falhas causam novas tentativas imediatas | Mais carga durante a indisponibilidade | Novas tentativas espaçadas, com limite, e falhas visíveis para investigação. |
| Equipe perde autorização enquanto há casos ativos | Casos sem cobertura ou acesso indevido | Revalidação de acesso e procedimento explícito de revogação/transferência; preservar histórico. |
| Interface reconecta ou recebe eventos fora de ordem | Mensagens duplicadas, sumidas ou antigas na tela | Identificadores estáveis, sequência por conversa e recuperação do estado pela API. |

O padrão outbox registra a alteração e o envio pendente na mesma transação;
isso não elimina a possibilidade de reentrega. O receptor ainda precisa lidar
com repetição. [Referência: AWS sobre outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).

Limitar e espaçar novas tentativas ajuda a evitar que falhas sejam ampliadas
pela própria recuperação. [Referência: AWS sobre retries](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_mitigate_interaction_failure_limit_retries.html).

### Disputa de capacidade também pode limitar throughput

Vários workers podem tentar escolher o mesmo analista de menor carga. Travas e
revalidação são parte da correção, mas trazem espera. Consultar toda a carteira
de todos os candidatos a cada atribuição também pode ficar caro.

Uma implementação candidata mantém a reserva de carga junto da atribuição,
com histórico e verificação de consistência. O mecanismo concreto depende do
banco escolhido. PostgreSQL, ainda candidato, oferece recursos para coordenar
consumidores; pular linhas bloqueadas pode reduzir disputa, mas altera a visão
disponível na seleção e não deve ser confundido com uma garantia de ordem global
estrita. [Referência: bloqueios no PostgreSQL](https://www.postgresql.org/docs/current/sql-select.htm).

Não há medição para afirmar que banco, broker ou número de workers é o gargalo
dominante. Contenção, tempo de atribuição e idade das filas devem ser medidos.

### Interface e volume de referência

Uma listagem unificada sem paginação pode crescer demais. Atualizar muitas telas
por consultas frequentes pode gerar carga relevante: dez mil telas consultando
a cada dois segundos significariam cerca de cinco mil consultas HTTP por segundo,
antes das mensagens. Esse cálculo é ilustrativo, não uma carga escolhida.

Precisamos separar clientes conectados, analistas conectados, novos casos por
segundo, mensagens por segundo e atualizações de tela. A plataforma pode aceitar
mensagens rapidamente e ainda ter atendimento lento por falta de humanos.

## V1.1 — Melhorias compatíveis com as decisões vigentes

Esta é a recomendação inicial para o MVP: manter as políticas escolhidas e
delimitar sua implementação e suas evidências.

1. Preservar marca, equipes compartilháveis, filas por marca, fila única,
   responsável único, carga absoluta e desempate favorecendo quem está há mais
   tempo sem receber uma atribuição.
2. Preservar peso integral na espera e troca somente após concluir/transferir.
3. Mostrar no painel carga, capacidade, peso de cada caso, espera e motivo de
   não atribuição ou de bloqueio da troca.
4. Propor uma preparação de troca que suspenda novas atribuições antes de
   concluir/transferir os casos existentes, conforme o fluxo já apresentado.
5. Usar configuração delimitada de filas, categorias, pesos e encaminhamento.
   Um motor genérico com scripts arbitrários não é necessário para demonstrar
   edição pela operação.
6. Propor alterações de configuração para casos futuros no primeiro recorte;
   definir separadamente reclassificação e tratamento de casos já atribuídos.
7. Prever reserva consistente de capacidade, eventos identificados, envios
   persistidos, reentregas seguras e proteção contra IA tardia.
8. Expor casos pesados sem vaga e casos antigos para intervenção da operação;
   aprovar uma política simples de ordem e espera antes da implementação.

**Ganhos:** menor mudança de produto, regras fáceis de demonstrar, continuidade
do atendimento e foco na robustez exigida pela integração.

**Custos:** mais trabalho de persistência e testes do que um protótipo ingênuo;
o bloqueio operacional de espera e troca permanece. Alertas não criam capacidade.

### Organização técnica candidata

Manter Rails API e React. Dentro do monólito, organizar responsabilidades em:

- Configuração e acesso: marcas, equipes, participantes e vínculos com filas.
- Atendimento: mensagens, estados e responsabilidade principal.
- Distribuição: candidatos, carga, capacidade, atribuição e transferência.
- Integração: webhooks, eventos, tentativas e comunicação com o atendente mock.
- Auditoria e medição: histórico das decisões e resultados do experimento.

Processos de segundo plano podem usar o mesmo código Rails. Broker e atendente
simulado ficam explícitos na integração; tecnologia do broker e localização do
adaptador entre webhook e mensageria ainda precisam ser escolhidas. O banco
relacional único é uma proposta técnica; PostgreSQL não foi confirmado.

O primeiro caminho demonstrável deve atravessar entrada, persistência, evento,
atendente mock, resposta, handoff e resposta humana. Depois se amplia a cobertura
de marcas, equipes, configurações e carga. Contratos e limites de responsabilidade
precisam preceder tarefas dependentes executadas por agentes em paralelo.

## V2 — Separar responsabilidade do caso e atenção ativa

Esta versão pode aproveitar melhor os períodos de espera, mas altera escolhas
confirmadas. É proposta para comparação, sem adoção automática.

### Funcionamento proposto

- Manter o mesmo responsável principal durante a espera pelo cliente.
- Ter dois limites por analista: pontos de trabalho ativo e quantidade total
  de casos não concluídos sob sua responsabilidade, incluindo pendências.
- Um caso aguardando cliente continua na carteira e conta no limite total,
  mas deixa de consumir o peso integral do orçamento de trabalho ativo.
- Manter uma única marca de atuação humana por vez. Permitir mudar de contexto
  após terminar ou transferir os casos que exigem ação imediata, mesmo havendo
  pendências de cliente em outra marca.
- Quando o cliente retorna, o caso entra em estado de aguardando retomada na
  sua fila operacional atual. Isso é um estado/listagem, não uma segunda fila
  operacional nem um segundo responsável.
- A retomada revalida capacidade e marca em operação antes de voltar ao trabalho
  ativo. O caso não interrompe automaticamente um atendimento de outra marca.
- Continuar escolhendo a menor carga absoluta para o orçamento ativo, com o
  desempate já escolhido.

### Escolhas alteradas

- D008: a espera deixa de reservar peso integral no orçamento ativo; ocupa uma
  vaga na carteira total de casos.
- D009: a troca deixa de exigir zerar todas as pendências atribuídas; exige
  terminar/transferir o trabalho que requer atenção imediata.
- D010: preserva a preferência por carga absoluta, mas muda a carga comparada
  para pontos de trabalho ativo; os casos em espera ficam limitados pela carteira
  total em outra métrica.

D003 a D007 são preservadas em sua estrutura. A preferência de D010 por carga
absoluta é mantida, mas sua semântica de carga é alterada; portanto D010 não é
preservada integralmente.

### Ganhos e custos

**Ganho potencial:** pessoas com clientes que demoram a responder podem ajudar
outra marca sem transferir todo o histórico para outro responsável. O limite de
carteira impede acumular indefinidamente novos casos só porque estão em espera.

**Custos:** mais estados, duas métricas de capacidade, retomada e prioridades
entre marcas, além de interface e testes mais complexos. A resposta de um cliente
pode aguardar a retomada da sua marca. Se novas atribuições nunca pararem na
marca atual, pendências de outra marca podem esperar indefinidamente.

Seriam necessárias regras adicionais para limitar essa espera, preparar a troca
quando há retomadas antigas e transferir casos se o responsável ficar indisponível.
V2 não permite atender duas marcas ao mesmo tempo e não garante maior throughput.

Ferramentas existentes também tratam liberação de capacidade e retorno de
conversas como políticas explícitas; liberar sem controlar a reativação pode
ultrapassar capacidade. [Referência: Zendesk](https://support.zendesk.com/hc/en-us/articles/4776409839770-Creating-capacity-rules-to-balance-agent-workloads).

## Comparação resumida

| Critério | V1 vigente | V1.1 proposta para MVP | V2 alternativa |
| --- | --- | --- | --- |
| Peso na espera | Integral | Integral | Fora do orçamento ativo; mantém vaga na carteira total. |
| Troca de marca | Concluir/transferir tudo. | Mesma regra, com preparação e bloqueios visíveis. | Pode manter pendências de outra marca, sem atuar nelas simultaneamente. |
| Distribuição | Menor carga absoluta. | Mesmo critério, com execução consistente. | Menor carga absoluta de trabalho ativo. |
| Continuidade | Mesmo responsável, salvo transferência. | Igual à V1. | Mesmo responsável pode retomar depois. |
| Uso de períodos ociosos | Limitado pelas reservas e pela marca. | Mesmo limite operacional. | Potencialmente maior; depende das regras de retomada. |
| Complexidade | Regras definidas; falhas ainda precisam de desenho. | Implementação delimitada com proteções de execução. | Mais estados, dois limites e coordenação de retomadas. |
| Principal risco | Capacidade presa em pendências. | Mesmo risco, agora observável e testável. | Acumular retomadas e elevar tempo de resposta. |

## Evidências necessárias antes de alegar melhoria

| Cenário | Evidência esperada |
| --- | --- |
| Mesma carga, última atribuição diferente | Preferência pelo analista há mais tempo sem receber caso. |
| Um analista aparece por duas equipes | Uma única candidatura e reserva por pessoa. |
| Duas atribuições disputam uma vaga | Respeito à capacidade e responsabilidade única. |
| Cliente fica sem responder | Carga e possibilidade de trocar marca seguem a política escolhida. |
| Capacidade livre fragmentada | Caso pesado aguarda com motivo explícito; não se inventa capacidade. |
| Fluxo contínuo de casos leves | Medir espera dos pesados e efeito da política de ordem. |
| Analista offline ou vínculo revogado | Novas atribuições e casos existentes têm tratamento rastreável. |
| Broker/adapter indisponível e depois recuperado | Eventos persistidos têm resultado rastreável, sem efeitos duplicados indevidos. |
| Resposta da IA chega após handoff | Não é publicada como resposta do responsável atual. |
| Vários clientes retornam juntos na V2 | Retomadas respeitam marca e capacidade, com espera medida. |

Comparar V1/V1.1 e V2 usando os mesmos casos sintéticos, elegibilidade, capacidade,
pesos, chegadas e tempos simulados de resposta. Medir espera até atribuição e
retomada, casos concluídos, carga reservada/ativa, idade dos casos pesados,
transferências e trocas de marca. Separar esses resultados do teste técnico de
requisições, mensagens, filas do broker, CPU, memória e latência.

Os resultados só sustentam conclusões para os cenários e o ambiente declarados.
Um simulador pode validar políticas; não demonstra produtividade humana real.

## Recomendação desta revisão

Para o MVP, preferir V1.1: conservar as decisões já escolhidas, fechar estados e
contratos, demonstrar o ciclo completo e medir os limites operacionais com
honestidade. V2 merece consideração se aproveitar espera e remanejar pessoas
entre marcas for uma prioridade maior do que reduzir estados e regras no MVP.

A recomendação é condicional ao tempo disponível e ao recorte final, ainda
pendentes. Serviços independentes, Redis ou mais workers não são correções
automáticas para as restrições operacionais identificadas.
