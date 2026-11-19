# F05 · Atendimento pela API

A raiz abre o simulador. `/analista` abre a caixa operacional. As duas telas
usam a API na mesma origem. Para demonstrar com armazenamento local, abra
`/?fixture=demo`. Use `/?fixture=empty` ou `/?fixture=error` para os cenários
de histórico vazio e erro de leitura.

## Executar

Com o backend integrado e ouvindo na porta 3000, a partir de `frontend/`:

```sh
rtk npm ci
rtk npm test
rtk npm run build
API_PROXY_TARGET=http://127.0.0.1:3000 rtk npm run dev
```

No Compose, o destino padrão é `http://api:3000`. Use a credencial
operacional de demonstração configurada no Rails.

## Dependências da integração

A base `e1b97d9` oferece sessão operacional, filtros, lista, detalhe,
mensagens e ações do analista. A interface usa a disponibilidade e a
marca informadas pela sessão. A retomada é aplicada pelo distribuidor.

| Operação | Fornecimento na rodada F04 |
| --- | --- |
| `POST /api/v1/simulator/session` | Criar e recuperar identidade sintética com cookie e CSRF. |
| `GET /api/v1/channels` | Listar canais autorizados com `brand_name` e cursor. |
| `GET /api/v1/simulator/cases`, detalhe e mensagens | Restringir ao cliente autenticado e devolver identidade para continuar a conversa. |
| `POST /api/v1/simulator/channels/{channel_id}/messages` | Persistir a mensagem e devolver o recibo idempotente. |
| `/cable` · `CaseUpdatesChannel` | Autorizar a assinatura do caso e avisar após alterações, inclusive as feitas por workers. |

## Aceite com o backend real

1. Envie uma mensagem em chat, WhatsApp e e-mail entre duas marcas. Recarregue,
   reabra uma conversa pelo histórico e envie um complemento.
2. Na área do analista, abra um handoff e siga o resumo até a mensagem
   referenciada. Responda, aguarde o cliente e volte ao simulador para enviar
   o complemento. Observe a retomada e resolva o atendimento.
3. Abra um caso de outra marca e confira as ações disponíveis. Desconecte e
   reconecte o chat e confira a nova confirmação de assinatura e as leituras.
4. Faça duas ações simultâneas com a mesma versão. Observe o conflito,
   a nova versão carregada e o rascunho preservado.

Exercício: no painel de rede, siga um envio do analista e compare o
`Idempotency-Key`, o `expected_version` e a consulta disparada pelo aviso
`case.updated`.
