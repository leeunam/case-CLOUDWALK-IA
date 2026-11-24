# C05-R2 · Conferência final de similaridade

Os 36 relatos podem ser mantidos quanto à similaridade. O texto atualizado de `r2-014` apresenta diferença material frente aos 60 históricos. Os outros 35 vereditos foram preservados após conferir cada hash.

**Status** · Sem pendências de similaridade para a versão conferida.

A revisão foi conduzida pelo conferente independente de similaridade, fora da autoria, da frente de prompt e da revisão dos rótulos.

## Inventários

A branch é `docs/r2-protocolo-dados`, na worktree `.worktrees/r2-dados`, a partir da base `c00ac5431630c92d30349c13529d5071ad9879b4`. Foram comparadas as versões `96b9dfa920756236b5e81a08e04df2a3e71a4acf` e `9648208b47112fa87a8e584bb30e2779f2449ed8`.

| Inventário | Caminho | IDs | SHA-256 do arquivo | SHA-256 da projeção de IDs e textos |
| --- | --- | --- | --- | --- |
| Histórico | `script/f08/jev/dataset.json` | `jev-001` a `jev-060` (60) | `0e7e4c342c2a39cefd89855d8c0513f447d7878303eb4091488ca8af78928880` | `e7b6af54450e099f5954db7b6cb4204fbf03e16ff9cfc20e0e333150c4118f97` |
| R2 anterior | `docs/planejamento/classificacao-comparativa/r2/final-cases.json` | `r2-001` a `r2-036` (36) | `4f1d712b87bbee326e3602b3fb74398558f929b08c1709b11407676869a21145` | `93ee908d68a99f8b46f070e2b72cfc4a2fc137f26e7cf7f19ace858606a1bb5f` |
| R2 final | `docs/planejamento/classificacao-comparativa/r2/final-cases.json` | `r2-001` a `r2-036` (36) | `17f5bae372983f90aa1956d0d583db25483a77a3ff35e4f1041ad4d51b897af9` | `88b4122e96080de0cddec9536f26ad6960da720c109b396b8e372311bb1fd420` |

O JSON registra o SHA-256 individual de cada texto e os hashes da conferência anterior. A projeção de IDs e textos segue a ordem original dos casos em JSON compacto e UTF-8.

## Método e limites

1. Extraí somente IDs e textos das versões no Git. Os hashes confirmam a preservação do histórico e de 35 textos. Apenas `r2-014` mudou.
2. Recalculei a triagem lexical dos 2.160 pares cruzados, por trigramas de caracteres, cosseno com TF-IDF e maior sequência de palavras em comum. Houve zero duplicatas literais e zero após normalização.
3. Examinei o único caso alterado contra os 60 históricos. A avaliação considera o mecanismo e a sequência factual do caso. A terminologia comum e um nível de impacto semelhante podem ocorrer em casos materialmente diferentes.

A análise qualitativa descreve a similaridade textual e narrativa nestas versões. O procedimento não demonstra a origem da redação nem independência matemática. Rótulos e resultados de modelos ficam fora desta conferência.

## Vereditos consolidados

| ID R2 | Conferência | Veredito | Referências históricas por ID | Motivo |
| --- | --- | --- | --- | --- |
| `r2-001` | Texto preservado | Manter | `jev-055`, `jev-006`, `jev-024` | A dúvida surge do armazenamento do terminal após encerrar a temporada e diz respeito à conservação da bateria por meses. O momento e a ação pedida são diferentes das configurações ou anomalias comparadas. |
| `r2-002` | Texto preservado | Manter | `jev-035`, `jev-009`, `jev-058` | Há descontos identificados em múltiplos créditos, com investigação dos ajustes. O problema de conciliação decorre de retenções registradas, distinto de uma diferença de saldo sem ajuste identificado ou de um crédito faltante. |
| `r2-003` | Texto preservado | Manter | `jev-005`, `jev-042` | O pedido é copiar e divulgar uma chave que já existe, com finalidade específica. As ações históricas comparadas dizem respeito ao cadastro ou à remoção da chave. |
| `r2-004` | Texto preservado | Manter | `jev-034`, `jev-025` | A avaria está na base de recarga e o mesmo equipamento segue operando alimentado diretamente. O efeito e a alternativa de uso distinguem o incidente. |
| `r2-005` | Texto preservado | Manter | `jev-030`, `jev-009` | A conciliação exige separar, por unidade, dinheiro efetivamente agrupado em um único depósito. O critério de separação e a origem da demanda são próprios do relato. |
| `r2-006` | Texto preservado | Manter | `jev-010`, `jev-059`, `jev-021` | Uma cobrança expira na leitura e o pagamento daquele pedido funciona por chave. A falha é localizada e a troca do identificador no mesmo pagamento cria uma contingência específica. |
| `r2-007` | Texto preservado | Manter | `jev-006`, `jev-038`, `jev-026` | O manual explica como repartir o valor da mesma venda entre dois cartões na hora da cobrança. Preparação de treinamento e uso de maquininha são o contexto em comum. A ação comercial é diferente de configuração de visor ou de parcelamento e repasse. |
| `r2-008` | Texto preservado | Manter | `jev-031`, `jev-026`, `jev-049` | A consulta específica é alterar o dia recorrente do crédito. As coincidências de redação tratam de vendas futuras e recebimentos, vocabulário comum do domínio. |
| `r2-009` | Texto preservado | Manter | `jev-033`, `jev-051` | O evento envolve valores errados em transferências de auxílio já feitas e rastreio de devoluções. Causa, fase do fluxo e recomposição são distintos. |
| `r2-010` | Texto preservado | Manter | `jev-012`, `jev-020` | A leitura difícil decorre de pouca luminosidade e é contornada no mesmo visor, com pagamentos aprovados. O modo da falha e o efeito no caixa são próprios. |
| `r2-011` | Texto preservado | Manter | `jev-040`, `jev-050`, `jev-015` | O contato decorre do redirecionamento inesperado de um QR em material de oficina. A pergunta é sobre o destino do código durante uma preparação. |
| `r2-012` | Texto preservado | Manter | `jev-028`, `jev-020`, `jev-052` | A duplicação de uma linha com detalhe inacessível motiva conferência manual localizada. O evento e o alcance operacional distinguem o caso. |
| `r2-013` | Texto preservado | Manter | `jev-057`, `jev-038`, `jev-055` | Silenciar uma unidade de demonstração é uma configuração de áudio própria. O uso de equipamento separado para treinamento é contexto compartilhado. |
| `r2-014` | Nova leitura | Manter | `jev-021`, `jev-017`, `jev-059` | O débito é confirmado, mas o caixa eletrônico não entrega as cédulas de um Pix Saque. A falta do dinheiro físico inviabiliza uma compra com prazo de embarque. O mecanismo de saque e a sequência débito, falha de dispensação e impedimento da compra são distintos dos casos históricos de confirmação de pedido, crédito atrasado ou falha no meio de pagamento do estabelecimento. |
| `r2-015` | Texto preservado | Manter | `jev-054`, `jev-028`, `jev-030` | A ausência de uma coluna em um arquivo de filial, com repasses efetivos e conciliação manual, define uma falha documental diferente. |
| `r2-016` | Texto preservado | Manter | `jev-046`, `jev-056`, `jev-048` | A falha atinge um grupo de leitores após configuração. A operação continua redistribuída entre os equipamentos restantes e a recuperação exige reinstalação por posto. |
| `r2-017` | Texto preservado | Manter | `jev-023`, `jev-060`, `jev-039` | É uma continuação de conversa com referência a um protocolo. O trecho atual indica Pix e deixa o incidente no atendimento anterior. |
| `r2-018` | Texto preservado | Manter | `jev-026`, `jev-054`, `jev-038` | O pedido é interpretar títulos de colunas do calendário para quem fará a cobertura. Consulta de previsão, alteração de datas e acesso a manual são objetivos distintos. |
| `r2-019` | Texto preservado | Manter | `jev-002`, `jev-036`, `jev-047` | A ocorrência é fumaça que persiste perto dos clientes mesmo após desconectar o carregador. O risco em torno do aparelho e a solicitação de encaminhamento dão outro motivo ao contato, diferente de perder a possibilidade de cobrar. |
| `r2-020` | Texto preservado | Manter | `jev-021`, `jev-041`, `jev-001` | A transferência tem comprovante, mas um convênio recusa a despesa por corte do identificador no PDF. O efeito é parar um reembolso administrativo por defeito documental, com resolução pela troca do documento. |
| `r2-021` | Texto preservado | Manter | `jev-016`, `jev-009`, `jev-035` | A conclusão aparente de repasses contrasta com a falta de recebimento por dezenas de destinatários. A estrutura de distribuição e a investigação de retenções por operação dão um recorte próprio à inconsistência. |
| `r2-022` | Texto preservado | Manter | `jev-049`, `jev-037`, `jev-017` | Uma antecipação integral aparece sem solicitação, com confirmação prestes a ocorrer e tarifa que consumiria a verba da folha. A ação indevida é iminente e há uma função de suspensão indisponível. A folha é uma consequência em comum, mas a causa financeira é diferente. |
| `r2-023` | Texto preservado | Manter | `jev-054`, `jev-044`, `jev-020` | O relógio de um terminal desloca a data das vendas embora as autorizações funcionem. Buscar operações por identificador para fechar aquele turno decorre de um problema de fuso no caixa, uma ocorrência diferente de falhas na agenda de créditos ou de impressão. |
| `r2-024` | Texto preservado | Manter | `jev-024`, `jev-029` | O texto acrescenta somente a posição de um ícone em resposta a uma pergunta anterior. A origem e a alteração observada ficam ausentes desse trecho. |
| `r2-025` | Texto preservado | Manter | `jev-033`, `jev-015`, `jev-050` | A finalidade é preparar uma demonstração sobre agendar uma transferência futura. O objetivo da aula e a operação a demonstrar distinguem o pedido. |
| `r2-026` | Texto preservado | Manter | `jev-034`, `jev-012`, `jev-007` | Com uma tela tátil inoperante, o cliente usa teclas físicas do próprio dispositivo. O componente afetado e a forma de concluir a transação são específicos. |
| `r2-027` | Texto preservado | Manter | `jev-009`, `jev-030`, `jev-058` | Um depósito recebido agregou diversas unidades e exige reconstruir os créditos por extrato. A agregação inesperada e a dimensão por unidade definem o problema. |
| `r2-028` | Texto preservado | Manter | `jev-032`, `jev-051`, `jev-031` | O destino de repasses automáticos deixou de pertencer à associação. Origem, troca de titularidade e fila de depósitos distinguem esta rota incorreta das cobranças e devoluções comparadas. |
| `r2-029` | Texto preservado | Manter | `jev-011`, `jev-055`, `jev-006` | A consulta é instalar um terminal sem cabo de rede antes da abertura de um ponto em obra. A dúvida de infraestrutura se distingue das configurações e falhas em operação. |
| `r2-030` | Texto preservado | Manter | `jev-033` | A edição da próxima data de uma única série de pagamentos a prestador deixa a programação antiga visível. O negócio suspende só essa série e assume manualmente o pagamento. Há tema comum de agenda Pix, com outra etapa afetada, outro sentido da transação e outra contingência. |
| `r2-031` | Texto preservado | Manter | `jev-020`, `jev-048`, `jev-057` | A impressora sofre contaminação por resíduo de bobina em muitos dispositivos. A via digital preserva a emissão e o trabalho pendente é limpeza física em rodízio. Compartilha o sintoma de impressão com um relato antigo, porém tem causa, operação alternativa e recuperação próprias. |
| `r2-032` | Texto preservado | Manter | `jev-059`, `jev-010`, `jev-018` | A falha ocorre no Pix enviado a um único destinatário, impede o pagamento de caução e ameaça a reserva de horário. A transação, a parte afetada e a perda iminente compõem um cenário próprio. |
| `r2-033` | Texto preservado | Manter | `jev-016`, `jev-004`, `jev-058` | O dinheiro já entrou, mas um estado incorreto bloqueia a conciliação automática. Registrar o valor no fechamento trata uma inconsistência de controle depois do crédito, diferente dos cenários de crédito ausente. |
| `r2-034` | Texto preservado | Manter | `jev-027`, `jev-002`, `jev-047` | O bloqueio de acesso ocorre antes das funções do painel e paralisa a equipe. A causa imediata difere das falhas nas formas de cobrança e dos problemas nos equipamentos. |
| `r2-035` | Texto preservado | Manter | `jev-015`, `jev-038`, `jev-057` | A solicitação é localizar um menu visto em uma apresentação para repetir a navegação num curso. Preparação de treinamento e operação normal são o contexto em comum. |
| `r2-036` | Texto preservado | Manter | `jev-028`, `jev-024`, `jev-039` | O texto parcial de um aviso temporário foi recuperado e o contato é continuação em outro canal. A operação subjacente e as consequências não aparecem no relato. |
