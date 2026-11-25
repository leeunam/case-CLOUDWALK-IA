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

## Segunda onda — implementação em andamento

Continuação autorizada após a conclusão de 00/01/02. Base comum dos agentes:
`1f55d316f29afe7a749317ce136ebde28c2991be`.

| Frente | Agente | Branch / worktree | Aceite desta onda |
| --- | --- | --- | --- |
| 03 · treino e adaptador | Sol, alto | `feat/sf2-treinamento` · `.worktrees/sf2-treinamento` | Pins/imports, export/reload e comportamento do worker com fixtures identificadas |
| 04 · avaliador | Astra, alto | `feat/sf2-avaliador` · `.worktrees/sf2-avaliador` | Métricas, grade, auditoria/congelamento e execução com fixtures matemáticas e de processo |

Os dois códigos passaram pelas revisões individuais e foram integrados em
`237df80`. O aceite combinado conferiu transporte, extração idêntica dos
scores e bloqueio do final com fixture inelegível. Identificou, porém, um
vínculo incompleto entre o índice do adaptador e os arquivos executados;
a correção 2 de 04 está em andamento. A integração ainda não libera 05.

03 prepara o código de treino e o adaptador; 04 prepara o avaliador e a
seleção da regra de revisão. Essas implementações podem trabalhar com fixtures
em paralelo, consumindo a nova base integrada. O treino real continua em 05,
depois do aceite de 03 e 04. Esta primeira onda não produziu pesos, métricas
de classificação SF2 ou chamadas à API de classificador.

A [interface local](interface-onda2.md) registra o transporte e a coleta única
de validação. Neste chat, o integrador acompanha interfaces, revisões
independentes e o aceite combinado antes de liberar o treino.
