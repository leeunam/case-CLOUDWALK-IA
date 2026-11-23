# C05 · Qualificar o Qwen contra os critérios aprovados

Decisão do responsável em 23/11/2026: «Focar na avaliação do Qwen» e encerrar
novos ajustes GLiClass nesta entrega. Essa decisão substitui a exigência de
dois candidatos na execução final. Não seleciona automaticamente o Qwen.
Base de preparação: `e06143dfc49505894e707f446fa97a93fc58ba24`.

O plano estático foi gerado e conferido na branch
`docs/resultado-classificacao`, worktree `.worktrees/c05-comparacao`, após a
emenda integrada `99b6230`. Foram confirmados 36 relatos, 13 controles e 44
possíveis chamadas do candidato, sem iniciar o adaptador nem acessar a chave.
[Conferência e reprodução](../../c05.md). A execução real continua pendente
da disponibilidade e dos limites do executor final; não há resultado C05.

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

O executor C02 suporta plano estático `final_test` sem iniciar adaptadores.
O adaptador pago atual continua limitado a desenvolvimento/controles e ao
protocolo do piloto antigo. Um plano estático válido não torna esse adaptador
apto ao lote final. A adaptação deve fixar o conjunto final autorizado e o
protocolo novo antes da credencial, preservar a medição C02 e impedir reenvio
ou gasto fora do lote registrado.

## Orçamento total e limites de execução

O teto humano total permanece **US$ 10**, com mínimo de requisições. Já foram
contabilizados conservadoramente US$ 0,000519 pelo único piloto; o restante
conhecido é no máximo o orçamento autorizado menos esse valor. Não há nova
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
execução final precisa fixar IDs, hashes, modelo, limites e teto cumulativo.
Sem disponibilidade ou limite verificável, continuar somente offline.

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
