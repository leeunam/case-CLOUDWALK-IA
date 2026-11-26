# SF2 — acompanhamento das ondas

Primeira onda autorizada pelo responsável em 25/11/2026. Base comum:
`5c6cc6330a7247be6694be7cff8315d546824ab0`.
[Aprovação](aprovacao.json) · [Especificação](especificacao.md) ·
[Cards e aceites](tarefas.md).

**Primeira onda concluída:** 00, 01 e 02 aceitas após revisões independentes.
Contratos, dados públicos e selo do final foram integrados localmente.

| Frente | Responsável | Estado | Próxima evidência |
| --- | --- | --- | --- |
| 00 · contratos e validadores | Agente Astra, alto, com revisão independente | Aceita e integrada em `c4fe01f`; 16 testes passaram após corrigir cinco achados da revisão | Consumidores usam o contrato integrado; não há modelo treinado nesta entrega |
| 01 · dados públicos | Agente Sol, alto, anotadores B e revisores independentes | Aceita e integrada em `4e006a3`; pacote completo com 150 + 90 relatos, duas anotações por relato e recibos reais | Preservar os bytes aprovados; não treinar antes do aceite de 02–04 |
| 02 · teste final reservado | Agente Sol, alto, distinto do autor da candidata, com anotadores B e auditor independente | Aceita e integrada em `88df18a`; 120 relatos selados, com 96 classificáveis, 24 revisões e 17 urgentes-alvo | Preservar o pacote privado; somente o executor de 05 abre o final após validação elegível e congelamento da candidata |

O chat dispõe de dois agentes de trabalho além do integrador. As três frentes
já foram iniciadas e são escalonadas conforme as vagas; revisores
também usam essas vagas. Código de contratos e dados aceitos chegam aos demais
apenas por commits integrados, sem consumir arquivos em edição de outra frente.

A trilha reproduzível da SF2-01 está em
[dados-publicos-01](../../../evidencias/c05/sf2/dados-publicos-01/README.md).
O validador completo confirmou `accepted: true` para 150/90 na base integrada,
com anotações, revisão independente e comprimentos ligados aos bytes reais.
O [selo de 02](dados/final-seal.json) e o
[resumo da revisão](dados/final-review-summary.md) registram o aceite dos 120
finais. A CLI foi executada pelo custodiante nos arquivos canônicos reais;
o integrador conferiu os hashes e as permissões, sem expor textos ou IDs do
conjunto reservado. Os 16 testes de contrato de 00 passaram. Os dados públicos
e finais têm duas anotações por relato e zero divergências pendentes.

## O que acompanharemos aqui

1. **Significado dos rótulos.** Categoria descreve o assunto. Prioridade depende
   de impacto, funcionamento e prazo. Veremos exemplos públicos de treino;
   ausência de fatos pode exigir revisão, mesmo que o assunto esteja claro.
2. **Correção do contrato.** A entrada precisa indicar corretamente os campos
   ausentes. Valores válidos são preservados; uma revisão não permite aplicar
   metade da resposta. Fixtures demonstram essas regras, sem provar acerto do modelo.
3. **Revisão independente dos dados.** Um segundo anotador classifica os textos
   sem ver os primeiros rótulos. Desacordos são conciliados pela rubrica, antes
   do selo; a segunda anotação não será uma cópia da primeira.
4. **Contagens e independência.** Alvos planejados são 150/90/120, com 18 casos
   de revisão na validação e 24 no final. São quotas a verificar, não dados
   prontos. Aqui veremos apenas o resumo do final e seu hash, sem seus textos.

Esta onda prepara contratos e dados. Não treina os especialistas nem mede
acerto, confiança ou latência de classificação SF2. A demonstração continua
fixture e não há chamadas à API de classificador. Treino real espera os
aceites e selos previstos nos cards 00–04; adoção depende da qualificação.

A concordância dos anotadores não prova novidade nem qualidade do futuro
modelo. Nesta revisão, o filtro lexical não encontrou duplicatas, mas a leitura
semântica detectou cenários reaproveitados. Os rascunhos e as primeiras
anotações permanecem registrados; textos novos exigem anotações novas. O
teste final continua reservado e não é mostrado aos autores dos modelos.

## Segunda onda — concluída

Continuação autorizada após a conclusão de 00/01/02. Base comum dos agentes:
`1f55d316f29afe7a749317ce136ebde28c2991be`.

| Frente | Agente | Branch / worktree | Aceite desta onda |
| --- | --- | --- | --- |
| 03 · treino e adaptador | Sol, alto | `feat/sf2-treinamento` · `.worktrees/sf2-treinamento` | Pins/imports, export/reload e comportamento do worker com fixtures identificadas |
| 04 · avaliador | Astra, alto | `feat/sf2-avaliador` · `.worktrees/sf2-avaliador` | Métricas, grade, auditoria/congelamento e execução com fixtures matemáticas e de processo |

Os dois códigos passaram pelas revisões individuais. O aceite combinado
conferiu transporte, ausência de aquecimento, extração idêntica de 120 vetores
dos mesmos 90 frames e bloqueio do final com fixture inelegível. A lacuna
do inventário foi corrigida e reavaliada: as quatro alterações de fonte foram
recusadas. O roteiro de reprodução também passou por revisão e correção de
autenticação e caminhos. A evidência final foi integrada em `9507887`.

03 prepara o código de treino e o adaptador; 04 prepara o avaliador e a
seleção da regra de revisão. Essas implementações podem trabalhar com fixtures
em paralelo, consumindo a nova base integrada. O treino real continua em 05,
depois do aceite de 03 e 04. Esta primeira onda não produziu pesos, métricas
de classificação SF2 ou chamadas à API de classificador.

A [interface local](interface-onda2.md) registra o transporte e a coleta única
de validação. Neste chat, o integrador acompanha interfaces, revisões
independentes e o aceite combinado antes de liberar o treino.

## SF2-05 — validação concluída e reprovada

O pedido de continuidade retoma o fluxo aprovado, agora com 00–04 e a
integração aceitas. 05 executa a receita fixa, sem busca de hiperparâmetros:
um treino por campo, coleta única de validação e comparação das 225 políticas.
O limite acumulado de treino é 30 minutos em CPU. O executor é separado do
autor da candidata. Textos e anotações finais continuam privados até a
validação cumprir os gates, a auditoria aprovar a seleção e o pacote ser
congelado. Essa liberação produziu a entrega abaixo, sem adoção ou chamadas pagas.

SF2-05A foi executada na base `99885274`, branch `feat/sf2-qualificacao`,
worktree `.worktrees/sf2-qualificacao`. Os dois especialistas completaram
um ajuste por campo em 913,685 s acumulados; os seis testes de reload
reproduziram os scores. Uma coleta registrou 90 relatos e cinco controles.
Os extratores 03 e 04 concordaram nos mesmos 120 vetores, sem nova inferência.

**Nenhuma das 225 políticas ficou elegível.** Todas concluíram pelo menos
dois dos 18 casos que exigiam revisão. Na política de coleta, categoria
acertou 45/47 complementos aplicados e prioridade 39/44; houve um urgente
rebaixado. O p95 observado dessa coleta foi 177,61 ms. Essas métricas
descrevem a validação e sua política de coleta, não um teste final ou uma
política vencedora.

A [evidência](../../../evidencias/c05/sf2/qualificacao-01/README.md), integrada
em `4eb86a3`, passou por
[revisão independente](../../../evidencias/c05/sf2/revisoes-qualificacao-01/revisao.md).
O primeiro lançamento falhou com erro de permissão sem anúncio de ajuste;
os registros foram preservados. O relançamento autorizado manteve código,
dados e receita. A operação exata da primeira falha não foi identificada.

| Etapa | Estado após a revisão |
| --- | --- |
| 05 · treino e validação | Entrega negativa aceita; nenhum congelamento ou digest de liberação |
| Final independente | 120 relatos continuam privados, sem execução |
| 06 · integração | Bloqueada por qualificação e decisão de adoção |
| 07 · reprodução real | Bloqueada por 06; demonstração fixture preservada |

Qualquer extensão da grade ou novo treino exige proposta separada. A receita,
o protocolo e os dados desta execução permanecem inalterados. A próxima
decisão não autoriza antecipar o final nem reduzir os critérios de qualidade.

## SF2-R1 — candidata elegível na validação

Após o resultado negativo, o responsável aprovou uma extensão única da grade:
tau 0,95 só em categoria, com 45 combinações adicionais sobre os mesmos
vetores. O [plano R1](sf2-r1-plano.md) e sua [emenda](sf2-r1-protocolo.json)
preservam os 225 resultados, contratos e protocolo originais. As metas e os
dados não mudam. Há duas passagens: código por fixtures e depois uma execução
offline, ambas com revisão independente. Não autoriza novo treino, inferência,
API, abertura do final ou adoção. O risco de sobreajuste na validação é
explicitado. A execução posterior concluiu uma rodada das 45 políticas, sem nova
inferência. A paridade dos 225 resultados originais foi confirmada por
objetos e bytes. Nove das 45 extras passaram. O desempate selecionou
categoria tau 0,95 e prioridade tau 0,70, com deltas zero. A candidata
concluiu corretamente 51/72 classificáveis e revisou 39/90 relatos,
incluindo os 18 que exigiam revisão; houve zero urgentes rebaixados.
Acertos aplicados: categoria 32/32, prioridade 33/33.

A [execução](../../../evidencias/c05/sf2/revisao-01/README.md) foi aceita
com [revisão global independente](../../../evidencias/c05/sf2/revisao-01/revisoes/revisao-final.md),
integração local em `53e3e87`. A cobertura ficou exatamente no mínimo
planejado. O ganho custa mais revisões humanas e ainda não prova
generalização. O teste independente de 120 casos, a adoção e C06/C07
continuam bloqueados. A próxima preparação é um contrato de execução
compatível com a política R1, preservando modelos e critérios; a abertura
do final será uma liberação separada após esse preparo.
