# C01 — critérios e separação dos dados aprovados

Estado: **critérios e divisão aprovados pelo responsável em 2026-11-23**, pela
resposta “aprovo” no chat central. São escolhas para o MVP, não exigências do
TAPI ou resultados medidos. O fechamento dos contratos ainda precede a
liberação de C02; chamadas reais continuam sem orçamento autorizado.

[Definições estruturadas](protocolo-comparacao.json) ·
[IDs e contagens da divisão](divisao-dados.json) ·
[Origem da revisão dos rótulos](revisao-de-rotulos.md).

## Régua aprovada

| Critério | Meta aprovada | Motivo |
| --- | --- | --- |
| Preservar dados válidos do canal | 100%; controles com entrada completa ou inválida fazem zero chamadas ao modelo. | O modelo só complementa campos ausentes. |
| Aplicação íntegra | Zero aplicação parcial após abstenção, erro ou campo inválido. | Um resultado incompleto deve seguir para revisão. |
| Urgentes rebaixados | Zero casos com prioridade urgente omitida automaticamente aplicada abaixo de urgente. | Esse erro impede a elegibilidade, mesmo com média alta. |
| Reconhecer urgência | Pelo menos 80% das escolhas brutas válidas do campo esperado urgente: 5 dos 6 casos do teste. | Mandar todos os urgentes para revisão não basta para demonstrar reconhecimento. |
| Acerto aplicado | Pelo menos 90%, separadamente em categoria e prioridade, entre os campos ausentes efetivamente aplicados. | Campos fornecidos pelo canal, abstenções e resultados não aplicados não contam como acertos. |
| Cobertura automática | Pelo menos 70% dos casos cujo gabarito permite complemento completo: 21 dos 29 casos do teste. | Evita considerar bom um modelo que só responde a poucos casos fáceis. |
| Ambiguidade esperada | Os 7 casos com pelo menos um campo esperado como informação insuficiente devem ir para revisão. | Nesses casos não se deve aplicar um complemento completo por suposição. |
| Tempo de resposta | p95 da tentativa completa com modelo/processo aquecido até 3 segundos; timeout de 5 segundos por relato. | Meta inicial para classificar sem alongar excessivamente o atendimento. |

As metas de 90%, 70%, 80% e 3 segundos são escolhas aprovadas para este MVP.
Acerto considera confiabilidade das decisões aplicadas; cobertura considera
quanto trabalho o modelo consegue assumir. Exigir os dois evita premiar apenas
uma média obtida em poucas respostas. Essas metas devem ser congeladas antes
de observar os resultados finais, com possibilidade de nenhum candidato passar.

## Denominadores e resultados que devem continuar visíveis

- Acerto aplicado por campo: decisões corretas divididas por todas as decisões
  aplicadas daquele campo. Se não houver aplicação, o resultado é inconclusivo.
- Reportar também acerto bruto por campo, abstenções, erros e campos não
  aplicados. A aplicação tudo-ou-revisão pode impedir aplicar uma escolha bruta correta.
- Cobertura automática: casos completamente aplicados divididos pelos 29 casos
  classificáveis do teste. Uma conclusão errada continua sendo automática e é
  penalizada no acerto. Reportar também a cobertura de conclusões corretas.
- Nos seis urgentes com prioridade omitida, reconhecer `urgent` é uma escolha
  bruta válida do campo. Abstenção, falha ou outra escolha não é reconhecimento.
  Reportar separadamente rebaixamento aplicado, revisão, saída inválida e transporte.
- O caso 027 tem prioridade esperada urgente e categoria insuficiente. É possível
  reconhecer a urgência e ainda encaminhar o conjunto para revisão corretamente.
- Tempo é por relato completo, incluindo todas as perguntas de campo, validação
  e interpretação da saída. Incluir todas as durações observadas, inclusive
  falhas/timeouts. Reportar carregamento inicial/cold start separadamente.
- Usar p95 por posto mais próximo: ordenar as n durações e selecionar o posto
  `ceil(0.95 * n)`. Com 36 tentativas, o posto é 35. Informar também p50 e n.
- Rodar as 36 tentativas do teste por candidato com concorrência 1 e uma tentativa
  por relato. Ensaio incompleto, métrica ausente ou denominador zero é inconclusivo.

## Separação aprovada: 24 para desenvolver e 36 para testar

| Grupo | Casos | Categoria ausente | Prioridade ausente | Ambos ausentes | Campos-alvo | Urgentes com prioridade omitida |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Desenvolvimento/calibração | 24 | 8 | 8 | 8 | 32 | 4 |
| Teste final | 36 | 12 | 12 | 12 | 48 | 6 |

O teste contém 29 casos classificáveis e 7 com revisão esperada. Dois dos 36
casos têm aprovação direta do responsável e 34 foram revisados por IA delegada.
O conjunto é sintético e exploratório; seis urgentes não sustentam uma conclusão
de segurança em produção. Os IDs e as demais contagens estão no manifesto da divisão.

Os dois modelos recebem os mesmos relatos, campos válidos, campos ausentes e
catálogo/definições. Não enviar `expected`, justificativas, estrato, origem da
revisão ou ressalvas ao modelo. Casos do teste não entram como exemplos nos prompts.
Usar somente desenvolvimento para ajustar instruções e limiares de abstenção;
congelar tudo antes do teste final, sem ajustar depois de observar seus resultados.
Como os rótulos existem no repositório e foram revisados no chat, esta é uma
reserva para o ensaio, não um teste externo cego.

## Uso de API e recursos locais

O teto monetário permanece **pendente**, sem chamadas reais autorizadas por
este protocolo. Antes do piloto, confirmar tarifa e estimar o lote; decidir com
o responsável o limite e registrar como interromper antes de ultrapassá-lo.
Fixtures e validação de contratos podem ser preparadas enquanto isso.

Reportar uso/custo observado de API, estimativas identificadas e valores ausentes.
Na execução local, registrar CPU/GPU, memória, carregamento e inferência; custo
por chamada de API zero não representa custo total de infraestrutura zero.

## Como decidir depois

Um candidato só é elegível com todos os critérios satisfeitos e evidência completa.
Entre elegíveis, comparar conclusões corretas, acerto por campo, resultados em
urgentes, latência e custo/recursos. O responsável registra a escolha fundamentada;
inconclusão e nenhum candidato elegível são resultados possíveis. Não combinar
violações de segurança com médias altas para produzir uma nota compensatória.

## Base metodológica

A separação de dados de ajuste e teste segue a prevenção de vazamento descrita
na [documentação do scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html).
O compromisso entre cobertura e erros nas decisões aceitas é discutido em
[Selective Classification for Deep Neural Networks](https://arxiv.org/abs/1705.08500).
Essas referências apoiam o método; os valores numéricos deste protocolo são
decisões locais aprovadas, não limites prescritos pelas fontes.

## O que falta para C01

Completar/congelar rubrica e schemas com exemplos válidos/inválidos e registrar
o aceite do protocolo completo. O orçamento
pode continuar pendente para C02 com fixtures, mantendo execuções reais bloqueadas.
