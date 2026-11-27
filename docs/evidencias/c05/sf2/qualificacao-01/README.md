# SF2-05A · qualificação local

**Validação reprovada.** Os dois especialistas completaram o treino e o
reload. A coleta registrou 90 relatos e 5 controles. Nenhuma das 225
políticas passou por todos os critérios. Todas concluíram automaticamente
pelo menos 2 casos que exigiam revisão. O final continua fechado e C06
segue bloqueada.

Base `99885274faef5b5ee281ca4d87b9d840f85550ac`, branch
`feat/sf2-qualificacao`, worktree `.worktrees/sf2-qualificacao`.

## Pré-voo e treino

O ambiente reutilizado passou na verificação de 73 pins, dos imports, do
wheel CPU, do `pip check` e dos 10 arquivos do snapshot. Os 240 comprimentos
retokenizados coincidiram com o recibo público, de 14 a 78 tokens. O
congelamento vincula fontes, protocolo, dados públicos e selo. [Pré-voo](preflight.json) ·
[Congelamento](training-freeze.json).

O lançamento 01 encerrou antes de registrar ajuste de qualquer campo. O log
da execução registrou `PermissionError`, sem identificar a operação negada.
Uma sonda separada do integrador demonstrou a restrição de comunicação entre
processos no ambiente padrão. O integrador autorizou novo lançamento com
permissão para IPC local, preservando o mesmo comando e congelamento e
usando uma pasta de saída distinta. [Lançamento 01](launch-training.json) ·
[Status 01](status.json) · [Log 01](commands.log) ·
[Recibo 02](execucao-02/preflight.json).

O lançamento 02 concluiu um ajuste por campo em
**913,685 s acumulados**. A categoria usou
1500 pares, 188 passos e 23 iterações da cabeça. A prioridade usou
1500 pares, 188 passos e 21 iterações. O peso monitorado mudou nos dois
encoders. Os seis testes de reload reproduziram os scores com diferença
absoluta máxima 0. [Recibo do supervisor](execucao-02/treino/status.json) ·
[Evidência do treino](execucao-02/treino/evidence.json) ·
[Manifesto do pacote](execucao-02/pacote/manifest.json).

## Resultados da validação

A tabela usa as decisões da política de coleta fixa, com `tau=0,50` e
`delta=0,00` nos dois campos. A última coluna conta quantas combinações
do replay passaram por cada critério isoladamente. Não houve política
selecionada. [Relatório da coleta](execucao-02/avaliacao/validation/report.json) ·
[Conferência 03/04](execucao-02/avaliacao/validation-audit.json).

| Critério | Meta | Observado na coleta | Políticas que passaram |
| --- | --- | --- | --- |
| Preservação dos campos recebidos | 100% | 60/60 | 225/225 |
| Chamadas dos controles completos ou inválidos | 0 | 0 | 225/225 |
| Complementos parciais | 0 | 0 | 225/225 |
| Conclusões em revisão esperada | 0/18 | 3/18 | 0/225 |
| Urgente aplicado como não urgente | 0 | 1 | 135/225 |
| Acerto aplicado de categoria | ≥ 90% | 45/47 (95,74%) | 225/225 |
| Acerto aplicado de prioridade | ≥ 90% | 39/44 (88,64%) | 210/225 |
| Cobertura automática dos classificáveis | ≥ 51/72 | 67/72 (93,06%) | 180/225 |
| Urgentes reconhecidos na escolha bruta | ≥ 11/13 | 12/13 | 225/225 |

Urgentes aplicados corretamente em 11/13 casos, cobertura correta
de 63/72 e revisão de 20/90 casos. Os controles confirmaram zero
chamadas para canal completo ou inválido. Categoria em branco, prioridade
nula e ambos omitidos acionaram apenas os especialistas previstos.
[Controles](execucao-02/avaliacao/validation/run/controls.jsonl).

A latência externa observada foi p50 60,82 ms, p95 177,61 ms e máxima
254,01 ms. A partida até READY levou 9,198 s. A latência descreve
a política de coleta de validação. A grade reaproveitou os mesmos vetores,
e o extrator 03 produziu objetos iguais aos do 04, com 60 vetores por
campo e zero erros de score. [Journal](execucao-02/avaliacao/validation/run/timings.jsonl) ·
[Selo](execucao-02/avaliacao/validation/run/seal.json) ·
[Seleção](execucao-02/avaliacao/validation/selection.json).

## Compromissos observados na grade

- 90 políticas cumpriram todos os critérios exceto o de revisão esperada.
  As 90 concluíram 2/18 casos que exigiam revisão. A maior cobertura correta
  entre elas foi 62/72.
- A grade teve 135 políticas com 2 conclusões indevidas e 90 com 3. O corte
  máximo em ambos os campos chegou a 26/26 acertos aplicados em prioridade,
  eliminou o rebaixamento observado, mas manteve 2/18 conclusões em
  revisão esperada e reduziu a cobertura para 46/72.

| ID público | Campo | Rótulo de referência | Valor aplicado na coleta | Maior score | Margem |
| --- | --- | --- | --- | --- | --- |
| `sf2-validation-001` | Prioridade | `urgent` | `advanced` | 0,631387 | 0,290562 |
| `sf2-validation-028` | Prioridade | `informacao_insuficiente` | `basic` | 0,659234 | 0,335514 |
| `sf2-validation-030` | Categoria | `informacao_insuficiente` | `pix` | 0,902685 | 0,813941 |
| `sf2-validation-061` | Categoria | `informacao_insuficiente` | `pix` | 0,904549 | 0,817659 |

Em `sf2-validation-030` e `sf2-validation-061`, só a categoria estava
ausente. Ambos passaram até pelo maior corte de score (0,90) e margem
(0,20). Os vetores refletem scores da cabeça sem calibração de probabilidade.
[Registros de diagnóstico](execucao-02/avaliacao/tradeoffs.json).

## Como conferir

- Nesta pasta e em `execucao-02/`, execute
  `rtk proxy sha256sum -c SHA256SUMS` para conferir os arquivos.
- Para conferir o hash dos bytes originais da grade, execute
  `rtk proxy gzip -dc execucao-02/avaliacao/validation/grid.json.gz | rtk proxy sha256sum`
  e compare com `grid-original.json` e `selection.json`.
- Os originais e o pacote local estão em
  `script/classification_comparison/setfit_sf2/.cache/qualificacao-01/`
  na worktree. O pacote pesa cerca de 931 MiB. O manifesto e os índices
  versionados permitem verificar os pesos locais pelos hashes.
- Os arquivos `*-launch.json` preservam os comandos executados. Para
  reproduzir a conferência dos mesmos frames sem nova inferência, use
  `training scores` com os argumentos de `scores-launch.json` e saída nova.
  Compare o objeto extraído às chaves em `validation/scores.json`. A auditoria
  documentada em `roteiros/audit-validation.py` faz essa comparação e confere
  o selo, o journal e a contagem da grade.

O conjunto público é sintético, com quotas planejadas e anotações de IA.
As medidas se aplicam à rodada local. O bloqueio da validação impediu
congelamento, digest de liberação e métricas finais.

**Exercício.** Siga `sf2-validation-030` em `predictions.jsonl` até o vetor
do extrator e o diagnóstico. Confira o erro no denominador de categoria
aplicada e no denominador de revisão esperada.
