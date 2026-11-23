# C01 — revisão dos rótulos sob delegação

Estado: **60 casos revisados para referência exploratória**: oito com aprovação
direta do responsável (dez decisões de campo) e 52 com revisão/aprovação da IA
sob delegação explícita (70 decisões de campo). Nenhum rótulo foi alterado.
A revisão caso a caso está concluída; C01 continua em andamento e C02 ainda
não foi liberada.

Fonte: [dataset de 60 relatos](../../../script/f08/jev/dataset.json), versão
1.1.0, SHA-256
`0e7e4c342c2a39cefd89855d8c0513f447d7878303eb4091488ca8af78928880`.
O dataset e os relatórios históricos F08 permanecem inalterados. O metadado
`review: provisional` do formato legado é preservado; a origem e o estado desta
revisão estão no [registro estruturado](revisao-de-rotulos.json).

## Delegação e alcance

Em 2026-11-23, após aprovar oito casos individualmente, o responsável pediu:
“tem como skippar todos os 60 casos e vocÊ aprovar?”. Essa instrução delega a
revisão restante ao integrador IA e substitui a exigência anterior de revisão
humana individual dos 60 exemplos. Duas frentes revisaram os 52 casos restantes,
e o integrador leu e consolidou as recomendações usando os critérios discutidos.

O conjunto é uma referência sintética exploratória. Os 52 casos delegados não
possuem validação humana independente; essa limitação acompanha a comparação.
A delegação não aprova orçamento, vencedor, protocolo completo ou divisão dos
exemplos entre desenvolvimento e teste. As escolhas não foram obtidas de
respostas dos candidatos Qwen ou GLiClass.

## Aprovações diretas anteriores, preservadas

| Caso | Campo ausente | Rótulo esperado aprovado | Justificativa | Origem da aprovação |
| --- | --- | --- | --- | --- |
| jev-001 | category | informacao_insuficiente | Pagamento por QR não identifica, sozinho, o meio de pagamento. | Aprovação anterior do responsável, já registrada na CLASS-SPEC-001. |
| jev-041 | priority | informacao_insuficiente | O relato de reembolso Pix não informa prazo nem impacto suficientes para decidir prioridade. | Aprovação anterior do responsável, já registrada na CLASS-SPEC-001. |
| jev-002 | priority | urgent | Toda a cobrança está interrompida durante a operação e não há alternativa. | Chat central, 2026-11-23: responsável concordou com o bloco 002/005/044. |
| jev-005 | priority | basic | Pedido de orientação para uso futuro, sem falha operacional atual relatada. | Chat central, 2026-11-23: responsável concordou com o bloco 002/005/044. |
| jev-044 | priority | informacao_insuficiente | Faltam prazo e impacto para determinar a prioridade da mudança na agenda. | Chat central, 2026-11-23: responsável concordou com o bloco 002/005/044. |
| jev-003 | category | pix | O relato identifica explicitamente transferências por Pix. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |
| jev-003 | priority | urgent | Há transferências não autorizadas em andamento e necessidade de intervenção imediata. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |
| jev-008 | priority | intermediate | O atraso afeta uma venda pequena e o cliente consegue manter a operação e pagar as despesas de hoje. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |
| jev-009 | category | payouts | A divergência está na agenda de recebimento das vendas a crédito. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |
| jev-009 | priority | advanced | A divergência abrange metade das vendas, mas há caixa para operar pelos próximos dias. | Chat central, 2026-11-23: responsável respondeu "sim" ao bloco 008/009/003. |


## Revisão delegada à IA

Cada linha aprova apenas os campos ausentes. Os valores válidos recebidos do
canal permanecem preservados. Justificativas e ressalvas estão registradas por
caso aqui e no JSON.

| Caso | Rótulos esperados mantidos | Justificativa da revisão | Ressalvas |
| --- | --- | --- | --- |
| jev-004 | category=payouts | A informação ausente é o assunto da solicitação: o lote de uma venda no crédito não apareceu na conta, embora os demais tenham aparecido. Isso descreve recebimento/liquidação de venda. | Sem ressalva adicional. |
| jev-006 | category=terminal, priority=basic | Aumentar a letra da tela é uma configuração da maquininha. O equipamento ainda será colocado no balcão e não há falha ou prejuízo atual relatado, compatível com orientação básica. | Sem ressalva adicional. |
| jev-007 | category=terminal | O leitor de cartão da maquininha não reconhece chip; a prioridade avançada já foi fornecida pelo canal e não foi avaliada aqui. | Sem ressalva adicional. |
| jev-010 | category=pix | O texto identifica pagamentos por Pix e falhas nos códigos de cobrança. A prioridade urgente já veio do canal e não foi avaliada aqui. | Sem ressalva adicional. |
| jev-011 | priority=intermediate | A conexão da maquininha falha intermitentemente, gerando repetição de cobranças, enquanto outro caixa funciona. Há impacto moderado com alternativa operacional. | Sem ressalva adicional. |
| jev-012 | category=terminal, priority=intermediate | O visor lento e a repetição de cobranças apontam para a maquininha. O segundo equipamento mantém as vendas; o retrabalho sugere impacto moderado. | Sem ressalva adicional. |
| jev-013 | category=informacao_insuficiente | A descrição vaga de dinheiro passado pelo aparelho e exibido no aplicativo não distingue transação no terminal, Pix ou liquidação de venda. | A expressão 'passou pelo aparelho' pode sugerir cartão, mas o percurso e o problema não estão especificados o bastante para fixar a categoria. |
| jev-014 | priority=advanced | As cobranças Pix falham para quase todos os clientes e há perda relevante de vendas, mas o recebimento por cartão continua disponível; isso é impacto significativo sem interrupção total. | O texto não informa duração prevista nem quantifica 'boa parte'; a classificação como avançado pressupõe que a perda descrita seja relevante. |
| jev-015 | category=informacao_insuficiente, priority=basic | O relato pede um histórico de uma operação sem identificar qual tipo; treinamento e funcionamento normal sustentam prioridade básica. | Sem ressalva adicional. |
| jev-016 | category=payouts | A solicitação trata de lote de vendas marcado como pago que não apareceu no extrato bancário, assunto de recebimento/liquidação. A prioridade avançada já foi fornecida pelo canal e não foi avaliada aqui. | Sem ressalva adicional. |
| jev-017 | priority=urgent | Nenhum recebimento caiu, a conta está sem saldo e há consequência iminente nesta manhã se o pagamento não for feito. A necessidade de ação imediata atende ao critério de urgente. | A urgência depende do prazo explícito do fornecedor nesta manhã; não é inferida apenas do montante ou da falta de saldo. |
| jev-018 | category=payouts, priority=urgent | O lote de vendas não caiu antes da abertura e o fornecedor está presente, com consequência imediata caso não haja pagamento. O assunto é liquidação de vendas e o prazo sustenta urgência. | A mensagem não declara expressamente que não existe outra fonte de pagamento; a urgência é sustentada pela condição imediata do fornecedor, sem afirmar a inexistência de alternativas. |
| jev-019 | category=terminal | A alteração desejada é o nome impresso no comprovante do aparelho de cartão, uma configuração da maquininha. A prioridade básica já foi fornecida pelo canal e não foi avaliada aqui. | Sem ressalva adicional. |
| jev-020 | priority=advanced | Duas maquininhas deixaram de imprimir comprovantes e o fechamento terá retrabalho considerável, mas as vendas continuam. O efeito é relevante sem bloquear a operação. | Sem ressalva adicional. |
| jev-021 | category=pix, priority=intermediate | O cliente pagou por Pix, mas a confirmação de um pedido está pendente; os demais pedidos passam. A categoria é Pix e o problema localizado, com operação em geral disponível, é compatível com impacto moderado. | Não há informação sobre valor, duração ou se o pedido específico ficou bloqueado; a prioridade intermediária é plausível, mas a evidência de impacto é limitada. |
| jev-022 | category=pix | A pergunta é sobre um Pix enviado ao telefone antigo e a devolução ao banco de origem. A prioridade intermediária já foi fornecida pelo canal e não foi avaliada aqui. | Sem ressalva adicional. |
| jev-023 | priority=informacao_insuficiente | 'Não está do jeito de sempre' não informa estado, alcance nem consequência. Não há base para escolher nível de urgência. | Sem ressalva adicional. |
| jev-024 | category=terminal, priority=informacao_insuficiente | Código após atualização identifica assunto da maquininha. Como o cliente não sabe se ela ainda aceita cartão, o impacto operacional permanece desconhecido e a prioridade deve abster-se. | Sem ressalva adicional. |
| jev-025 | category=terminal | O teclado travado é de uma maquininha e nenhum cartão passa. A prioridade urgente já veio do canal e não foi avaliada aqui. | Sem ressalva adicional. |
| jev-026 | priority=basic | É uma consulta para planejamento do próximo trimestre sobre datas habituais de recebimento, sem atraso atual ou prejuízo relatado. | Sem ressalva adicional. |
| jev-027 | category=informacao_insuficiente, priority=urgent | Cobranças e recebimentos sumiram da tela, sem causa de domínio suficiente para distinguir Pix, repasse ou terminal; contudo, ambas as unidades foram fechadas por impossibilidade de pagamento, evidência forte de interrupção imediata. | A causa da interrupção permanece desconhecida; isso sustenta abstenção de categoria, sem impedir reconhecer o impacto urgente. |
| jev-028 | category=informacao_insuficiente | O relato refere-se apenas a 'uma operação' sem identificar se é Pix, recebimento ou terminal. A prioridade avançada já foi fornecida pelo canal e não foi avaliada aqui. | Sem ressalva adicional. |
| jev-029 | priority=informacao_insuficiente | Uma luz diferente, sem venda de teste nem falha observada, não demonstra prejuízo nem urgência. Não há base para inferir prioridade. | Sem ressalva adicional. |
| jev-030 | category=payouts, priority=basic | A consulta é sobre separar vendas conforme o dia de depósito, portanto liquidação/repasse. Os recebimentos ocorreram normalmente e o pedido é apenas de relatório, compatível com básico. | Sem ressalva adicional. |
| jev-031 | category=payouts | A solicitação trata de escolher a conta que receberá vendas futuras; isso pertence a repasse/liquidação. Os recebimentos atuais estão corretos. | Sem ressalva adicional. |
| jev-032 | priority=urgent | Pagamentos continuam sendo desviados para outra conta e o cliente precisa suspender cobranças imediatamente; há possível prejuízo em curso. | O texto aponta para ação imediata, mas não explicita se o mecanismo de suspensão está disponível ao cliente. |
| jev-033 | category=pix, priority=advanced | O fluxo é de cobranças por Pix. A correção abrange todos os contratos, mas o envio foi pausado e boletos seguem disponíveis, permitindo resolver sem interrupção imediata. | A expressão 'todos os contratos' indica abrangência alta; avançado é plausível dado que existe alternativa e a falha está pausada. |
| jev-034 | category=terminal | O botão físico afundou em um leitor de cartão; isso é defeito de maquininha. O balcão continua atendendo com outro leitor. | Sem ressalva adicional. |
| jev-035 | priority=advanced | A diferença em todo o lote é grande, caracterizando impacto relevante. A reserva cobre os compromissos da semana, então o texto não indica necessidade de ação imediata. | O caso não informa se há prazo para contestar a diferença; a categoria avançado é razoável conforme a definição atual, mas esse sinal pode ser útil na rubrica final. |
| jev-036 | category=terminal, priority=urgent | A única leitora apagou, não há alternativa de pagamento e o caixa parou durante uma feira; a categoria é maquininha e a interrupção exige ação imediata. | Sem ressalva adicional. |
| jev-037 | category=payouts | As vendas foram autorizadas; o dinheiro está ausente na liquidação dos lotes, que é assunto de repasses. A prioridade urgente já veio do canal e deve ser preservada. | A prioridade recebida não foi reavaliada nesta revisão, que cobre somente o campo ausente. |
| jev-038 | priority=basic | O leitor funciona e a pessoa quer exportar o manual para treinar um turno novo; é uma orientação de rotina sem prejuízo atual. | Sem ressalva adicional. |
| jev-039 | category=informacao_insuficiente, priority=informacao_insuficiente | 'Aquele negócio no canto' não identifica o produto nem relata impacto ou urgência; faltam evidências para ambos os campos. | A frase depende de contexto visual compartilhado que não existe no relato recebido. |
| jev-040 | category=pix | O cliente pergunta sobre gerar um QR Pix de valor livre para recebimento futuro; o assunto é Pix. | Sem ressalva adicional. |
| jev-042 | category=pix, priority=basic | Remover uma chave Pix antiga é assunto Pix. A chave atual segue funcionando, então é manutenção sem impacto operacional, compatível com básico. | Sem ressalva adicional. |
| jev-043 | category=informacao_insuficiente | Uma repetição que depois funcionou não esclarece se a origem foi o terminal, Pix ou liquidação; categoria insuficiente é apropriada. A prioridade intermediária fornecida é preservada. | O usuário pergunta qual componente falhou; uma pergunta de esclarecimento pode resolver a categoria. |
| jev-045 | category=payouts, priority=intermediate | A parcela ausente é de uma venda já realizada, portanto assunto de liquidação. É uma divergência isolada e os outros lotes cobrem o caixa, compatível com impacto moderado. | Sem ressalva adicional. |
| jev-046 | category=terminal | A aproximação falha em parte das maquininhas, enquanto inserir o cartão continua possível; categoria maquininha. A prioridade avançada recebida é preservada. | O relato informa queda significativa no fluxo, mas a revisão do campo ausente não altera a prioridade fornecida. |
| jev-047 | priority=urgent | O único equipamento trava antes de concluir pagamentos durante o evento; todo o caixa está parado e não há método alternativo, exigindo ação imediata. | Sem ressalva adicional. |
| jev-048 | category=terminal, priority=advanced | A função desativada pertence às leitoras. A venda padrão segue, mas reservas de toda a rede precisarão ser reprocessadas, impacto amplo sem urgência imediata. | A abrangência é alta, mas uma via de venda permanece disponível. |
| jev-049 | category=payouts | Antecipar parcelas de vendas é assunto de recebíveis e liquidação. Nenhum atraso foi relatado. | Sem ressalva adicional. |
| jev-050 | priority=basic | A dúvida é sobre reutilizar um QR de cobrança no futuro, antes do início das vendas; não há prejuízo atual, compatível com orientação básica. | Sem ressalva adicional. |
| jev-051 | category=pix, priority=urgent | A devolução duplica em cada tentativa por Pix e a automação continua reduzindo o saldo; há perda ativa que exige interrupção imediata. | Sem ressalva adicional. |
| jev-052 | category=pix | As devoluções não autorizadas que continuam entrando são por Pix; o campo urgente recebido pelo canal é preservado. | A prioridade fornecida não foi reavaliada nesta revisão. |
| jev-053 | priority=intermediate | Dois créditos atrasaram um dia, mas o comércio continua aberto e apenas uma compra menor foi adiada; impacto localizado e operação disponível. | Sem ressalva adicional. |
| jev-054 | category=payouts, priority=informacao_insuficiente | A mudança ocorreu na agenda de repasses, identificando a categoria. Como o cliente não sabe se algo venceu e não informa impacto, a prioridade não pode ser determinada. | Sem ressalva adicional. |
| jev-055 | category=terminal | Ajustar o tempo de bloqueio de tela em uma maquininha reserva é configuração do terminal. A prioridade básica veio do canal e é preservada. | A prioridade fornecida não foi reavaliada nesta revisão. |
| jev-056 | priority=advanced | A falha afeta a aproximação em todas as leitoras e prejudica compras corporativas, mas chip e link mantêm vendas; impacto relevante sem paralisação total. | Sem ressalva adicional. |
| jev-057 | category=terminal, priority=basic | Habilitar comprovante por mensagem na maquininha de treinamento é configuração do terminal. A leitora do caixa funciona, sem prejuízo atual. | Sem ressalva adicional. |
| jev-058 | category=payouts | A venda já foi dividida e o problema é que uma parte não aparece no extrato, portanto recebimento/liquidação. A prioridade intermediária recebida fica intacta. | A prioridade fornecida não foi reavaliada nesta revisão. |
| jev-059 | priority=urgent | Todos os pagamentos Pix falham e a retirada de pedidos está interrompida sem alternativa, exigindo ação imediata. | Sem ressalva adicional. |
| jev-060 | category=pix, priority=informacao_insuficiente | A mensagem é explicitamente sobre Pix; não se sabe se houve débito ou nova tentativa, então o impacto/prioridade é insuficiente. | Sem ressalva adicional. |

## Consolidação e limitações

Os rótulos foram mantidos nos 52 casos delegados. As ressalvas registram limites
do texto, especialmente no caso 021: há um problema localizado de confirmação,
mas valor, duração e bloqueio do pedido não são explícitos. A prioridade
intermediária é uma referência plausível sob a régua atual, com evidência limitada;
seu acerto isolado não sustenta conclusão de qualidade operacional. Ausência de
uma informação não autoriza afirmar que ela existe: por exemplo, a urgência de
018 é sustentada pelo prazo imediato, sem presumir inexistência de outros meios.

A classificação básica exige um pedido de orientação/manutenção e evidência de
uso futuro ou funcionamento preservado; simples ausência de detalhes não basta.
Urgência considera necessidade imediata, como perda em curso ou interrupção sem
alternativa. Os casos previamente aprovados ilustram essa interpretação. A rubrica
operacional final ainda será congelada na C01.

## Pendências antes do protocolo final

- Detalhar e congelar a rubrica e a informação comum fornecida aos candidatos.
- Separar desenvolvimento/calibração e teste final antes de usar exemplos em prompts.
- Definir critérios de escolha, schema/fixtures e limites de execução conforme
  a [C01](cards/C01-protocolo.md).
- Manter os rótulos fixos durante o teste final e declarar a origem da revisão.

Nenhum caso deste conjunto foi enviado a Qwen ou GLiClass nesta revisão.
