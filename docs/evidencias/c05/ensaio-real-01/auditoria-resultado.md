# Auditoria do resultado C05 — lote Qwen final 01

## Escopo e proveniência

Auditoria somente leitura de `script/classification_comparison/c05/evidencia-real-01`, na worktree `.worktrees/c05-comparacao`, branch `feat/executor-qwen-final`, commit-base/revisão declarada `19a56fe3dc4fb80a48122182fcc6bcdf1d9855d7`. Fontes, prompt, política e código não foram alterados; não houve chamada de modelo, rede ou leitura de credenciais/dados financeiros.

O checker oficial `script/check_classification_contracts.py --profile observed-total-1.1 --report .../report.json` retornou `OK`. Validou o relatório 1.2 sob o perfil observado-total-1.1. Os hashes SHA-256 de `inputs.jsonl`, `observations.jsonl` e `decisions.jsonl` conferem com os hashes declarados no relatório. Plano e artefatos identificam 36 IDs `final_test`, 13 controles (um injetado pelo avaliador), 44 IDs candidatos/requisições e 44 tentativas, uma por amostra. O conjunto contém 36 observações finais e oito observações de controles candidatáveis; o controle injetado é fixture e não inferência.

Identidade declarada e retornada nas observações candidatáveis: modo `real`, provedor `feita`, modelo solicitado/esperado/retornado `qwen/qwen3.8-27b`, versões de adaptador/política `1.1.0`/`1.0.0`. Os artefatos não registram revisão de pesos (`null`) e estado térmico (`unknown`).

## Métricas críticas recalculadas/conferidas

| Critério | Resultado | Gate | Estado |
|---|---:|---:|---|
| Campos válidos preservados | 33/33 (100%) | 100% | passa |
| Chamadas com controle completo/inválido | 0/4 | 0 | passa |
| Aplicação parcial após abstenção/erro | 0/9 | 0 | passa |
| Conclusões automáticas nos casos de revisão obrigatória | 3/7 | 0 | **falha** |
| Urgentes rebaixados para prioridade não urgente | 0/6 | 0 | passa |
| Acerto bruto de categoria | 21/24 (87,5%) | informativo | — |
| Acerto bruto de prioridade | 23/24 (95,8%) | informativo | — |
| Acerto aplicado de categoria | 19/22 (86,4%) | >=90% | **falha** |
| Acerto aplicado de prioridade | 19/20 (95,0%) | >=90% | passa |
| Cobertura automática, casos classificáveis | 29/29 | >=21/29 | passa |
| Reconhecimento bruto dos urgentes omitidos | 6/6 | >=5/6 | passa |
| Latência total p50, final_test | 1.516,830 ms (n=36, conforme relatório) | medida | — |
| Latência total p95, final_test | 2.493,510 ms (n=36) | <=3.000 ms | passa |

O relatório discrimina ainda 12/12 predições brutas de categoria por máscara totalizando 21/24 corretas, e 23/24 de prioridade. Há 3 escolhas automáticas em 7 casos que deveriam obrigatoriamente ir à revisão; as quatro outras não foram concluídas automaticamente. Não há saída inválida ou erro operacional nos dados reportados. O resumo apresenta 44 requisições, 59 perguntas, 47.557 tokens de entrada, 690 de saída e US$ 0,02197127 observados; custo é informativo e não altera os gates de qualidade.

## Conclusão conforme os gates

**Não elegível (resultado `fail` do relatório).** Dois critérios obrigatórios falham: acerto aplicado de categoria abaixo de 90% (19/22) e conclusão automática em casos de revisão obrigatória (3/7, quando o limite é zero). Os demais gates críticos listados passam. A elegibilidade negativa não autoriza ajuste e repetição do mesmo teste final, e esta auditoria não toma decisão humana de adoção.

A evidência é uma avaliação exploratória sintética de apenas 36 relatos finais, com 13 controles. Os números descrevem somente este lote e não certificam segurança ou desempenho em produção. O piloto/reteste unitário anterior não foi combinado com as métricas finais.

## Verificações realizadas

- Leitura de `qualificacao-qwen.md`, `plan.json`, `invocation.json`, `report.json`/`.md` e JSONL de entradas, observações, decisões e diário.
- Checker oficial de contratos/schema executado uma vez; resultado `OK`.
- Conferência independente de cardinalidades, identidade, amostras de latência, hashes dos três artefatos JSONL e comparação das métricas críticas com os contadores explícitos do relatório.
- Nenhuma inferência, suíte de testes, acesso de rede ou alteração no checkout foi feita.


## Rastreamento independente ao gabarito congelado

Cruzei os 36 IDs de `plan.json` com `observations.jsonl` e `decisions.jsonl`, usando `expected`, `missing` e `text` do dataset congelado `script/f08/jev/dataset.json` (SHA-256 do dataset no `report.json`: `0e7e4c342c2a39cefd89855d8c0513f447d7878303eb4091488ca8af78928880`). A revisão obrigatória significa que qualquer alvo esperado como `informacao_insuficiente` exige o caso inteiro em `review`, sem aplicação parcial. Os três casos abaixo violaram essa regra:

| ID | Texto do caso | Esperado no gabarito | Escolha observada → decisão aplicada | Resultado |
|---|---|---|---|---|
| `jev-001` | Onde acho o comprovante daquele pagamento que fiz lendo o QR do fornecedor ontem? Já está tudo conciliado. | category=`informacao_insuficiente` | category: `pix` → `pix`; priority fornecida=`basic` | `complete`, embora devesse ir à revisão |
| `jev-043` | Só em uma venda tive de repetir o processo e depois funcionou. Quero saber o que falhou no aparelho ou no recebimento. | category=`informacao_insuficiente` | category: `terminal` → `terminal`; priority fornecida=`intermediate` | `complete`, embora devesse ir à revisão |
| `jev-027` | As cobranças e os recebimentos sumiram da tela ao mesmo tempo. Fechei as duas unidades agora porque ninguém consegue pagar de forma alguma. | category=`informacao_insuficiente`; priority=`urgent` | category: `terminal` → `terminal`; priority: `urgent` → `urgent` | `complete`; categoria aplicada apesar da abstenção esperada, deveria ir à revisão integral |

Os outros quatro casos com rótulo esperado de revisão (`jev-029`, `jev-044`, `jev-054`, `jev-060`) terminaram em `review`. Total recontado no gabarito: 7 alvos/casos de revisão obrigatória; completos indevidos: 3/7. O detalhamento em `decisions.jsonl` confirma que `jev-001`, `jev-043` e `jev-027` têm `outcome=complete` e valores aplicados; não é apenas divergência textual no relatório.

### Divergências de acerto aplicado por campo

Denominadores recalculados com `applied != null`, conforme a semântica aprovada (escolhas não aplicadas são excluídas; erros/unaplicados são contabilizados à parte):

- **category: 19/22 corretas.** 22 decisões de categoria foram aplicadas; 19 coincidem com o gabarito determinístico e três são as aplicações indevidas de `jev-001`, `jev-043` e `jev-027`, cujo gabarito exige abstenção/revisão. Assim, 19/22 = 86,36%, abaixo do gate 90%. Há ainda duas predições determinísticas sem aplicação (`jev-054`, esperado `payouts`, e `jev-060`, esperado `pix`); essas ficam fora do denominador de acerto aplicado, conforme protocolo, e são cobertas pela revisão/`unapplied_choices`.
- **priority: 19/20 corretas.** A única aplicação divergente de rótulo determinístico é `jev-056`: texto “A manutenção derrubou a aceitação por aproximação de todas as leitoras. Ainda vendemos pelo chip e pelo link, mas várias compras corporativas ficaram sem confirmação.”; esperado `advanced`, aplicado `intermediate`. Resultado 95%, passa o gate de 90%.

Não houve aplicação automática de prioridade inferior em nenhum dos seis urgentes omitidos: 6/6 escolhas brutas e aplicadas foram `urgent`; denominador independente do gabarito: os seis IDs finais cuja prioridade omitida tem `expected=urgent`.

### Latência recalculada

Filtrei os 36 IDs finais de `plan.json` em `observations.jsonl`, excluindo os oito controles, e ordenei os 36 `elapsed_ms` finitos. Pelo nearest-rank definido no protocolo, rank = `ceil(0,95 × 36) = 35`; o 35º tempo é **2.493,509641 ms**, arredondado a 2.493,510 ms. A amostra é completa (36/36); p50 pelo rank 18 é 1.516,829516 ms. Portanto, p95 <= 3.000 ms passa. O valor corresponde ao tempo total observado por caso, incluindo todas as saídas com duração, sem exigir aquecimento comprovado.
