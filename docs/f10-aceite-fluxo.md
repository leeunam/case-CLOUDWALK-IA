# F10-A · Aceite do fluxo público

A execução de 25/11/2026 usou o projeto `cloudwalk_publish_integrator` e o
[simulador publicado em HTTPS](https://newbie-aqua-stem-reveal.trycloudflare.com/).
O formulário estava conectado à API, com classificador fixture e atendente
simulado. A classificação real e o SetFit seguiram em espera. A publicação foi
preservada, com zero chamadas pagas.

## Resultados

| Etapa | Origem e método | Horário de Brasília | Resultado |
| --- | --- | --- | --- |
| Aurora · Chat · Pix + Básica | Brave no computador de origem, formulário e histórico pelo HTTPS público | 13h30 | Primeiro retorno sem recarga. Segundo turno encerrou o atendimento. Após recarregar e reabrir pelo Histórico, as quatro mensagens estavam na mesma ordem. A API confirmou as sequências 1–4 no mesmo caso. |
| Aurora · Chat · Maquininha + Avançada | Brave no computador de origem, formulário e leitura do caso na API do simulador | 13h31 | O atendente simulado avisou do encaminhamento. O simulador exibiu **Com a equipe de suporte** e a API registrou `human_active`. O relato original e o aviso constavam no histórico. |
| Horizonte · Chat · Pix + Básica | Brave no computador de origem, formulário e leitura do caso na API do simulador | 13h29 | O controle `F10-HORIZONTE` recebeu resposta do atendente simulado e ficou `ai_active`, disponível para a verificação da F10-B. |
| Aurora · Chat · Pix + Básica | Celular por dados móveis, relato do responsável no chat | Confirmação às 13h34 | O responsável informou os dois retornos automáticos e confirmou as quatro mensagens em ordem após recarregar e reabrir pelo Histórico. Informou o UUID `d5e8b8b6-e825-45f6-bd33-fb735001ba88` via lista da API na mesma sessão móvel. |

[Manifesto de casos e IDs](evidencias/f10/fluxo-publico/cases.json) ·
[Mensagens verificadas na API](evidencias/f10/fluxo-publico/mensagens.json)

## Consolidação do aceite

Em 25/11/2026, às 14h09 de Brasília (17h09 UTC), uma consulta somente leitura
ao banco da publicação encontrou o caso de handoff
`fdb5f11f-2401-41bf-b26d-8cecb76f03bc` em `human_active`, versão 6, com duas
mensagens. Alex era o responsável e estava com Aurora Pagamentos em operação.
O resumo incluía o relato original e fazia referência a
`eb55d79a-16dc-4a50-b459-09195f683395`, o ID da mensagem do cliente.
[Consulta registrada](evidencias/f10/aceite-integrado/estado-inicial.json).

Na conferência do relato móvel original, o responsável respondeu à pergunta
sobre as quatro mensagens após recarregar e reabrir pelo Histórico e informou
o UUID solicitado na lista da API da mesma sessão. Essa confirmação se refere
à conversa de dois turnos.

## Verificações e pendências

- A API do simulador confirmou o UUID e o estado dos três casos do computador.
  A aba do analista abriu no formulário de login. A conferência do handoff no
  painel do analista, o envio da resposta humana e a resolução dependem da
  sessão privada da operação.
- O computador de origem acessou o túnel pelo navegador. A execução direta
  pelo terminal retornou erro de resolução do host público e bloqueio de
  socket na sondagem de loopback. A consulta Docker retornou acesso negado ao
  socket. As observações do celular são registradas a partir do relato do
  responsável.
- O handoff no celular e a confirmação da resposta humana e da resolução
  antes e após recarregar permanecem pendentes.

## Reprodução

1. No celular usando dados móveis, abra a origem HTTPS informada no
   [registro de restabelecimento](evidencias/f10/aceite-integrado/restabelecimento.json)
   e selecione **Aurora Pagamentos**, **Chat**, **Pix** e **Básica**. Envie
   `F10-CLIENTE: qual é o
   prazo de confirmação de um Pix?` e aguarde a resposta. Envie `F10-CLIENTE:
   funcionou, obrigado!` no mesmo atendimento e espere o encerramento.
2. Recarregue a página, reabra a conversa pelo **Histórico** e confira as quatro
   mensagens. Na sessão do simulador, consulte `GET /api/v1/simulator/cases` e
   `GET /api/v1/simulator/cases/{id}/messages` para associar o UUID e as
   sequências à conversa.
3. Abra outro atendimento da Aurora e selecione **Maquininha** e **Avançada**.
   Envie `F10-HUMANO: o visor da maquininha apagou desde a troca de bateria.`.
   Aguarde **Com a equipe de suporte**. Com a sessão privada do responsável
   efetivo pela Aurora, abra o caso em `/analista`, confira o relato, o resumo
   e as referências, envie uma resposta sintética e resolva o atendimento. A
   interface usa a versão observada e uma chave de idempotência para cada
   ação. Confira a resposta e a resolução no celular antes e após recarregar.

Como exercício, compare a ordem das quatro mensagens no Histórico com os
campos `sequence` da API de mensagens para o mesmo UUID.
