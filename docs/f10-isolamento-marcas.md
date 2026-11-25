# F10-B · Acesso aos atendimentos por marca

Base `81d5bf11bcd54e3ef4d1a96413a701976ece6aa8`, branch `feat/aceite-isolamento-marcas`, worktree `.worktrees/f10-isolamento-marcas`. A publicação usa o projeto `cloudwalk_publish_integrator`. [Painel de analistas](https://newbie-aqua-stem-reveal.trycloudflare.com/analista).

## Casos do manifesto

Commit F10-A `090f67bb23e141a1473310ee9954ea6e125215e7`, conferido no bundle da frente A. Os dois casos foram criados no Brave do computador de origem pela URL pública.

| Caso | ID | Link para as sessões de teste |
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

No computador com acesso ao endereço publicado, use a worktree desta tarefa, Python com Playwright e Chrome ou Chromium do Playwright. O commit do manifesto precisa estar disponível para leitura pelo Git. Nesta máquina, enquanto estiver apenas no bundle verificado da F10-A, o prefixo de ambiente `GIT_ALTERNATE_OBJECT_DIRECTORIES=/tmp/cloudwalk-f10-a.vtsEiXhN/git/objects` também permite ler o commit. O verificador lê do Git os IDs, os marcadores e a URL. Confere o destino e usa o fluxo privado de credenciais do checkout principal. [Verificador](../script/f10/isolation/verificar.py).

```sh
rtk proxy python3 -B script/f10/isolation/verificar.py 090f67bb23e141a1473310ee9954ea6e125215e7
```

1. Cada analista recebe um contexto de navegador novo. O único POST é o login em `/api/v1/session`. A releitura da sessão valida a identidade. `GET /api/v1/case-filters` permite conferir as filas e marcas efetivas. Uma divergência encerra a verificação daquele perfil e fica registrada.
2. Em `GET /api/v1/cases`, percorrer até `next_cursor: null` e comparar os dois IDs. No painel, abrir `/analista?case=<ID>`. Conferir também `GET /api/v1/cases/<ID>` e `GET /api/v1/cases/<ID>/messages`. Nos casos permitidos, conferir a marca e localizar a mensagem pelo marcador do manifesto. No restrito, conferir o corpo integral das duas respostas de erro e a ausência de mensagens e contexto na tela.
3. Em `wss://newbie-aqua-stem-reveal.trycloudflare.com/cable`, usar o cookie do próprio contexto, o subprotocolo `actioncable-v1-json` e a audiência `staff`. Depois de `welcome`, conferir o identificador na resposta a `subscribe`. O controle positivo exige `confirm_subscription`. O negativo exige `reject_subscription`. O painel só assina depois de carregar o detalhe, por isso o verificador abre e fecha uma assinatura explícita para o controle negativo. Timeout, desconexão ou falta de resposta deixam esse teste inconclusivo.
4. A saída associa o commit, a origem e o método às observações por horário UTC, ator, caso e operação. Qualquer exibição de dados restritos ou confirmação da assinatura restrita reprova o controle correspondente. Um login inválido ou uma falha de transporte impede concluir sobre permissão.

## Conferência por dados móveis

Com Wi-Fi desligado, entre como Bia em um navegador privado pela URL acima. Use o acesso sintético pelo fluxo privado já existente. Confira primeiro o caso Aurora e depois abra `/analista?case=<horizonte_control>`. Registre se o painel informa “Atendimento não encontrado.” e se alguma mensagem do caso aparece. Em outro navegador com armazenamento independente, entre como Cris e abra **o mesmo link de Horizonte**. Confira se o histórico contém a mensagem com `F10-HORIZONTE`. O contraste entre as duas sessões verifica a recusa para um caso que existe. Para o registro bastam horário com fuso, origem móvel, ator, ID e resultado de cada tela.

[Registro das verificações](evidencias/f10/isolamento-marcas/verificacoes.md) · [Registro móvel anterior](evidencias/f10/integrator-f10-mobile-2026-11-25.json).
