# C05-R3 · Proposta de outra estratégia real

Estado: opção D — GPT-5.6 Luna, uma chamada — aprovada pelo responsável em
24/11/2026 para preparação offline. Implementação e revisão ainda pendentes,
sem novas chamadas pagas autorizadas. B/C permanecem como alternativas históricas.
Em 24/11/2026 o responsável escolheu preparar outra estratégia real antes de
considerar o projeto concluído. Isso mantém C06/C07 como dependências da
entrega. O [resultado R2](../../c05-r2-resultado.md) permanece negativo no
desenvolvimento, sem execução dos 36 novos finais.

## Opções e recomendação

| Abordagem | Ganho possível | Custo e limite |
| --- | --- | --- |
| **D · Outro modelo rápido, uma chamada** | Mudar a capacidade de interpretar insuficiência e reduzir tempo, mantendo a plataforma e o contrato de decisão integral. | Exige novo adaptador/candidata congelada e avaliação real; o nome ou a velocidade anunciada não garantem acerto ou p95. |
| B · Qwen com regras adicionais de veto | Barrar categorias sem suporte nos padrões definidos pela operação. | Exige manter regras e negações; pode recusar casos claros ou deixar padrões desconhecidos passar. Sozinha não resolve o tempo observado do Qwen. |
| C · Segunda chamada verificadora | Outra avaliação pode vetar uma proposta indevida. | Acrescenta latência e custo; os dois modelos podem concordar no erro. Piora o risco de exceder três segundos se as chamadas forem seriais. |

Recomendo D: avaliar **`openai/gpt-5.6-luna` pela Feita**, uma chamada por caso,
sem raciocínio estendido, saída JSON estruturada e as mesmas regras semânticas.
Não prometer aprovação. Não mudar modelo e gabarito para fazer o resultado
parecer melhor. Não retornar ao GLiClass automaticamente, cujo ajuste nesta
entrega foi encerrado pelo responsável.

## Fontes consultadas, sem inferência

O catálogo público da Feita foi consultado em 24/11/2026:

| Candidata | Entrada/saída por milhão, na Feita | Estado e tempo publicados na consulta |
| --- | --- | --- |
| [GPT-5.6 Luna](https://feita.ai/models/openai/gpt-5.6-luna) | US$ 0,20 / US$ 1,20 | Operational, 1,2 s na janela de 24 h |
| [Claude Haiku 5.5](https://feita.ai/models/anthropic/claude-haiku-5.5) | US$ 0,10 / US$ 0,50 | Operational, 2,3 s na janela de 24 h |

Esses tempos do gateway não são o p95 do nosso experimento nem o tempo total
de espera do usuário. O Qwen já demonstrou essa diferença. A menor tarifa do
Haiku não basta para recomendá-lo diante da meta total de três segundos.
Os dois têm saída estruturada anunciada; disponibilidade precisa ser conferida
no pré-voo e a identidade efetiva na resposta real.

A [documentação oficial OpenAI](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
descreve Luna para alto volume/custo, com saída estruturada, Chat Completions e
esforço `none`. Não usar a configuração média de raciocínio por padrão para
esta tarefa. A página oficial informa máximo de saída 128.000, enquanto a
rota Feita mostra 32K. Para reserva usar o limite conservador superior; conferir
também preços de contexto longo e cache, sem transformar preço ausente em zero.
As tarifas da Feita não são presumidas iguais às da conta direta OpenAI.

## Desenho de D para aprovação

1. Preservar os textos de instrução/política R2 e a rubrica. Mudar a identidade
   da candidata e os parâmetros necessários ao novo modelo, com campos
   solicitados restritos ao JSON Schema e à opção de informação insuficiente.
   O código preserva os válidos e mantém revisão integral se qualquer campo
   não puder ser aplicado. Uma chamada mesmo com dois campos ausentes.
2. Reusar a execução, a contabilidade e os verificadores existentes. Acrescentar
   fonte/perfil próprios que não reinterpretem os relatórios Qwen. Separar o
   transporte compatível Feita da identidade fixa Qwen, preservando o caminho
   histórico. Não criar uma plataforma de escolha de modelos ou fallback.
3. Preparar reuso seguro de conexão HTTPS entre casos, sem retentativa
   automática. A primeira conexão/TLS continua dentro do relógio da primeira
   chamada; não deslocar trabalho para fora da medição para passar a meta.
   Falha encerra o lote e conserva a reserva como nas rodadas anteriores.
4. Congelar a candidata antes de inferência. A frente de instruções/adaptador
   não lê os textos/gabaritos dos 36 finais inéditos. Esses finais continuam
   não consumidos e podem ser usados prospectivamente, mantendo seus bytes e
   revisões. Somente os 24 development antigos podem orientar escolhas.
5. Propor seis development uma vez e, somente se todo o gate passar, até
   44 chamadas finais/controles. Mesmos seis IDs, oito alvos, três completos,
   três revisões, quatro fornecidos, um urgente, zero erro e p95 até3s.
   No final: ≥90% por campo aplicado, cobertura≥21/29, revisão indevida0/7,
   rebaixamento urgente0/6, reconhecimento≥5/6, preservação100%, aplicação
   parcialzero e p95total≤3s(n36). Controles/startup separados.
6. Mesmo teto cumulativo US$10 e mesma conta v4. Acumulado conservador atual
   US$0,02687405, sem reserva pendente; não é saldo do fornecedor. Plano de
   consumo e fonte de tarifas/limites passam por pré-voo/revisão antes de nova
   autorização específica. Nenhuma chamada paga é liberada por esta proposta.

Preparação offline inclui testes de formato, bypass, abstenção integral,
transporte sem retry, conexão reaproveitada sem ocultar latência, custos e
preservação dos relatórios antigos. Depois do aceite e da decisão sobre o
consumo, medir o comportamento real. Somente candidato elegível e decisão de
adoção liberam a integração. A publicação com fixture não encerra essa frente.

**Exercício.** Explique por que um modelo anunciado como rápido ainda pode
ultrapassar três segundos entre nossa solicitação e a decisão disponível.
