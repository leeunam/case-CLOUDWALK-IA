# C05-R2 · Conferência de similaridade

Dos 36 relatos finais congelados, 26 podem ser mantidos e 10 pedem substituição. A comparação com os 60 relatos históricos cobriu 2.160 pares e encontrou zero duplicatas textuais, tanto na redação original quanto na forma normalizada.

**Status** · Pendente de substituição e nova conferência do conjunto atualizado.

**IDs para substituição** · `r2-001`, `r2-007`, `r2-014`, `r2-019`, `r2-020`, `r2-022`, `r2-023`, `r2-030`, `r2-031`, `r2-033`.

A revisão foi conduzida pelo conferente independente de similaridade, fora da autoria, da frente de prompt e da revisão dos rótulos.

## Inventários

A conferência usa a branch `docs/r2-protocolo-dados` em `.worktrees/r2-dados`, com base `c00ac5431630c92d30349c13529d5071ad9879b4` e candidata `29973d74209796c54076fcaf9348c14a37ab1743`.

| Inventário | IDs | SHA-256 do arquivo | SHA-256 da projeção de IDs e textos |
| --- | --- | --- | --- |
| `script/f08/jev/dataset.json` | `jev-001` a `jev-060` (60) | `0e7e4c342c2a39cefd89855d8c0513f447d7878303eb4091488ca8af78928880` | `e7b6af54450e099f5954db7b6cb4204fbf03e16ff9cfc20e0e333150c4118f97` |
| `docs/planejamento/classificacao-comparativa/r2/final-cases.json` | `r2-001` a `r2-036` (36) | `de29a2de28e9b643dfe82eff97ef54263afa3eca7ad0b8642f5c3fc4ee22d4b8` | `1d6db8ddc0604f27b08979fbab40ea7ed0ecd33dd884c71505d662dc1d007aec` |

O relatório JSON contém cada ID e o SHA-256 do respectivo texto original decodificado em UTF-8. O hash da projeção usa uma lista de objetos com `id` seguido de `text`, na ordem do arquivo, em JSON UTF-8 com caracteres literais, separadores compactos e sem quebra final.

## Método e limites

1. Extraí os campos `id` e `text` de cada relato. Conferi a igualdade literal e após normalização por `casefold`, decomposição NFKD, remoção de marcas combinantes e junção de sequências alfanuméricas por um espaço.
2. Comparei todos os pares cruzados por Dice de trigramas de caracteres, cosseno de palavras ponderadas por TF-IDF e maior sequência contígua de palavras em comum. As pontuações serviram para localizar pares para leitura qualitativa.
3. Li os 96 relatos e examinei os cenários mais próximos para cada novo ID, incluindo coincidências semânticas com pouca sobreposição lexical. Comparei o evento ou pedido específico, seu mecanismo, seu efeito operacional e as alternativas mencionadas. Uma paráfrase do mesmo pedido ou a repetição de uma combinação característica de circunstâncias motivou substituição. Termos, padrões de atendimento e temas comuns ao domínio tiveram peso apenas quando faziam parte dessa combinação específica.

Os maiores resultados lexicais foram 0.437 em Dice e 0.288 em cosseno. A maior sequência compartilhada teve 4 palavras. A revisão identificou 4 paráfrases semânticas e 6 sobreposições de cenário.

O veredito descreve proximidade textual e narrativa entre as versões identificadas e depende de julgamento qualitativo. Ele não demonstra como os casos foram escritos e não estabelece independência matemática. Rótulos e saídas dos modelos ficam fora desta conferência.

## Vereditos por relato

| ID R2 | Veredito | Tipo de achado | Referências históricas por ID | Motivo |
| --- | --- | --- | --- | --- |
| `r2-001` | Substituir | Paráfrase semântica | `jev-019` | A solicitação específica permanece a personalização do nome impresso no comprovante da maquininha. A finalidade do nome e o uso de um equipamento reserva mudam o entorno, mas o pedido central é o mesmo. |
| `r2-002` | Manter | Diferença material | `jev-035`, `jev-009`, `jev-058` | Há descontos identificados em múltiplos créditos, com investigação dos ajustes. O problema de conciliação decorre de retenções registradas, distinto de uma diferença de saldo sem ajuste identificado ou de um crédito faltante. |
| `r2-003` | Manter | Diferença material | `jev-005`, `jev-042` | O pedido é copiar e divulgar uma chave que já existe, com finalidade específica. As ações históricas comparadas dizem respeito ao cadastro ou à remoção da chave. |
| `r2-004` | Manter | Diferença material | `jev-034`, `jev-025` | A avaria está na base de recarga e o mesmo equipamento segue operando alimentado diretamente. O efeito e a alternativa de uso distinguem o incidente. |
| `r2-005` | Manter | Diferença material | `jev-030`, `jev-009` | A conciliação exige separar, por unidade, dinheiro efetivamente agrupado em um único depósito. O critério de separação e a origem da demanda são próprios do relato. |
| `r2-006` | Manter | Diferença material | `jev-010`, `jev-059`, `jev-021` | Uma cobrança expira na leitura e o pagamento daquele pedido funciona por chave. A falha é localizada e a troca do identificador no mesmo pagamento cria uma contingência específica. |
| `r2-007` | Substituir | Paráfrase semântica | `jev-006` | Repete a consulta de acessibilidade para ampliar a exibição de uma maquininha nova antes de usá-la no balcão. O local e a justificativa mudam, e a ação solicitada se mantém. |
| `r2-008` | Manter | Diferença material | `jev-031`, `jev-026`, `jev-049` | A consulta específica é alterar o dia recorrente do crédito. As coincidências de redação tratam de vendas futuras e recebimentos, vocabulário comum do domínio. |
| `r2-009` | Manter | Diferença material | `jev-033`, `jev-051` | O evento envolve valores errados em transferências de auxílio já feitas e rastreio de devoluções. Causa, fase do fluxo e recomposição são distintos. |
| `r2-010` | Manter | Diferença material | `jev-012`, `jev-020` | A leitura difícil decorre de pouca luminosidade e é contornada no mesmo visor, com pagamentos aprovados. O modo da falha e o efeito no caixa são próprios. |
| `r2-011` | Manter | Diferença material | `jev-040`, `jev-050`, `jev-015` | O contato decorre do redirecionamento inesperado de um QR em material de oficina. A pergunta é sobre o destino do código durante uma preparação. |
| `r2-012` | Manter | Diferença material | `jev-028`, `jev-020`, `jev-052` | A duplicação de uma linha com detalhe inacessível motiva conferência manual localizada. O evento e o alcance operacional distinguem o caso. |
| `r2-013` | Manter | Diferença material | `jev-057`, `jev-038`, `jev-055` | Silenciar uma unidade de demonstração é uma configuração de áudio própria. O uso de equipamento separado para treinamento é contexto compartilhado. |
| `r2-014` | Substituir | Cenário sobreposto | `jev-003`, `jev-051`, `jev-052` | A sequência de três saídas por Pix e uma quarta que aparece durante a escrita coincide com um cenário histórico de débito inesperado em andamento. A origem relatada muda e a progressão específica permanece. |
| `r2-015` | Manter | Diferença material | `jev-054`, `jev-028`, `jev-030` | A ausência de uma coluna em um arquivo de filial, com repasses efetivos e conciliação manual, define uma falha documental diferente. |
| `r2-016` | Manter | Diferença material | `jev-046`, `jev-056`, `jev-048` | A falha atinge um grupo de leitores após configuração. A operação continua redistribuída entre os equipamentos restantes e a recuperação exige reinstalação por posto. |
| `r2-017` | Manter | Diferença material | `jev-023`, `jev-060`, `jev-039` | É uma continuação de conversa com referência a um protocolo. O trecho atual indica Pix e deixa o incidente no atendimento anterior. |
| `r2-018` | Manter | Diferença material | `jev-026`, `jev-054`, `jev-038` | O pedido é interpretar títulos de colunas do calendário para quem fará a cobertura. Consulta de previsão, alteração de datas e acesso a manual são objetivos distintos. |
| `r2-019` | Substituir | Paráfrase semântica | `jev-036`, `jev-002`, `jev-047` | A combinação de único leitor apagado, evento em curso, público na fila e impossibilidade de receber por outro meio reproduz um cenário antigo. O tipo de ponto de venda muda o cenário de fundo. |
| `r2-020` | Substituir | Cenário sobreposto | `jev-021` | O núcleo é um Pix recebido com comprovante cuja confirmação do pedido fica ausente, enquanto pedidos comparáveis seguem normais. Repetição num guichê e baixa manual ampliam o mesmo mecanismo central. |
| `r2-021` | Manter | Diferença material | `jev-016`, `jev-009`, `jev-035` | A conclusão aparente de repasses contrasta com a falta de recebimento por dezenas de destinatários. A estrutura de distribuição e a investigação de retenções por operação dão um recorte próprio à inconsistência. |
| `r2-022` | Substituir | Cenário sobreposto | `jev-018`, `jev-017`, `jev-037` | A falta de crédito das vendas ameaça impedir a retirada de mercadoria em poucos minutos e falta reserva para cumprir a obrigação. A combinação de causa, consequência e contingência se repete. |
| `r2-023` | Substituir | Cenário sobreposto | `jev-007`, `jev-046`, `jev-056` | A falha específica de leitura de chip em uma bancada, com desvio para outra bancada para manter vendas, coincide com um cenário histórico. A aproximação na unidade afetada acrescenta uma alternativa ao mesmo incidente. |
| `r2-024` | Manter | Diferença material | `jev-024`, `jev-029` | O texto acrescenta somente a posição de um ícone em resposta a uma pergunta anterior. A origem e a alteração observada ficam ausentes desse trecho. |
| `r2-025` | Manter | Diferença material | `jev-033`, `jev-015`, `jev-050` | A finalidade é preparar uma demonstração sobre agendar uma transferência futura. O objetivo da aula e a operação a demonstrar distinguem o pedido. |
| `r2-026` | Manter | Diferença material | `jev-034`, `jev-012`, `jev-007` | Com uma tela tátil inoperante, o cliente usa teclas físicas do próprio dispositivo. O componente afetado e a forma de concluir a transação são específicos. |
| `r2-027` | Manter | Diferença material | `jev-009`, `jev-030`, `jev-058` | Um depósito recebido agregou diversas unidades e exige reconstruir os créditos por extrato. A agregação inesperada e a dimensão por unidade definem o problema. |
| `r2-028` | Manter | Diferença material | `jev-032`, `jev-051`, `jev-031` | O destino de repasses automáticos deixou de pertencer à associação. Origem, troca de titularidade e fila de depósitos distinguem esta rota incorreta das cobranças e devoluções comparadas. |
| `r2-029` | Manter | Diferença material | `jev-011`, `jev-055`, `jev-006` | A consulta é instalar um terminal sem cabo de rede antes da abertura de um ponto em obra. A dúvida de infraestrutura se distingue das configurações e falhas em operação. |
| `r2-030` | Substituir | Paráfrase semântica | `jev-041` | Uma devolução por Pix de um único pedido falha no aplicativo e as demais seguem normalmente. A possibilidade de resolver pelo caixa acrescenta uma contingência ao mesmo evento e recorte. |
| `r2-031` | Substituir | Cenário sobreposto | `jev-048`, `jev-056` | Uma atualização desativa em várias lojas uma função específica da maquininha. Vendas continuam pelo caminho padrão e sobra retrabalho disseminado. O recurso afetado e o objeto do retrabalho mudam dentro da mesma sequência. |
| `r2-032` | Manter | Diferença material | `jev-059`, `jev-010`, `jev-018` | A falha ocorre no Pix enviado a um único destinatário, impede o pagamento de caução e ameaça a reserva de horário. A transação, a parte afetada e a perda iminente compõem um cenário próprio. |
| `r2-033` | Substituir | Cenário sobreposto | `jev-004`, `jev-008`, `jev-045`, `jev-058` | Um conjunto pequeno de vendas específicas fica fora do depósito esperado, com os demais créditos recebidos e a operação mantida. Tipo e quantidade de vendas variam, e a combinação do evento e de seu alcance se repete. |
| `r2-034` | Manter | Diferença material | `jev-027`, `jev-002`, `jev-047` | O bloqueio de acesso ocorre antes das funções do painel e paralisa a equipe. A causa imediata difere das falhas nas formas de cobrança e dos problemas nos equipamentos. |
| `r2-035` | Manter | Diferença material | `jev-015`, `jev-038`, `jev-057` | A solicitação é localizar um menu visto em uma apresentação para repetir a navegação num curso. Preparação de treinamento e operação normal são o contexto em comum. |
| `r2-036` | Manter | Diferença material | `jev-028`, `jev-024`, `jev-039` | O texto parcial de um aviso temporário foi recuperado e o contato é continuação em outro canal. A operação subjacente e as consequências não aparecem no relato. |

Para encaminhamento à autoria, use somente os novos IDs sinalizados e o pedido de outros cenários. Os pareamentos históricos ficam no registro da conferência.
