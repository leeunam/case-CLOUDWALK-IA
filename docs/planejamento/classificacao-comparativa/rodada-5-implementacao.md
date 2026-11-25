# C05-R5 · Preparação de Luna com evidência

Data: 25/11/2026. Base de planejamento: `d53df8d`.
Subplano da [conclusão do projeto](../conclusao-projeto.md).

O responsável escolheu manter Luna e acrescentar evidência verificável com
validação conservadora. O integrador adota o desenho abaixo para preparação
offline: um contrato privado com código, critério e trecho; um veto local;
uma mensagem auditável na mesma comunicação existente. Não alterar os critérios
para acomodar o erro R4. Código, testes e revisão precedem qualquer novo ensaio.
Não há autorização para chamadas pagas pelos agentes desta preparação.

## Fatias, propriedade e aceite

| Tarefa | Propriedade | Entrada e prova de saída |
| --- | --- | --- |
| R5-A candidata | Novo `script/classification_comparison/adapters/luna/r5/`, teste sintético e relatório técnico. | Base com este plano; implementar contrato/validação, comprovar uma chamada e prazo/custos/erros, revisão independente e congelamento dos bytes antes de usar o final. |
| R5-B executor | Perfil opt-in, contrato de relatório, runner/gate existentes e guia da nova rodada. | Só consumir A commitada, revisada e congelada; ligar envelope e arquivo de evidência ao recibo, reusar critérios/conta, testar adulteração, bloqueios, compatibilidade e CLI sintética6+44. |
| R5-C integrador | Revisão ampla, reprodução, pré-voo, evidências e passagem de adoção. | Uma revisão ampla de A+B e reparos dirigidos; fixture não qualifica modelo. Pré-voo real confere tarifas/conta/limites e consentimento vigente; desenvolvimento real reprovado impede final. |

Nenhuma dessas fatias altera Rails, frontend, autenticação, canais ou Kafka.
C06 depende de qualificação e decisão de adoção. E01 segue posterior/opcional.
README e consolidação documental podem avançar independentemente, preservando
as limitações reais. Não transformar o teto experimental em orçamento público.

## Preflight das interfaces

| Interface | Produtor e consumidor | Resolução |
| --- | --- | --- |
| Envelope R5 | A produz; B valida e persiste | Schema/política/bytes congelados em A; B não ajusta semântica após ver finais. |
| Adaptadores históricos | A importa auxiliares; verificadores usam freezes R3/R4 | Não editar arquivos pinados, conferência por SHA original obrigatória. |
| Relatório/recibo/gate | B produz; integrador reproduz | Só R5 admite envelope/evidências, bijeção e hashes obrigatórios, gates não mudam. |
| Dados reservados | B e integrador avaliam; A implementa candidata | A não lê finais nem suites/imports que os carregam, mesmo após entrega. |
| Ledger financeiro | Executor reutiliza; root controla real | Conta histórica schema4/cap10, sem reset/novo saldo/chave para agentes. |

A implementação abaixo deriva da estratégia já escolhida; detalhes reversíveis
foram decididos pelo integrador. Origem de uma citação é verificável; suficiência
semântica continua falível. Medir cobertura impede aprovar uma política que
apenas manda tudo para revisão.

## Restrições globais

Base histórica: main 1c89c26. A base exata da implementação será o commit que integrar o resultado R4 e este plano. Não iniciar código antes da base informada.

Responsável escolheu explicitamente Luna com evidência verificável e validação conservadora, incluindo mudança de contrato e código. Preparação offline autorizada; não chamar fornecedor nesta fatia. Preservar globalUSD10 e conta existente (acumuladoUSD0.03093512); nenhum agente acessa a conta ou chave. Uma chamada por caso. Nada de fallback, segunda opinião externa ou retries.

Tarefa A: implementar exclusivamente nova candidata R5 e envelope auditável, com campos ausentes code/criterion/quote, política de suporte e testes sintéticos. Não alterar bytes pinados de Qwen/R3/R4. Código comum somente importar helpers de leitura/validação sem carregar dados finais. Autor nunca abre final-cases/dataset/outputs finais ou preflight/Plan/suites que os importam até congelar; depois de congelar continua sem usar final para ajustar candidata.

Tarefa B: somente após freeze A revisado e integrado, conectar perfil opt-in R5 ao executor/gate existente, preservando validação de auditoria e hashes/contagem no recibo. Reusar ledger/gates/controles/populações/critérios, conta real não pode ser criada/resetada. Regressões históricas após A freeze feitas pelo integrador/autor B que não ajusta a candidata.

Revisão por tarefa + única revisão ampla após A/B, com reparos dirigidos. CLI sintética6+44 deve registrar inconclusive (fixture não mede qualidade). Pré-voo real separado sem chamadas extras.

Arquitetura: nenhuma alteração de API Rails/frontend/canais, Kafka ou autenticação nesta fatia. Classificador não é atendente. C06 só depois de qualificação e adoção. Não declarar projeto concluído.

Critérios: development6/8alvos:8/8corretos,4/4recebidos,3completos/3reviews,1urgente,0erro/timeout,custosconciliados,p95total<=3000ms(n6). Final36+13controles/44POSTs, precisão>=90%porcampo,cobertura>=21/29,zero indevida0/7,zero rebaixamento0/6,reconhecimento>=5/6,preservação100%,aplicaçãoparcialzero,p95total<=3000ms(n36). Não alterar textos/gabaritos/denominadores.

Limites de honestidade: quote presente e posições são verificáveis; suporte semântico continua falível. Não classificar por ID, copiar frases de finais, hardcode para um único caso, atribuir confiança/probabilidades inventadas ou aceitar só palavras-chave isoladas. Políticas têm relações/construções e contexto de negação/hipótese/foco. Caso fora das construções suportadas vai para revisão; medir perda de cobertura.

## Desenho normativo

Desenho adotado pelo integrador para preparação offline. Base `1c89c264ca7cba4e8cde72ec9098181435def74d`, branch `main`, checkout principal. A R4 acertou 7/8 campos no desenvolvimento informado. A falha foi inferir recebimento de vendas de um relato que mencionava dinheiro, aparelho e aplicativo. A prioridade basic era adequada. A categoria precisa abster-se. Se a prioridade vier do canal, a decisão a preserva. Se também tiver sido predita, a observação registra seu resultado e a decisão não a aplica parcialmente.

## Duas opções na mesma chamada

| Resposta da Luna | O que o adaptador verifica | Consequência |
|---|---|---|
| Código e trecho literal | Código ativo e presença do trecho no relato | Aceitaria uma citação verdadeira sobre dinheiro como justificativa para repasse. Serve para rastreabilidade, é insuficiente para esta mudança. |
| Código, critério da rubrica e trecho literal | Presença do trecho, compatibilidade entre critério e código e reconhecimento local da relação no contexto | Permite rejeitar uma escolha do modelo mesmo quando a citação é autêntica. Expressões ainda desconhecidas podem seguir para revisão. |

Recomendo a segunda opção. A Luna continua classificando uma vez por caso elegível. A política local só confirma ou veta sua escolha. Um veto jamais escolhe outro código automaticamente.

## Contrato privado com a Feita

Manter o contexto atual (`text`, `brand`, `catalog`, `missing`, `received`). A raiz do JSON estrito exige exatamente os campos de `missing`. Cada campo contém exatamente `code`, `criterion` e `quote`, todas strings obrigatórias. `code` aceita as chaves do catálogo daquele campo e `informacao_insuficiente`. Em abstenção explícita exigir `criterion="none"` e `quote=""`. Em predição exigir uma citação contínua, literal, não vazia, de até 160 caracteres Unicode. O exemplo sintético abaixo recebe a prioridade do canal.

~~~json
{"category":{"code":"payouts","criterion":"sales_settlement","quote":"Quando o valor das vendas a crédito entra na minha conta?"}}
~~~

Os critérios possíveis para categoria são `pix_operation` (pix), `sales_settlement` (payouts) e `terminal_operation` (terminal). Para prioridade são `routine` (basic), `localized_impact` (intermediate), `broad_impact` (advanced), `immediate_harm` (urgent). Incluir `none` nos dois enums. Não inserir exemplos de casos ou identificadores reais no prompt. O schema limita tipos e enums. O intérprete repete essas verificações localmente e verifica as relações entre campos.

**Tratamento da resposta.** JSON quebrado, chave inesperada, tipo errado, código fora do catálogo, critério fora do enum, citação vazia ou acima de 160 caracteres em predição, ou resposta truncada seguem o caminho técnico existente (`invalid`, revisão e encerramento da sessão). Falta de chave obrigatória usa `missing_output`. Uma predição exige critério diferente de `none`. Uma predição bem formada com critério conhecido incompatível, citação ausente do relato, repetida sem localização inequívoca, recorte insuficiente ou categoria ativa sem política segue como `abstained/policy`. Uma abstenção bem formada segue como `abstained/explicit`. Para uma combinação impossível do marcador explícito com citação ou critério preenchidos, usar `invalid_output`. Recusa do provedor, procedência, uso e falha de transporte conservam o tratamento existente. Nenhum erro dispara uma segunda chamada.

## O que sustenta uma escolha

1. Localizar o trecho exatamente no texto original e calcular início inclusivo e fim exclusivo em caracteres Unicode. Fazer isso antes de normalizar acentos, caixa ou flexões para a política. Extrair o enunciado inteiro que contém a citação e os enunciados vizinhos do texto original. Ler o pedido completo para detectar mudança de assunto e contradições. Um trecho que só funciona quando suprime uma ressalva falha.
2. Reconhecer famílias pequenas de construções compostas. Implementá-las como padrões revisáveis de palavras e relações **na mesma proposição**, com alternativas de flexão e ordem. O vínculo tem de envolver o objeto da dúvida, ação pretendida ou operação que falhou. Posição, vizinhança de palavras ou coocorrência em frases distintas são insuficientes. Quando a política não consegue resolver o escopo da negação, atribuição, condição ou mudança de foco, abstém-se.

| Critério | Relação a confirmar no contexto |
|---|---|
| Operação Pix | Pedido, ação ou falha vinculada à transferência/pagamento por Pix. Incluir paráfrases distintivas como enviar um valor usando a chave do destinatário. QR, transferência ou aplicativo isolados deixam o meio ambíguo. |
| Repasse | Origem em vendas associada a crédito, liquidação, prazo, valor a receber ou destino do recebimento. “Quanto tempo leva para cair na conta o que vendi a débito?” e a construção com o repasse explícito de vendas expressam o mesmo vínculo. |
| Terminal | Pedido de configuração, uso, instalação ou falha funcional ligado a um equipamento identificável como terminal de pagamento. “A leitora de cartões deixou de imprimir os comprovantes” continua elegível sem a palavra “maquininha”. |
| Prioridade | Rotina exige orientação/preparação explícita ou funcionamento preservado pertinente ao pedido. Moderado exige prejuízo localizado e disponibilidade remanescente. Relevante exige abrangência, impacto ou retrabalho significativo sem necessidade imediata evidenciada. Urgente exige perda em curso, interrupção total sem alternativa ou consequência relevante vinculada a prazo imediato. Considerar alternativas e restauração no relato inteiro. Complexidade técnica, pedido de pressa e ausência de detalhes são insuficientes. |

Usar construções de foco e escopo tanto para aceitar quanto para vetar. “O repasse das vendas não entrou” identifica a operação que falhou. “Minha dúvida não é sobre o repasse das vendas” descarta essa operação. “Talvez seja o repasse” expressa hipótese de causa. “O repasse caiu normalmente. Como troco a bobina da maquininha?” muda o foco para o terminal. Uma consulta sobre como receber vendas futuras pode satisfazer a categoria mesmo com prioridade de rotina. Só aceitar a categoria se o critério for sustentado e o pedido puder ser distinguido dos demais. Se o catálogo ativo mudar o significado de um código, exigir política revisada para a nova definição antes de aceitá-lo. Uma categoria nova pode chegar do canal como valor válido e continua preservada.

**Alcance da verificação.** A existência do trecho, a posição, a chave no catálogo e o casamento com uma construção cadastrada são reprodutíveis. Decidir de que fato o cliente fala e qual impacto ele descreve continua sujeito a erro do modelo e a limitações dos padrões. Sarcasmo, elipses, co-referências e hipóteses sem marcadores explícitos podem escapar. Registrar em desenvolvimento quantos acertos se perderam por veto e quantos erros passaram com evidência aparentemente aceitável. Um classificador que sempre abstém pode passar em testes exclusivamente negativos.

## Fronteiras, versões e verificação

- O contrato privado **Feita → adaptador** exige evidência. O contrato comum IPC 1.1.0 comporta as escolhas projetadas, mas fecha as propriedades da observação e exige string em `raw` para uma predição. O método `metadata()` do Qwen trata apenas strings de procedência. O Rails já tem JSONB em `classification_attempts.evidence`, gravado por `Classification::CompleteRequest` em outro fluxo. Publicar a evidência experimental ali não resolveria a auditoria do C05.
- Recomendo uma única mensagem de saída pelo canal que já transporta a observação. Criar o **envelope IPC exclusivo do perfil R5, versão 1.0.0**, com as chaves exatas `profile_version`, `observation` e `audit`. `observation` mantém o contrato comum 1.1.0 completo e os códigos de status correntes. `audit` contém obrigatoriamente `input_sha256`, `policy_sha256`, `raw_content` (string retornada em `message.content`, ou null se ausente), `finish_reason` e `fields`. Cada campo solicitado em `fields` contém `value` (código proposto), `criterion`, `quote`, `start`, `end`, `verdict` e `reason`. Campos inacessíveis recebem null. Veredictos `accepted|explicit|veto|invalid|error`. Exigir motivo enumerado e pertinente ao veredicto, inclusive para sucesso (`supported_relation`) e veto (`no_literal_span|ambiguous_span|unsupported_code|criterion_mismatch|insufficient_relation|context_conflict`). O envelope conserva **todas** as escolhas, inclusive uma predição correta que o caso não aplicou parcialmente. O identificador, tentativa, rodada e identidade vêm de `observation`. Em falha técnica, devolver a observação de erro e evidência disponível. Falta ou invalidez de envelope, arquivo interrompido ou incongruência bloqueia o gate.
- O executor existente deve aceitar esse envelope **somente no perfil R5**, verificar seu schema, extrair `observation` para o avaliador atual e gravar o envelope completo (uma linha por caso com chamada) em `<rodada>/luna-evidence.jsonl`. Antes da execução, congelar no plano/recibo os hashes de schema, código da política, adaptador, prompt, rubrica e configuração. Definir o digest da entrada sobre o UTF-8 de JSON canônico do item IPC (`sort_keys=True, ensure_ascii=False, separators=(",", ":")`). No fechamento, ordenar pelo plano, verificar unicidade por rodada/caso/tentativa, correspondência 1:1 com todas as observações R5 esperadas, conferir digests e recalcular as posições e decisões locais a partir do conteúdo bruto e do insumo congelado. Finalizar o arquivo uma vez e incluir seu SHA-256, contagem e versão de schema no recibo que vincula o hash do relatório. O gate verifica ambos antes de aceitar. Um caso sem despacho conserva a contabilidade original e, se houve observação do adaptador, entra na verificação 1:1. Escrita e leitura são locais ao executor; nenhum novo canal de rede, log opcional ou coletor de produção. Uma extensão do perfil é mais simples de conciliar que duas gravações independentes por processo. A API do produto e os envelopes históricos R3/R4 e Qwen continuam consumíveis.
- Criar `adapters/luna/r5/{prompt.txt,candidate.json,operational.json,adapter.py,evidence.py,evidence-envelope.schema.json,test_evidence.py}`. Versionar e identificar por SHA-256 o texto da política, ou o próprio módulo se ele for sua fonte executável. Registrar a rubrica comum 1.0.0. Propor adaptador R5 **2.0.0**, política **2.0.0**, envelope IPC R5 **1.0.0**, prompt **2.0.0**, perfil operacional **2.0.0**, schema privado **1.0.0**. A criação do novo adaptador e a seleção de perfil seguem o apêndice abaixo.
- Solicitar **384 tokens de saída** no perfil R5. Dois objetos pequenos podem conter duas citações de 160 caracteres com acentos ou aspas escapadas. O limite de 128 foi escolhido para dois códigos curtos. Conferir com respostas extensas, cortes e uso realmente retornado antes de qualquer conclusão sobre adequação. Uma requisição com limite de tokens não garante teto financeiro. Recalcular reserva e estimativa, observar tokens e custo reais, conservar parada por custo desconhecido, exigir autorização operacional específica antes de chamadas pagas. O perfil não habilita o modelo no serviço.
- Testar com gateway simulado e textos novos. Checar uma chamada para dois campos, seleção de um único campo ausente, preservação integral do canal e zero chamadas para entrada completa/inválida. Cobrir termos genéricos, paráfrases positivas das três categorias, operação negada versus falha afirmada, menção incidental, hipóteses e consultas futuras. Incluir citações inventadas, repetidas, com acentos e aspas, truncamento, ampliação de catálogo e revisão após predição parcial. Variar extensão do impacto, alternativas e prazo em cada prioridade. Incluir pares em que só o trecho **fora** da citação altera a decisão, um falso urgente e uma urgência genuína. Repetir com IDs trocados. Tentar adulterar uma citação aceita, trocar o campo de outro caso, remover ou duplicar uma linha e substituir o hash do arquivo. Exigir bloqueio do gate. Revalidar R3/R4 e Qwen. Congelar a candidata antes de abrir a avaliação final.
- Avaliar com os mesmos gabaritos e critérios. Meta final de cobertura **≥21/29**, precisão **≥90%**, zero erros críticos de urgência e zero decisões indevidas nos casos de revisão obrigatória. Usar as definições originais dos contadores. Nenhuma dessas metas foi medida nesta etapa. Dados de desenvolvimento e pares sintéticos orientam a implementação. O conjunto final continua reservado ao avaliador independente.

**Decisão para implementação.** Adotar o perfil R5 com evidência obrigatória para todos os campos e o conjunto inicial de construções. A revisão da proposta usou apenas leitura local. Foram feitas zero chamadas de inferência.


## Apêndice · compatibilidade com os congelamentos históricos

**Escolha.** Implementar `adapters/luna/r5/adapter.py::R5Adapter` por composição. O método histórico `qwen.Adapter.classify` aceita outro construtor de requisição, mas chama diretamente o intérprete dos códigos simples. `LunaAdapter` fixa ainda a identidade e os 128 tokens da R3/R4. Por isso, o R5 terá um método próprio para coordenar uma classificação. O executor seleciona a classe pelo perfil R5 opt-in. Se o ponto de entrada atual também tiver hash congelado, criar um ponto de entrada irmão exclusivo R5 e compartilhar as funções existentes de execução e relatório.

- Reutilizar diretamente `LunaTransport`, normalização e validação C01, `parse_object`, `usage_from`, `choice`, `choices_for`, `metadata`, `rates` e o orçamento já injetado pelo executor. O método R5 valida pins e orçamento, inicia o prazo absoluto com a margem IPC já usada, constrói o corpo, reserva pelo tamanho dos bytes, entrega ao transporte o callback de despacho e contabiliza a única resposta. Concilia também o uso de HTTP não-200 e o estado de custo desconhecido. Verifica modelo retornado e prazo, valida a evidência, projeta a observação, confere o schema do envelope e fecha a sessão em falha técnica. O prazo cobre toda a execução, inclusive validação e construção da auditoria. A decisão e a aplicação integral continuam com o avaliador existente.
- Congelar o novo módulo, os auxiliares históricos que ele importa e a entrada R5. Verificar no HEAD os SHA-256 **originais** dos arquivos pinados pelos dois congelamentos, inclusive os dois adaptadores, o transporte e o perfil operacional. Rodar os verificadores históricos na revisão independente. Refazer recibos antigos para acomodar alterações invalidaria essa verificação. Dados finais continuam vedados ao autor da candidata.
- Ensaiar no perfil novo, por injeção, uma reserva antes do despacho, falha anterior ao POST, 429 com uso, timeout posterior ao despacho, procedência divergente, resposta truncada e recusa sem repetição. Para paráfrases de desenvolvimento, registrar numerador e denominador por família, os acertos vetados e as atribuições indevidas aceitas. O verificador local só atesta origem do trecho e cumprimento das regras congeladas. A capacidade de reconhecer significado continua sendo medida contra os rótulos independentes.
