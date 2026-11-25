# Auditoria independente do resultado real R5

- Tarefa: C05-R5, revisão do ensaio real.
- Branch/worktree: `feat/luna-executor-r5`, `.worktrees/r5-luna-executor`.
- Base e HEAD mantido: `8314ca56645e016167adf94833cb991be44421f6`.
- Escopo: leitura de evidências e verificação pública offline; zero inferências novas e nenhuma leitura da conta financeira original.

## Verificações reproduzidas

O verificador público offline aprovou tanto `development/report.json` quanto `final/prefix-report.json` com `--profile observed-total-luna-r5`. A validação confirma integridade estrutural dos relatórios e das fontes, não qualifica um ensaio interrompido.

No desenvolvimento real, o gate registra 8/8 alvos corretos, 4/4 campos do canal preservados, três conclusões completas, três revisões integrais, uma urgência reconhecida, zero falhas/timeout e p95 de 2.886 ms. Custo observado nesta etapa: US$ 0,00227389.

O final foi interrompido no item `r2-030`: 30 das 44 chamadas planejadas foram tentadas; 29 tiveram resposta do fornecedor e uma falhou com custo inconciliável. As 14 chamadas restantes não foram iniciadas. O relatório oficial permanece `inconclusive`, corretamente. A única tentativa sem conciliação tem reserva financeira de US$ 1,239, não uma cobrança confirmada; não reconciliar por suposição nem repetir a chamada. O extrato filtrado registra 35 liquidações R5 somando US$ 0,00992557, mais essa reserva. O total conservador global, incluindo reserva, é US$ 1,27986069 e deixa US$ 8,72013931 sob o teto. Isso não é fatura da Feita.

## Diagnóstico adicional da proposta bruta da Luna

Este diagnóstico separado lê `audit.fields.value`, que preserva o código proposto pelo modelo antes do veto local. Não altera o relatório nem os contadores oficiais.

Entre 33 propostas válidas em 36 campos solicitados, 30 coincidem com o rótulo esperado: categoria 15/16 e prioridade 15/17. As três divergências são os três campos cujo rótulo esperado é `informacao_insuficiente`; portanto, nos campos classificáveis observados, as propostas brutas acertaram 30/30, mas também completaram indevidamente os três campos de ambiguidade esperada. Um campo teve abstenção explícita e dois campos tiveram erro de transporte na mesma tentativa.

A política aplicou apenas duas propostas de categoria e uma de prioridade. Vetou 31 propostas: 28 corretas em campos classificáveis e as três respostas indevidas nos casos que exigiam revisão. Como exemplos de veto de respostas corretas: `r2-001` propôs `terminal` para orientação de conservação de uma maquininha guardada; `r2-002` propôs `payouts` para vendas parceladas com ajuste; `r2-003` propôs `pix` para uma pergunta sobre a chave usada em transferências instantâneas. Todas foram marcadas `insufficient_relation`. Em prioridade, as quatro urgências observadas foram propostas como `urgent`, mas também vetadas. Os dois urgentes restantes ainda não foram executados.

Isso aponta para cobertura insuficiente na política semântica 2.1, não para falha de extração da citação: o texto citado era literal e o código proposto era válido. A política só reconhece um conjunto estreito de relações locais. Essa limitação era conhecida no desenho e foi explicitamente posta à prova; a candidata falhou em generalizar. Também não é seguro aprovar a saída bruta sem política, pois ela classificou os três campos que deveriam ir para revisão. O achado é diagnóstico desta amostra, não uma nova pontuação oficial nem evidência de comportamento geral do modelo.

## Por que completar as chamadas restantes não mudaria a decisão

- Cobertura automática: o prefixo tem 1/26 casos classificáveis concluídos. Restam três casos classificáveis entre os seis não executados; mesmo no melhor cenário, 4/29 fica abaixo da meta 21/29.
- Urgência: o gate oficial reconheceu 0/4 urgentes observados após a política. Restam dois dos seis; o máximo seria 2/6, abaixo de 5/6. O diagnóstico bruto identificou quatro propostas urgentes corretas, mas a política as suprimiu.
- Latência: p95 parcial é 3.269 ms em 30 observações. Com o posto mais próximo, p95 final em 36 amostras é o 35º valor. Mesmo que as seis amostras restantes fossem inferiores a 3 s, as observações já registradas mantêm pelo menos duas no patamar de 3.269 ms ou superior; o 35º valor não poderia cair abaixo de 3 s.

Logo, a versão congelada já não poderia satisfazer as metas mesmo se o lote pudesse terminar sem outra falha. Não usar os resultados finais consumidos para ajustar e repetir essa candidata. Qualquer estratégia alterada precisa de um novo conjunto final independente, congelado antes da medição.

## Limites e encaminhamento

A causa HTTP/rede exata da resposta sem uso/custo conciliável não ficou registrada. Os artefatos permitem afirmar somente erro de transporte e parada por custo desconhecido. Não atribuir a uma indisponibilidade específica do fornecedor.

C05-R5 não qualificou Luna+política 2.1; C06 continua bloqueada. Preservar o prefixo, a interrupção e a reserva desconhecida no histórico. Próximo passo depende de escolher outra estratégia de classificação e definir como avaliar uma nova candidata sob o teto acumulado. Nenhuma chamada paga adicional foi feita nesta auditoria.

Comando reproduzido:
```bash
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-luna-r5 --report docs/evidencias/c05/luna-r5-ensaio-real-01/development/report.json
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-luna-r5 --report docs/evidencias/c05/luna-r5-ensaio-real-01/final/prefix-report.json
```
