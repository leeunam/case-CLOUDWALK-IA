# Help desk multimarca

MVP do TAPI Inteli/CloudWalk. A plataforma recebe atendimentos sintéticos de
Chat, WhatsApp e E-mail, organiza filas por marca, complementa classificações
incompletas com SetFit R1 e encaminha casos ao atendente simulado ou a um
analista humano. Supervisores configuram filas, equipes e regras, e consultam
as decisões registradas.

**Entrega do MVP e piloto E01 concluídos em 26/11/2026.** Os testes de carga
registraram limites na recuperação após interrupção do Kafka e na escala do
chat. Veja [estado, evidências e próximos passos](docs/estado-entrega.md).

## Arquitetura

![Fluxo e componentes do help desk](docs/arquitetura/arquitetura.png)

Rails é a API e a autoridade sobre atendimentos, permissões, filas e auditoria.
PostgreSQL persiste o estado e o outbox. O worker Rails executa jobs internos
com Solid Queue. A ponte Python publica pedidos no Kafka e consome os
resultados. O mock determinístico responde pelo mesmo fluxo de eventos. React
usa a API e recebe atualizações do chat pelo Action Cable.

Uma classificação válida segue ao atendente simulado. Se categoria ou
prioridade estiver ausente, o Rails agenda o complemento pelo serviço SetFit
local. Campos válidos do canal são preservados; entradas inválidas ou incertas vão
para revisão humana. O serviço de classificação não decide acesso nem
encaminhamento.

## Rodar a demonstração

Requisitos: Python 3.10+, Docker com Compose 2.24.4+ e acesso ao daemon Docker.
Na primeira execução, o Compose baixa e constrói as imagens necessárias.

```sh
python3 script/demo.py up
python3 script/demo.py check
```

Abra o simulador em `http://127.0.0.1:45179/` e a área de operação em
`http://127.0.0.1:45179/analista`. Para entrar como supervisor, obtenha a senha
sintética no terminal com:

```sh
python3 script/demo.py login supervisor@example.test
```

O comando `check` envia turnos sintéticos e verifica a reentrega pelo fluxo
Rails/Kafka. Para ver serviços, consultar logs ou encerrar a demonstração:

```sh
python3 script/demo.py status
python3 script/demo.py logs api worker outbox events mock
python3 script/demo.py down
```

O padrão usa classificação fixture e dados fictícios. Para instalar e executar
o pacote SetFit R1, siga o [guia de reprodução local](docs/c07.md). Para
desenvolvimento, consulte [frontend](frontend/README.md),
[contratos](docs/contratos/README.md) e [plano de execução](docs/planejamento/plano-de-execucao.md).

## Resultados e limites

- **F08:** a recuperação do Kafka e o teste de escala do chat precisam de
  novos ajustes e medições. Os resultados e comandos de reprodução estão em
  [docs/f08.md](docs/f08.md).
- **SetFit R1:** adotado após avaliação independente e integrado à aplicação.
  Os pesos são distribuídos em pacote separado do Git. A classificação pode
  ser reproduzida em modo fixture sem esse pacote.
- **Atendimento real:** E01 avaliou um modelo de linguagem com conhecimento
  sintético por marca. A demo publicada usa o atendente simulado.
- **Publicação:** a URL de demonstração é temporária e depende do computador e
  do túnel ativos. Integrações bancárias e canais externos de produção estão
  fora do escopo.

Consulte o [estado detalhado da entrega](docs/estado-entrega.md), a
[especificação](docs/planejamento/especificacao-mvp.md), as
[decisões](docs/planejamento/decisoes.md) e as
[evidências do piloto E01](docs/evidencias/e01/README.md).
