# F10-B · Acesso aos atendimentos por marca

> **Registro histórico de 25/11/2026.** Os bloqueios nas tabelas abaixo
> descrevem a tentativa original da F10-B. A matriz autenticada posterior e
> a pendência em outra rede estão no [aceite integrado F10](f10-aceite-integrado.md).

Base `81d5bf11bcd54e3ef4d1a96413a701976ece6aa8`, branch `feat/aceite-isolamento-marcas`, worktree `.worktrees/f10-isolamento-marcas`. A publicação usa o projeto `cloudwalk_publish_integrator`. Para as consultas atuais, use a origem do [registro de restabelecimento](evidencias/f10/aceite-integrado/restabelecimento.json).

## Casos do manifesto

O registro original da frente B cita o commit F10-A `090f67bb23e141a1473310ee9954ea6e125215e7`. O bundle final da frente A trouxe o manifesto para a integração, onde ele está disponível no commit `92246f96f578767e0f42de45ff722aa2863dbe5c` com os mesmos IDs e marcadores. Os dois casos foram criados no Brave do computador de origem pela primeira URL pública. Os links da tabela registram essa origem histórica.

| Caso | ID | Link na origem de criação |
| --- | --- | --- |
| Aurora · `aurora_chat` | `ad4a4699-5d96-4cce-a248-96b3568447fc` | [Abrir Aurora](https://newbie-aqua-stem-reveal.trycloudflare.com/analista?case=ad4a4699-5d96-4cce-a248-96b3568447fc) |
| Horizonte · `horizonte_control` | `32ab943b-2bea-428f-adb7-a802fe53bfaf` | [Abrir Horizonte](https://newbie-aqua-stem-reveal.trycloudflare.com/analista?case=32ab943b-2bea-428f-adb7-a802fe53bfaf) |

## Esperado e observado

Os valores abaixo vêm do seed e da política da base. Cada linha se refere ao caso `aurora_chat` ou `horizonte_control` do manifesto da F10-A. A coluna final reserva o resultado da publicação autenticada.

| Ator | Marca | Lista completa | Link direto e detalhe REST | Histórico REST | Assinatura do caso | Observado na publicação |
| --- | --- | --- | --- | --- | --- | --- |
| Bia | Aurora | Presente | Abre, HTTP 200 com ID e marca | 200 com mensagem do caso | Confirma | Bloqueado antes do login |
| Bia | Horizonte | Ausente | Erro genérico no painel e HTTP 404 | 404 genérico | Rejeita explicitamente | Bloqueado antes do login |
| Cris | Aurora | Presente | Abre, 200 | 200 com mensagem do caso | Confirma | Bloqueado antes do login |
| Cris | Horizonte | Presente | Abre, 200 | 200 com mensagem do caso | Confirma | Bloqueado antes do login |
| Alex | Aurora | Presente | Abre, 200 | 200 com mensagem do caso | Confirma | Bloqueado antes do login |
| Alex | Horizonte | Presente | Abre, 200 | 200 com mensagem do caso | Confirma | Bloqueado antes do login |

Bia integra Especialistas Aurora. Cris integra Suporte compartilhado. Alex integra ambas as equipes. O seed vincula Suporte compartilhado às duas filas de cada marca. A API limita as consultas pelas filas das equipes do analista, inclusive quando ele opera em outra marca. A mesma relação restringe o detalhe, as mensagens e a assinatura da audiência `staff`. A resposta prevista para Bia em Horizonte é exclusivamente `{"error":{"code":"not_found","message":"Atendimento não encontrado."}}`. [Seed](../backend/db/seeds.rb) · [Visibilidade](../backend/app/services/attendances/visibility.rb) · [Consultas REST](../backend/app/controllers/api/v1/cases_controller.rb) · [Sessão do canal](../backend/app/models/browser_access/session.rb) · [Assinatura](../backend/app/channels/case_updates_channel.rb).

## Reproduzir na publicação

No computador com acesso ao endereço publicado, use a worktree de integração, Python com Playwright e Chrome ou Chromium do Playwright. O verificador lê do commit integrado os IDs, os marcadores e a URL de criação do manifesto. A origem de consulta vem do registro confiável informado em `--publication-record`, validado antes de carregar as credenciais privadas do checkout principal. [Verificador](../script/f10/isolation/verificar.py).

```sh
rtk proxy python3 -B script/f10/isolation/verificar.py \
  92246f96f578767e0f42de45ff722aa2863dbe5c \
  --publication-record docs/evidencias/f10/aceite-integrado/restabelecimento.json
```

1. Cada analista recebe um contexto de navegador novo. O verificador lê o CSRF da sessão anônima, autentica com `POST /api/v1/session` e relê a identidade antes de abrir o painel. As chamadas diretas de login e API recusam redirecionamentos. `GET /api/v1/case-filters` permite conferir as filas e marcas efetivas. Uma divergência encerra a verificação daquele perfil e fica registrada.
2. Em `GET /api/v1/cases`, percorrer até `next_cursor: null` e comparar os dois IDs. No painel, abrir `/analista?case=<ID>`. Conferir também `GET /api/v1/cases/<ID>` e `GET /api/v1/cases/<ID>/messages`. Nos casos permitidos, conferir a marca e procurar o marcador do manifesto nas páginas indicadas por `next_after_sequence`. No restrito, conferir o corpo integral das duas respostas de erro e a ausência de mensagens e contexto na tela.
3. No `/cable` do domínio consultado, usar WSS, o cookie do próprio contexto, o subprotocolo `actioncable-v1-json` e a audiência `staff`. Depois de `welcome`, conferir o identificador na resposta a `subscribe`. O controle positivo exige `confirm_subscription`. O negativo exige `reject_subscription` e reprova se chegar um quadro de dados com o mesmo identificador antes da rejeição. O painel só assina depois de carregar o detalhe, por isso o verificador abre e fecha uma assinatura explícita para o controle negativo. Timeout, desconexão ou falta de resposta deixam esse teste inconclusivo.
4. A saída registra a URL de criação, a URL consultada, o commit do manifesto e os SHA-256 do manifesto e do registro de publicação. Cada observação informa horário UTC, ator, caso, método ou operação e resultado. Uma interrupção indica a fase e, quando disponível, o status HTTP. O resultado do WebSocket usa apenas a classificação do quadro.

## Conferência por dados móveis

No terminal privado do computador da publicação, obtenha os acessos
sintéticos com o comando abaixo. `rtk run` preserva o terminal interativo
exigido para exibir as credenciais localmente.

```sh
rtk run 'python3 -B /home/inteli/Documents/projetos/case-CLOUDWALK-IA/script/publish.py --project cloudwalk_publish_integrator credentials'
```

Com Wi-Fi desligado, use a origem indicada no registro de restabelecimento e entre como Bia em um navegador privado. Use o acesso sintético pelo fluxo privado já existente. Confira primeiro o caso Aurora e depois abra `/analista?case=<horizonte_control>`. Registre se o painel informa “Atendimento não encontrado.” e se alguma mensagem do caso aparece. Em outro navegador com armazenamento independente, entre como Cris e abra **o mesmo link de Horizonte**. Confira se o histórico contém a mensagem com `F10-HORIZONTE`. A comparação entre as sessões verifica a recusa para um caso que existe. Para o registro bastam horário com fuso, origem móvel, ator, ID e resultado de cada tela.

[Registro das verificações](evidencias/f10/isolamento-marcas/verificacoes.md) · [Registro móvel anterior](evidencias/f10/integrator-f10-mobile-2026-11-25.json).
