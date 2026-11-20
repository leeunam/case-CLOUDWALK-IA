# Rodada paralela · configuração F06 e robustez F07-A

Preparação central em 2026-11-20, sobre a base de código `67906fe`.
O commit que acrescenta este documento será a base comum das duas frentes;
o integrador informa seu hash nos prompts. Não consumir alterações locais
ou commits da outra frente antes da integração central.

## Frentes e propriedade dos arquivos

| Frente | Branch | Worktree na raiz do repositório | Pode editar |
| --- | --- | --- | --- |
| F06 | `feat/configuracao-operacao` | `.worktrees/f06-configuracao` | Rails, React, migrations/schema, contratos/fixtures, testes da configuração e `docs/f06.md`. Ajustes de execução estritamente necessários devem ser justificados. |
| F07-A | `feat/ensaios-robustez` | `.worktrees/f07-robustez` | Apenas `script/f07/` e `docs/f07.md`: runner, testes, fixtures de ensaio, proxy de falhas e override Compose próprios. |
| Integrador | `main` e futura branch de integração | Checkout central | Planejamento, revisão, correções comuns e aceite combinado; integração das branches após conferir o resultado. |

Ler AGENTS.md, CONTEXT.md, as tarefas no plano, a especificação, as decisões
atuais e os contratos antes de implementar. Os registros antigos de pesos e
troca de marca são históricos: preservar a política V2 vigente. Reutilizar
as worktrees preparadas; não criar outro clone por iniciativa própria.
Se o acesso aos metadados Git falhar, registrar o impedimento e continuar
as verificações que não dependem dele. O integrador resolve a gravação Git.

## F06 · configuração operacional pela API e pela interface

Entregar a tarefa F06 completa como fatias pequenas, verificáveis e commitadas.
Começar pelo caminho vertical supervisor → criar fila → vincular equipes →
configurar regra → novo atendimento na fila escolhida → auditoria. Prosseguir
para catálogo/perfis e revisão/falhas, preservando os fluxos já integrados.

1. Implementar as rotas administrativas já previstas em OpenAPI e as telas
   React conectadas à API: marcas existentes e seus vínculos, equipes e seus
   membros, filas, regras ordenadas, catálogo, analistas e perfis de capacidade.
   O contrato atual prevê listar/editar marcas, sem criação de marca. Não
   acrescentar criação/exclusão de marcas como requisito implícito da rodada.
2. A regra ativa de menor posição que corresponda escolhe uma fila da marca;
   a fila padrão é fallback. Aplicar quando a classificação inicial ficar
   válida, tanto na entrada quanto no complemento Jev ou correção inicial.
   Registrar regra e versão. Edição posterior não move casos em curso;
   reclassificação de caso em andamento conserva sua fila.
3. Validar vínculos marca/equipe/fila, fila padrão ativa e dependências para
   desativação. Equipe compartilhada exige autorização sobre todas as marcas
   afetadas pela edição. Revogar vínculo retira acesso REST/WebSocket e
   reconcilia os responsáveis/carteiras de acordo com a especificação.
4. Publicar versões com `expected_version` e gravar auditoria na mesma
   transação, com ator, marcas afetadas e fotografias antes/depois sem segredos
   ou dados de marcas não autorizadas. Preservar a ordem dos bloqueios de
   marca, analistas e casos; operações que afetam várias marcas precisam de
   uma ordem estável. Retornar conflitos sem efeitos parciais.
5. Perfis usam alternativas de pares prioridade/categoria e teto de carteira:
   um conjunto ativo deve caber inteiro numa única alternativa. Não somar
   alternativas, pesos ou criar complexidade. Redução/edição preserva ativos
   e impede novas entradas/retomadas incompatíveis conforme a especificação.
   O catálogo aceita categorias configuráveis; preservar os quatro códigos
   de prioridade do contrato e as restrições do adaptador Jev. Verificar
   dependências de categorias em regras/perfis e a apresentação no cliente.
6. Dar ao supervisor revisão de classificação, consulta de falhas, correção
   com motivo, auditoria, transferência e recuperação por `retry_agent` ou
   `force_handoff`. Reutilizar serviços e transições F03/F04, sem acesso
   administrativo direto às tabelas como caminho do produto.

O backend F02–F05 já está implementado, mas as rotas de configuração
declaradas em OpenAPI ainda não estão no routes.rb. F06 é a única dona das
mudanças de produto nesta rodada. Identificar lacunas de contrato necessárias
para a configuração funcionar (inclusive catálogo dinâmico no React),
documentar os consumidores e atualizar schema/fixtures em conjunto. Preservar
as interfaces existentes; mudança incompatível ou ampliação de produto volta
ao chat central. A F07-A continua sobre a base congelada durante esse trabalho.

### Aceite F06

- Supervisor cria uma fila, vincula duas equipes autorizadas e publica uma
  regra. Uma nova entrada segue a regra; uma já existente mantém a fila.
- Criar/editar equipe e vínculos respeita escopo, inclusive equipe compartilhada.
  Vínculos de outra marca, perda da fila padrão e desativação com dependências
  são recusados sem alteração parcial.
- Editar catálogo e publicar perfil muda o comportamento de novos casos e da
  elegibilidade. Alternativas inválidas, pares duplicados, versão defasada e
  teto insuficiente são recusados. Reduzir perfil com ativos preserva os casos.
- Revogação impede leitura/ação/aviso e reconcilia responsabilidade conforme
  a política existente. Duas edições concorrentes não perdem atualizações.
- Corrigir caso em revisão encaminha uma vez; reentrega não duplica rodada;
  corrigir caso já resolvido é conflito. Recuperação usa as ações canônicas.
- A auditoria administrativa é consultável mesmo sem atendimento associado,
  paginada e limitada às marcas autorizadas.
- Testes Rails no runtime fixado, contratos, lockfile/testes/build frontend e
  uma passagem real no navegador. Registrar o que passou, falhou ou não rodou.

## F07-A · ensaios sobre F02–F05, em paralelo

Construir um verificador reutilizável e executá-lo sobre a base comum.
F07-A é uma entrega parcial da F07: configuração/revogação pela administração
e recuperação pela tela de supervisão serão exercitadas após integrar F06.

O runner deve subir/usar uma pilha isolada com Rails, PostgreSQL, Kafka,
ponte, mock, outbox e worker quando necessário. Um override próprio pode
acrescentar os componentes sem editar o Compose principal. Reutilizar os
Dockerfiles, contratos e serviços existentes; dependências de ensaio ficam
declaradas dentro de `script/f07/`.

### Cenários desta fatia

1. Kafka indisponível depois de aceitar uma entrada: mensagem e outbox
   permanecem no banco. Restaurar Kafka e recuperar o processo necessário;
   conferir publicação e um único efeito. Se exigir reinício manual, registrar
   como limitação; não chamar isso de recuperação automática.
2. Mesmos bytes/evento reentregues no webhook e no callback mantêm recibos e
   contagens; corpo divergente com mesmo ID é conflito. Um proxy pode devolver
   falha somente depois de o Rails persistir, para provar resposta ambígua.
   Incluir a expectativa `X-Simulator-Session-Id` nas escritas do cliente real
   e a troca de identidade durante confirmação incerta.
3. Releitura Kafka e retorno de rodada antiga após handoff não duplicam
   mensagens nem sobrescrevem o humano; o descarte permanece auditado.
4. Assinaturas/segredos inválidos são rejeitados sem efeito. Acesso cruzado
   REST/WebSocket e audiência errada são recusados; logout encerra acesso.
   Confirmar aviso entre processos e recuperação do estado após reconexão.
5. Falhas transitórias esgotadas publicam em `agent.failures` com origem e
   só depois avançam o offset. Se publicar a falha não funcionar, o offset
   fica pendente e o mesmo registro deve ser reentregue após a recuperação:
   registrar tópico, partição e offset antes/depois. Provar com broker/HTTP
   reais, além dos testes isolados já existentes. Usar proxies/mecanismos
   externos ao código de produção.

Cada cenário declara pré-condição, ação, pós-condição e evidência, incluindo
IDs/correlação, tópico/partição/offset quando aplicável, backlog, contagem de
mensagens e auditoria. Gerar relatório estruturado por cenário: aprovado,
reprovado ou bloqueado com motivo; falhas não podem virar sucesso silencioso.
Uma tentativa de conexão ou um timeout isolado não prova perda de evento.

Esperar Kafka e grupos ficarem prontos por condições observáveis. A integração
anterior observou rebalance demorado ao recriar consumidores; não usar esse
tempo como SLA nem aumentar timeout do produto para esconder um teste frágil.
Importar helpers só depois de conferir que não executam ensaios ao importar.

Se o verificador expuser bug do produto, entregar a reprodução e o diagnóstico
em `docs/f07.md`. Não corrigir Rails, React, ponte, contratos, schema ou Compose
principal nessa branch. Esses arquivos pertencem à F06/integração central.
Isso permite preservar uma reprodução falhando até a correção apropriada.

## Execução isolada e retorno

- Usar projetos Compose distintos: `cloudwalk_f06_dev` e `cloudwalk_f07_a`,
  com portas de aplicação distintas (sugestão: API/UI 3106/5176 para F06 e
  3107/5177 para F07-A, após conferir disponibilidade). Não disputar o mesmo
  volume/banco, nome de contêiner, grupo ou serviços de outra tarefa.
- Preparar desenvolvimento e teste em série. Cada frente pode iniciar/parar
  apenas os recursos da sua pilha. Não executar ensaio destrutivo no ambiente
  do usuário; não encerrar recursos da outra frente.
- Usar dados sintéticos e Jev fixture ou classificação pronta. A chamada real
  TypeSafe continua pendente da chave e não bloqueia esta rodada. Não imprimir
  credenciais/cookies/tokens nos artefatos. Não testar dez mil usuários aqui;
  experimento de carga e métricas de qualidade são F08.
- Cada agente entrega tarefa, base, branch, worktree, commits, mudanças,
  comandos/resultados reais, verificações pendentes e um exercício curto de
  aprendizagem. Usar Conventional Commits em português e arquivos explícitos.
- Não mesclar nem publicar branches. O usuário traz os dois relatórios a este
  chat; o integrador revisa e integra. Concluir primeiro as fatias independentes
  sem esperar commits não publicados da outra worktree.

## O que fica para este chat

Revisar F06 e F07-A, resolver bugs do produto revelados pelos ensaios e unir
as branches numa base comum. Reexecutar as regressões F02–F05 e a matriz F07
com configuração criada por API/UI da F06: revogação de vínculo/equipe/fila,
restrições de supervisor em equipes compartilhadas, corrida de configuração
com atribuição/correção e recuperação pela supervisão. Só esse resultado
combinado pode concluir a F07 inteira. Publicação e carga permanecem fora
desta integração.
