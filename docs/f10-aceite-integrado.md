# F10 · Aceite integrado da demonstração

O túnel reabriu em 25/11/2026 às 17:16:23 UTC (14h16 de Brasília). A API
passou na verificação de saúde em HTTPS, com as mesmas imagens de API e web e
os volumes preservados. A [URL temporária](https://jason-dollar-lcd-bought.trycloudflare.com/)
depende do computador e do túnel ativos. A demonstração usa classificação
fixture e atendente simulado, com zero novas chamadas pagas.
[Registro do restabelecimento](evidencias/f10/aceite-integrado/restabelecimento.json).

## Provas do aceite

| Etapa | Caso ou ator | Ponto de observação | Resultado | Evidência |
| --- | --- | --- | --- | --- |
| Conversa automática e persistência | Aurora, caso `d5e8b8b6-e825-45f6-bd33-fb735001ba88` | Celular do responsável por dados móveis, na URL histórica `newbie-aqua-stem-reveal.trycloudflare.com` | Às 13h34 de Brasília, o responsável confirmou dois retornos automáticos e quatro mensagens em ordem após recarregar e reabrir pelo Histórico. A consulta posterior ao banco corroborou o caso. | [Manifesto A](evidencias/f10/fluxo-publico/cases.json) · [Relato F10-A](f10-aceite-fluxo.md) · [Consulta ao banco](evidencias/f10/aceite-integrado/estado-inicial.json) |
| Transferência para atendimento humano, resposta e resolução | Aurora, caso `fdb5f11f-2401-41bf-b26d-8cecb76f03bc`, Alex | Caso criado no computador de origem. Painel do analista no Chrome, pela URL pública atual, no mesmo computador | Alex autenticado conferiu o resumo e o link para a mensagem original, enviou a resposta pelo botão (HTTP 201) e resolveu pelo botão (HTTP 200). O detalhe consultado antes da recarga mostrou `resolved`, versão 8. Após recarregar, o painel exibiu a resposta humana e o histórico da API confirmou três mensagens em ordem. A prova cobre o caso do computador de origem. A conversa móvel `F10-MOBILE-HUMANO` segue sem UUID associado, conforme a linha de encaminhamento no celular. | [Registro](evidencias/f10/aceite-integrado/human-fdb5f11f-2401-41bf-b26d-8cecb76f03bc.json) · [Contexto](evidencias/f10/aceite-integrado/context-fdb5f11f-2401-41bf-b26d-8cecb76f03bc.png) · [Histórico após recarga](evidencias/f10/aceite-integrado/history-fdb5f11f-2401-41bf-b26d-8cecb76f03bc.png) |
| Matriz de acesso por marca | Bia, Cris e Alex nos casos Aurora e Horizonte do manifesto A | Três contextos independentes no Chrome, do computador de origem pelo HTTPS/WSS público atual, das 17:29:19 às 17:29:53 UTC | 36/36 verificações passaram (código de saída 0) na listagem, detalhe REST, histórico, painel e Action Cable. Bia acessou Aurora. Horizonte ficou fora da lista de Bia, devolveu 404 genérico no detalhe e histórico e `reject_subscription` explícito no WebSocket. Cris e Alex acessaram ambas as marcas. A matriz foi de consulta e preservou os casos. | [Resumo da execução](evidencias/f10/aceite-integrado/matrix-origin-01-execution.json) · [Observações JSONL](evidencias/f10/aceite-integrado/matrix-origin-01.jsonl) |
| Sinal de encaminhamento no celular | Aurora / Maquininha / Avançada, mensagem `F10-MOBILE-HUMANO` | Tela do celular, segundo o relato do responsável | O responsável viu “Com a equipe de suporte”. O integrador ainda não localizou o marcador e pediu a URL com `?case=` ou o UUID. O relato de tela segue sem associação a um caso e o fluxo ponta a ponta está pendente. | Relato do responsável no chat de execução |

Em 25/11/2026, o responsável relatou erro de acesso ou DNS no celular. O
integrador registrou HTTP 200 na verificação de saúde, resolução pelo DNS
público do Google e túnel ativo. Após a orientação de ligar o modo avião por
dez segundos e tentar novamente, o responsável confirmou que a aplicação abriu.
O caso móvel segue sem UUID associado.
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

## Pendências externas

1. **Handoff no celular.** Com dados móveis, recupere a URL com `?case=` ou o
   UUID do caso com `F10-MOBILE-HUMANO`. Com o caso identificado, o analista
   responsável deve conferir o resumo e a referência à mensagem original,
   responder pela interface e resolver. No celular, confirme a chegada da
   resposta e o estado resolvido. Recarregue, reabra o mesmo caso pelo
   Histórico e confirme que a resposta e o estado persistem.
2. **Isolamento por marca em outra rede.** Em sessões independentes por outra
   rede, abra `/analista?case=32ab943b-2bea-428f-adb7-a802fe53bfaf` no endereço
   ativo. Como Bia, confira “Atendimento não encontrado.” e a ausência de
   mensagens. Como Cris, abra o mesmo caso e confira `F10-HORIZONTE` no
   histórico. Use o acesso sintético pelo procedimento em terminal privado.
   [Conferência por dados móveis no guia B](f10-isolamento-marcas.md#conferência-por-dados-móveis).

Ao completar essas duas verificações, registre a origem da conexão, o horário
com fuso, o UUID e o resultado de cada etapa. A classificação real (C05, C06 e
C07/F09 final) segue em espera até retomada explícita. O atendente real (E01)
fica como evolução posterior e opcional. [Estado da entrega](estado-entrega.md).
