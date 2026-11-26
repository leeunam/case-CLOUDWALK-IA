# Evidências da publicação com SetFit R1

O integrador registrou a configuração local e o aceite público em
26/11/2026, na revisão `977ec3f21096d66c6b462d3cc94880e4a94eb490`.
Os registros contêm IDs sintéticos e hashes, sem credenciais ou mensagens
em texto. A C07 em clone limpo e a F10 móvel em fixture têm evidências
próprias. [Publicação SetFit](../../../c07-publicacao-setfit.md) ·
[Reprodução C07](../README.md) · [Aceite F10](../../../f10-aceite-integrado.md).

| Registro | Escopo |
| --- | --- |
| [public-local-check.json](public-local-check.json) | Rotas, CSRF, sessão e WebSocket no HTTPS local. Conferência dos dados anteriores com o túnel fechado. |
| [public-production-local-case.json](public-production-local-case.json) | Caso sintético pelo HTTPS local, com complemento de dois campos e resposta pelo Kafka. |
| [public-setfit.json](public-setfit.json) | Prontidão, dois casos enviados pelo HTTPS público, origem dos campos, tentativas, outbox, mensagens e checagem REST por marca. |
| [public-repeat-check.json](public-repeat-check.json) | Publicação repetida na mesma URL e recusa de troca de modo com o túnel ativo. |
| [public-browser.json](public-browser.json) | Dois turnos no navegador público, atualização automática, resolução e IDs das quatro mensagens após recarga. |
| [public-wss.json](public-wss.json) | Decisão de acesso nas três assinaturas WSS públicas. |
| [public-preservation-final.json](public-preservation-final.json) | Revisão, migração, imagens e preservação dos IDs e hashes. O total passou de 15 para 19 casos e de 46 para 56 mensagens. |

`case_to_result_ms` vai da criação do caso ao resultado Kafka persistido.
`turn_to_result_ms` usa a criação do turno como início. `queue_ms`,
`http_ms` e `sidecar_ms` medem etapas da tentativa. O campo
`public_client_to_observation_ms` cobre o verificador inteiro, incluindo
reentrega, polling, consulta de histórico e SQL. Use esse campo apenas
para caracterizar a execução do verificador. A amostra pública de dois
casos da API ilustra o fluxo funcional.
