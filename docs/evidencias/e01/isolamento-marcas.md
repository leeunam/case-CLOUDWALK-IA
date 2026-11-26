# E01-06 · Isolamento dos casos do piloto real

**Resultado aprovado** nas seis combinações de analista e caso. Execução em 26/11/2026, das 17:32:50.752 às 17:32:52.753, horário de Brasília.

A aplicação local rodava no projeto `cloudwalk_e01_pilot_20261126`, a partir do commit `7a73df5` da branch `feat/atendente-real`, na worktree `.worktrees/e01-atendente`. A API e o banco responderam saudáveis em `GET /api/v1/health` (HTTP 200) no início e no fim da janela.

| Caso | Marca | ID registrado no journal E01-Q1 |
| --- | --- | --- |
| P1.1 | Aurora | `507061b1-1fb5-45f7-a206-70fc34768dbe` |
| P2.1 | Horizonte | `d101242b-dc42-4f40-8e84-35d7a0ae8163` |

| Analista | Marca | Listagem unificada (200) | Detalhe | Histórico | Assinatura WebSocket | Resultado |
| --- | --- | --- | --- | --- | --- | --- |
| Bia | Aurora | Presente | 200, ID e marca conferem | 200, mensagem do caso conferida | `confirm_subscription` | Passou |
| Bia | Horizonte | Ausente | 404 genérico | 404 genérico | `reject_subscription` | Passou |
| Cris | Aurora | Presente | 200, ID e marca conferem | 200, mensagem do caso conferida | `confirm_subscription` | Passou |
| Cris | Horizonte | Presente | 200, ID e marca conferem | 200, mensagem do caso conferida | `confirm_subscription` | Passou |
| Alex | Aurora | Presente | 200, ID e marca conferem | 200, mensagem do caso conferida | `confirm_subscription` | Passou |
| Alex | Horizonte | Presente | 200, ID e marca conferem | 200, mensagem do caso conferida | `confirm_subscription` | Passou |

As três identidades foram confirmadas separadamente com sessões de demonstração e autenticação com CSRF. As listagens foram consultadas até o fim, sem filtro de marca. Em Horizonte, o detalhe e o histórico consultados por Bia retornaram exclusivamente `not_found` e a mensagem “Atendimento não encontrado.”. Nos históricos autorizados, a consulta conferiu ID, sequência e texto da primeira mensagem de cada caso com o registro do piloto.

## Reprodução

1. Consulte os IDs e a primeira mensagem de P1.1 e P2.1 no journal local do E01-Q1.
2. Use uma sessão independente por analista. Obtenha o CSRF com `GET /api/v1/session`, autentique com `POST /api/v1/session` e confirme a identidade com outro `GET /api/v1/session`. A API usada no ensaio foi `http://127.0.0.1:43319`.
3. Consulte `GET /api/v1/cases?limit=100`, seguindo o cursor até o fim, e consulte `GET /api/v1/cases/<id>` e `GET /api/v1/cases/<id>/messages` para os dois IDs.
4. Abra `ws://127.0.0.1:45389/cable` pelo proxy da interface, com origem `http://127.0.0.1:45389`, o cookie da sessão autenticada e o protocolo `actioncable-v1-json`. Após `welcome`, envie `subscribe` para `CaseUpdatesChannel` com o ID do caso e `audience: "staff"`. Confira o quadro de decisão correspondente ao identificador enviado.

O ensaio verificou confirmação ou recusa da assinatura. A entrega de novos eventos pelo canal e o aceite visual da interface ficam fora desta evidência. As únicas requisições POST foram as de login. A checagem acrescentou **zero chamadas pagas**, preservando 14 disparos, US$ 0,1500054 contabilizados e zero reservas no journal antes e depois.
