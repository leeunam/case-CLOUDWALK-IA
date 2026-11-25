# F10 · Aceite integrado da demonstração

O túnel reabriu em 25/11/2026 às 17:16:23 UTC (14h16 de Brasília). A API
passou na verificação de saúde em HTTPS, com as mesmas imagens de API e web e
os volumes preservados. A [URL temporária](https://jason-dollar-lcd-bought.trycloudflare.com/)
depende do computador e do túnel ativos. A demonstração usa classificação
fixture e atendente simulado, com zero novas chamadas pagas.
[Registro do restabelecimento](evidencias/f10/aceite-integrado/restabelecimento.json).

O aceite externo da F10 foi concluído nesse modo. O responsável confirmou
por dados móveis a conversa simulada e a persistência na URL anterior, e o
handoff e o isolamento por marca na URL atual.

## Provas do aceite

| Etapa | Caso ou ator | Ponto de observação | Resultado | Evidência |
| --- | --- | --- | --- | --- |
| Conversa automática e persistência | Aurora, caso `d5e8b8b6-e825-45f6-bd33-fb735001ba88` | Celular do responsável por dados móveis, na URL histórica `newbie-aqua-stem-reveal.trycloudflare.com` | Às 13h34 de Brasília, o responsável confirmou dois retornos automáticos e quatro mensagens em ordem após recarregar e reabrir pelo Histórico. A consulta posterior ao banco corroborou o caso. | [Manifesto A](evidencias/f10/fluxo-publico/cases.json) · [Relato F10-A](f10-aceite-fluxo.md) · [Consulta ao banco](evidencias/f10/aceite-integrado/estado-inicial.json) |
| Transferência para atendimento humano, resposta e resolução | Aurora, caso `fdb5f11f-2401-41bf-b26d-8cecb76f03bc`, Alex | Caso criado no computador de origem. Painel do analista no Chrome, pela URL pública atual, no mesmo computador | Alex autenticado conferiu o resumo e o link para a mensagem original, enviou a resposta pelo botão (HTTP 201) e resolveu pelo botão (HTTP 200). O detalhe consultado antes da recarga mostrou `resolved`, versão 8. Após recarregar, o painel exibiu a resposta humana e o histórico da API confirmou três mensagens em ordem. O atendimento criado no celular tem evidência própria na linha de aceite móvel. | [Registro](evidencias/f10/aceite-integrado/human-fdb5f11f-2401-41bf-b26d-8cecb76f03bc.json) · [Contexto](evidencias/f10/aceite-integrado/context-fdb5f11f-2401-41bf-b26d-8cecb76f03bc.png) · [Histórico após recarga](evidencias/f10/aceite-integrado/history-fdb5f11f-2401-41bf-b26d-8cecb76f03bc.png) |
| Matriz de acesso por marca | Bia, Cris e Alex nos casos Aurora e Horizonte do manifesto A | Três contextos independentes no Chrome, do computador de origem pelo HTTPS/WSS público atual, das 17:29:19 às 17:29:53 UTC | 36/36 verificações passaram (código de saída 0) na listagem, detalhe REST, histórico, painel e Action Cable. Bia acessou Aurora. Horizonte ficou fora da lista de Bia, devolveu 404 genérico no detalhe e histórico e `reject_subscription` explícito no WebSocket. Cris e Alex acessaram ambas as marcas. A matriz foi de consulta e preservou os casos. | [Resumo da execução](evidencias/f10/aceite-integrado/matrix-origin-01-execution.json) · [Observações JSONL](evidencias/f10/aceite-integrado/matrix-origin-01.jsonl) |
| Aceite móvel do handoff, resposta e resolução | Aurora, categoria Maquininha (`terminal`), prioridade Avançada (`advanced`), caso `51cdd26f-f9f1-47df-84b4-5c03de2f8033` | Cliente no celular com Wi-Fi desligado, conforme confirmação no chat. Alex autenticado no Chrome do computador de origem, pela URL pública atual | O responsável viu “Com a equipe de suporte”. Alex conferiu o resumo e a referência à mensagem original, respondeu (HTTP 201) e resolveu (HTTP 200). O detalhe antes da recarga mostrou `resolved`, versão 8. Após recarregar, o painel exibiu a resposta e a API retornou três mensagens em ordem, com uma resposta humana. No celular, o responsável confirmou que a resposta apareceu automaticamente, permaneceu após recarregar e o estado era “Resolvido”. | [Confirmação do responsável](evidencias/f10/aceite-integrado/mobile-human-confirmation.json) · [Registro da execução](evidencias/f10/aceite-integrado/human-51cdd26f-f9f1-47df-84b4-5c03de2f8033.json) · [Contexto](evidencias/f10/aceite-integrado/context-51cdd26f-f9f1-47df-84b4-5c03de2f8033.png) · [Histórico após recarga](evidencias/f10/aceite-integrado/history-51cdd26f-f9f1-47df-84b4-5c03de2f8033.png) |
| Acesso móvel da F10-B | Bia, Aurora, caso `ad4a4699-5d96-4cce-a248-96b3568447fc` | Celular com Wi-Fi desligado, conforme confirmação do responsável | Abriu a conversa. | [Confirmação móvel](evidencias/f10/aceite-integrado/mobile-brand-isolation-confirmation.json) |
| Bloqueio móvel da F10-B | Bia, Horizonte, caso `32ab943b-2bea-428f-adb7-a802fe53bfaf` | Celular com Wi-Fi desligado, conforme confirmação do responsável | A interface exibiu “Atendimento não encontrado”. | [Confirmação móvel](evidencias/f10/aceite-integrado/mobile-brand-isolation-confirmation.json) |
| Acesso móvel da F10-B | Cris, Horizonte, caso `32ab943b-2bea-428f-adb7-a802fe53bfaf` | Celular com Wi-Fi desligado, conforme confirmação do responsável | Abriu o histórico do mesmo caso Horizonte. | [Confirmação móvel](evidencias/f10/aceite-integrado/mobile-brand-isolation-confirmation.json) |

A F10-A foi aprovada com a conversa simulada e seu histórico na URL anterior
e com o handoff, a resposta humana e a resolução na URL atual. O integrador
identificou o atendimento móvel pelo endereço da conversa aberta e conferiu o
texto “o visor da maquininha apagou desde a troca de bateria”, a marca, a
categoria e a prioridade. A busca por `F10-MOBILE-HUMANO` retornou vazia. A
referência apontava para a mensagem `dec985e2-2a18-4a58-9550-711e04be9d4d`.
O caso estava em `human_active`, versão 6, atribuído a Alex antes da resposta.

A execução de Alex ocorreu entre 17:54:18 e 17:54:26 UTC de 25/11/2026. O
campo `mobile_receipt_confirmation: pending` registra aquele momento. A
confirmação posterior, registrada às 17:55:22 UTC, vincula o mesmo UUID e o
SHA-256 do registro da execução. A observação no celular confirma a atualização
sem recarga. O mecanismo de atualização pode ter sido WebSocket ou polling.

A confirmação da F10-B foi registrada às 18:00:28 UTC de 25/11/2026 e vincula
pelo SHA-256 a matriz complementar do computador de origem. O responsável
relatou três resultados de interface pelo celular. Para o isolamento por
marca, os códigos HTTP e as respostas de WebSocket são observações da matriz
do computador de origem.
[Confirmação do isolamento por marca](evidencias/f10/aceite-integrado/mobile-brand-isolation-confirmation.json).

Em 25/11/2026, o responsável relatou erro de acesso ou DNS no celular. O
integrador registrou HTTP 200 na verificação de saúde, resolução pelo DNS
público do Google e túnel ativo. Após a orientação de ligar o modo avião por
dez segundos e tentar novamente, o responsável confirmou que a aplicação abriu.
[Registro da conectividade móvel](evidencias/f10/aceite-integrado/mobile-connectivity.json).

O histórico da publicação registra o reinício com persistência e a
restauração em uma instalação isolada. [Resultado da publicação](f10-resultado.md).

## Proveniência de A e B

- **F10-A.** Os commits `d4e02f7` e `92246f9` trouxeram a entrega final. O
  manifesto usado na matriz está no commit `92246f9`. O `090f67b` foi uma
  referência preliminar relatada e ficou fora do bundle final de A.
  [Roteiro e resultados A](f10-aceite-fluxo.md) ·
  [Manifesto de casos](evidencias/f10/fluxo-publico/cases.json).
- **F10-B.** A frente relatou o commit original `a363741` e um bundle
  indisponível no computador de origem. A integração registrou em `e3e7765`
  uma cópia dos três arquivos compartilhados, com hashes preservados. As
  correções do verificador entraram em `86d5c57`. Cinco testes offline
  passaram e a revisão de A e B foi aprovada.
  [Registro da importação](evidencias/f10/isolamento-marcas/importacao-central.json) ·
  [Guia B](f10-isolamento-marcas.md) ·
  [Primeiras verificações B](evidencias/f10/isolamento-marcas/verificacoes.md).

## Reprodução do isolamento em outra rede

Com o túnel ativo, siga o guia B para repetir a F10-B com os perfis sintéticos.
Em sessões independentes, compare o acesso de Bia e Cris ao mesmo caso
Horizonte, `32ab943b-2bea-428f-adb7-a802fe53bfaf`, e registre a origem da
conexão, o horário com fuso e o resultado para cada perfil.
[Conferência por dados móveis no guia B](f10-isolamento-marcas.md#conferência-por-dados-móveis).

A classificação real (C05, C06 e C07/F09 final) segue em espera até retomada
explícita. O atendente real (E01) fica como evolução posterior e opcional.
[Estado da entrega](estado-entrega.md).
