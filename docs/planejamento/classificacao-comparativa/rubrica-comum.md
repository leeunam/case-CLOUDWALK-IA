# Rubrica comum de classificação — versão 1.0.0

Esta é a informação semântica comum para Qwen e GLiClass no experimento.
Usar o mesmo texto e o catálogo fixado em ambos, adaptando somente o formato
necessário à interface. Registrar versão/hash das instruções e qualquer
limitação do candidato antes do teste final. Esta rubrica explicita a régua
discutida no chat; não altera os rótulos já revisados.

## Categoria

- `pix`: transferência ou pagamento por Pix, incluindo prazo, estorno ou falha.
- `payouts`: repasse, recebimento ou liquidação de valores de vendas.
- `terminal`: instalação, uso, configuração ou defeito da maquininha de cartão.
- `informacao_insuficiente`: o relato não permite distinguir o assunto. QR,
  aparelho ou uma operação mencionados isoladamente não provam uma categoria.

## Prioridade

- `basic`: orientação de rotina, preparação, treinamento ou manutenção sem
  operação prejudicada. Uso futuro ou funcionamento preservado podem sustentar
  esse nível; mera ausência de detalhes não basta.
- `intermediate`: impacto localizado/moderado, com a operação ainda disponível.
- `advanced`: impacto relevante, abrangente ou retrabalho significativo, sem
  evidência de necessidade imediata de intervenção.
- `urgent`: necessidade de agir imediatamente, como perda em andamento,
  interrupção total sem alternativa ou consequência relevante com prazo imediato.
- `informacao_insuficiente`: faltam fatos sobre impacto/prazo/funcionamento
  suficientes para escolher uma prioridade. Não completar informações ausentes
  por suposição. Reconhecer a falta de informação não cria uma quinta prioridade.

Prioridade mede urgência/impacto para o cliente, não esforço do atendente,
complexidade técnica ou familiaridade do cliente com uma função. Interpretar
o conjunto do relato, inclusive alternativas e prejuízo atual, sem depender de
uma palavra-chave isolada ou inventar valores, prazos e condições.

## Preservação e aplicação

Responder apenas pelos campos ausentes, com códigos do catálogo ou abstenção.
Campos válidos recebidos do canal permanecem idênticos. Entrada completa ou
inválida não chama o classificador. Ausente inclui campo omitido, nulo ou texto
vazio após remover espaços. Um valor presente fora do catálogo é inválido.

Se qualquer campo solicitado se abstiver, falhar ou vier inválido, o caso vai
para revisão; nenhum dos valores preditos é aplicado parcialmente. Valores
válidos que vieram do canal permanecem preservados durante a revisão.

## Informação do experimento

O caso enviado ao modelo contém texto, campos válidos recebidos, campos
ausentes e catálogo/definições. Gabarito, justificativas, estrato, autoria da
revisão e resultados anteriores ficam fora do contexto enviado.

A linha de base usa zero exemplos no prompt em ambos os candidatos. Ajustes
de instruções e de política de abstenção usam somente os 24 casos de
desenvolvimento e conservam a informação comum entre candidatos. Qualquer
mudança dessa linha de base é registrada antes do teste final; os 36 casos
reservados não servem para ajustar instruções, limiares ou rótulos.
