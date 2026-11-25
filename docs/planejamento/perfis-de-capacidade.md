# Perfis de capacidade da V2 ajustada

## Estado

O responsável escolheu V2 com combinações configuráveis e limite de carteira
(D011). Abaixo está a interpretação proposta para tornar seus exemplos
verificáveis. A [especificação do MVP](especificacao-mvp.md#capacidade-e-distribuição-humana)
propõe os valores do seed e as políticas de espera, retomada e distribuição.

## Duas verificações independentes

1. O trabalho ativo precisa caber em uma combinação permitida pelo perfil.
2. A carteira total precisa respeitar seu teto, contando casos atribuídos uma
   vez em todas as marcas: ativos, aguardando cliente e aguardando retomada.

Liberar espaço de trabalho ativo não cria uma vaga extra na carteira total.
Um retorno do cliente não cria outro atendimento nem outra vaga na carteira.
O teto limita a quantidade potencial de retornos, mas não garante tempo de
resposta se vários ocorrerem juntos. Não foi aprovado um teto de vinte casos.

## Combinações alternativas propostas

O responsável esclareceu em D012 que básico/intermediário/avançado eram níveis
de prioridade. Os nomes abaixo continuam ilustrativos. Urgente exclusivo e
urgente compatível representam dois regimes para casos urgentes; a condição
concreta que os distingue ainda não foi definida. D013 confirma o uso conjunto
de prioridade e categoria, sem acrescentar uma escala de complexidade.

| Alternativa | Urgente exclusivo | Urgente compatível | Básico | Intermediário | Avançado |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 1 | 0 | 0 | 0 | 0 |
| B | 0 | 1 | 1 | 0 | 0 |
| C | 0 | 0 | 3 | 1 | 0 |
| D | 0 | 0 | 0 | 1 | 1 |

Interpretação recomendada: são tetos alternativos. Uma combinação menor também
cabe. Para receber um caso, o conjunto ativo após a entrada precisa caber por
inteiro em pelo menos uma alternativa. As alternativas não são somadas.

Exemplo: somente um intermediário cabe em C e D. É possível adicionar básicos
seguindo C ou um avançado seguindo D. Adicionar um básico e depois um avançado
produziria um conjunto que não cabe em nenhuma delas.

## Exemplos de verificação dessa interpretação

| Trabalho ativo depois da entrada | Resultado esperado |
| --- | --- |
| Um básico | Cabe como parte de B ou C. |
| Dois básicos e um intermediário | Cabe em C, com espaço para mais um básico. |
| Três básicos e um intermediário | Cabe em C. |
| Um avançado e um intermediário | Cabe em D. |
| Um básico, um intermediário e um avançado | Não cabe em nenhuma alternativa. |
| Um urgente exclusivo e um básico | Não cabe. |
| Um urgente compatível e um básico | Cabe em B. |
| Um urgente compatível e dois básicos | Não cabe. |

As regras dizem se um caso cabe. Não determinam, sozinhas, qual pessoa deve
recebê-lo nem a ordem em que casos aguardando serão examinados.

## Prioridade e aderência ao TAPI

O TAPI pede filas configuráveis por marca, equipe, categoria ou prioridade e
triagem/priorização/distribuição. Não exige pesos, medição de esforço ou escala
de complexidade. Os perfis de combinações são uma escolha do nosso projeto.

O recorte atual usa prioridade e categoria como critérios das combinações; não incorpora
um campo obrigatório de complexidade. Prioridade expressa urgência, e usá-la
para restringir simultaneidade é uma política operacional, não uma comprovação
de que todo caso urgente consome mais esforço.

Se dois casos urgentes permitem combinações diferentes, a configuração precisa
explicar a diferença por categoria e condições explícitas. A escolha dos critérios
está confirmada; nomes dos níveis, categorias, condições e regras concretas ainda
precisam de definição.

[Referência: prioridade como urgência no Zendesk](https://support.zendesk.com/hc/en-us/articles/4408882997530-Lesson-3-Solving-tickets).

## Espera, retomada e exclusividade

Na direção da V2, aguardar o cliente mantém o responsável e a vaga na carteira.
O retorno precisa validar novamente o perfil e a marca em operação antes de
voltar ao trabalho ativo. Se não couber, permanece aguardando retomada.

Há uma decisão específica em aberto: um urgente exclusivo pode liberar sua
exclusividade enquanto aguarda o cliente, ou essa exclusividade permanece até
concluir/transferir? O segundo caminho reserva disponibilidade, reduzindo a
flexibilidade obtida com V2 para esse tipo de caso.

Propostas a avaliar: interromper novas atribuições quando houver retomadas
pendentes, ordenar retomadas por prioridade e espera e permitir intervenção
supervisionada. Nada disso garante retomada imediata; a política precisa ser
medida e não pode abandonar casos ou interromper outro atendimento silenciosamente.

## Escolha entre candidatos

O critério antigo de menor soma de pesos deixa de existir. Uma opção para
discussão é usar menor quantidade de casos ativos entre os candidatos cujo
perfil aceita o caso, mantendo o desempate por maior tempo sem atribuição.
Essa contagem não é uma decisão confirmada e não representa esforço equivalente
entre casos de prioridades diferentes.

## Limites da abordagem e recorte sugerido

- Perfis são mais expressivos para exclusividade e misturas, mas a quantidade
  de alternativas cresce conforme prioridades, categorias e exceções aumentam.
- A interface deve prever configurações contraditórias, mostrar exemplos do que
  cabe e informar por que um caso foi recusado.
- A capacidade é por pessoa, não multiplicada por equipes/filas. Candidatos
  repetidos por participação em várias equipes devem ser unificados.
- Verificação de combinação, reserva e atribuição precisam permanecer coerentes
  sob concorrência; dois casos não podem ocupar a mesma combinação livre.
- Alterar prioridade, categoria ou perfil durante um atendimento pode invalidar a
  combinação atual. A política de edição deve ser explícita e não pode remover
  ou reclassificar casos silenciosamente.
- Para o MVP, recomenda-se um editor de alternativas com contagens e campos
  definidos, em vez de scripts arbitrários. O catálogo inicial continua a definir.

## Casos adversariais para verificar

- Dois casos concorrentes caberiam individualmente, mas juntos violam o perfil.
- A carteira chega ao teto com vários casos aguardando cliente.
- Todos os clientes pendentes respondem ao mesmo tempo.
- Um retorno é reentregue e não duplica vagas nem mensagens.
- Um urgente exclusivo chega quando já existe trabalho ativo incompatível.
- O analista está em outra marca quando um caso sob sua responsabilidade retorna.
- Uma mudança de perfil torna a combinação atual inválida.
- Casos de uma classe ficam repetidamente sem combinação disponível.

São critérios candidatos para a implementação futura, sem resultados de teste
ou capacidade de produção medidos nesta etapa.
