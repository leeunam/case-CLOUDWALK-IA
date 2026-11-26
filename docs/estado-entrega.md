# Estado da entrega em 26/11/2026

A publicação temporária da plataforma passou no aceite externo da F10 com
classificação fixture e atendente simulado. O responsável retomou a classificação
com SetFit e aprovou 360 relatos novos (150 de treino, 90 de validação, 120 finais).
A SF2 concluiu contratos, dados, código e a validação dos dois especialistas
treinados. Nenhuma das 225 políticas de revisão atingiu todos os critérios.
Na extensão offline SF2-R1, nove regras adicionais atingiram as metas de
validação. A selecionada concluiu corretamente 51/72 classificáveis e
revisou todos os 18 casos que exigiam revisão. A
[preparação pública revisada da SF2-FINAL-R1](evidencias/c05/sf2/final-r1-preparacao-02/README.md)
teve aceite independente. Os 120 casos finais permanecem fechados e nenhum
modelo foi adotado.
[Plano de execução e critérios de aceite](planejamento/plano-de-execucao.md).

## Plataforma e demonstração

| Frente | Evidência registrada |
| --- | --- |
| F01–F07 | Implementadas e aceitas localmente. A operação percorre três canais e duas marcas, com classificação fixture, revisão humana, atendente simulado via Kafka, handoff, isolamento e reentrega. A qualificação real do classificador passou ao CLASS-001. [Plano de execução](planejamento/plano-de-execucao.md) · [F04/F05](integracao-f04-f05.md) · [F06/F07](integracao-f06-f07.md). |
| F08, R01 e R02 | O experimento de referência teve cinco rodadas aprovadas e uma reprovada por falha de recuperação após a parada do Kafka. A R01 foi aceita com recuperação em ensaio controlado posterior. A R02 foi aceita com a correção do analisador e a conferência dos dados arquivados. A matriz de referência preserva a reprovação e segue sem nova execução após as correções. [F08](f08.md) · [R01](r01.md) · [R02](r02.md). |
| F09-A | A instalação limpa com fixture comprovou dois turnos, reentrega, três canais, duas marcas, handoff, revisão humana e persistência. O trecho com complemento real pertence à C07/F09 final. [Roteiro e evidências F09](f09.md). |
| F10 e UX02 | A publicação temporária em HTTPS usa fixture e atendente simulado. Reinício com persistência e restauração em instalação isolada foram verificados. A F10-A passou com conversa simulada e histórico por dados móveis na URL anterior e com handoff, resposta e resolução na URL atual. A F10-B passou com o contraste entre Bia e Cris por dados móveis. A matriz pública passou em 36 de 36 verificações de acesso por marca no computador de origem. [Aceite integrado](f10-aceite-integrado.md) · [Histórico da publicação](f10-resultado.md) · [Aceite UX02](ux02.md). |

A [URL temporária](https://jason-dollar-lcd-bought.trycloudflare.com/) foi
verificada em HTTPS quando o túnel reabriu em 25/11/2026. O acesso depende do
computador e do túnel ativos. Alex conferiu o resumo e a referência do caso
`51cdd26f-f9f1-47df-84b4-5c03de2f8033`, respondeu e resolveu. Com o Wi-Fi
desligado, o responsável confirmou a chegada automática da resposta, a
persistência após recarregar e o estado “Resolvido”. Também confirmou que Bia
abriu Aurora, teve acesso negado ao caso Horizonte e que Cris abriu o histórico
do mesmo caso Horizonte.
[Provas do aceite externo](f10-aceite-integrado.md#provas-do-aceite).

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

A demonstração continua com fixture. No histórico da R5, a candidata foi
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
7,53 s. Os tempos do replay medem fixture e cálculo da decisão. O teste
final e a medição de inferência aguardam a confirmação do nome do
inventário e dos quatro papéis previstos no protocolo e a autorização
específica vinculada ao recibo revisado.
[Evidências da preparação pública](evidencias/c05/sf2/final-r1-preparacao-02/README.md).

A integração (C06) e a reprodução do complemento real (C07/F09 final) continuam
bloqueadas. O fechamento completo ainda requer qualificação conforme
os critérios vigentes, adoção aprovada e o aceite do complemento real com
proveniência, revisão humana, broker e handoff. O atendente conversacional
real (E01) fica como evolução posterior e opcional.
[Plano de conclusão](planejamento/conclusao-projeto.md).
