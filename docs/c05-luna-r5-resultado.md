# C05-R5 · Resultado real Luna com evidência

Em 25/11/2026, a candidata Luna com política 2.1.0 passou no desenvolvimento,
mas o final foi interrompido e não autoriza adoção. A fonte executada foi
`8314ca56645e016167adf94833cb991be44421f6`, branch `feat/luna-executor-r5`,
worktree `.worktrees/r5-luna-executor`. O modelo solicitado foi
`openai/gpt-5.6-luna`, pela Feita. A preparação e as revisões offline não
substituíram esta medição real.

## Desenvolvimento e final são etapas distintas

As seis chamadas de desenvolvimento terminaram entre 10h35min38s e
10h35min52s, no horário de São Paulo. O gate passou: 8/8 campos corretos,
4/4 campos recebidos preservados, 3/3 conclusões corretas, 3/3 revisões
integrais e 1/1 urgente reconhecido. O p95 total foi 2.886,371 ms e o custo
confirmado foi US$ 0,00227389. O selo foi conferido antes de liberar o final.
[Gate e evidências](evidencias/c05/luna-r5-ensaio-real-01/development/development-gate.json).

O final começou às 10h37min34s e parou às 10h38min36s. Foram despachadas
30 das até 44 chamadas planejadas: 29 têm resposta e custo conciliados;
a tentativa `r2-030` terminou com erro de transporte, sem resposta do
modelo nem custo informado. O controle financeiro interrompeu a etapa,
preservou a reserva e não enviou as 14 chamadas restantes. Não houve
repetição, sondagem ou retomada. Os arquivos não registram o código HTTP
ou a causa exata da falha de transporte; não é possível atribuí-la a
limite, indisponibilidade ou cobrança confirmada do fornecedor.

O [relatório do prefixo](evidencias/c05/luna-r5-ensaio-real-01/final/prefix-report.json)
é parcial e registra elegibilidade `inconclusive`. Não existe recibo final
completo. Esses estados não aprovam a candidata.

| Medida no prefixo de 30 tentativas | Resultado parcial |
| --- | ---: |
| Campos recebidos preservados | 24/24 |
| Conclusões automáticas em casos que exigiam revisão | 0/4 |
| Casos classificáveis concluídos automaticamente | 1/26 |
| Urgentes reconhecidos após a política | 0/4 |
| p95 do tempo total observado | 3.269,135 ms |

A proteção evitou conclusões indevidas nos casos ambíguos observados,
mas bloqueou quase todos os casos claros. O resultado mede **Luna com
a política local**, e não o modelo isolado. A auditoria guarda a proposta
original em `audit.fields.value`; a observação usada pelo avaliador contém
a abstenção resultante do veto. Não interpretar esse veto como acerto ou
abstenção espontânea do modelo.

A [auditoria independente](evidencias/c05/luna-r5-ensaio-real-01/auditoria.md)
separou essas duas saídas. Das 33 propostas válidas do modelo, 30 coincidiram
com os rótulos: 15/16 de categoria e 15/17 de prioridade. Entre as propostas
de classificação efetivamente emitidas para campos claros, foram 30/30
corretas; nos três campos ambíguos,
o modelo também propôs valores, quando deveria pedir revisão. Houve ainda
uma abstenção explícita e dois campos com erro de transporte na tentativa
interrompida. Os dois campos claros sem proposta por erro de transporte
ficam fora do denominador 30/30. São diagnósticos parciais, não uma aprovação
do modelo puro.

O filtro vetou 28 das propostas corretas e as três propostas indevidas.
As quatro urgências observadas foram propostas corretamente pela Luna e
vetadas pela política. A relação semântica reconhecida pelas regras era
estreita demais; o problema não foi a extração da citação literal. Retirar
simplesmente o filtro também não resolve os três completamentos ambíguos.
Os verificadores offline aprovaram a integridade dos dois relatórios; isso
não altera a reprovação da estratégia ou a incompletude do lote.

## Custo confirmado e reserva pendente

Os 35 recibos conciliados nas duas etapas somam **US$ 0,00992557**:
US$ 0,00227389 no desenvolvimento e US$ 0,00765168 nas 29 respostas do
final. A tentativa interrompida conserva **US$ 1,239 de reserva**, sem
valor confirmado de cobrança. A reserva é uma proteção interna do orçamento;
não representa débito observado na Feita.

O total conservador da conta histórica é **US$ 1,27986069**, incluindo essa
reserva; o total sem a nova reserva é US$ 0,04086069. Restam US$ 8,72013931
sob o teto global de US$ 10 enquanto a pendência for mantida. Esses valores
não são uma consulta ao saldo do fornecedor. O extrato filtrado foi obtido
em modo somente leitura da mesma conta SQLite v4, sem reinicialização,
nova conta, liquidação fictícia ou acesso à chave.
[Recibos e reserva](evidencias/c05/luna-r5-ensaio-real-01/financial-receipts.json).

## Continuidade

A candidata não será adotada em C06. O desenvolvimento aprovado era uma
triagem inicial, e o conjunto maior mostrou que o filtro não generalizou.
Preservar os resultados negativos, os gabaritos e os critérios. Não ajustar
a candidata aos exemplos finais consumidos e depois apresentar o mesmo
conjunto como avaliação cega. Uma estratégia posterior precisa registrar
o novo desenho e prever validação independente antes de outras chamadas.

Novas chamadas estão suspensas. A pendência financeira exige evidência
real de cobrança para conciliação, sem reenviar o relato. A demonstração
publicada permanece em fixture. C05, C06 e C07/F09 final continuam abertos;
o atendente conversacional real E01 continua posterior e opcional.

Exercício: compare a proposta original de um campo em `luna-evidence.jsonl`
com a escolha em `observations.jsonl`. Identifique se foi o modelo que pediu
revisão ou a política que vetou a proposta.
