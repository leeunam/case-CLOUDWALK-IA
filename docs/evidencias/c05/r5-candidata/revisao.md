# R5-A · Revisão independente da candidata

**SPEC — requer correção. QUALITY — requer correção.** O motor comum aplicou três tipos de decisão sem suporte em exemplos novos. O replay também aceitou um envelope que declara ter recebido resposta sem ter feito uma requisição. Recomendo uma rodada dirigida de correção e rechecagem antes de congelar a candidata.

Base `0b0223eb2fc8d258c7e0351212b0b22959c05697`, commit `065deee14b03e350a4d96a360cdca47b477519cd`, branch `feat/luna-evidencias-r5`, worktree `.worktrees/r5-luna-evidencias`. Revisão focal da tarefa A em 25/11/2026. Zero inferências, rede, credenciais ou SQLite. Os textos abaixo são artificiais. Uma busca de símbolos ampla exibiu referências e metadados de artefatos históricos. Nenhum relato, rótulo ou resultado de avaliação final foi usado nas verificações ou nos achados. O material sintetizado pelo integrador antecede a leitura desta implementação.

## Achados para uma rodada de correção

Os números de linha são do commit acima. Os nomes curtos dos arquivos apontam para `script/classification_comparison/adapters/luna/r5/`. Para reproduzir os exemplos, construa um item de `test_evidence.item` com só o campo em questão faltando, devolva `response({campo: prediction(código, critério, citação)})` pelo `Gateway` local e chame `R5Adapter.classify`, `replay_envelope` e `common.decide`. Os demais campos são os valores válidos oferecidos pelo helper. Exceto onde indicado, a citação é o texto todo. Cada falso positivo abaixo retornou `accepted/supported_relation`, `predicted` e decisão `complete`.

### P1 · Consequência negada ou já atendida é aceita como urgente

`evidence.py:282`, `:289`, `:331` e `:340`. A ocorrência de “multa” perto de “hoje” basta para formar uma consequência imediata. “Não há multa hoje. Quero apenas uma orientação para fechar o caixa.” e “Consigo pagar a multa hoje com tranquilidade.” foram aceitos como `urgent/immediate_harm`. A primeira frase nega a consequência e a segunda afirma que o cliente consegue lidar com ela. Em outro caminho, “Nenhuma venda passa. Não temos outra forma de receber. Mas agora sigo vendendo pelo celular sem atraso.”, com citação “Nenhuma venda passa.”, aceitou a urgência apesar da alternativa atual. Preservar urgências sustentadas por perda presente, paralisação sem alternativa e prazo com consequência, e vetar escolhas contrariadas pelo texto inteiro.

### P1 · A pergunta de rotina pode rebaixar prejuízo atual

`evidence.py:268`, `:291` e `:352`. “Como posso configurar a maquininha? Todos os clientes são debitados duas vezes a cada tentativa agora.”, com citação apenas “Como posso configurar a maquininha?”, terminou com `basic/routine` aplicado. O relato declara cobrança repetida em andamento para todos. A leitura de contexto não sinaliza esse dano e a pergunta de configuração basta para liberar rotina. A mesma família apareceu no cenário independente 9, que vetou a urgência correta. A correção deve sobretudo impedir o rebaixamento mesmo quando não houver evidência local suficiente para confirmar outra prioridade. Uma orientação genuína com funcionamento preservado deve continuar elegível.

### P1 · Negação direta e coocorrência podem confirmar assunto incorreto

`evidence.py:45`, `:97`, `:113` e `:175`. Os padrões usam palavras próximas ou uma ação genérica. A lista de exclusões não cobre “não quero” seguido diretamente do verbo de operação. Cada uma das frases abaixo foi aceita, embora o pedido trate de outro objeto.

| Escolha proposta | Relato artificial |
| --- | --- |
| `pix/pix_operation` | Não quero fazer um Pix. Preciso atualizar meu endereço. |
| `terminal/terminal_operation` | Não quero configurar a maquininha. Preciso atualizar meu endereço. |
| `payouts/sales_settlement` | Não quero consultar o valor das vendas. Preciso atualizar meu endereço. |
| `pix/pix_operation` | O adesivo do Pix não chegou pelo correio. Quero uma segunda via do adesivo. |
| `terminal/terminal_operation` | A etiqueta da maquininha não chegou pelos correios. |
| `payouts/sales_settlement` | Quando vendi a débito o cupom saiu ilegível. Como peço uma segunda via? |

Nos dois relatos de correio, a falha é da entrega física. No último, “quando” situa a impressão do cupom no tempo e o relato não menciona recebimento de vendas. A correção deve exigir o vínculo entre ação e objeto, e distinguir a exclusão de um assunto da falha afirmada da operação. Os positivos de Pix/chave, repasse não creditado e equipamento sem impressão são controles de regressão. Um novo pedido de outro assunto, mesmo sem “minha dúvida é”, também merece veto conservador quando deixa o foco ambíguo.

### P2 · Replay aprova resposta de fornecedor com zero despachos

`adapter.py:72` e `:92`. Parta de um envelope aceito para “Como consultar um Pix?”. Mantenha o texto bruto, o modelo retornado, o motivo de término e os índices. Reconstrua a auditoria com `build_audit(item, raw_content, finish_reason, error="timeout")`; projete as escolhas usando `project_choices` e ponha `requests=0, questions=0, request_usage=[]`. O replay aceitou o resultado. O próprio adaptador só popula o corpo e o modelo depois do callback de despacho (`adapter.py:200`). O replay pode refutar essa contradição usando apenas o envelope. A cronologia real de um timeout após envio e a correspondência financeira continuam dependendo da evidência externa da tarefa B. Reproduzir ambos os casos legítimos, pré-despacho sem resposta e pós-despacho com uso, junto com a adulteração.

## Cenários independentes anteriores à implementação

Foram exercitados com `R5Adapter.classify`, replay e decisão comum. A entrada do cenário 11 propôs Pix pelo trecho “Fiz um Pix” e declarou perda em curso no restante. A entrada do 12 incluiu `chargeback` na lista ativa de categorias. Para os cenários completos/inválidos, o teste focal versionado verifica zero usos do gateway.

| Nº | Previsão artificial | Esperado | Observado |
| --- | --- | --- | --- |
| 1 | payouts · dinheiro/app/aparelho | Revisão | Veto, `insufficient_relation`; basic recebido preservado |
| 2 | payouts · cair na conta o que vendi a débito | Aceitar | Aceito |
| 3 | pix · “Pix” negado / terminal · substituir bobina da leitora de cartões | Vetar Pix, aceitar terminal | Pix vetado e terminal também vetado, `insufficient_relation` |
| 4 | terminal · equipamento como contexto de falha Pix | Vetar | Veto, `insufficient_relation` |
| 5 | urgent · terminais desligaram com venda por celular | Vetar | Veto, `insufficient_relation`; neste texto a falha já não é reconhecida |
| 6 | basic · aprendizado para o próximo mês | Aceitar | Aceito |
| 7 | intermediate · uma das três leitoras parou e as outras duas atendem | Aceitar | Veto, `insufficient_relation` |
| 8 | advanced · divergências exigem refazer o fechamento inteiro | Aceitar | Veto, `insufficient_relation` |
| 9 | urgent · todos debitados duas vezes, continua agora, sem alternativa | Aceitar | Veto, `insufficient_relation` |
| 10 | urgent · pedido de pressa sem impacto | Vetar | Veto, `insufficient_relation` |
| 11 | pix · priority basic válida do canal | Preservar o canal | Pix aceito, basic preservada |
| 12 | chargeback ativa, sem política | Preservar se recebida, vetar se predita | Ambos confirmados, predição vetada com `unsupported_code` |

Os falsos vetos em 3, 7, 8 e 9 ilustram perda de cobertura em português corrente. O cenário 9 também deixa visível um dano que precisa impedir `basic`. Não usar estes números como métrica de desempenho de Luna nem exigir um dicionário universal de sinônimos.

## Verificações adicionais

- Reexecutei os 17 métodos parametrizados de `adapters.luna.r5.test_evidence` com gateway local. Todos passaram. Os cenários de erro estrutural interrompem a sessão. O veto semântico permite o caso seguinte. A verificação de citação cobre literalidade, Unicode, duplicidade e alteração de trecho e offset. A decisão comum conservou campos recebidos e reteve escolhas de um caso parcial para revisão.
- Inspecionei reserva antes do transporte, callback único, ausência de retries e reconciliação do 429 no orçamento simulado. O timeout pós-despacho preserva uso desconhecido; o teste de expiração durante a validação guarda resposta e custo. O teste de procedência confirma `version_mismatch` e modelo devolvido intactos, e `adapter_error` para ausência de versão. O caminho de erro ao fechar a sessão não inicia outra tentativa. A configuração solicita 384 tokens. A reserva máxima faturável e o vínculo com o recibo real são responsabilidades do executor injetado.
- O diff da base ao commit contém oito arquivos novos. `git diff --check` passou. Recalculei o SHA-256 dos blobs do HEAD nos mapas originais de fontes executáveis/semânticas dos congelamentos R3 e R4. Coincidiram 12/12 e 7/7, respectivamente. A validação usou somente esses mapas, sem executar os avaliadores de rodadas anteriores. Não houve medição de modelo, latência remota ou custo real.

**Exercício reproduzível.** Compare no mesmo gateway artificial “O Pix não chegou ao destinatário” e “O adesivo do Pix não chegou pelo correio”. Mantenha `pix/pix_operation` para ambos, observe o sujeito de “não chegou” e confira a decisão comum depois do reparo.

## Rechecagem dirigida da primeira correção

**Veredicto — FIX.** No commit `01eddbebfb416231eed8f13661460b34e59dd8bf`, os exemplos originais dos quatro achados passam. A candidata ainda libera prioridade urgente em três exemplos em que as novas construções encontram uma consequência negada, ausência explícita de vítimas ou uma pergunta sobre a existência do dano. Conferi apenas o delta, seus contraexemplos e os controles positivos.

| Achado anterior | Situação após a correção |
| --- | --- |
| P1 · consequência negada ou já atendida | **Parcialmente corrigido.** Os dois exemplos originais de multa e o de alternativa atual são vetados. Uma nova construção de multa ainda aceita negação explícita, conforme o par abaixo. |
| P1 · rotina durante débito duplicado em andamento | **Corrigido para o rebaixamento.** O relato com pergunta de configuração e clientes debitados duas vezes agora veta basic. A cobrança afirmada, contínua e sem alternativa sustenta urgent. O novo ramo que permite urgent precisa resolver a afirmação de dano antes de aceitar. |
| P1 · categoria negada ou incidental | **Corrigido.** As três recusas de assunto, o adesivo, a etiqueta e o cupom produziram veto. Foram aceitos Pix que não chegou ao destinatário, repasse das vendas que não entrou e leitora que deixou de imprimir. |
| P2 · resposta do fornecedor com zero despachos | **Corrigido.** Reconstruí a adulteração original. O schema recusou `returned_model` não nulo para `requests=0`. As coberturas legítimas antes e depois do despacho permanecem verdes. |

### P1 residual · A nova regra local de urgência não distingue afirmação, negação e dúvida

Proponha `urgent/immediate_harm` com `quote` igual ao texto completo, usando o mesmo gateway artificial descrito acima. O replay validou cada decisão e `common.decide` aplicou urgent nos quatro relatos. Os veredictos das duas versões abaixo foram comparados diretamente com a política executável de cada commit.

| Texto | Esperado | `065deee` | `01eddbe` |
| --- | --- | --- | --- |
| Serei multado hoje. | Aceitar | Veto | Aceito |
| Não serei multado hoje. | Vetar | Veto | **Aceito** |
| Nenhum cliente está sendo cobrado duas vezes agora. | Vetar | Veto | **Aceito** |
| Como posso confirmar se os clientes estão sendo debitados duas vezes agora? | Vetar | Veto | **Aceito** |

Em `evidence.py:372` e `:443`, a consequência “serei multado” pode casar dentro da negação. Em `evidence.py:344`, `:358` e `:455`, a detecção de débito em curso pode casar dentro do escopo de “nenhum cliente” e “confirmar se”. São três falsas aceitações diretamente introduzidas neste delta. “Não terei multa hoje.” também foi aceita nos dois commits, corroborando o achado de negação já aberto. O reparo dirigido deve manter o par afirmativo e guardar o escopo de polaridade e pergunta antes de permitir o resultado. Nenhuma ampliação de catálogo é necessária.

**Conferências.** Executei os 24 métodos focais com sucesso e reproduzi as 14 propostas dos 12 cenários independentes com os resultados esperados, incluindo os quatro vetos excessivos da versão anterior. Nos vetos semânticos conferi `observation.choices.*.raw="informacao_insuficiente"`, `reason="policy"`, proposta e citação originais na auditoria e decisão de revisão. O documento técnico distingue essa saída pós-política do corpo bruto. Saídas inválidas permanecem no caminho técnico. `git diff --check 065deee HEAD` passou. A worktree da candidata estava limpa. Não houve chamada externa, leitura de dados finais nem alteração de código nesta rechecagem.

## Rechecagem dirigida da segunda correção

**Veredicto — FIX.** Commit `c233f0edc4a0646419409b2471088a21c880b282`, base da correção `01eddbeb`, mesma branch e worktree limpa. O P1 de urgência espúria foi corrigido nos três relatos que o motivaram. A alteração introduziu um rebaixamento a basic quando a pergunta de orientação vem depois de uma declaração de dano na mesma frase.

Conferi “Não serei multado hoje”, “Nenhum cliente está sendo cobrado duas vezes agora” e “Como posso confirmar se os clientes estão sendo debitados duas vezes agora?”. Nos três casos urgent passou de aceito a vetado. “Serei multado hoje” permaneceu aceito. Testei afirmação e negação de perda, operação totalmente parada sem alternativa e consequência de condição operacional pendente. O replay também distinguiu uma citação de perda afirmada de outra, no mesmo relato, sobre multa negada. Os 27 métodos da suíte focal passaram. A checagem do diff entre os dois commits passou.

### P1 · A interrogação da segunda oração apaga a perda declarada na primeira e libera basic

Nos exemplos abaixo, proponha `urgent/immediate_harm` citando a primeira oração; em uma execução independente, proponha `basic/routine` citando “como posso configurar a maquininha?”. Conferi a política da base, a resposta atual de `R5Adapter` com gateway local, o replay e a aplicação pelo motor comum.

| Texto completo | Resultado em `01eddbeb` | Resultado em `c233f0e` |
| --- | --- | --- |
| Estamos perdendo vendas a cada minuto: como posso configurar a maquininha? | urgent aceito, basic vetado | urgent vetado, **basic aplicado** |
| Todos os clientes estão sendo debitados duas vezes agora, como posso configurar a maquininha? | urgent aceito, basic vetado | urgent vetado, **basic aplicado** |

Em `evidence.py:439`, uma interrogação em qualquer posição veta todas as ocorrências do segmento, inclusive a afirmação que precede a pergunta. A remoção da perda atual em `evidence.py:480` e `:501` permite que a pergunta de configuração sustente rotina sozinha. O texto equivalente com ponto entre as duas orações mantém o veto a basic. O reparo precisa considerar o escopo da pergunta na ocorrência citada. Se o escopo for incerto, o efeito conservador é enviar para revisão e impedir a aplicação de basic. Os relatos que somente perguntam se o dano existe continuam sendo controles negativos de urgent.

Esta rechecagem comparou 19 propostas sintéticas dirigidas aos ramos alterados. Não houve acesso a finais, serviços externos ou conta. Não abri novas famílias de classificação.

## Rechecagem dirigida da terceira correção

**Veredicto — SHIP para congelamento de R5-A.** Commit exato `53b11319c5450b7ab01bca64d98fb499f5fe9412`, base da correção `c233f0edc4a0646419409b2471088a21c880b282`, branch `feat/luna-evidencias-r5`, worktree limpa. O P1 de rebaixamento por interrogação posterior está corrigido. O integrador pode congelar esses bytes e entregá-los à tarefa B.

Repeti os relatos de perda de vendas em andamento e de débito duplicado em todos os clientes, seguidos de “como posso configurar a maquininha?”. Para cada um, propus urgent citando só a declaração de dano e basic citando só a pergunta. Com ponto, dois-pontos, vírgula e ponto e vírgula, o gateway local produziu o resultado esperado nas **16/16** combinações. O motor comum aplicou urgent e enviou a proposta de basic para revisão. Oito decisões da matriz mudaram em relação a `c233f0e`, todas nos dois separadores em que havia rebaixamento. Nos dois exemplos de fronteira incerta, urgent e basic seguiram para revisão.

**Estado dos achados.**

| Achado acompanhado | Estado neste commit |
| --- | --- |
| P1 · urgência negada, resolvida ou em consulta | Corrigido. Os controles negativos permanecem vetados, o prazo e a paralisação afirmados permanecem elegíveis. |
| P1 · rotina sobre prejuízo atual, inclusive se seguido de pergunta | Corrigido. A matriz reproduz as duas falhas relatadas na rechecagem anterior e comprova que a pergunta deixou de apagar o dano. |
| P1 · categoria negada ou logística incidental | Corrigido na primeira onda. Os testes de regressão de categoria passaram novamente. |
| P2 · replay de resposta com zero despachos | Corrigido na primeira onda. O teste de adulteração continua bloqueando o envelope. |

Executei **57 propostas dirigidas** com `R5Adapter`, replay e `common.decide`. Foram 16 de dano e pergunta, 32 de negação, consulta ou hipótese variando pontuação, cinco controles isolados e quatro propostas de fronteira incerta. Conferi valor original, citação, posição, abstenção pós-política e preservação do campo recebido. Os 29 métodos da suíte focal passaram e o diff passou sem erros de formatação. As seis referências de `candidate.json` e os mapas de fontes originais R3 (12/12) e R4 (7/7) coincidem com os hashes dos blobs deste HEAD.

A verificação semântica continua limitada às construções descritas no documento da candidata. Esta liberação conclui a revisão offline da tarefa A. O congelamento formal, o vínculo com recibos pelo executor e as métricas de qualidade do modelo são etapas posteriores. Nenhuma chamada externa, leitura de avaliação final ou alteração na worktree foi feita nesta rechecagem.
