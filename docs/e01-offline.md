# Aceite local do atendente E01

O ambiente E01 offline roda Rails, PostgreSQL, Kafka e o executor da Luna.
Uma fixture responde no lugar do transporte HTTP da Feita. Os textos,
contagens, tarifas e custos deste ensaio são sintéticos. A demonstração
usa o mock determinístico e a qualidade e o faturamento da Luna são
avaliados no canário E01-05.

## Subir, verificar e consultar

Na raiz do checkout, com Docker Compose 2.24.4+ e Python 3.10+, execute

```sh
python3 -B script/e01/offline.py config
python3 -B script/e01/offline.py up
python3 -B script/e01/offline.py --report /tmp/e01-matriz.json check
python3 -B script/e01/offline.py --matrix-report /tmp/e01-matriz.json --report /tmp/e01-falhas.json faults
python3 -B script/e01/offline.py status
python3 -B script/e01/offline.py down
```

A API escuta em `http://127.0.0.1:43309`. `--with-web up` também sobe o
simulador em `http://127.0.0.1:45379`. Esse ambiente usa HTTP local sem
endpoint WSS. Os seis cenários fornecem classificação válida na entrada.
O runner usa `RAILS_ENV=test` e fornece valores sintéticos ao Compose.
PostgreSQL e Kafka ficam na rede interna e usam volumes do projeto
`cloudwalk_e01_offline`. O runtime da fixture funciona nessa rede e o build
pode baixar imagens e dependências quando não houver cache local.

`check` executa nove turnos nas duas marcas e três canais. O relatório
mostra IDs, correlação, latência e estado, além dos hashes que ligam os
bytes da outbox, do ledger e do recibo. `faults` usa o relatório da matriz
do mesmo projeto, interrompe o consumidor de forma controlada e deixa o
piloto pausado com uma reserva incerta. Use `--correlation-id UUID status`
para consultar a trilha de um caso. `down` preserva banco e tópicos.
Para repetir desde zero, use outro `--project cloudwalk_e01_offline_NOME`
em todos os comandos e escolha portas livres com `--api-port` e `--web-port`.
Use um caminho novo para cada relatório.

## Seletor e configuração do canário separado

`compose.e01.yml` complementa `compose.yml` e `compose.demo.yml`. O serviço
`mock` continua sendo o consumidor único de pedidos. Ele usa o grupo Kafka
`mock-agent-v1` em todos os modos. `CLOUDWALK_AGENT_BACKEND` escolhe `mock`,
`luna_fixture` ou `luna`. Pelo overlay, a variável de entrada é `E01_BACKEND` e
o valor padrão é `mock`. `luna_fixture` requer `E01_RAILS_ENV=test`.

Para o canário E01-05, a operação escolhe um projeto isolado, configura o
`E01_LEDGER_SECRET` dedicado à API e ao consumidor e informa
`E01_PREFLIGHT_FILE` com a evidência aprovada, montada para leitura somente
na API. A rede interna usada pelas pontes e pelo ledger permanece ativa.
Um overlay adicional de operação habilita a saída HTTPS do serviço
`mock` e monta nele o arquivo de credencial para leitura, indicado em
`CLOUDWALK_E01_FEITA_KEY_FILE`. A operação escolhe então `E01_BACKEND=luna`
e usa o protocolo e as travas descritos no [ledger E01](../backend/E01.md).

A captura financeira do canário pode ser ativada com
`CLOUDWALK_E01_AUDIT_DIR` no consumidor `luna`. Monte um diretório gravável
dedicado, do usuário do contêiner (UID 10001) e com modo `0700`. Cada POST
gera um recibo JSON com modo `0600`, contendo horário UTC, duração, status,
hash do pedido, ID, modelo e campos financeiros permitidos da resposta.
Os campos ausentes permanecem ausentes e o recibo conserva a precisão
decimal. Credenciais, mensagens e decisões ficam fora do arquivo. Se a
gravação falhar depois do POST, o executor trata o uso como incerto e o
ledger preserva a reserva durante a pausa para conciliação.

## Exercício de reentrega

No relatório de `faults`, abra `publication[1]`. Siga o `request_event_id`
em `broker_before_restart` e `broker_after_replay`. Compare o hash de
`case.result_sha256` com cada cópia do evento no Kafka. A contagem
`fixture_posts` permanece em um e os IDs de mensagem registram uma única
resposta da IA. Compare esse recibo `offline-fixture-*` com o formato do
recibo de uso do canário E01-05 para identificar qual transporte foi usado.
