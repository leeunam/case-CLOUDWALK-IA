# Help desk multimarca CloudWalk

Projeto individual do TAPI Inteli/CloudWalk. O help desk reúne atendimentos
simulados de chat, WhatsApp e e-mail em filas por marca. O operador pode
completar a classificação com SetFit R1 local ou usar a fixture determinística
habilitada por padrão. Um atendente simulado responde pelo Kafka e encaminha casos ao analista com
histórico e referências da conversa. O frontend usa a API Rails real e os
atendimentos ficam no PostgreSQL. A supervisão pode revisar a classificação,
auditar decisões e configurar a operação.

O recorte do MVP foi concluído em 26/11/2026.
[Estado da entrega](docs/estado-entrega.md).

## Demonstração local

Pré-requisitos de host: Git, Python 3.10+ em Linux ou macOS, Docker com
Compose 2.24.4+ e acesso às imagens e às dependências de build. Ruby, Rails,
Node, PostgreSQL, Kafka e o Python da integração executam nos contêineres.
Na raiz do checkout, rode

```sh
python3 script/demo.py up
python3 script/demo.py check
```

Para usar o classificador real, solicite ao custodiante o arquivo portátil
`setfit-r1-package.tar.gz` e instale-o com Python 3.11 em um diretório novo.
O roteiro inclui a conferência dos hashes, o comando da demo, os cliques do
simulador e as provas de persistência e isolamento. [Instalação limpa com SetFit R1](docs/c07.md).

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
preserva os volumes vinculados ao nome. Para retomar a mesma demonstração,
use o mesmo nome de projeto e o arquivo privado original. A preparação F09
foi verificada em instalação limpa. O [roteiro completo](docs/f09.md) inclui
três canais, duas marcas, revisão, atendimento humano, reinício, troca de
portas e comandos Docker diretos.

## Publicação temporária

Em 26/11/2026, a demonstração passou no aceite HTTPS com SetFit R1 local
e atendente simulado via Kafka. O teste cobriu complemento de campos
ausentes, acesso por marca em REST e WSS, resposta automática no navegador
e persistência das mensagens após recarga. A
[URL verificada em 26/11](https://mortality-windsor-weed-watt.trycloudflare.com)
depende do computador e do túnel ativos e pode mudar ao reabrir o túnel.
[Roteiro de operação e matriz de aceite](docs/c07-publicacao-setfit.md).

O teste por dados móveis do responsável ocorreu na publicação de 25/11
com fixture. Ele confirmou conversa automática, handoff humano, resolução,
persistência e isolamento entre marcas. O reinício e a restauração em
instalação isolada também foram verificados na F10. A atualização para
SetFit preservou os 15 casos e as 46 mensagens da instalação.
[Aceite histórico F10](docs/f10-aceite-integrado.md) ·
[Histórico da publicação](docs/f10-resultado.md) ·
[Aceite UX01](docs/ux01.md) · [Aceite UX02](docs/ux02.md).

## Arquitetura

![Arquitetura do help desk com React, Rails, PostgreSQL, SetFit privado, ponte e Kafka](docs/arquitetura/arquitetura.png)

[SVG editável](docs/arquitetura/arquitetura.svg) ·
[Fonte Mermaid](docs/arquitetura/arquitetura.mmd).

1. React envia a mensagem ao Rails pelo proxy do Vite na demonstração local
   e pelo Caddy na publicação. A API persiste o caso no PostgreSQL e devolve
   o recibo idempotente.
2. A classificação completa recebida segue direto para o atendimento. Para
   campos ausentes, Solid Queue usa o provedor selecionado. No modo SetFit, o
   serviço Python privado consulta somente os especialistas correspondentes aos
   campos ausentes. Uma abstenção leva o caso à supervisão.
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

### Experimento de carga F08

**Hipótese.** O outbox preserva os pedidos aceitos durante uma parada do
Kafka, e a aplicação escoa o trabalho após a retomada sem perder nem duplicar
efeitos, inclusive quando há reentrega.

**Método.** O k6 ofereceu 5 novos casos/s em seis rodadas isoladas de cinco
minutos, três com Kafka disponível e três com parada programada de 30 s.
Cada rodada planejou 1.500 entradas sintéticas em duas marcas e três canais,
com segundo turno em 20% dos casos e mais 120 s de observação após a carga.
As entradas já tinham classificação válida e o atendente era o mock
determinístico.

**Métricas.** O ensaio mediu p50 e p95 do aceite HTTP e da primeira resposta
persistida, vazão, erros, pendências, tempo de escoamento e uso de CPU e RAM.
A reconciliação cruzou recibos HTTP `202`, registros e offsets Kafka e efeitos
no PostgreSQL para distinguir trabalho pendente, efeitos duplicados e perdas
comprovadas. A identificação de uma reentrega exige evidência do consumidor.
[Método e reprodução](docs/f08-carga.md).

Cinco rodadas passaram. Das 9.000 entradas aceitas, 7.801 tiveram primeira
resposta persistida. As 1.199 sem resposta pertencem à rodada que reprovou na
recuperação após a interrupção. A R01 demonstrou a recuperação em um ensaio
controlado posterior, e a R02 corrigiu o analisador e conferiu os dados
arquivados. A matriz de referência preserva a falha e segue sem repetição
após a correção. O ensaio exploratório de dez mil conexões de chat ainda está
sem medição.
[Resultados F08](docs/f08.md) · [R01](docs/r01.md) · [R02](docs/r02.md).

### Classificação

A Luna acertou 7 de 8 campos em seis chamadas de desenvolvimento na C05-R4,
com zero erros técnicos e p95 de 1.762,223 ms. A atribuição de categoria a
um caso com informação insuficiente reprovou o gate e bloqueou as 44 chamadas
finais. O custo conservador acumulado até essa rodada foi de US$ 0,03093512.
[Resultado C05-R4](docs/c05-luna-r4-resultado.md).

A R5, Luna com evidência e política 2.1.0, passou nos 8/8 alvos do
desenvolvimento real. O final parou na tentativa 30 de até 44 por falha de
transporte sem custo conciliável. No prefixo, o filtro permitiu apenas 1/26
conclusões em casos classificáveis: a candidata não está apta para adoção.
O custo confirmado da R5 foi US$ 0,00992557; uma reserva de US$ 1,239 permanece
pendente e não representa cobrança confirmada. Não houve repetição. Novas
chamadas pagas estão suspensas.

O piloto local SetFit precedeu a avaliação SF2 com 150 relatos de treino, 90
de validação e 120 finais. A política R1 adotada passou nos dez critérios do
teste independente. A C06 comprovou o fluxo da aplicação com o pacote
aprovado. A reprodução C07 inclui a instalação desse pacote em um clone novo,
o atendimento nos três canais e a releitura dos casos após reiniciar.
[Decisão de adoção](docs/planejamento/classificacao-comparativa/sf2/decisao-adocao-r1.md) ·
[Aceite da aplicação](docs/evidencias/c06/aceite-integrado/README.md) ·
[Roteiro de reprodução](docs/c07.md).

O atendente conversacional real (E01) fica como evolução posterior e opcional.
[Resultado real R5](docs/c05-luna-r5-resultado.md) ·
[Candidata R5](docs/c05-luna-r5-candidata.md) ·
[Preparação R5](docs/planejamento/classificacao-comparativa/rodada-5-implementacao.md) ·
[Piloto SetFit](docs/planejamento/classificacao-comparativa/setfit-piloto.md) ·
[SF2 e divisão dos agentes](docs/planejamento/classificacao-comparativa/sf2/especificacao.md) ·
[Plano de conclusão](docs/planejamento/conclusao-projeto.md).

[Contrato HTTP e eventos](docs/contratos/openapi.yaml) ·
[Roteiro de desenvolvimento do frontend](frontend/README.md) ·
[Instruções para agentes](AGENTS.md)
