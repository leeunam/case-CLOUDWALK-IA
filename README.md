# Help desk multimarca CloudWalk

Projeto individual do TAPI Inteli/CloudWalk. O help desk reúne atendimentos
simulados de chat, WhatsApp e e-mail em filas por marca. A demonstração usa
respostas determinísticas (fixture) para completar a classificação. Um
atendente simulado responde pelo Kafka e encaminha casos ao analista com
histórico e referências da conversa. O frontend usa a API Rails real e os
atendimentos ficam no PostgreSQL. A supervisão pode revisar a classificação,
auditar decisões e configurar a operação.

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
preserva os volumes vinculados ao nome. Para retomar a mesma demonstração,
use o mesmo nome de projeto e o arquivo privado original. A preparação F09
foi verificada em instalação limpa. O [roteiro completo](docs/f09.md) inclui
três canais, duas marcas, revisão, atendimento humano, reinício, troca de
portas e comandos Docker diretos.

## Publicação temporária

A demonstração da F10 foi publicada em HTTPS com classificação fixture e
atendente simulado. O reinício preservou os atendimentos, e a restauração da
cópia em uma instalação isolada recuperou o mesmo caso. A reorganização da
interface e o tema inspirado na CloudWalk foram aceitos e publicados.
[Resultado F10](docs/f10-resultado.md) ·
[Aceite UX01](docs/ux01.md) · [Aceite UX02](docs/ux02.md).

A [última URL verificada](https://tribal-louisville-container-bind.trycloudflare.com/)
é a da UX02. O endereço depende do computador e do túnel ligados e muda ao
recriar o túnel. O serviço limita a 200 requisições simultâneas em voo e não
garante disponibilidade. Na URL anterior, o acesso por dados móveis confirmou
a abertura da página com marcas e canais visíveis. A verificação de todo o
fluxo a partir de outra rede continua pendente.
[Evidências da publicação](docs/f10-resultado.md).

O [roteiro de publicação](docs/f10.md) orienta a escolher um projeto exclusivo
e executar `init`, `up` e `check` com `script/publish.py` antes de `prepare` e
`publish`. Use `credentials` em terminal privado para obter o acesso sintético.
O mesmo roteiro cobre como parar, retomar e restaurar a demonstração.

## Arquitetura

1. React envia a mensagem ao Rails pelo proxy do Vite na demonstração local
   e pelo Caddy na publicação. A API persiste o caso no PostgreSQL e devolve
   o recibo idempotente.
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

A R5, que mantém a Luna e acrescenta evidência verificável com validação
conservadora, tem a candidata com política 2.1.0 congelada após testes offline.
O executor e a reprodução com fixture estão em revisão ampla e a qualidade
real da R5 segue sem medição. A integração do classificador (C06) aguarda
qualificação e decisão de adoção. A validação final (C07/F09) também está
pendente. O atendente conversacional real (E01) fica como evolução posterior
e opcional.
[Candidata R5](docs/c05-luna-r5-candidata.md) ·
[Preparação R5](docs/planejamento/classificacao-comparativa/rodada-5-implementacao.md) ·
[Plano de conclusão](docs/planejamento/conclusao-projeto.md).

[Contrato HTTP e eventos](docs/contratos/openapi.yaml) ·
[Roteiro de desenvolvimento do frontend](frontend/README.md) ·
[Instruções para agentes](AGENTS.md)
