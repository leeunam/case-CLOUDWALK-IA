# Classificação recebida e contingência para campos ausentes

## Estado

O responsável escolheu receber prioridade e categoria dos canais simulados e
validá-las na plataforma (D015). Na primeira entrega, o Jev completa apenas
campos ausentes. Com ambos os campos válidos, a plataforma encaminha o ticket
ao agente de atendimento pelo broker.
O tratamento proposto de falhas e os prazos estão na
[especificação do MVP](especificacao-mvp.md#entrada-classificação-e-fila).

## Caminho principal confirmado

1. Canal simulado envia solicitação vinculada à marca, com categoria e prioridade.
2. Plataforma valida os valores no catálogo permitido para essa marca e os registra.
3. Regras de filas e de distribuição usam esses campos, respeitando permissões,
   perfis de capacidade e carteira. Campos válidos não exigem inferência.

Isso é uma escolha de simulação do MVP. Não é uma afirmação de que integrações
reais de WhatsApp ou e-mail sempre enviam esses metadados.

## Complemento de campos ausentes

| Entrada | Tratamento |
| --- | --- |
| Ambos os campos válidos | Usar os valores e enviar pelo broker ao agente de atendimento. |
| Apenas um campo ausente | Preservar o válido e solicitar ao Jev somente o campo ausente. |
| Ambos ausentes | Solicitar ao Jev os dois campos entre opções permitidas para a marca. |
| Campo recebido fora do catálogo | Proposta de revisão humana da classificação. |
| Jev falha, demora ou retorna decisão incerta | Proposta de revisão humana após as tentativas previstas. |

A plataforma valida os valores completados antes de enviar o atendimento pelo
broker. O agente de atendimento recebe a solicitação depois dessa validação.

Persistir primeiro e executar o complemento em segundo plano preserva a entrada
durante indisponibilidade do serviço externo. A especificação propõe a fila
padrão da marca durante classificação e uma ação de correção pelo supervisor.

O modelo recebe o relato, o contexto necessário e as categorias/prioridades
permitidas com descrições claras. Ele complementa campos, não decide permissões,
marca, capacidade ou atribuição de responsável.

## Modelo escolhido

Jev, da TypeSafe AI, recebe perguntas tipadas e devolve decisões estruturadas.
A primitiva Choice seleciona uma opção de um catálogo e fornece probabilidades;
o quickstart oficial usa um atendimento de suporte como exemplo.
[Choice](https://docs.typesafe.ai/primitives/choice),
[Quickstart](https://docs.typesafe.ai/introduction/quickstart).

O Jev completa a classificação e o agente simulado atende o cliente e pode
encaminhar o caso a um analista humano. A versão do Jev será fixada ao verificar
a integração real. As condições iniciais de aceitação estão na especificação.

## Probabilidade, confiança e avaliação

Opção válida não significa opção correta. A documentação do Jev distingue a
probabilidade da opção e o campo confidence, calculado da distribuição: não são
duas evidências independentes de acerto. Limiar de aplicação automática precisa
ser avaliado com exemplos do domínio, sem assumir que confiança alta elimina
erros. [Documentação de confiança](https://docs.typesafe.ai/confidence).

Avaliação candidata com relatos sintéticos em português, rótulos
esperados e catálogo:

- Acerto de categoria e prioridade separadamente e do par completo.
- Erros de prioridade, especialmente urgentes classificados como não urgentes.
- Cobertura automática e casos encaminhados para revisão, evitando aumentar
  aparente acurácia apenas recusando quase tudo.
- Latência p50/p95 incluindo rede e falhas, número de chamadas e custo.
- Exemplos ambíguos ou fora das categorias, textos curtos e campos parcialmente ausentes.

Esses testes não foram executados. Velocidade de uma demonstração do fornecedor
não substitui uma medida a partir do ambiente do projeto.

## Consistência proposta

- Guardar origem do campo: canal, complemento de modelo ou correção humana.
- Validar novamente a classificação antes de aplicá-la e verificar compatibilidade
  com os campos já válidos; saída tipada não garante coerência do par categoria/prioridade.
- Não sobrescrever campo válido nem correção humana com uma resposta antiga.
- Reconhecer reentrega para não duplicar atualização, atendimento ou evento.
- Usar tentativas limitadas e falhas visíveis. Não bloquear indefinidamente a
  chegada de solicitações por falha do classificador.
- Se prioridade depender de uma categoria recém-inferida, respeitar essa dependência
  no desenho das perguntas ou validar a combinação; perguntas paralelas são independentes.

## Verificações da implementação

- Confirmar a versão disponível e o orçamento do ensaio com API externa.
- Verificar o comportamento de classificação, tentativas e revisão com fixtures.
- Rodar o complemento real em dados sintéticos e registrar o resultado.
