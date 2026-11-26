# Aceite integrado da classificação de atendimento

Em 26/11/2026 a plataforma do commit `263efb93baefe7dd190589cfc51ec41c1630432c` recebeu seis atendimentos por configuração. O simulador, o painel, as filas Rails, o PostgreSQL, o Kafka e o agente conversacional de demonstração participaram do fluxo. A configuração SetFit executou a inferência no pacote R1 aprovado em CPU.

| Entrada | Marca e canal | Resultado observado com SetFit |
| --- | --- | --- |
| Categoria e prioridade válidas | Aurora, chat | `terminal/advanced` do canal. Encaminhamento a Bia, resposta humana e resolução. |
| Categoria inválida | Horizonte, e-mail | Revisão por `invalid_input`, prioridade `basic` do canal. |
| Falta categoria | Aurora, WhatsApp | SetFit aplicou `pix` e preservou `basic` do canal. |
| Falta prioridade | Horizonte, e-mail | SetFit aplicou `urgent` e preservou `pix` do canal. |
| Faltam os dois campos | Aurora, chat | SetFit aplicou `pix/urgent` em conjunto. |
| Falta categoria e o relato é ambíguo | Horizonte, WhatsApp | SetFit pediu revisão. O supervisor registrou `pix`, preservou `basic` do canal e ativou o turno. |

Os dois primeiros casos tiveram zero pedidos de classificação. Os demais registraram uma tentativa cada. Os JSONs preservam o recibo, a classificação por campo, a tentativa, os identificadores Kafka, a auditoria e cada mensagem por identificador e autor. O ensaio verificou reentrega e conflito no simulador, repetição de evento Kafka e efeito único no histórico. Para os casos Pix, confrontou a fila e a versão da regra de cada marca com a auditoria. Bia recebeu acesso à Aurora e rejeição à Horizonte em REST, painel e assinatura WebSocket. Alex acessou ambas as marcas.

A regressão em fixture repetiu as seis entradas e as verificações funcionais. Os dois relatos que pedem prioridade urgente receberam a palavra “Urgente.” para acionar o comportamento determinístico da fixture. A trilha da tentativa identifica `jev/fixture`. Os pedidos do agente usam contrato 1.1 nos três casos classificados automaticamente pelo SetFit e 1.0 nos demais. Os resultados usam 1.0 nas duas configurações.

## Tempos observados com SetFit

Durações em milissegundos. A fila vai da criação do pedido à criação da tentativa no banco. O adaptador mede a execução do worker residente. O serviço inclui a projeção e a verificação pelo sidecar. O HTTP privado é medido pelo cliente Rails. Turno até resposta inclui outbox, Kafka, agente de demonstração e persistência do callback. Caso até resposta começa na criação do atendimento no banco.

| Entrada | Fila | Adaptador | Serviço | HTTP privado | Turno até resposta | Caso até resposta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Válida | — | — | — | — | 720,205 | 879,594 |
| Inválida | — | — | — | — | — | — |
| Falta categoria | 1.027,559 | 112,630 | 187,999 | 213,643 | 300,895 | 1.965,637 |
| Falta prioridade | 527,743 | 66,789 | 107,958 | 117,016 | 239,958 | 939,407 |
| Faltam ambos | 445,125 | 152,386 | 187,904 | 196,095 | 279,144 | 978,661 |
| Revisão com correção | 419,541 | 42,046 | 68,383 | 74,776 | 176,755 | 935,153 |

Na última linha, o tempo do caso inclui a correção feita pelo cliente de teste. A primeira carga do serviço levou 41,701 s durante a subida da pilha. O reinício isolado levou 30,081 s. O mesmo PID atendeu às quatro chamadas da matriz. O reinício preservou integralmente o registro do caso com dois campos preenchidos.

Nos dez serviços em execução, a soma de memória corrente dos cgroups passou de 3.764.670.464 para 3.876.761.600 bytes. O pico registrado pelo cgroup SetFit foi de 2.573.438.976 bytes. A CPU acumulada dos dez serviços cresceu 107,246 s de CPU durante o intervalo que também incluiu as verificações no navegador e os clientes Kafka. São observações desta execução sequencial. Os contadores individuais e as medições da regressão constam nos JSONs.

## Reprodução

Use um checkout de teste, um projeto Compose novo para cada modo e portas livres em loopback. O auxiliar cria as credenciais sintéticas em `.env.demo.local` no checkout. A matriz cria regras e casos, republica um evento e reinicia o sidecar do projeto informado. Requer Docker Compose, Python com `requests` e `playwright`, e Chrome ou Chromium do Playwright. A execução registrada usou requests 2.32.5, Playwright 1.61.0 e Chrome 158.0.8127.88. Indique o diretório do pacote R1 instalado no lugar de `/caminho/para/setfit-r1`.

```sh
MODELO=/caminho/para/setfit-r1
projeto=cloudwalk_demo_aceite_real
rtk proxy python3 script/demo.py --project "$projeto" --api-port 43469 --web-port 45469 --classifier setfit --model-dir "$MODELO" up
rtk proxy python3 -B -m script.c06.aceite_integrado --origin http://127.0.0.1:45469 --project "$projeto" --classifier setfit --credentials .env.demo.local --output /tmp/aceite-setfit.json
rtk proxy docker exec -e RAILS_ENV=test "$projeto-api-1" bundle exec rails db:create db:prepare
rtk proxy docker exec -e RAILS_ENV=test "$projeto-api-1" bundle exec rails test test/integration/classification_concurrency_test.rb test/integration/setfit_classification_flow_test.rb --seed 603
rtk proxy python3 script/demo.py --project "$projeto" --api-port 43469 --web-port 45469 --classifier setfit --model-dir "$MODELO" down

projeto=cloudwalk_demo_aceite_fixture
rtk proxy python3 script/demo.py --project "$projeto" --api-port 43469 --web-port 45469 --classifier fixture up
rtk proxy python3 -B -m script.c06.aceite_integrado --origin http://127.0.0.1:45469 --project "$projeto" --classifier fixture --credentials .env.demo.local --output /tmp/aceite-fixture.json
rtk proxy python3 script/demo.py --project "$projeto" --api-port 43469 --web-port 45469 --classifier fixture down
```

As duas suítes Rails exercitam atrasos controlados em PostgreSQL e HTTP. Nesta base executaram 12 testes e 256 asserções em 7,359537 s, com zero falhas, erros ou testes ignorados. Os tempos da tabela provêm das chamadas reais com as duas cabeças residentes.

Para entender a preservação dos valores do canal, compare `cases.prioridade.initial.attempts[0]` e `cases.ambos.initial.attempts[0]` em [setfit.json](setfit.json). Observe os campos `received`, `calls` e `applied`, depois confira as origens no registro `initial`. A [execução em fixture](fixture.json) permite seguir o mesmo percurso até o atendimento respondido.
