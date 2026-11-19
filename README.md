# Help desk multimarca CloudWalk

Projeto individual do TAPI Inteli/CloudWalk. A plataforma terá canais simulados,
atendente de IA simulado via webhooks e broker, filas editáveis e handoff humano.
O Jev complementará apenas categoria e prioridade ausentes.

## Estado da entrega

F01 prepara o ambiente, o banco inicial e os contratos. Rails expõe a consulta
de saúde, React verifica essa consulta, PostgreSQL contém a operação sintética
e Kafka fica pronto para a integração de F02. As rotas de atendimento e
administração descritas nos contratos serão implementadas nas próximas tarefas.

Verificação local da F01 em 2026-11-17 passou com cinco testes Rails e quatorze
asserções, OpenAPI e 43 fixtures, build React/TypeScript, execução de um job
pelo worker e instalação com bancos vazios. O teste de reinício preservou uma
autorização removida. O aviso de dependência de desenvolvimento está descrito
ao fim deste README.

Em 2026-11-18, Kafka passou a ser o broker padrão. O teste de mensageria
consumiu e releu o mesmo evento com grupos diferentes e confirmou a leitura
de um evento após recriar o contêiner com o volume persistente.

- [Escopo e arquitetura](docs/planejamento/especificacao-mvp.md)
- [Backlog e critérios de aceite](docs/planejamento/plano-de-execucao.md)
- [Decisões confirmadas](docs/planejamento/decisoes.md)
- [Contratos, exemplos e modelo de dados](docs/contratos/README.md)
- [Instruções para agentes](AGENTS.md)

## Instalação e execução local

É necessário Git, Docker e o plugin Docker Compose com suporte a `--wait`.
Ruby, Bundler e Node executam nos contêineres. No diretório deste README, rode

```sh
docker compose up --build --wait
```

Na primeira execução o Docker baixa as imagens, instala as dependências, cria
os bancos e carrega o seed. Nos próximos inícios prepara as migrações pendentes.
PostgreSQL precisa estar saudável antes da preparação
do banco. A API inicia após a preparação. A interface aguarda a API e a
preparação dos tópicos Kafka.
[Inicialização no Compose](https://docs.docker.com/compose/how-tos/startup-order/)

| Componente | Acesso local |
| --- | --- |
| React | http://localhost:5173 |
| Saúde Rails + PostgreSQL | http://localhost:3000/api/v1/health |
| Kafka na rede interna Docker | `kafka:9092` |

As variáveis de `.env.example` permitem mudar portas, credenciais locais e
retenção do Kafka. Para usar
outros valores, copie esse exemplo para `.env` antes de subir. Serviços internos
usam os nomes `db`, `api` e `kafka` dentro da rede do Compose. As portas
publicadas ficam limitadas ao computador local.

Para conferir os serviços e o banco

```sh
docker compose ps
curl --fail http://localhost:3000/api/v1/health
docker compose exec -T api bundle exec rails runner 'puts Operations::Brand.pluck(:name)'
```

A resposta de saúde esperada é `{"status":"ok","database":"ok"}`. O banco
contém duas marcas fictícias, três equipes, quatro filas, seis canais, três
analistas e um supervisor. Uma equipe atende ambas as marcas e cada fila tem
duas equipes autorizadas. Os perfis usam prioridade e categoria em combinações
alternativas e teto de carteira inicial de seis casos.

Alex participa das duas equipes da fila Aurora, Bia participa da equipe exclusiva
Aurora e Cris participa da equipe compartilhada, com Horizonte em operação.
Essas pessoas permitem demonstrar deduplicação por equipe e restrição de marca.

Para recompor explicitamente os dados iniciais da demonstração sem duplicar os
registros existentes, incluindo vínculos de autorização que tenham sido removidos

```sh
docker compose exec -T api bundle exec rails db:seed
```

Para acompanhar erros ou parar o ambiente preservando os dados

```sh
docker compose logs --tail=80 api worker db_setup
docker compose down
```

## Entendendo o caminho

1. O navegador abre o simulador React em `localhost:5173`.
2. Em **Status da API**, o React faz `GET /api/v1/health`. O proxy do Vite entrega a requisição ao Rails.
3. [A rota Rails](backend/config/routes.rb) chama
   [HealthController](backend/app/controllers/api/v1/health_controller.rb).
4. O controller consulta PostgreSQL e devolve JSON. React mostra o resultado.

Em Python/FastAPI, esse controller equivale à função ligada a uma rota. O model
Active Record representa uma tabela e oferece consultas como
`Operations::Brand.find_by(code: "aurora")`. O arquivo de migration descreve
a criação ou alteração de tabelas. O seed cria os dados iniciais da demonstração.

O worker executa jobs internos com Solid Queue, persistidos num segundo banco
PostgreSQL no mesmo serviço. Kafka transportará mensagens entre plataforma,
ponte e atendente simulado em F02. [Active Job e Solid Queue](https://guides.rubyonrails.org/active_job_basics.html)

## Eventos e retenção no Kafka

O Compose inicia Kafka em modo KRaft, com um nó para a demonstração. O serviço
`kafka_setup` cria `agent.requests`, `agent.events` e `agent.failures`, cada um
com três partições e replicação um. O volume `kafka_data` mantém os registros
entre reinícios. Os serviços usam `kafka:9092` dentro da rede Docker.

A política `cleanup.policy=delete` e a configuração `retention.ms` controlam
a expiração dos registros. A retenção inicial é de sete dias
(`KAFKA_RETENTION_MS=604800000`). A leitura avança a posição de um grupo de
consumidores. Outros grupos podem ler os mesmos eventos enquanto estiverem
retidos. O histórico persistente dos atendimentos e a auditoria ficam no
PostgreSQL. [Conceitos do Kafka](https://kafka.apache.org/intro/)

O valor `KAFKA_RETENTION_MS=-1` permite desativar a expiração por tempo.
[Configuração de retenção](https://kafka.apache.org/44/configuration/topic-configs/#retention.ms)

Para listar os tópicos e demonstrar o consumo seguido de releitura

```sh
docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list
docker compose exec -T kafka bash /workspace/script/check_kafka.sh
```

O teste cria um tópico temporário, publica um evento, faz uma leitura, avança
a posição do primeiro grupo e relê o evento com outro grupo. Ao terminar,
remove apenas o tópico e os grupos criados para o teste. `kafka_setup` reaplica
a retenção configurada quando é executado novamente. O protocolo da F02 usa
`case_id` como chave dos eventos e confirma offsets após persistir o efeito
ou registrar a falha, conforme o [contrato](docs/contratos/README.md).

## Verificação da F01

```sh
docker compose exec -T api bundle exec ruby /workspace/script/check_contracts.rb
docker compose exec -T -e RAILS_ENV=test api bundle exec rails db:prepare test
docker compose exec -T web npm run build
```

Os testes do banco verificam reexecução do seed e impedem que uma fila receba
equipe de outra marca ou tenha duas filas padrão na mesma marca. O teste de
saúde também verifica o JSON 503 numa pilha de desenvolvimento sem conexão
ao banco. Os contratos
validam as fixtures e os formatos acordados. Para verificar o worker, envie um job

```sh
docker compose exec -T api bundle exec rails runner 'puts Infrastructure::HealthCheckJob.perform_later.job_id'
docker compose logs --tail=30 worker
```

Confira no log a execução de `Infrastructure::HealthCheckJob` e a mensagem de
conexão ao Solid Queue. Para praticar, abra o controller de saúde, localize a
consulta ao banco e siga a rota até a mensagem exibida pelo React. Em seguida,
reexecute o seed e confira que continuam existindo duas marcas.

## Organização para as próximas tarefas

| Local | Responsabilidade |
| --- | --- |
| `backend/app/models/operations/` | Marcas, equipes, filas, catálogos, identidades e perfis iniciais. |
| `backend/app/controllers/` | Receber HTTP e delegar as regras do domínio. |
| `backend/app/jobs/` | Executar processamento interno em segundo plano. |
| `frontend/src/` | Telas React e consumo da API. |
| `docs/contratos/` | OpenAPI, schemas, estados, permissões e fixtures comuns aos agentes. |
| `docs/planejamento/` | Escopo, arquitetura, decisões e tarefas. |

F02 acrescenta casos, mensagens, auditoria e outbox, com regras de domínio em
serviços Rails para transições de atendimento, classificação e distribuição.
Controller, job e webhook chamam esses mesmos serviços. Integrações HTTP e Kafka
ficam em adaptadores. O contrato documenta as interfaces antes do paralelismo
entre backend e telas.

## Configurações e limites atuais

As versões de bibliotecas ficam em `backend/Gemfile.lock` e
`frontend/package-lock.json`. Imagens têm tag e digest nos Dockerfiles e no
Compose. A base usa Ruby 3.4, Rails 8.1, PostgreSQL 17, Kafka 4.4 e Node 22.
O servidor web usa Vite para desenvolvimento. Publicação por URL é F10.

`npm audit` identificou um aviso em `picomatch`, dependência transitiva das
ferramentas de desenvolvimento. O fornecedor informa versões corrigidas ainda
indisponíveis na data da F01. O ambiente local mantém o Vite limitado a
localhost. A publicação F10 deverá servir o build estático e revisar as
dependências. [Aviso do picomatch](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)

### Preparação da F05 com fixtures

Em `frontend/`, execute `npm ci`, `npm run build` e `npm run dev`.
Abra `http://localhost:5173/`. A tela do cliente funciona com dados
sintéticos guardados no navegador. Use **Novo atendimento** e **Usar
exemplo** para enviar em Chat, WhatsApp ou E-mail. O chat consulta respostas
automaticamente enquanto o caso está ativo. Nos canais assíncronos,
use **Atualizar conversa** ou volte pelo histórico. Recarregar a página
restaura a conversa selecionada.

Em um perfil novo do navegador, `/?fixture=empty` começa com histórico vazio.
`/?fixture=error` simula uma falha na primeira leitura do histórico e permite
repetir a consulta. A cópia dos exemplos de `docs/contratos/fixtures/` fica em
`frontend/src/simulator/fixtures.json` para funcionar também com o contexto de
build do Docker. Para exercitar o fluxo sem classificador, o formulário
oferece categoria e prioridade sugeridas por canal. Omitir um valor deixa o
caso aguardando classificação.

O contrato de acesso da tela fica em `frontend/src/simulator/contract.ts`.
O adaptador Rails deve implementar sessão, catálogo, leituras e envio com
CSRF e chave de idempotência. O integrador precisa definir a origem dos
nomes das marcas para o simulador. `GET /api/v1/channels` devolve apenas
`brand_id` e `GET /api/v1/brands` atende à supervisão. A atualização por
WebSocket, a caixa do analista e as ações humanas fazem parte da integração
da F05.

F01 usa exclusivamente dados sintéticos. Credenciais Jev e chamada externa
entram em F04. O experimento de carga, os resultados medidos e a análise das
limitações entram em F08, conforme o plano. Na entrega final, este README
também apresentará metodologia, resultados e possibilidades de evolução.
