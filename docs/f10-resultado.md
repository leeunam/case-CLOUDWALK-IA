# F10 · Resultado da publicação de demonstração

## Endereço atual

Em 25/11/2026, às 12h44 de Brasília, o integrador renovou o túnel após a
expiração da URL da UX02. A verificação da
[nova URL temporária](https://newbie-aqua-stem-reveal.trycloudflare.com/)
confirmou a saúde da API em HTTPS. O fluxo completo por outra rede segue
pendente. O acesso depende do computador e do túnel ativos.
[Evidência da renovação](evidencias/f10/integrator-f10-renewal-2026-11-25.json).

## Registro da publicação UX02

A demonstração foi reaberta na entrega UX02 em
[tribal-louisville-container-bind.trycloudflare.com](https://tribal-louisville-container-bind.trycloudflare.com/).
O tema `8ac8a00` foi publicado e verificado em HTTPS, com conversa de dois turnos
pela API e atendente simulado. O túnel anterior estava parado; os volumes foram
preservados. A confirmação por dados móveis registrada abaixo pertence ao
endereço anterior, não constitui um novo teste externo deste link.
[Evidências UX02](ux02.md).

## Registro da primeira publicação

Em 24/11/2026 o integrador publicou a demonstração em
<https://mirrors-labour-crafts-characteristic.trycloudflare.com>, usando o projeto
isolado `cloudwalk_publish_integrator`. A URL é temporária e depende do computador
e do processo ligados. O código integrado da aplicação foi verificado na revisão
`7f04b9b3b2e75c3db4993bcaf0ce82140a86f96f`.

## Verificações realizadas

- HTTPS público com validação normal de certificado, API e banco saudáveis,
  páginas React, rotas da API e cache dos arquivos compilados.
- Login sintético privado, cookie seguro, rejeição de CSRF e origem incorretos,
  upgrade WebSocket aceito na origem configurada e negado em outra origem.
- Conversa de Chat da Aurora, duas mensagens do cliente e duas do atendente
  simulado, encerrada e recuperada pelo mesmo ID após recarregar o navegador.
- Reinício de API, frontend e worker, preservando o túnel, a URL e o atendimento
  anterior com histórico e handoff. A verificação pública passou novamente.
- Backup offline dos três volumes e configuração privada, seguido de restauração
  em projeto e volumes novos. O mesmo atendimento foi recuperado pelo ID na
  revisão exata da cópia, `6c13f40d54d989ddf2a7359869947ab8beee2dd9`.

As provas estão em [publicação](evidencias/f10/integrator-f10-public.json),
[restauração](evidencias/f10/integrator-f10-restore.json) e
[verificação local](evidencias/f10/integrator-f10-local.json).
Nenhum segredo ou arquivo privado de backup foi versionado.

## Limitações e continuidade

A classificação publicada usa fixture determinística e o atendente usa mock.
Essas verificações fizeram zero chamadas de IA. A preparação offline da Luna
continua separada da qualificação real, da decisão de adoção e da integração C06.
A publicação da demonstração não conclui esses marcos.

As sondas e o navegador usaram o endereço público a partir do computador de
origem. A ferramenta remota de consulta não conseguiu acessar esse endereço.
O responsável confirmou que as marcas e os canais aparecem no celular usando
dados móveis, atendendo à verificação por outra rede.
Não há servidor permanente nem compromisso de disponibilidade. As condições do
Quick Tunnel e os procedimentos para obter credenciais em terminal privado,
parar, reabrir e restaurar estão no [roteiro F10](f10.md).
