# Publicação temporária com SetFit R1

## Acesso verificado às 20h18 de 26/11/2026

Após uma interrupção da publicação, o SetFit voltou a ficar pronto e o
[endereço HTTPS atual](https://tactics-ment-kathy-cookie.trycloudflare.com/)
serviu a interface e respondeu com API e banco saudáveis. A consulta ao
PostgreSQL confirmou que o caso do teste das 17h47 conservou o status
Resolvido, Pix e Urgente com origem `setfit` e as quatro mensagens.

## Renovação anterior, às 17h47

O túnel anterior expirou. Às 17h47 de Brasília, a aplicação respondeu pelo
[endereço HTTPS daquele teste](https://eos-comp-donors-grocery.trycloudflare.com/).
O banco, Kafka e o serviço SetFit foram reaproveitados. A API e o proxy
receberam a nova origem e passaram na verificação de saúde.

No simulador público, um chat sintético da Aurora sem categoria nem
prioridade recebeu Pix e Urgente, ambos com origem `setfit`. O atendente
simulado respondeu nos dois turnos sem atualização manual. Depois da
confirmação do cliente, a página mostrou **Resolvido** e manteve as quatro
mensagens após recarregar. A consulta ao banco confirmou os mesmos campos
no caso `b2a9974b-4769-4fd8-8a2c-e2746f39415c`. O endereço permanece
temporário. Os registros completos do primeiro endereço seguem abaixo.

## Aceite no primeiro endereço

Em 26/11/2026, a demonstração foi verificada em
[mortality-windsor-weed-watt.trycloudflare.com](https://mortality-windsor-weed-watt.trycloudflare.com).
O SetFit R1 instalado no computador completou campos ausentes com o pacote
aprovado. O atendente que respondeu às mensagens foi o mock via Kafka.
As verificações da configuração local e do HTTPS usaram a revisão
`977ec3f21096d66c6b462d3cc94880e4a94eb490`.

## O que passou

| Verificação | Resultado observado |
| --- | --- |
| HTTPS · Aurora / Chat | Categoria e prioridade ausentes. SetFit completou Pix e Urgente. |
| HTTPS · Horizonte / E-mail | Categoria Pix enviada pelo canal. SetFit acrescentou Urgente e preservou Pix com origem `channel`. |
| API e WebSocket públicos | Bia leu Aurora e recebeu HTTP 404 em Horizonte. Cris leu Horizonte. O WSS confirmou, recusou e confirmou as assinaturas para esses três pares, respectivamente. |
| Navegador público · Aurora / Chat | SetFit preencheu Pix e preservou a prioridade Básica recebida. A primeira resposta apareceu automaticamente. O segundo turno resolveu o caso. As quatro mensagens conservaram os IDs após recarregar. |
| Repetição da publicação | Repetir `publish` em SetFit preservou a URL. Solicitar fixture com o túnel ativo retornou código 1 e preservou API, worker e túnel no modo vigente. |

Cada um dos dois casos da API teve uma tentativa aplicada, um turno e uma
outbox publicada com request Kafka 1.1, além da resposta do mock. A atualização
preservou os IDs dos 15 casos e das 46 mensagens anteriores e os hashes dos
textos. Foram acrescentados quatro casos sintéticos de aceite, um deles
verificado pelo HTTPS local com o túnel fechado.
[Registros da publicação](evidencias/c07/publicacao-setfit/README.md).

## Operar a publicação

Reaproveite a configuração privada e o projeto Compose
`cloudwalk_publish_integrator` da instalação original. Obtenha o pacote
pelo custodiante e aproveite apenas os passos de validação e extração dos
pesos da seção **Obter código e modelo** da
[instalação limpa C07](c07.md#obter-código-e-modelo). Mantenha o checkout em
`977ec3f` ou posterior com as correções de publicação. O comando de
checkout em `89b9e68` serve exclusivamente para reproduzir o ensaio
histórico.

No terminal, aponte `MODELO` para o diretório instalado. Na primeira
publicação com o túnel desligado, use a sequência abaixo. Se o projeto já
estiver publicado em SetFit, use `publicacao_setfit check` e
`publicacao_setfit publish` diretamente para confirmar a origem em uso.

```sh
MODELO=/caminho/escolhido/setfit-r1
publicacao_setfit() {
  rtk proxy python3 -B script/publish.py --project cloudwalk_publish_integrator \
    --classifier setfit --model-dir "$MODELO" "$@"
}
publicacao_setfit init
publicacao_setfit up
publicacao_setfit check
publicacao_setfit prepare
publicacao_setfit publish
publicacao_setfit credentials
```

Execute `credentials` em terminal privado para obter o acesso sintético.
Use a URL exibida por `publish` e abra `/analista` para entrar na operação.
A função usa as portas locais padrão. Para instalações com outras portas,
passe os mesmos valores em todas as ações.

Use `publicacao_setfit status` e `publicacao_setfit logs` para diagnóstico.
Para trocar de modo ou atualizar a pilha, execute `unpublish` com o
classificador em uso antes da troca. Em SetFit, execute
`publicacao_setfit unpublish`. A ação `down` para a pilha e preserva os
volumes. Para copiar ou restaurar esta instalação, conserve o pacote aprovado
separado dos volumes e use a seleção SetFit nas ações de `script/publish.py`.
Os passos de cópia, restauração e parada de emergência estão no
[procedimento geral F10](f10.md).

## Limites do aceite

A URL é temporária e depende do computador e do túnel ativos. O endereço
pode mudar ao reabrir o túnel. O aceite público foi funcional e usou
inferência local, sem chamadas pagas. Os ensaios F08 ocorreram em ambiente
isolado e têm seus próprios limites de recuperação sob carga e escala.
[Resultados F08](f08.md) · [R01](r01.md) · [R02](r02.md).

O aceite por dados móveis do responsável ocorreu na F10 em fixture, nas
URLs de então. O primeiro endereço SetFit foi verificado por HTTPS, WSS e
navegador. Hospedagem permanente fica fora do recorte.
O atendente conversacional Luna foi aprovado em um piloto isolado e está
desligado após o ensaio. A demonstração pública usa o atendente simulado.
[Evidências E01](evidencias/e01/README.md).
[Aceite histórico F10](f10-aceite-integrado.md) ·
[Estado da entrega](estado-entrega.md).
