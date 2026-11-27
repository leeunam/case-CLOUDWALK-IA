# SF2-R1 · extensão offline da validação

**Elegível apenas na validação.** Das 45 políticas adicionais, 9 cumpriram
todos os critérios. A grade histórica segue com 0/225 elegíveis, e a união
ficou em 9/270. O desempate escolheu categoria com tau 0,95 e delta 0 e
prioridade com tau 0,70 e delta 0, no subcontrato `sf2-r1-offline/1.0`.
[Política selecionada](selected-policy.json) · [Emenda aprovada](../../../../planejamento/classificacao-comparativa/sf2/sf2-r1-protocolo.json).

## Captura, pré-voo e rodada

A Task 2 partiu de `99cf2f33e1803838e33813d5c4ff46971181ce4e` na branch
`feat/sf2-replay-r1`, worktree `.worktrees/sf2-replay-r1`. O pré-voo
conferiu 30 fontes efetivas e 28 insumos do commit aceito, além dos 19
vínculos da captura e 17 fontes do adaptador no commit histórico
`4eb86a3282f94f32119042a0f6aa075e9f72960a`. Também conferiu o congelamento
de treino e 36 entradas dos índices públicos do pacote. A proveniência dos
pesos vem da captura histórica. A mudança em `selection.py` afeta a
avaliação por replay e preserva as fontes de treino e do adaptador.
[Atestações e hashes](preflight.json).

O selo validou 90 relatos, 5 controles e 95 registros de tempo. Os scores
03 e 04 coincidiram por objeto com os vetores reconstruídos da captura. Os
225 resultados originais, a baseline argmax e a seleção vazia coincidiram
por objeto e pelos bytes descomprimidos da grade. A rodada única executou
com ambiente mínimo e Python 3.11.13 em modo isolado. A CLI retornou código
0 com `eligible_validation_only`. A conferência posterior leu a mesma
saída e recalculou a aritmética dos critérios, denominadores, intervalos,
estatísticas por classe e desempate. [Recibo da execução](execution.json) ·
[Grade original](../qualificacao-01/execucao-02/avaliacao/validation/grid.json.gz).

Não houve inferência, carregamento de modelos, treino, chamadas de API,
acesso aos casos finais, congelamento de seleção, adoção, publicação ou
mudança da demonstração. O final e C06/C07 seguem bloqueados.

## Critérios e métricas

A validação pública sintética tem 90 relatos, dos quais 72 são
classificáveis e 18 exigem revisão. Há 60 alvos omitidos por campo e 13
alvos de prioridade urgente. O acerto aplicado usa como denominador os
campos de fato preenchidos. Cobertura automática conta as conclusões entre
os 72 classificáveis e cobertura correta exige acerto de todos os campos
omitidos nesses casos. A decisão é atômica quando faltam os dois campos.

| Critério da validação | Meta | Selecionada | Passaram na original | Passaram nas extras | Passaram na união |
| --- | ---: | ---: | ---: | ---: | ---: |
| Preservação de campos recebidos | 100% | 60/60 (100%) | 225/225 | 45/45 | 270/270 |
| Chamadas em controles completos ou inválidos | 0 | 0 nos 2 controles | 225/225 | 45/45 | 270/270 |
| Aplicações parciais | 0 | 0 nos 90 relatos | 225/225 | 45/45 | 270/270 |
| Conclusões em revisão esperada | 0/18 | 0/18 | 0/225 | 27/45 | 27/270 |
| Urgente aplicado como não urgente | 0 | 0 nos 13 alvos | 135/225 | 27/45 | 162/270 |
| Acerto de categoria aplicada | ≥ 90%, com denominador positivo | 32/32 (100%) | 225/225 | 45/45 | 270/270 |
| Acerto de prioridade aplicada | ≥ 90%, com denominador positivo | 33/33 (100%) | 210/225 | 45/45 | 255/270 |
| Cobertura automática nos classificáveis | ≥ 51/72 | 51/72 (70,83%) | 180/225 | 27/45 | 207/270 |
| Reconhecimento bruto de urgentes | ≥ 11/13 | 12/13 (92,31%) | 225/225 | 45/45 | 270/270 |

Os controles históricos confirmaram zero chamadas no caso completo e no
inválido. O controle com categoria em branco chamou só categoria, o de
prioridade nula chamou só prioridade e o de ambos omitidos chamou os dois.
[Controles da captura](../qualificacao-01/execucao-02/avaliacao/validation/run/controls.jsonl).

Na selecionada, a cobertura correta foi **51/72 (70,83%)**, com
**39/90 (43,33%)** relatos encaminhados para revisão e **10/13 (76,92%)**
urgentes aplicados corretamente. A rejeição por campo antes da decisão do
caso foi 24/60 em categoria e 20/60 em prioridade. O suporte bruto de
categoria foi Pix 17, repasse 16, maquininha 17 e informação insuficiente
10. O de prioridade foi básica 12, intermediária 13, avançada 12, urgente
13 e informação insuficiente 10.

A tabela completa registra matrizes, suporte, precisão, revocação, F1 e
intervalos de Wilson de 95%. Na selecionada, os intervalos foram
89,28%–100% para acerto de categoria aplicada, 89,57%–100% para acerto de
prioridade aplicada e 59,49%–80,06% para cobertura automática. Os gates
usam as contagens observadas. [Tabela completa das 270 políticas](result.json.gz).

## Efeito dos cortes

| Medida | Coleta histórica, tau 0,50 em ambos | Política original comparável, categoria tau 0,90 | Selecionada, categoria tau 0,95 |
| --- | ---: | ---: | ---: |
| Conclusões em revisão esperada | 3/18 | 2/18 | 0/18 |
| Cobertura automática | 67/72 | 58/72 | 51/72 |
| Cobertura correta | 63/72 | 58/72 | 51/72 |
| Revisão por caso | 20/90 | 30/90 | 39/90 |
| Urgente bruto | 12/13 | 12/13 | 12/13 |
| Urgente aplicado corretamente | 11/13 | 11/13 | 10/13 |
| Urgente aplicado como não urgente | 1 | 0 | 0 |
| Acerto de categoria aplicada | 45/47 | 39/41 | 32/32 |
| Acerto de prioridade aplicada | 39/44 | 38/38 | 33/33 |

As duas políticas comparáveis mantêm prioridade tau 0,70 e ambos os
deltas em 0. A mudança de tau de categoria encaminhou mais nove casos para
revisão. Desse total, dois exigiam revisão e sete eram classificáveis. Os
dois casos de revisão com apenas categoria ausente tinham maiores scores
0,902685 e 0,904549, abaixo de 0,95. A política compara os scores da cabeça com o limiar, e a calibração
desses scores como probabilidades permanece desconhecida. [Diagnóstico da captura](../qualificacao-01/execucao-02/avaliacao/tradeoffs.json).

Entre as 45 novas, 18 com tau de prioridade 0,50 ou 0,60 fizeram 1/18
conclusões em revisão esperada e rebaixaram um urgente. Outras 18 com tau
de prioridade 0,80 ou 0,90 fizeram 0/18 conclusões indevidas, mas cobriram
46/72 ou 41/72. As nove com tau de prioridade 0,70 tiveram métricas iguais.
O desempate histórico prioriza conclusões corretas, urgentes aplicados
corretamente, menos conclusões erradas e maior cobertura automática,
seguidos dos cortes em ordem crescente. Por isso a selecionada ficou com
ambos os deltas em 0.

## Limites e verificação

O cálculo da extensão levou 0,147 s. Na coleta original, a latência
externa medida foi p50 60,82 ms, p95 177,61 ms e máxima 254,01 ms. A
partida até READY levou 9,198 s. Nessas métricas, a captura histórica
usou a política de coleta. O limite de p95 de 3.000 ms pertence à
qualificação final e segue sem observação nesta rodada.
[Relatório original](../qualificacao-01/README.md).

A validação já tinha informado a escolha de testar tau 0,95. Os resultados
descrevem esse conjunto e ainda não demonstram generalização. Uma futura
qualificação exigiria aprovação de um contrato de execução para a nova
política, proveniência vinculada aos insumos e modelos e autorização
específica para a etapa final. A política registrada é uma candidata do
subcontrato offline.

Nesta pasta, execute `rtk proxy sha256sum -c SHA256SUMS` para verificar os
arquivos versionados. Execute
`rtk proxy gzip -dc result.json.gz | rtk proxy sha256sum` para conferir o
SHA-256 dos bytes da saída original, registrado em `execution.json`. O
array `policies` do JSON contém as 225 linhas originais seguidas das 45
extras, com o motivo de veto de cada linha. Os hashes de grade e união
foram calculados antes de acrescentar `failed_gates`, conforme a
serialização compacta documentada pela CLI.

**Exercício.** Compare as políticas de categoria tau 0,90 e 0,95 com os
demais cortes fixos. Calcule quantos relatos a mais vão para revisão e
quantas conclusões corretas são perdidas entre os 72 classificáveis.
