# SF2-R1 — extensão única da revisão, somente offline

## Especificação e aprovação

O responsável respondeu **“boa, prossiga”** à proposta concreta de acrescentar
um corte 0,95 só para categoria, com 45 combinações adicionais sobre os
resultados já gravados. O [protocolo desta emenda](sf2-r1-protocolo.json) registra
aprovação, hashes dos insumos, quotas, critérios e limites. A aprovação é para
esta avaliação offline; não libera treino, inferência, API, final, adoção ou
publicação. Base inicial `9bb52144083494aa206b25a59a33b409576c5a4f`.

A SF2 original continua reprovada: 0/225 políticas elegíveis. Seus dados,
modelos, protocolo, schema, freeze, frames, tempos e grade permanecem intactos.
O corte novo é o ponto médio entre 0,90 e 1,00; não será aproximado dos scores
específicos que motivaram a proposta. Os dados de validação já informaram a
emenda, com risco de sobreajuste: um passe offline não prova generalização.

## Contrato e fronteira

A política SF2 aceita apenas os cortes originais. R1 terá um **subcontrato
offline separado** `sf2-r1-offline/1.0`. Não produzir uma política 0,95 fingindo
ser válida no schema/IPC original. As 225 políticas antigas preservam o tipo
original; as 45 extras têm tipo próprio. A comparação usa os mesmos campos
de corte, métricas, gates e desempate; o tipo não altera a ordenação.

Uma extração pequena do replay puro de `evaluation/selection.py` é permitida
para evitar duas implementações da regra. A API `select` continua a gerar
225, com baseline e resultados por objeto idênticos à grade arquivada. Não
monkeypatchar `PROTOCOL`, nem acrescentar 0,95 à grade de prioridade. Gates,
rank, métricas e fontes de treino/adaptador não mudam.

Essa refatoração altera um dos hashes da captura histórica. Atestar **bytes
históricos no commit-pai** separadamente dos bytes efetivamente executados em
R1, antes do replay. Nunca substituir o hash da captura para fazê-la passar.
O manifesto de fontes R1, com digest fornecido pelo integrador/executor a
partir do commit aceito, vincula todas as fontes usadas, inclusive novo
subcontrato/CLI, dependências SF2 e fontes alteradas. Caminhos canônicos,
conjunto completo e SHA dos membros devem ser conferidos antes de importar o
motor de seleção. Catálogo/protocolo/schema/core originais continuam iguais
aos hashes da captura. A grade descomprimida confere com o hash registrado;
03/04 devem ter scores iguais por objeto e os vetores devem derivar dos mesmos
frames. O selo deve ser auditado com os 90 relatos, 5 controles e 95 tempos.

R1 não chama `workflow.checked_development`, `freeze` ou executor original
para fabricar uma liberação. A saída diz explicitamente que é replay, não
uma nova observação de modelo ou latência. A latência antiga pode ser citada
apenas como diagnóstico da captura original. Mesmo se houver candidata
elegível, o final e C06/C07 continuam bloqueados: ainda faltariam contrato
runtime, proveniência e passagem separada para execução final.

## Global Constraints

- Ler AGENTS.md, CONTEXT.md e RTK; usar RTK. Worktree/branch próprias, base
  concreta do integrador, commits Conventional em português, sem push.
- Não ler/listar/varrer `.superpowers/sdd/conclusao-projeto/sf2-final/` nem
  `.env`, segredos, contabilidade ou resultados de outros fornecedores.
- Uma rodada adicional de exatamente 45 políticas: categoria tau 0,95,
  deltas 0/0,1/0,2 e prioridade com 5 taus e 3 deltas originais. União270,
  sem duplicatas. Comparar 225 originais + 45 novas pelo desempate original.
- Manter 72 classificáveis, 18 revisões, 60 alvos por campo e 13 urgentes;
  acerto aplicado ≥90% por campo com denominador positivo; cobertura ≥51/72;
  urgente bruto ≥11/13; zero conclusão em revisão, zero urgente rebaixado,
  canal 100%, controles completos/inválidos 0 chamadas e parcial 0. Usar gates
  originais, sem trocar denominadores ou rebatizar cobertura correta.
- Não treinar, inferir, carregar pesos, usar API, mudar rubrica/gold/catálogo,
  criar outro corte, repetir a busca, aquecer modelo, abrir final, adotar,
  mudar aplicação/Docker ou publicar. Nenhum resultado real antes da revisão
  do código e do congelamento da emenda.
- Preservar insumos originais. Recusar divergência de hash, fonte, caminho,
  selo, score, quota ou configuração antes da primeira política nova. Atestar
  fontes históricas e atuais separadamente. Não fabricar freeze/release.
- Fixtures de teste são identificadas e não são o resultado real. Testes
  cobrem riscos reais da alteração; não repetir suítes alheias sem motivo.
- Não delegar subagentes; root atribui implementação, execução e revisão.

## Task 1: replay puro e subcontrato offline R1

**Agente:** GPT-6.2 Astra, alto; revisão independente fresca.
**Base:** commit de emenda fornecido pelo integrador.
**Branch/worktree:** `feat/sf2-revisao-grade` / `.worktrees/sf2-revisao-grade`.
**Possui:** `evaluation/selection.py` (extração mínima do replay), novo módulo
`script/classification_comparison/setfit_sf2/revision_r1/`, seu README e testes,
e schema separado `sf2-r1.schema.json` junto deste plano. Não altera contratos
SF2, outras fontes de avaliação, dados ou protocolo desta emenda.

Implementar CLI offline com insumos definidos no protocolo, schema R1,
inventário de fontes e digest confiável. Atestar antes de importar o motor:
versão/bytes da emenda, conjunto completo do inventário atual, fontes do
commit-pai e todos os insumos de captura. Sem depender dos caminhos absolutos
registrados no config antigo: mapear artefatos públicos canônicos e manter o
config original como evidência histórica. Recusar path traversal/symlinks
fora das raízes explícitas. Não importar SetFit/Torch/joblib/worker.

O protocolo da emenda terá hash confiável explícito no comando, assim como
o inventário atual. A árvore histórica pode ser a worktree de qualificação
intacta, explicitamente fornecida, com todos os hashes capturados verificados
antes de imports. Não seguir caminhos absolutos não autorizados do config.
A proveniência dos pesos vem da captura aceita e dos índices públicos; não
carregar nem afirmar nova conferência dos pesos se ela não foi executada.

Auditar decisões originais com política de coleta original e conferir o selo,
scores03/04 e derivação dos frames. Refazer 225 por replay para provar paridade
com o objeto arquivado e baseline; só depois calcular45 e ranquear união270.
Registrar matriz por política, razões de veto, critérios, suporte, intervalos,
seleção ou ausência dela, fontes/hashes, contagens de consumo0, tempo apenas
computacional e inexistência de liberação final. Saída nova, sem sobrescrever
originais ou uma saída existente. Estados/exitcodes elegível0, negativo1 e
insumo/execução inválida2 devem ficar claros.

Aceite: testes de fixture para paridade225 e baseline; 45/270semduplicatas;
top igual a tau aceita/margem igual a delta revisa; score 0,92 aceito no corte 0,90 e
vetado no 0,95; atomicidade, campos fornecidos, score malformado e revisão
bruta; alteração de selo/frames/scores/fonte/manifesto/caminho/corte recusada
antes do replay; seleção/desempate e todas as combinações inelegíveis. Provar
que não há chamada a modelo/processo externo, rede ou final. Nenhum replay
real45 nesta tarefa. Entregar relatório com comandos/resultados, commit,
limites e exercício: seguir o mesmo vetor pelos cortes0,90 e0,95.

## Task 2: execução única e parecer de elegibilidade em desenvolvimento

**Agente:** GPT-6.2 Sol, alto, independente do autor do código; revisão fresca
Astra, alto, também revisão final da emenda completa.
**Base:** commit com Task1 revisada e integrada.
**Branch/worktree:** `feat/sf2-replay-r1` / `.worktrees/sf2-replay-r1`.
**Possui:** `docs/evidencias/c05/sf2/revisao-01/` com recibos, tabela e relatório;
saídas originais ignoradas na própria worktree. Sem alteração de produto/código.

Registrar pré-voo, hashes da emenda e fontes atuais no commit aceito; usar
apenas arquivos públicos. Depois dos checks determinísticos, executar uma
rodada extra45 com o CLI aceito. Publicar tabela270, diagnóstico comparativo,
política selecionada em subcontratoR1 se houver, métricas/denominadores e
limites. Não tratar tempo de replay como latência do modelo, não reescrever
captura original. Se negativo, manter final fechado e parar; não adicionar
corte/treino. Se elegível, documentar somente elegibilidade na validação e
lacunas contratuais da futura qualificação; não executar final ou produzir
freeze/release original. Registrar declaração de ausência de nova inferência,
API, treino, exposição final ou mudança de demonstração.

Aceite: originais225 idênticos por objeto, grade original intacta,45extras e
270união completas; fontes e hashes conferidos; todos gates/denominadores e
tradeoffs corretos; resultado negativo também válido. Revisão independente
recalcula aritmética a partir dos artefatos sem nova execução de modelo. Root
integra somente após SPEC+QUALITY e atualiza estado do projeto. Fechamento
inteiro recebe revisão final, sem duplicar a revisão de código já encerrada.

## Coordenação

Preparação e revisão estática podem ocorrer em paralelo; implementação e
execução seguem as dependências acima. A implementação usa fixtures, a
execução real espera a aceitação do código. Este plano não autoriza outra
rodada R1, Task06/07 ou qualificação final. Exercício final: comparar o número
de revisões e a cobertura antes/depois do corte, sem confundir as duas métricas.
