# C05 · Qualificar o Qwen contra os critérios aprovados

Decisão do responsável em 23/11/2026: «Focar na avaliação do Qwen» e encerrar
novos ajustes GLiClass nesta entrega. Essa decisão substitui a exigência de
dois candidatos na execução final. Não seleciona automaticamente o Qwen.
Base de preparação: `e06143dfc49505894e707f446fa97a93fc58ba24`.

O plano estático foi gerado e conferido na branch
`docs/resultado-classificacao`, worktree `.worktrees/c05-comparacao`, após a
emenda integrada `99b6230`. Foram confirmados 36 relatos, 13 controles e 44
possíveis chamadas do candidato, sem iniciar o adaptador nem acessar a chave.
[Conferência e reprodução](../../c05.md). A adaptação C05-E foi implementada
offline e aceito em `e4ce14c`, com 37 testes C05 e regressões C02/Qwen.
Usa conta SQLite persistente, reserva por despacho e conciliação verificada.
A versão 4 é a primeira conta suportada; protótipos são recusados sem alteração.
[Aceite e revisão independente](../../evidencias/c05/executor-aceite.json).
O lote final pago ainda exige autorização própria, consolidação dos gastos
anteriores e confirmação das fontes financeiras. Não há resultado C05.

## Escopo e evidências

- Avaliar somente `qwen/qwen3.8-27b`, com os 36 IDs de `final_test` da divisão
  congelada, 13 controles e uma tentativa sequencial por caso. O plano estático
  deve confirmar 44 possíveis chamadas do candidato: 36 relatos e oito
  controles naturais. Quatro controles de entrada completa/inválida não
  chamam o modelo; um controle reservado é injetado pelo avaliador.
- Usar `observed-total-1.1`: protocolo de qualidade 1.1, relatório 1.2 e IPC 1.1.
  Não modificar os bytes do protocolo, dataset, divisão, rubrica, catálogo,
  prompt ou política. Não adicionar exemplos nem calibrar com o teste final.
- Preservar o piloto real de uma chamada e todos os resultados GLiClass como
  desenvolvimento. Não incorporá-los às taxas nem ao p95 da população final.
  Não produzir uma alegação de comparação pareada final.
- A conclusão pode ser elegível, não elegível ou inconclusiva. Se incompleto,
  preservar prefixo, tentativas e custos conhecidos; nunca completar ausências
  com zero, reexecutar silenciosamente ou declarar aprovação.
- C06 só começa após elegibilidade comprovada e aprovação humana da adoção.
  Uma falha não autoriza ajustar o candidato e repetir o mesmo teste como se
  fosse a primeira avaliação.

## Metas preservadas

| Critério | Limite aprovado |
| --- | --- |
| Campos válidos do canal | 100% preservados |
| Chamadas com entrada completa/inválida | Zero |
| Aplicação parcial após abstenção/erro | Zero |
| Conclusões automáticas nos sete casos de revisão obrigatória | Zero |
| Urgente automaticamente rebaixado | Zero |
| Acerto aplicado por campo | Pelo menos 90% |
| Cobertura automática nos 29 casos classificáveis | Pelo menos 21 casos |
| Reconhecimento bruto dos seis urgentes omitidos | Pelo menos cinco |
| Tempo total observado | p95 até 3.000 ms, uma amostra por relato |
| Prazo e tentativas | 5 s, tolerância de transporte do protocolo, uma tentativa |

Esses critérios têm todos os denominadores e semânticas do protocolo.
A amostra sintética é exploratória e não certifica segurança em produção.

## Pré-voo de 23/11/2026

A página pública da Feita exibiu o modelo como **`Down`**, disponibilidade
de 21,05% nas últimas 24 horas e latência pública de 4,7 s.
[Página do fornecedor](https://feita.ai/models/qwen/qwen3.8-27b).
[Registro local da consulta](../../evidencias/c05/preflight-publico-2026-11-23.json).
Esses indicadores são do fornecedor: não substituem uma medição C05 nem
demonstram o resultado que os nossos 36 casos teriam. Não foi feito POST.
Verificar novamente o estado antes de uma execução real.

O reteste posterior **C03-P2**, explicitamente autorizado para uma chamada de
desenvolvimento, respondeu `pix` e `urgent` em 1,894 s e teve US$ 0,000518
exibidos no log individual. A API respondeu apesar do indicador anterior.
Os dois registros experimentais do gateway somaram aproximadamente
US$ 0,00104 no resumo. Esse reteste do mesmo caso não entra no teste final
nem comprova disponibilidade estável ou p95. [Recibo](../../evidencias/c03/reteste-unitario-real-02.json).

O executor C02 suporta plano estático `final_test` sem iniciar adaptadores.
Na preparação estática original, o adaptador pago aceitava apenas
desenvolvimento/controles e o protocolo antigo. C05-E adiciona o executor final
com manifesto próprio, conjunto e conta vinculados, bloqueios pré-credencial
e proteção contra repetição, preservando a medição C02. O piloto antigo
permanece reproduzível. Exemplos reais continuam desabilitados; código e
simulação não autorizam o lote pago. [Executor e reprodução](../../c05.md).

## Orçamento total e limites de execução

O teto humano total permanece **US$ 10**, com mínimo de requisições. Os dois
pilotos já consumidos têm contabilização conservadora de US$ 0,001038,
separada do valor arredondado pelo painel. A abertura da conta deve consolidar
todos os gastos anteriores e eventuais reservas pendentes. Não há nova
verba de US$ 10 por lote, nem autorização para consumir todo o crédito da conta.

A reserva histórica do piloto foi US$ 1,4004736 por requisição, pelo pior
limite publicado de entrada/cache/saída. Replicá-la para 44 requisições exigiria
US$ 61,6208384, acima do teto. **Isso é uma reserva pessimista, não uma previsão
do custo real**; o painel do único piloto exibiu cerca de US$ 0,000518.

Antes de executar, resolver o limite com evidência do fornecedor sobre tokens
faturáveis ou um controle cumulativo com reconciliação comprovada. Não trocar
uma reserva garantida pela extrapolação de um caso, presumir que raciocínio
foi desativado, devolver reserva de timeout sem recibo ou aumentar o teto.
A autorização/configuração do piloto não será reutilizada. O manifesto da
execução final fixa IDs, hashes, modelo, limites e teto cumulativo. C05-E
concilia USD comprovado ou, quando explicitamente confirmada, a conversão
documentada de `usage.credits`, mantendo o maior custo verificado. Sem custo
conciliável, conserva a reserva e interrompe com prefixo inconclusivo, mesmo
que exista saldo para outra reserva. Não precisa reservar as 44 chamadas de
uma só vez. Recibos posteriores preservam a liquidação original; aumentos
atualizam o total do caso e congelam a conta se violarem reserva ou teto.
Sem autorização e referências verificáveis, continuar somente offline.

## Entrega de preparação

1. Registrar a emenda D017, os cards e as dependências; encerrar as melhorias
   GLiClass desta entrega sem declarar aceite do modelo.
2. Gerar plano estático do Qwen com `--dry-run`, no perfil e divisão finais,
   em branch/worktree próprias. Não chamar modelo nem carregar credencial.
3. Conferir 36 relatos, 13 controles, 44 possíveis chamadas, hashes e ausência
   de mudanças nas fontes congeladas. Publicar o pré-voo e as pendências.
4. Só então preparar e revisar o executor final e seus limites financeiros.
   Disponibilidade, pré-voo válido e manifesto próprio precedem os POSTs.

**Exercício.** Explique por que um classificador que evita erros encaminhando
tudo à revisão ainda falha no critério de cobertura. Depois diferencie o custo
observado de um caso da reserva necessária para autorizar um lote.
