# Help desk multimarca CloudWalk

Projeto individual do TAPI Inteli/CloudWalk. A plataforma terá canais simulados,
atendente de IA simulado via webhooks e broker, filas editáveis e handoff humano.
O Jev complementará apenas categoria e prioridade ausentes.

## Estado da entrega

F01 prepara o ambiente, o banco inicial e os contratos. Rails expõe a consulta
de saúde, React verifica essa consulta, PostgreSQL contém a operação sintética
e RabbitMQ fica pronto para a integração de F02. As rotas de atendimento e
administração descritas nos contratos serão implementadas nas próximas tarefas.

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
do banco. A API inicia após a preparação, e a interface inicia após a API.
[Inicialização no Compose](https://docs.docker.com/compose/how-tos/startup-order/)

| Componente | Acesso local |
| --- | --- |
| React | http://localhost:5173 |
| Saúde Rails + PostgreSQL | http://localhost:3000/api/v1/health |
| Painel RabbitMQ | http://localhost:15672 |

O painel RabbitMQ usa `cloudwalk` e `cloudwalk_local` na configuração local.
As variáveis de `.env.example` permitem mudar portas e credenciais. Para usar
outros valores, copie esse exemplo para `.env` antes de subir. Serviços internos
usam os nomes `db`, `api` e `rabbitmq` dentro da rede do Compose. As portas
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

1. O navegador abre o React em `localhost:5173`.
2. React faz `GET /api/v1/health`. O proxy do Vite entrega a requisição ao Rails.
3. [A rota Rails](backend/config/routes.rb) chama
   [HealthController](backend/app/controllers/api/v1/health_controller.rb).
4. O controller consulta PostgreSQL e devolve JSON. React mostra o resultado.

Em Python/FastAPI, esse controller equivale à função ligada a uma rota. O model
Active Record representa uma tabela e oferece consultas como
`Operations::Brand.find_by(code: "aurora")`. O arquivo de migration descreve
a criação ou alteração de tabelas. O seed cria os dados iniciais da demonstração.

O worker executa jobs internos com Solid Queue, persistidos num segundo banco
PostgreSQL no mesmo serviço. RabbitMQ transportará mensagens entre plataforma,
ponte e atendente simulado em F02. [Active Job e Solid Queue](https://guides.rubyonrails.org/active_job_basics.html)

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
Controller, job e webhook chamam esses mesmos serviços. Integrações HTTP e AMQP
ficam em adaptadores. O contrato documenta as interfaces antes do paralelismo
entre backend e telas.

## Configurações e limites atuais

As versões de bibliotecas ficam em `backend/Gemfile.lock` e
`frontend/package-lock.json`. Imagens têm tag e digest nos Dockerfiles e no
Compose. A base usa Ruby 3.4, Rails 8.1, PostgreSQL 17, RabbitMQ 4.2 e Node 22.
O servidor web usa Vite para desenvolvimento. Publicação por URL é F10.

`npm audit` identificou um aviso em `picomatch`, dependência transitiva das
ferramentas de desenvolvimento. O fornecedor informa versões corrigidas ainda
indisponíveis na data da F01. O ambiente local mantém o Vite limitado a
localhost. A publicação F10 deverá servir o build estático e revisar as
dependências. [Aviso do picomatch](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)

F01 usa exclusivamente dados sintéticos. Credenciais Jev e chamada externa
entram em F04. O experimento de carga, os resultados medidos e a análise das
limitações entram em F08, conforme o plano. Na entrega final, este README
também apresentará metodologia, resultados e possibilidades de evolução.
