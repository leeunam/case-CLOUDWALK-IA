# SF2 — acompanhamento da primeira onda

Primeira onda autorizada pelo responsável em 25/11/2026. Base comum:
`5c6cc6330a7247be6694be7cff8315d546824ab0`.
[Aprovação](aprovacao.json) · [Especificação](especificacao.md) ·
[Cards e aceites](tarefas.md).

| Frente | Responsável | Estado | Próxima evidência |
| --- | --- | --- | --- |
| 00 · contratos e validadores | Agente Astra, alto | Implementação `16133fb` entregue; correção dos achados da revisão em curso | Fechar cinco falhas de vínculo/aceite com regressões; nova revisão antes de integrar |
| 01 · dados públicos | Agente Sol, alto | Autoria A registrada em `50ee50a`: 150 textos de treino + 90 de validação; manifesto ainda em rascunho | Anotação B independente, conciliação, aceite pelo validador integrado e auditoria de novidade |
| 02 · teste final reservado | Agente Sol, alto, distinto do autor da candidata | Autoria privada iniciada na worktree `sf2-dados-finais` | 120 textos privados, duas anotações e auditoria; somente contagens/hash ficam públicos |

O chat dispõe de dois agentes de trabalho além do integrador. As três frentes
já foram iniciadas e são escalonadas conforme as vagas; revisores
também usam essas vagas. Código de contratos e dados aceitos chegam aos demais
apenas por commits integrados, sem consumir arquivos em edição de outra frente.

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
