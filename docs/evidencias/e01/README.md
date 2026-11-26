# E01 — evidências do atendente experimental

Esta evolução usa a Luna pela Feita, com conhecimento fictício separado por marca. A demonstração pública do MVP permanece com o atendente simulado. O piloto usa projeto e volumes próprios, orçamento acumulado de US$ 1 e até 24 autorizações. [Primeiro ensaio real](piloto-20261126/primeiro-ensaio.json) · [Fontes e premissas financeiras](preflight/fontes-publicas.json).

## Primeiro ensaio — 26/11/2026

A candidata `e4442f1` executou cinco chamadas. P1, P2/1, P2/2 e P3/1 passaram: procedimentos distintos de Pix para Aurora e Horizonte, resolução após confirmação explícita e pergunta sobre condição ausente. P3/2 foi rejeitada como `invalid_decision`. O lote parou antes de P4–P6. A falha e o valor cobrado permanecem no registro; a candidata não foi aprovada integralmente.

P1 recebeu a orientação Pix da Aurora com fonte `aurora.manual` 1.0.0, preservou o histórico e permaneceu em atendimento. A orientação foi conferida na interface, recuperada após recarregar e aprovada pelo responsável no chat. A chamada usou 985 tokens de entrada e 109 de saída, sem cache nem raciocínio reportados. O modelo retornou `openai/gpt-5.6-luna`. Foram 3.227,134 ms no fornecedor e 8.579 ms da entrada à resposta persistida. A Feita reportou 0,03278 créditos, equivalentes a US$ 0,0003278 pela tabela de US$ 0,01 por crédito.

As cinco chamadas reportaram US$ 0,00176515. O ledger contabilizou US$ 0,0535457 de provisões, sem reserva pendente. A provisão inicial de cada chamada foi US$ 0,7654. Valor reportado pela API, provisão local e liquidação da carteira são medidas distintas. Os recibos privados foram conciliados sem modificar a falha comportamental.

Os turnos P2/2 e P3/1 levaram 48.743 e 49.539 ms da entrada à resposta persistida. O consumidor era parado entre as compras e sua saída por SIGTERM deixava a associação Kafka expirar por aproximadamente 45 segundos. Esses tempos são mantidos como medidos, sem descontar a espera. O novo ensaio adotará encerramento gracioso e manterá o relógio integral.

## Ajuste de qualidade em preparação

Com a requisição original de P3/2, o validador aceitou o encaminhamento canônico. A decisão rejeitada não foi preservada, portanto não se atribui o erro a um campo específico. E01-Q1 restringe a geração às escolhas que já passam pela aplicabilidade do histórico e registra submotivos fechados, sem conteúdo do cliente. E01-Q2 prepara um novo ensaio de nove turnos no mesmo projeto e orçamento: cinco anteriores mais nove novos, máximo previsto de 14 autorizações. O primeiro ensaio não será apagado ou renomeado como sucesso. [Especificação do ajuste](../../planejamento/e01-atendente-real.md#ajuste-após-a-primeira-execução-real--e01-q1-e-e01-q2).

A qualidade da candidata revisada e o aceite completo da interface permanecem pendentes. A autorização do piloto não libera consumo público contínuo.

## Verificações reproduzíveis de código

No commit integrado `406920d`, passaram 135 testes Rails com 1.986 asserções, com uma omissão deliberada do JEV ao vivo; 63 testes Python da integração, 19 do piloto e 3 auxiliares. Os contratos E01 validaram seis trocas completas e 65 rejeições. Após a correção final `e4442f1`, passaram mais 44 testes focais de captura, conhecimento e piloto. Um teste curto de transporte excedeu o prazo durante a execução concorrente com Rails; a reexecução sequencial dos mesmos 63 testes passou. A correção final não alterou Rails nem frontend.

O ensaio offline de interrupção confirmou duas cópias pós-ACK nos offsets 0 e 1, com a ponte de retorno confirmada em 2 e uma única resposta aplicada. O pedido cujo ACK de start foi perdido manteve seu offset enquanto `started`; avançou após `unknown` conservar a reserva e pausar o piloto. A simulação verifica protocolo e não mede a qualidade da Luna. [Reprodução offline](../../e01-offline.md) · [Operação do piloto](../../e01-piloto.md).

O resumo do runner pode agrupar falha de conciliação financeira em `without_verified_result` mesmo quando uma resposta já foi aplicada. Os registros por turno distinguem esses casos; uma falha financeira impede a chamada seguinte. Não há qualificação estatística de produção, nova prova de escala ou habilitação permanente do modelo nesta etapa.
