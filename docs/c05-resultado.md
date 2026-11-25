# C05 · Primeiro resultado final do Qwen

**Conclusão técnica: não elegível nesta configuração.** O Qwen cumpriu a meta
de latência e reconheceu os seis urgentes com prioridade omitida, mas concluiu
automaticamente três casos que exigiam revisão e ficou abaixo de 90% no acerto
de categoria aplicada. A C05 aguarda a deliberação do responsável; C06 continua
bloqueada. Não houve adoção operacional, alteração do candidato ou repetição.

## Execução e evidências

O responsável autorizou um lote em 24/11/2026. Fonte
`19a56fe3dc4fb80a48122182fcc6bcdf1d9855d7`, branch
`feat/executor-qwen-final`, worktree `.worktrees/c05-comparacao`.
Run `c05-58e8f0b5c64547b98d6f5ca738bf2c6e`, modelo solicitado e retornado
`qwen/qwen3.8-27b`, adaptador 1.1.0 e política 1.0.0.

Foram concluídos os 36 relatos reservados e os 13 controles: 44 chamadas
reais, 59 perguntas e uma tentativa sequencial por caso. Oito controles
chamaram o modelo, quatro entradas completas ou inválidas não o chamaram e
um controle foi injetado pelo avaliador. Este controle é sintético e não
participa da qualidade ou latência do candidato. Não houve retentativas,
falhas operacionais ou saída inválida no lote real.

- [Autorização](evidencias/c05/ensaio-real-01/autorizacao.md),
  [pré-voo](evidencias/c05/ensaio-real-01/preflight.json) e
  [configuração específica](evidencias/c05/ensaio-real-01/config.json).
- [Relatório canônico](../script/classification_comparison/c05/evidencia-real-01/report.json)
  e [versão legível](../script/classification_comparison/c05/evidencia-real-01/report.md).
- [Entradas](../script/classification_comparison/c05/evidencia-real-01/inputs.jsonl),
  [observações](../script/classification_comparison/c05/evidencia-real-01/observations.jsonl),
  [decisões](../script/classification_comparison/c05/evidencia-real-01/decisions.jsonl)
  e [diário](../script/classification_comparison/c05/evidencia-real-01/journal.jsonl).
- [Auditoria independente do resultado](evidencias/c05/ensaio-real-01/auditoria-resultado.md),
  [auditoria financeira](evidencias/c05/ensaio-real-01/auditoria-financeira.json) e
  [revisão anterior ao despacho](evidencias/c05/ensaio-real-01/revisao-liberacao.md).

## Critérios congelados e resultado

Perfil `observed-total-1.1`, protocolo de qualidade 1.1, relatório 1.2 e IPC 1.1.

| Critério | Resultado | Limite | Situação |
| --- | ---: | ---: | --- |
| Campos válidos do canal preservados | 33/33 | 100% | Passou |
| Controles completos/inválidos chamando modelo | 0/4 | 0 | Passou |
| Aplicação parcial após abstenção/erro | 0/9 | 0 | Passou |
| Conclusão automática onde a revisão era obrigatória | 3/7 | 0 | **Falhou** |
| Urgentes automaticamente rebaixados | 0/6 | 0 | Passou |
| Acerto da categoria aplicada | 19/22 = 86,36% | ≥90% | **Falhou** |
| Acerto da prioridade aplicada | 19/20 = 95% | ≥90% | Passou |
| Cobertura automática dos classificáveis | 29/29 | ≥21/29 | Passou |
| Reconhecimento bruto dos urgentes omitidos | 6/6 | ≥5/6 | Passou |
| p95 do tempo total | 2.493,510 ms, n=36 | ≤3.000 ms | Passou |

O acerto bruto foi 21/24 para categoria e 23/24 para prioridade. O p50 total
foi 1.516,830 ms. Campos recebidos válidos não contam como acerto do modelo.
Os denominadores aplicados são menores porque abstenções não produzem campo
aplicado. Cobertura alta, isoladamente, não basta: também é necessário recusar
classificações quando faltam informações. Os critérios exigem aprovação de
todos os gates; os dois resultados negativos determinam `eligibility=fail`.

As três conclusões indevidas foram `jev-001` (pagamento por QR sem evidência
suficiente para afirmar Pix), `jev-043` (falha sem distinguir aparelho de
recebimento) e `jev-027` (impacto urgente, mas origem ambígua). O modelo escolheu
respectivamente `pix`, `terminal` e `terminal`. No último caso, reconhecer a
urgência não tornou a categoria conhecida. O gabarito exigia revisão integral.
A auditoria lista textos, escolhas, campos aplicados e os quatro outros casos
de revisão corretamente recusados. Houve também `jev-056` com prioridade
`intermediate` em lugar de `advanced`; esse erro não é rebaixamento de urgente.

## Custo e ambiente

As 44 respostas informaram 2,197127 créditos; a conversão documentada de
US$ 0,01 por crédito conciliou **US$ 0,02197127**. A estimativa por tokens,
separada, foi US$ 0,021971225. Foram 47.557 tokens de entrada e 690 de saída.
Com os dois pilotos anteriores contabilizados conservadoramente em
US$ 0,001038, a conta global ficou em **US$ 0,02300927 de US$ 10**.

A auditoria cruzou uma execução, 44 despachos e recibos únicos, 44 reservas
liquidadas e zero pendências/correções. A reserva por chamada foi US$ 1,5032;
não foi cobrada como custo real. O maior comprometimento reconstruído, com
uma reserva ativa, foi US$ 1,52572095. A conta SQLite v4 e o manifesto
permanecem na área privada ignorada; não reinicializá-los. Os números são dos
retornos da API e da conta local, sem consulta a uma fatura posterior.

A execução ocorreu no desktop local com Python 3.11.13/x86_64, concorrência 1,
prazo de 5 s e duração global de aproximadamente 71,544 s. A inicialização
do adaptador foi 304,997 ms, registrada separadamente. O estado térmico do
fornecedor ficou desconhecido e nenhuma amostra foi excluída por esse motivo.
Não foram iniciados outros benchmarks de candidatos em paralelo. Banda, RTT,
contenção do host e infraestrutura monetária não foram medidos separadamente.
[Inventário e limitações do ambiente](evidencias/c05/ensaio-real-01/ambiente.json).

## Verificar sem gastar

Na raiz do checkout integrado, o comando abaixo confere schemas, fontes,
hashes, decisões e métricas dos artefatos existentes. Ele não chama o modelo.

```sh
rtk proxy python3 -B script/check_classification_contracts.py \
  --profile observed-total-1.1 \
  --report script/classification_comparison/c05/evidencia-real-01/report.json
```

O checker passou e as auditorias independentes conferiram contagens e custos.
Os 17 históricos mantiveram seus hashes; prompt, política, rubrica, divisão,
catálogo, dataset e código do executor permaneceram inalterados. Não foi
necessário repetir as suítes já aceitas, pois não houve mudança de código.
O lançador verificou que o valor literal da credencial não estava nos artefatos
ou no log; essa varredura não é uma garantia sobre toda representação possível.

## Limites e próxima decisão

Os relatos são sintéticos e exploratórios. O gabarito dos 60 relatos teve oito
aprovações diretas do responsável e 52 revisões por IA delegada. Os resultados
se referem somente aos 36 relatos finais; seis urgentes não certificam segurança
em produção. Pilotos anteriores, controles e resultados GLiClass não foram
incorporados às taxas ou ao p95 final. Não houve comparação pareada final.
Revisão de pesos, raciocínio efetivo e calibração de confiança são desconhecidos
ou não avaliados.

A recomendação técnica é manter o bloqueio da integração. Uma nova estratégia
de abstenção pode ser planejada com dados de desenvolvimento e critérios
explícitos, seguida por um novo conjunto de avaliação independente. Isso exige
uma decisão de escopo; não ajustar o candidato aos três casos finais e repetir
o mesmo conjunto como teste inédito. Não foram autorizadas ou realizadas
chamadas adicionais depois deste lote.

**Exercício.** Compare 29/29 de cobertura com 3/7 de conclusões indevidas.
Explique por que atender todos os casos claros não compensa inventar uma
classificação quando o relato deveria ir à revisão.
