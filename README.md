# Help desk multimarca CloudWalk

Projeto individual do TAPI Inteli/CloudWalk. A plataforma terá canais simulados,
atendente de IA simulado via webhooks e broker, filas editáveis e handoff humano.
O Jev complementa apenas categoria e prioridade ausentes, com modo fixture local
e modo HTTP explícito para o fornecedor real.

## Estado da entrega

F01 prepara o ambiente, o banco inicial e os contratos. A F02 implementa o
webhook de canal, a persistência do atendimento, o outbox, a ponte Kafka e o
atendente simulado, com consulta autenticada do histórico. A F03 fornece o
atendimento humano. A F04 integra o complemento de classificação em jobs e a
correção por supervisão. A F05 usa Rails e Action Cable no simulador e na caixa
do analista; as fixtures ficam no modo explícito `/?fixture=demo`.
A F06 fornece configuração administrativa e supervisão. A F07-A verifica os
cinco cenários de robustez dos fluxos F02–F05 sobre a base integrada da F06.
A matriz administrativa foi complementada com concorrência no PostgreSQL e
revogação em REST e WebSocket reais. A F08 fornece carga e avaliação offline;
a referência encontrou uma falha de recuperação dos consumidores Kafka.
A avaliação real do Jev e a publicação continuam pendentes.

Verificação local da F01 em 2026-11-17 passou com cinco testes Rails e quatorze
asserções, OpenAPI e 43 fixtures, build React/TypeScript, execução de um job
pelo worker e instalação com bancos vazios. O teste de reinício preservou uma
autorização removida. O aviso de dependência de desenvolvimento está descrito
ao fim deste README.

Em 2026-11-18, Kafka passou a ser o broker padrão. O teste de mensageria
consumiu e releu o mesmo evento com grupos diferentes e confirmou a leitura
de um evento após recriar o contêiner com o volume persistente.

Em 2026-11-19, a F02 passou com Rails e Kafka reais: dois turnos, resolução e
quatro mensagens preservadas após reentrega. A suíte Rails passou com 10 testes
e 111 asserções, a suíte Python com nove testes e os contratos com 43 fixtures.
O [roteiro F02](docs/f02.md) contém os comandos e os limites dessa verificação.
O comando padrão abaixo sobe a base e a interface conectada à API; a ponte e o
mock são iniciados pelo roteiro F03.

Na integração F03/F04 de 2026-11-19, a suíte Rails passou com 48 testes e
657 asserções, sem falhas nem erros. O ensaio real Jev foi pulado por falta
da chave TypeSafe. O [atendimento humano F03](docs/f03.md) foi verificado com
HTTP, Kafka e worker reais. O [adaptador F04](docs/f04.md) foi validado com
fixtures e transporte simulado naquela primeira fatia. Os resultados da
conclusão dos jobs e da conexão real da interface estão na
[integração F04/F05](docs/integracao-f04-f05.md). O ensaio TypeSafe ao vivo
continua dependendo de `TYPESAFE_API_KEY`.

Na integração F06/F07-A de 2026-11-20, passaram 86 testes Rails com 1.065
asserções (uma omissão da chamada TypeSafe real), 27 testes frontend com
instalação pelo lockfile e build, 10 testes da ponte, 12 do verificador e
47 fixtures contratuais. A configuração e a recuperação por supervisão foram
percorridas no navegador. Resultados, reprodução e limites estão na
[integração F06/F07-A](docs/integracao-f06-f07.md).

Na F08 de 2026-11-20, os 42 testes da carga e os 15 do avaliador passaram.
Foram medidas três rodadas por condição: cinco aprovadas e uma reprovada após
a interrupção do Kafka. Todas as 9.000 entradas iniciais receberam `202`, mas
1.199 ficaram sem primeira resposta na rodada reprovada. O
[relatório F08](docs/f08.md) preserva os dados, denominadores e limitações,
incluindo o [diagnóstico de recuperação](docs/f08-incidente-consumo.md).
O modo offline não mede a qualidade do Jev real; dez mil conexões de chat
ainda não foram ensaiadas. A R02 corrigiu os dois casos limite do analisador, com 49 testes aprovados
e reanálise dos sete históricos preservada. A recuperação R01 passou no ensaio real controlado, conforme
[seu relatório](docs/r01.md). A C01 fechou critérios, divisão de dados e contratos da
comparação; A [C02](docs/c02.md) está aceita com 27 testes e reprodução fixture.
C03 e C04 iniciam a implementação dos adaptadores; o ensaio pago aguarda
credencial e teto autorizado.

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
PostgreSQL no mesmo serviço. Na demonstração F02, Kafka transporta mensagens
entre plataforma, ponte e atendente simulado. [Active Job e Solid Queue](https://guides.rubyonrails.org/active_job_basics.html)

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

F02 acrescenta casos, mensagens, auditoria e outbox, com serviços Rails para
entrada, rodadas e resultados do atendente. F03 implementa a distribuição
humana e F04 integra os jobs de classificação Jev. Integrações HTTP e Kafka
ficam em adaptadores. O contrato
documenta as interfaces compartilhadas entre backend e telas.

## Configurações e limites atuais

As versões de bibliotecas ficam em `backend/Gemfile.lock` e
`frontend/package-lock.json`. As imagens da base F01 têm tag e digest nos
Dockerfiles e no Compose. A imagem Python da integração F02 usa a tag
`python:3.13-slim`; seu digest e as dependências transitivas ainda precisam
ser congelados para a reprodução final F09. A base usa Ruby 3.4, Rails 8.1,
PostgreSQL 17, Kafka 4.4 e Node 22.
O servidor web usa Vite para desenvolvimento. Publicação por URL é F10.

`npm audit` identificou um aviso em `picomatch`, dependência transitiva das
ferramentas de desenvolvimento. O fornecedor informa versões corrigidas ainda
indisponíveis na data da F01. O ambiente local mantém o Vite limitado a
localhost. A publicação F10 deverá servir o build estático e revisar as
dependências. [Aviso do picomatch](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)

### F05 com API e demonstração local

A raiz abre o simulador conectado ao Rails. `/analista` abre a operação com
login, caixa filtrada, handoff e comandos de resposta, espera e resolução.
Configure a credencial sintética conforme o [roteiro F03](docs/f03.md).
O [README do frontend](frontend/README.md) descreve a execução fora do Compose.

O catálogo autorizado fornece os nomes das marcas. O simulador solicita
`GET /api/v1/channels?audience=simulator` para exigir a própria identidade,
mesmo quando existe uma sessão operacional no navegador. Mensagens passam
pelo serviço canônico de entrada; cookies, CSRF, versões e chaves de
idempotência são verificados pelo Rails. O navegador não recebe o segredo
usado para assinar webhooks.

A assinatura de `/cable` acompanha o caso aberto. Ao receber um aviso ou
reconectar, a tela lê novamente o estado autorizado. WhatsApp e e-mail
mantêm consulta pelo histórico e atualização manual. Os resultados do
navegador e as limitações ficam na [integração F04/F05](docs/integracao-f04-f05.md).

Use `/?fixture=demo` para o modo local no navegador; `/?fixture=empty`
começa vazio e `/?fixture=error` simula erro de leitura. A API real exibe
suas falhas, sem recorrer silenciosamente às fixtures. A cópia dos exemplos
contratuais fica em `frontend/src/simulator/fixtures.json` para o build.
Omitir classificação usa Jev fixture se o worker tiver
`CLOUDWALK_JEV_MODE=fixture`; o padrão `disabled` encaminha à revisão com motivo.

Em `frontend/`, execute `rtk npm ci`, `rtk npm test` e `rtk npm run build`.
Use o Node 22 da imagem fixada se a versão local não oferecer a remoção de
tipos TypeScript requerida pelo runner. O [roteiro F05](docs/f05.md)
preserva o histórico da primeira revisão com fixtures.

A demonstração usa exclusivamente dados sintéticos. Credencial e chamada
Jev real têm verificação própria na F04. O experimento de carga, os resultados medidos e a análise das
limitações entram em F08, conforme o plano. Na entrega final, este README
também apresentará metodologia, resultados e possibilidades de evolução.
