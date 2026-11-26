# Estado da entrega em 26/11/2026

A entrega do MVP está concluída. A publicação temporária com SetFit R1
local e atendente simulado via Kafka foi verificada em 26/11/2026.
[Matriz de aceite e operação](c07-publicacao-setfit.md).

Para chegar à adoção do SetFit, o responsável aprovou 360 relatos novos
(150 de treino, 90 de validação, 120 finais).
A SF2 concluiu contratos, dados, código e a validação dos dois especialistas
treinados. Nenhuma das 225 políticas de revisão atingiu todos os critérios.
Na extensão offline SF2-R1, nove regras adicionais atingiram as metas de
validação. A selecionada concluiu corretamente 51/72 classificáveis e
revisou todos os 18 casos que exigiam revisão. No teste independente final, a R1 passou nos dez critérios, com 120 casos e cinco controles. O responsável adotou o SetFit R1 para C06 pela autorização condicionada ao resultado. A C06 comprovou a integração no Rails e a C07 reproduziu o fluxo em clone limpo com o pacote portátil. [Decisão](planejamento/classificacao-comparativa/sf2/decisao-adocao-r1.md) · [Plano de integração](planejamento/classificacao-comparativa/c06-setfit-integracao.md).

## Plataforma e demonstração

| Frente | Evidência registrada |
| --- | --- |
| F01–F07 | Implementadas e aceitas localmente. A operação percorre três canais e duas marcas, com classificação fixture, revisão humana, atendente simulado via Kafka, handoff, isolamento e reentrega. A qualificação real do classificador passou ao CLASS-001. [Plano de execução](planejamento/plano-de-execucao.md) · [F04/F05](integracao-f04-f05.md) · [F06/F07](integracao-f06-f07.md). |
| F08, R01 e R02 | O experimento de referência teve cinco rodadas aprovadas e uma reprovada por falha de recuperação após a parada do Kafka. R01 passou em ensaio controlado de recuperação e R02 passou na reanálise dos dados arquivados, ambas em reprodução independente. A matriz F08 preserva a reprovação e segue sem nova execução. [F08](f08.md) · [R01](r01.md) · [R02](r02.md) · [Reprodução](evidencias/c07/README.md). |
| F09-A | A instalação limpa com fixture comprovou dois turnos, reentrega, três canais, duas marcas, handoff, revisão humana e persistência. O trecho com complemento real pertence à C07/F09 final. [Roteiro e evidências F09](f09.md). |
| C06 e C07/F09 final | O serviço SetFit CPU complementou campos ausentes em instalação local. A reprodução em clone novo verificou três canais, duas marcas, revisão humana e históricos após reinício. [Aceite C06](evidencias/c06/aceite-integrado/README.md) · [Instalar e percorrer a C07](c07.md). |
| F10 e UX02 | A publicação histórica em fixture passou por reinício, restauração em instalação isolada e aceite por dados móveis em 25/11. O responsável conferiu dois turnos automáticos, handoff, resposta humana, resolução, persistência após recarga e acesso de Bia e Cris por marca. A matriz pública passou em 36 de 36 verificações de acesso por marca no computador de origem. [Aceite integrado](f10-aceite-integrado.md) · [Histórico da publicação](f10-resultado.md) · [Aceite UX02](ux02.md). |
| Publicação SetFit | Em dois casos enviados pelo HTTPS, o SetFit completou os campos ausentes e o mock respondeu via Kafka. A prova pública cobriu REST e WSS por marca, dois turnos no navegador e reabertura do histórico. A revisão focal fechou os cinco achados do parecer amplo. A atualização preservou os 15 casos e 46 mensagens anteriores. [Aceite público](c07-publicacao-setfit.md) · [Revisão final](evidencias/c06/revisao-final/README.md). |

A [URL verificada em 26/11](https://mortality-windsor-weed-watt.trycloudflare.com)
depende do computador e do túnel ativos. O teste do responsável por dados
móveis permanece registrado na F10 de 25/11, com fixture.

Repetir a matriz F08 nas mesmas condições reforçaria a evidência sob carga
após as correções. Aumento progressivo de taxa, carga de atendimento humano
e até dez mil conexões de chat são cenários exploratórios ainda sem medição.
[Método e resultados F08](f08.md).

## Classificação real

O piloto C05-SF1 de categoria foi concluído em CPU, fora da aplicação
publicada. Nos 16 casos sintéticos de desenvolvimento, acertou 15 decisões,
com 12/12 acertos nos casos classificáveis e 3/4 revisões reconhecidas. No
caso `jev-013`, o piloto previu `terminal` quando se esperava revisão. O p95
de inferência por texto foi de 21,078 ms (n=16). O resultado é histórico e
não substitui o ensaio SF2 de categoria e prioridade abaixo.
[Plano do piloto SetFit](planejamento/classificacao-comparativa/setfit-piloto.md).

A publicação temporária verificada na F10 usou fixture. No histórico da R5, a candidata foi
descartada para adoção e a reserva
da tentativa interrompida segue pendente. [Resultado R5](c05-luna-r5-resultado.md).

A escolha e a regra de revisão (C05) foram retomadas no planejamento da
[SF2](planejamento/classificacao-comparativa/sf2/especificacao.md), com
[tarefas para agentes](planejamento/classificacao-comparativa/sf2/tarefas.md).
Após o aceite de 00–04, os dois modelos completaram o treino em 913,685 s
acumulados e passaram no reload. A coleta SF2-05A registrou 90 relatos e cinco
controles. Na política de coleta, categoria acertou 45/47 complementos
aplicados e prioridade 39/44, com p95 de 177,61 ms. As 225 políticas testadas
concluíram pelo menos dois casos que exigiam revisão, impedindo a qualificação.
A [evidência revisada](evidencias/c05/sf2/qualificacao-01/README.md) foi
integrada localmente. Sem política elegível, não houve congelamento, avaliação
dos 120 finais ou liberação de C06.

A extensão [SF2-R1](evidencias/c05/sf2/revisao-01/README.md) reutilizou os
mesmos vetores sem treino ou inferência adicional. Das 45 políticas novas,
nove passaram; a selecionada usa categoria tau 0,95 e prioridade tau 0,70.
A cobertura correta foi 51/72, com zero conclusões indevidas nos 18 casos
de revisão esperada, zero urgentes rebaixados e 39/90 revisões.

Em 26/11/2026, a revisão independente aceitou a preparação pública da
SF2-FINAL-R1 após a correção dos três P1 da revisão ampla. O QA registrou
32 testes aprovados em 7,736 s e o revisor reproduziu o recibo revisado em
7,53 s. Os tempos do replay medem fixture e cálculo da decisão. [Evidências da preparação pública](evidencias/c05/sf2/final-r1-preparacao-02/README.md).

O teste independente único passou nos dez critérios, com duas auditorias idênticas em bytes. Houve 68 conclusões corretas entre 96 classificáveis, uma conclusão com prioridade incorreta e 51 revisões em 120 casos. O p95 de 71,96 ms mede a latência do adaptador nos casos. A C06 mediu o fluxo no help desk separadamente. Na C07, transcorreram 1.084,955 ms da criação do caso de complemento até o resultado Kafka persistido. [Resultado final e recursos observados](evidencias/c05/sf2/final-r1-01/README.md).

A C06 e a C07/F09 final verificaram o pacote e a política adotados, a origem
dos campos e a resposta via Kafka. O pacote portátil é fornecido pelo
custodiante. A publicação HTTPS foi validada depois da reprodução local,
sem chamadas pagas nesta continuação. E01, o atendente conversacional real,
permanece opcional após o fechamento.
[Plano de C06/C07](planejamento/classificacao-comparativa/c06-setfit-integracao.md) ·
[Publicação SetFit](c07-publicacao-setfit.md).
