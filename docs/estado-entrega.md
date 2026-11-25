# Estado da entrega em 25/11/2026

A plataforma de atendimento já foi demonstrada com classificador fixture e
atendente simulado. Falta completar o aceite externo da publicação temporária.
O complemento real da classificação continua pendente. O responsável autorizou
o piloto SetFit e propôs adiar a categorização para avançar nas demais frentes.
[Plano de execução e critérios de aceite](planejamento/plano-de-execucao.md).

## Plataforma e demonstração

| Frente | Evidência registrada |
| --- | --- |
| F01–F07 | Implementadas e aceitas localmente. A operação percorre três canais e duas marcas, com classificação fixture, revisão humana, atendente simulado via Kafka, handoff, isolamento e reentrega. A qualificação real do classificador passou ao CLASS-001. [Plano de execução](planejamento/plano-de-execucao.md) · [F04/F05](integracao-f04-f05.md) · [F06/F07](integracao-f06-f07.md). |
| F08, R01 e R02 | O experimento de referência teve cinco rodadas aprovadas e uma reprovada por falha de recuperação após a parada do Kafka. A R01 foi aceita com recuperação em ensaio controlado posterior. A R02 foi aceita com a correção do analisador e a conferência dos dados arquivados. A matriz de referência preserva a reprovação e segue sem nova execução após as correções. [F08](f08.md) · [R01](r01.md) · [R02](r02.md). |
| F09-A | A instalação limpa com fixture comprovou dois turnos, reentrega, três canais, duas marcas, handoff, revisão humana e persistência. O trecho com complemento real pertence à C07/F09 final. [Roteiro e evidências F09](f09.md). |
| F10 e UX02 | A publicação temporária em HTTPS usa fixture. Reinício com persistência e restauração em instalação isolada foram verificados. Na primeira URL da F10, o teste por dados móveis cobriu a abertura da página e a exibição de marcas e canais. [Resultado F10](f10-resultado.md) · [Aceite UX02](ux02.md). |

Para completar o aceite externo da F10, usar o endereço ativo por outra
rede com os perfis sintéticos de cliente e analista. Verificar atualização
do chat, resposta do atendente simulado, handoff com histórico e isolamento
por marca. A [última URL verificada](https://newbie-aqua-stem-reveal.trycloudflare.com/)
é do túnel reaberto em 25/11/2026, com verificação da saúde da API em HTTPS.
O responsável confirmou a abertura da página nesse endereço. O acesso
depende do computador e do túnel ativos e o endereço muda ao recriar o túnel.
[Resultado F10](f10-resultado.md) · [Roteiro F10](f10.md).

Repetir a matriz F08 nas mesmas condições reforçaria a evidência sob carga
após as correções. Aumento progressivo de taxa, carga de atendimento humano
e até dez mil conexões de chat são cenários exploratórios ainda sem medição.
[Método e resultados F08](f08.md).

## Classificação real

O piloto C05-SF1 de categoria foi concluído em CPU, fora da aplicação
publicada. Nos 16 casos sintéticos de desenvolvimento, acertou 15 decisões,
com 12/12 acertos nos casos classificáveis e 3/4 revisões reconhecidas. No
caso `jev-013`, o piloto previu `terminal` quando se esperava revisão. O p95
de inferência por texto foi de 21,078 ms (n=16). Prioridade, calibração e
qualificação final ficam para uma eventual retomada.
[Plano do piloto SetFit](planejamento/classificacao-comparativa/setfit-piloto.md).

A demonstração continua com fixture. A R5 é o último ensaio registrado do
protocolo de qualificação. A candidata foi descartada para adoção e a reserva
da tentativa interrompida segue pendente. [Resultado R5](c05-luna-r5-resultado.md).

A escolha e a calibração (C05), a integração (C06) e a reprodução do
complemento real em instalação limpa (C07/F09 final) ficam em espera até
retomada explícita. O fechamento completo ainda requer qualificação conforme
os critérios vigentes, adoção aprovada e o aceite do complemento real com
proveniência, revisão humana, broker e handoff. O atendente conversacional
real (E01) fica como evolução posterior e opcional.
[Plano de conclusão](planejamento/conclusao-projeto.md).
