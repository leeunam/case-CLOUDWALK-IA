# Help desk multimarca CloudWalk

Projeto individual do TAPI Inteli/CloudWalk. O help desk reúne atendimentos
simulados de chat, WhatsApp e e-mail em filas por marca. Um atendente simulado
responde pelo Kafka e encaminha casos que precisam de intervenção humana. O
analista recebe o histórico e as referências do encaminhamento. A supervisão
pode revisar a classificação, auditar decisões e configurar a operação.

## Demonstração local

Pré-requisitos de host: Git, Python 3.10+ em Linux ou macOS, Docker com
Compose 2.24.4+ e acesso às imagens e às dependências de build. Ruby, Rails,
Node, PostgreSQL, Kafka e o Python da integração executam nos contêineres.
Na raiz do checkout, rode

```sh
python3 script/demo.py up
python3 script/demo.py check
```

Abra o [simulador](http://127.0.0.1:45179/) e a [caixa do analista](http://127.0.0.1:45179/analista).
O simulador abre uma identidade sintética no Rails. Para entrar como analista
ou supervisor, leia a credencial local no terminal com
`python3 script/demo.py login alex@example.test` ou
`python3 script/demo.py login supervisor@example.test`. Há também Bia e Cris
para demonstrar permissões e operação em marcas distintas.

```sh
python3 script/demo.py status
python3 script/demo.py logs api worker outbox events mock
python3 script/demo.py down
```

A primeira subida cria o arquivo privado e ignorado `.env.demo.local`, prepara
os tópicos Kafka e inicializa o banco com Aurora e Horizonte, quatro filas,
três analistas e supervisão. O projeto Compose padrão é `cloudwalk_demo`.
Use um nome de projeto distinto por checkout ou worktree, pois `down`
preserva os volumes vinculados ao nome. O classificador usa respostas
fixture determinísticas, e a interface usa a API real. O
[roteiro completo](docs/f09.md) inclui três canais, duas marcas, revisão,
atendimento humano, reinício, troca de portas e comandos Docker diretos.

## Arquitetura

1. React envia a mensagem ao Rails pelo proxy do Vite. A API persiste o caso
   no PostgreSQL e devolve o recibo idempotente.
2. A classificação completa recebida segue direto para o atendimento. Para
   campos ausentes, Solid Queue executa o complemento fixture. Casos sem
   informação suficiente aguardam correção da supervisão.
3. O outbox entrega a solicitação assinada à ponte. Ela publica no
   `agent.requests`. O mock consome o pedido e publica no `agent.events`.
4. A ponte envia o resultado assinado ao Rails. A API grava a resposta ou
   encaminha o mesmo atendimento para o humano. O chat acompanha o caso via
   Action Cable. PostgreSQL guarda o histórico e a auditoria.

A aplicação é um monólito modular Rails API + React. Kafka roda em KRaft
single-node na rede interna, com três partições por tópico, chave `case_id`
e retenção padrão de sete dias. Os jobs internos usam Solid Queue no
PostgreSQL. Os dados de toda a demonstração são sintéticos.

[Escopo e arquitetura](docs/planejamento/especificacao-mvp.md) ·
[Decisões](docs/planejamento/decisoes.md) ·
[Contratos e modelo de dados](docs/contratos/README.md) ·
[Plano e critérios de aceite](docs/planejamento/plano-de-execucao.md)

## Desenvolvimento e verificações

O Compose de desenvolvimento sobe banco, Kafka, API, worker e frontend.
Com o checkout na raiz, o frontend abre em `http://localhost:5173` e a saúde
do Rails em `http://localhost:3000/api/v1/health`. Ajustes de desenvolvimento
ficam em [.env.example](.env.example).

```sh
docker compose up --build --wait
docker compose exec -T api bundle exec ruby /workspace/script/check_contracts.rb
docker compose exec -T -e RAILS_ENV=test api bundle exec rails db:prepare test
docker compose exec -T web npm test
docker compose exec -T web npm run build
docker compose down
```

As dependências estão fixadas em `backend/Gemfile.lock`,
`frontend/package-lock.json` e `integration/requirements.txt`. Os Dockerfiles
e o Compose registram os digests das imagens-base. Veja no
[roteiro F09](docs/f09.md#imagem-e-dependências-da-integração) a origem e a
verificação da imagem Python.

| Verificação | Evidência |
| --- | --- |
| Pilha local completa, dois turnos e reentrega, classificação e handoff | [Roteiro e verificação F09-A](docs/f09.md) |
| Permissões, configuração, concorrência e recuperação no atendimento | [Integração F06/F07](docs/integracao-f06-f07.md) |
| Carga, dados brutos, hipóteses e reprodução | [Resultados F08](docs/f08.md) · [Comandos do ensaio](docs/f08-carga.md) |
| Correção dos consumidores e do analisador da carga | [R01](docs/r01.md) · [R02](docs/r02.md) |
| Avaliação de classificadores e critérios para integração | [Primeira configuração C05](docs/c05-resultado.md) · [Protocolo e execução C05-R2](docs/c05-r2.md) |

## Resultados e limites

A matriz histórica F08 permanece com cinco das seis rodadas aprovadas. Na
rodada que reprovou após a interrupção do Kafka, 1.199 entradas ficaram sem
primeira resposta. A R01 confirmou a recuperação em um ensaio controlado
posterior. A R02 corrigiu o analisador e reprocessou as evidências preservadas.
A carga de dez mil sessões de chat continua sem medição de capacidade.

A fixture viabiliza percorrer a classificação, a revisão e o percurso do
atendente simulado. A qualidade, latência e custo de classificadores reais
são tratados na avaliação C05. C06, C07 e a publicação F10 ficam no
[plano de conclusão](docs/planejamento/conclusao-projeto.md). Os próximos
passos de evolução incluem a integração de um classificador elegível, a
validação da instalação por URL e novas medições de capacidade. A pilha
local serve o React pelo Vite e mantém as duas portas no loopback.

[Contrato HTTP e eventos](docs/contratos/openapi.yaml) ·
[Roteiro de desenvolvimento do frontend](frontend/README.md) ·
[Instruções para agentes](AGENTS.md)
