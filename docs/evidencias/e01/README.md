# E01 — evidências do atendente experimental

Esta evolução usa a Luna pela Feita, com conhecimento fictício separado por marca. **O piloto E01 foi concluído e aprovado para a demonstração em 26/11/2026.** A demonstração pública do MVP permanece com o atendente simulado. O piloto usa projeto e volumes próprios, orçamento acumulado de US$ 1 e até 24 autorizações. [Aceite final](piloto-20261126/aceite-final.json) · [Conversas completas](piloto-20261126/conversas.md) · [Fontes e premissas financeiras](preflight/fontes-publicas.json).

## Resultado da candidata revisada

Na candidata `7a73df5`, os nove turnos da matriz passaram em seis conversas, duas marcas e três canais simulados. Foram verificados os procedimentos próprios de cada marca, a pergunta por uma condição ausente, a resolução após confirmação explícita e quatro encaminhamentos com resumo e referências ao histórico. O responsável aprovou as seis conversas após sua apresentação. A Luna interpreta o histórico e escolhe entre alternativas aplicáveis; o executor materializa os textos publicados, sem redação livre nesta etapa. [Ensaio revisado](piloto-20261126/ensaio-q1.json).

| Turno | Ação verificada | Entrada até resposta persistida |
| --- | --- | --- |
| P1/1 | Orientação Pix Aurora | 6.943 ms |
| P2/1 | Orientação Pix Horizonte | 6.909 ms |
| P2/2 | Resolução após confirmação | 5.993 ms |
| P3/1 | Pergunta sobre o menu da maquininha | 6.141 ms |
| P3/2 | Encaminhamento por incerteza persistente | 5.989 ms |
| P4/1 | Encaminhamento a pedido do cliente | 6.164 ms |
| P5/1 | Encaminhamento de operação sensível | 5.756 ms |
| P6/1 | Orientação sobre repasse Horizonte | 6.515 ms |
| P6/2 | Encaminhamento após negativa do cliente | 6.310 ms |

Todas as propostas revisadas foram aplicadas durante a validade da rodada; não houve timeout nem resultado pendente na nova matriz. P3–P5 ficaram em atendimento humano. P6 aguardou capacidade e foi atribuído a Cris após a conclusão humana de P4.

O novo ensaio reportou US$ 0,00331830. **O acumulado dos dois ensaios é de 14 chamadas e US$ 0,00508345 reportados pela Feita**, com 14 recibos conciliados, US$ 0,1500054 contabilizados pelo Rails como provisão conservadora e zero reservas pendentes. Os IDs, hashes, tokens e valores dos 14 recibos foram conferidos em revisão independente. A conciliação comprova o valor informado pela API; não houve conferência de extrato para afirmar liquidação na carteira. O orçamento original e as falhas anteriores foram preservados.

## Aceite da interface e das marcas

Cris conferiu o resumo e a referência de P4 na interface, respondeu como analista responsável e resolveu o atendimento. A resposta humana e o estado Resolvido permaneceram após recarregar. Essas ações não fizeram novas chamadas à Luna. [Registro do aceite](piloto-20261126/aceite-final.json).

As seis combinações de analista e marca passaram: Bia acessou Aurora, mas Horizonte ficou ausente da lista e retornou 404 genérico no detalhe e no histórico, com assinatura WebSocket rejeitada. Cris e Alex acessaram ambas as marcas, com assinatura confirmada. Esse ensaio verificou a decisão da assinatura; não mediu a entrega de um novo evento WebSocket. [Matriz REST e WebSocket](isolamento-marcas.md).

O consumidor Luna foi parado ao concluir o piloto. A autorização não libera consumo público contínuo. Os canais WhatsApp e e-mail continuam simulados, as bases são fictícias e os nove turnos não constituem avaliação estatística de qualidade em produção. O contexto de marca foi conferido no código, nas bases e nas saídas; as capturas financeiras preservam hash do pedido, sem armazenar o corpo completo enviado ao fornecedor.

## Primeiro ensaio — 26/11/2026

A candidata `e4442f1` executou cinco chamadas. P1, P2/1, P2/2 e P3/1 passaram: procedimentos distintos de Pix para Aurora e Horizonte, resolução após confirmação explícita e pergunta sobre condição ausente. P3/2 foi rejeitada como `invalid_decision`. O lote parou antes de P4–P6. A falha e o valor cobrado permanecem no registro; a candidata não foi aprovada integralmente.

P1 recebeu a orientação Pix da Aurora com fonte `aurora.manual` 1.0.0, preservou o histórico e permaneceu em atendimento. A orientação foi conferida na interface, recuperada após recarregar e aprovada pelo responsável no chat. A chamada usou 985 tokens de entrada e 109 de saída, sem cache nem raciocínio reportados. O modelo retornou `openai/gpt-5.6-luna`. Foram 3.227,134 ms no fornecedor e 8.579 ms da entrada à resposta persistida. A Feita reportou 0,03278 créditos, equivalentes a US$ 0,0003278 pela tabela de US$ 0,01 por crédito.

As cinco chamadas reportaram US$ 0,00176515. O ledger contabilizou US$ 0,0535457 de provisões, sem reserva pendente. A provisão inicial de cada chamada foi US$ 0,7654. Valor reportado pela API, provisão local e liquidação da carteira são medidas distintas. Os recibos privados foram conciliados sem modificar a falha comportamental.

Os turnos P2/2 e P3/1 levaram 48.743 e 49.539 ms da entrada à resposta persistida. O consumidor era parado entre as compras e sua saída por SIGTERM deixava a associação Kafka expirar por aproximadamente 45 segundos. Esses tempos são mantidos como medidos, sem descontar a espera. O novo ensaio adotará encerramento gracioso e manterá o relógio integral.

## Ajuste após a primeira falha

Com a requisição original de P3/2, o validador aceitou o encaminhamento canônico. A decisão rejeitada não foi preservada, portanto não se atribui o erro a um campo específico. E01-Q1 restringiu a geração às escolhas que já passam pela aplicabilidade do histórico e registra submotivos fechados, sem conteúdo do cliente. E01-Q2 executou um novo ensaio explícito de nove turnos no mesmo projeto e orçamento: cinco anteriores mais nove novos, 14 autorizações acumuladas. O encerramento gracioso por SIGINT liberou o grupo Kafka antes da próxima entrada, preservando o relógio integral. O primeiro ensaio não foi apagado ou renomeado como sucesso. [Primeiro ensaio](piloto-20261126/primeiro-ensaio.json) · [Especificação do ajuste](../../planejamento/e01-atendente-real.md#ajuste-após-a-primeira-execução-real--e01-q1-e-e01-q2).

O snapshot do runner conserva os flags históricos de revisão por turno. A aprovação global posterior está vinculada por hash ao snapshot completo das conversas em `aceite-final.json`; os registros anteriores não foram reescritos para simular outra forma de aprovação.

## Verificações reproduzíveis de código

No commit integrado `406920d`, passaram 135 testes Rails com 1.986 asserções, com uma omissão deliberada do JEV ao vivo; 63 testes Python da integração, 19 do piloto e 3 auxiliares. Os contratos E01 validaram seis trocas completas e 65 rejeições. Após a correção final `e4442f1`, passaram mais 44 testes focais de captura, conhecimento e piloto. Um teste curto de transporte excedeu o prazo durante a execução concorrente com Rails; a reexecução sequencial dos mesmos 63 testes passou. A correção final não alterou Rails nem frontend.

O ensaio offline de interrupção confirmou duas cópias pós-ACK nos offsets 0 e 1, com a ponte de retorno confirmada em 2 e uma única resposta aplicada. O pedido cujo ACK de start foi perdido manteve seu offset enquanto `started`; avançou após `unknown` conservar a reserva e pausar o piloto. A simulação verifica protocolo e não mede a qualidade da Luna. [Reprodução offline](../../e01-offline.md) · [Operação do piloto](../../e01-piloto.md).

Após Q1, passaram 49 testes focais no host. A suíte Docker de 70 testes passou em uma execução; outras três tiveram falhas intermitentes nos testes curtos de prazo do transporte. As falhas não foram omitidas nem os prazos relaxados. Q2 passou em 38 testes focais e confirmou, em Kafka real com transporte fictício, a saída graciosa e a reentrada no grupo em aproximadamente 1,23 s.

O resumo do runner pode agrupar falha de conciliação financeira em `without_verified_result` mesmo quando uma resposta já foi aplicada. Os registros por turno distinguem esses casos; uma falha financeira impede a chamada seguinte. Não há qualificação estatística de produção, nova prova de escala ou habilitação permanente do modelo nesta etapa.
