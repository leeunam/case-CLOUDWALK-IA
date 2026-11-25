# C05-SF2 — especificação do classificador local

Versão aprovada: **1.0.0**, 25/11/2026. Base de aplicação `38e56e0013fcf2ce4fe773725c42e9cbcb4bb6b9`.

**Aprovado:** retomada com SetFit, 360 relatos novos (150 de treino, 90 de
validação, 120 finais), quotas, treinamento, política e execução descritos abaixo.
O responsável liberou a primeira onda 00/01/02 no
[registro de aprovação](aprovacao.json). Não há adoção aprovada, novo treino
executado, resultado SF2 ou autorização para API paga.

[Protocolo declarativo](protocolo.json) · [Tarefas e passagens](tarefas.md) ·
[Prompts dos agentes](prompts.md) · [Piloto SF1](../../../c05-setfit-piloto.md).

## 1. Resultado esperado e limites

Qualificar um pacote SetFit capaz de completar categoria e prioridade ausentes,
ou registrar reprovação/inconclusão com evidência. A demonstração F10 aceita
permanece em fixture durante a pesquisa. SF2 não altera webhook, Kafka,
filas/capacidade, autenticação, produção ou o atendente conversacional simulado.
Não reabre GLiClass/Qwen/Luna nem consulta chaves/contabilidade financeira.

São duas decisões supervisionadas independentes, com um pacote versionado:

- Categoria: `pix`, `payouts`, `terminal`, `informacao_insuficiente`.
- Prioridade: `basic`, `intermediate`, `advanced`, `urgent`, `informacao_insuficiente`.

`informacao_insuficiente` é classe privada de revisão, nunca novo item do
catálogo operacional. Prioridade continua sendo urgência/impacto, não esforço.
A [rubrica comum](../rubrica-comum.md) rege a anotação. As definições não serão
reescritas para acomodar previsões do modelo. Cada especialista ajusta seu
próprio encoder e cabeça: mais artefatos para manter, mas erros e regras por
campo ficam identificáveis. Um encoder compartilhado, classificação das
combinações e outros modelos ficam fora desta rodada.

## 2. Dados e separação

Todos os 360 relatos serão sintéticos em português, novos, sem dados pessoais
reais. Dados históricos, inclusive os 16 do SF1 e os finais já consumidos,
não entram em treino, seleção de limiar ou teste SF2. Servem somente à auditoria
de semelhança, por papel que não desenvolve a candidata.

| Partição | Quantidade | Composição |
| --- | ---: | --- |
| Treino | 150 | 120 com ambos os rótulos claros: 3 categorias × 4 prioridades × 10. Mais 12 com categoria insuficiente e prioridade clara (3 por nível), 12 com prioridade insuficiente e categoria clara (4 por categoria), e 6 com ambos insuficientes. |
| Validação | 90 | 30 por máscara: somente categoria ausente, somente prioridade ausente, ambos ausentes. Em cada máscara, 24 classificáveis e 6 de revisão obrigatória. |
| Final independente | 120 | 40 por máscara. Em cada máscara, 32 classificáveis e 8 de revisão obrigatória. Nenhum texto é repetido para simular outra máscara. |

No treino, cada categoria válida tem 44 exemplos e a revisão tem 18; cada
prioridade válida tem 33 e a revisão tem 18. Essa distribuição não representa
frequência real de clientes. Cada especialista recebe os mesmos 150 textos,
com apenas o rótulo do próprio campo. Não se duplicam exemplos para balancear.

Uma máscara informa quais campos foram omitidos da entrada, não quais rótulos
existem no arquivo gold. Todo relato tem anotação de ambos os campos. Um campo
presente deve ter valor válido e igual ao gold. Revisão obrigatória significa
que **algum alvo omitido** é `informacao_insuficiente`; um campo presente nunca
recebe esse valor. Em cada grupo `both`, distribuir revisões como:

- Validação: 2 apenas categoria insuficiente, 2 apenas prioridade insuficiente,
  2 ambos insuficientes.
- Final: 3 apenas categoria insuficiente, 3 apenas prioridade insuficiente,
  2 ambos insuficientes.

Nos classificáveis das máscaras `priority` e `both`, distribuir os níveis
igualmente: 6 de cada na validação e 8 de cada no final. Acrescentar exatamente
um `urgent` entre os casos `both` com categoria insuficiente e prioridade
clara, em cada partição. Assim há **13 urgentes-alvo na validação e 17 no final**.
As outras revisões com prioridade clara usam níveis não urgentes. Nos casos
classificáveis de **cada uma das três máscaras**, as categorias são distribuídas
em 8 Pix / 8 Repasses / 8 Maquininha na validação e 11 / 11 / 10 no final.

Cobrir erros de digitação, negação, operação preservada, alternativa disponível,
uso futuro, prejuízo atual, prazo imediato, falta de impacto/prazo, assunto
genérico, múltiplos assuntos sem predominância e texto fora do catálogo.
Não ensinar que ausência de informação é prioridade básica, nem que uma palavra
isolada como “urgente”, “Pix” ou “QR” resolve a classificação. Ausência de informação
é propriedade do relato sob a rubrica, não desacordo automático entre anotadores.

### Registro, rótulos e independência

O contrato de dados SF2-00 deve exigir: `id`, `family_id`, `partition`, `text`,
`gold.category`, `gold.priority`, justificativa e trechos de evidência por campo,
autoria, duas anotações independentes, decisão de conciliação, versão/hash da
rubrica e catálogo; em validação/final, também `missing_fields` e `received`.
Não criar ou revisar rótulos com base nos resultados de nenhum classificador.

Os dois anotadores não veem o rótulo do outro antes de entregar sua decisão e
não são a candidata SetFit. Pode haver autoria/revisão por IA sob a delegação
do responsável; declarar essa origem e limitações, sem chamar de validação humana.
Conciliar desacordos pela rubrica antes de publicar cada conjunto. Dúvida não
resolvida impede fechar aquele registro; substituição preserva quota e histórico.
O responsável pode discutir exemplos de **treino**, sem abrir o final.

Paráfrases e cenários com o mesmo evento-base pertencem à mesma família e não
atravessam partições. Família é o evento e seus fatos causais, não toda a categoria
Pix ou Maquininha. O autor do final audita semelhança com treino, validação e
históricos, antes de qualquer resultado de treino SF2:

1. Duplicata normalizada: NFKC, `casefold`, espaços consecutivos reduzidos;
   duplicatas entre partições/históricos reprovam o fechamento.
2. Similaridade lexical: Jaccard dos tokens alfanuméricos normalizados ≥ 0,80
   dispara revisão; texto com menos de cinco tokens sempre exige revisão de novidade.
3. Para cada registro, revisar também os três vizinhos de maior Jaccard em
   outras partições/históricos, com desempate por ID. Famílias, templates e
   fatos são conferidos semanticamente: registrar motivo e rejeitar variantes
   do mesmo evento-base. Detalhes que exponham o final ficam no pacote reservado.
   Semelhança lexical sozinha não demonstra independência ou duplicação semântica.

O treino/validação ficam públicos ao autor da candidata após revisão. Os 120
finais e suas anotações ficam em `.superpowers/sdd/conclusao-projeto/sf2-final/`
na raiz principal, fora do Git e dos diretórios de trabalho dos autores do
modelo. O compartilhamento físico de disco não constitui isolamento de segurança:
o acesso é restrito por papel/instruções, com cronologia de exposição registrada.
Antes do treino, publicar somente `final-seal.json`: hashes dos bytes de dados e
anotações, contagens, versão e recibo de revisão, sem textos, justificativas,
previsões ou rótulos individuais. O pacote selado não muda depois disso.

## 3. Treinamento fixo

Reutilizar o modelo e os arquivos públicos de
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revisão
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, e os pins completos do
[ambiente SF1](../../../../script/classification_comparison/setfit_pilot/requirements.txt)
e do [snapshot](../../../../script/classification_comparison/setfit_pilot/model-lock.json).
Não atualizar versões implicitamente nem executar código remoto do modelo.

| Parâmetro | Valor aprovado |
| --- | --- |
| Ambiente | Python 3.11, CPU; duas threads intra/inter-op; sem GPU |
| Inicialização | Um modelo novo a partir do mesmo snapshot para cada campo |
| Seed | 42 em Python/NumPy/PyTorch/SetFit e cabeça |
| Encoder | Uma época, cinco iterações de pares, batch 8, learning rate `2e-5` |
| Cabeça | `LogisticRegression(solver="lbfgs", C=1.0, tol=1e-4, max_iter=1000, class_weight="balanced", random_state=42)` |
| Seleção | Sem HPO, novos seeds, cross-validation ou escolha de checkpoints |
| Entrada | Somente texto; nenhum ID, gold, campo do canal, partição ou justificativa |
| Comprimento | Limite do snapshot (128 tokens); não truncar silenciosamente |
| Limites | Até 30 min para provisionar; até 30 min acumulados de treino dos dois modelos, com supervisor externo |

Tokenizar todos os textos de treino/validação antes do treino. O custodiante
faz a mesma checagem no final ainda fechado. Texto acima do limite deve ser
substituído e revisado **antes dos selos e do primeiro treino**; em runtime,
entrada longa vai para revisão com motivo, sem corte silencioso.

O rebalanceamento da cabeça é fixado agora para a classe de revisão minoritária;
não altera as quotas. Registrar os argumentos efetivamente aplicados pelo SetFit,
pares, passos e evidência de alteração do encoder. Aviso de não convergência,
ausência de classe, erro, cancelamento ou estouro de prazo impedem declarar treino
aceito. Correções de instalação/implementação são verificadas com fixtures antes
de usar os dados; não retreinar para escolher um resultado mais favorável.

Salvar os dois modelos, tokenizer e metadados como um pacote reutilizável.
Artefatos grandes ficam ignorados, não no Git. Manifesto rastreia hashes das
fontes, dependências, pesos originais/ajustados, cabeça, classes e ordem, dados
de treino, argumentos e versões. Encoder usa Safetensors; cabeça serializada
somente do treino local, carregada após conferir hash contra manifesto confiável.
Não aceitar cabeça arbitrária de download. O reload deve reproduzir decisões
e scores de exemplos públicos de treino com tolerância absoluta `1e-6`.

## 4. Regra de revisão

Há duas camadas: escolha bruta do especialista e aplicação da política.
Os scores da regressão logística permanecem **não calibrados como probabilidades**.
Nesta SF2, “calibrar a revisão” significa escolher cortes empiricamente na
validação, não provar que score 0,80 equivale a 80% de acerto.

Para cada campo solicitado, obter todos os scores e a margem entre os dois
maiores. O campo pede revisão se:

1. O primeiro rótulo é `informacao_insuficiente`.
2. O maior score é menor que `tau` daquele campo.
3. A margem é menor ou igual a `delta` daquele campo (empates revisam).
4. Entrada, score, saída ou catálogo são inválidos, ou há erro/timeout.

Score não finito, fora de `[0,1]`, classe/ordem inesperada ou soma diferente
de 1 por mais de `1e-6` são erros, nunca confiança alta. Rótulo que não esteja
ativo no catálogo da marca resulta em revisão; não renormalizar para escolher
outra classe permitida. O rótulo bruto usa a ordem de `classes_` em empate;
a decisão aplicada revisa o empate independentemente desse desempate bruto.

Grade fixada por campo: `tau ∈ {0.50,0.60,0.70,0.80,0.90}` e
`delta ∈ {0.00,0.10,0.20}`. São 15 opções por campo e **225 políticas conjuntas**,
calculadas dos scores dos mesmos 90 relatos, sem novo treino/inferência por corte.
Guardar também a linha de base de argmax, como diagnóstico, sem elegê-la fora
da grade. A seleção entre 225 opções torna a validação otimista: somente o final
independente sustenta o resultado de qualificação.

Aplicar primeiro todos os gates de qualidade da seção 6 na validação.
Entre políticas aprovadas, ordenar por: (1) mais casos totalmente corretos,
(2) mais urgentes-alvo corretamente aplicados, (3) menos conclusões automáticas
erradas, (4) maior cobertura automática. Empate final: tupla crescente
`(tau_category, delta_category, tau_priority, delta_priority)`.
Sem política elegível, não abrir o final nem selecionar “revisar tudo”.

Entrada completa ou inválida: **zero chamadas aos especialistas**. Um campo
ausente chama só seu especialista; ambos ausentes chamam os dois. Se qualquer
campo solicitado revisar/falhar, nenhum complemento é aplicado; os valores
válidos do canal ficam intactos. Não inventar score para campo que não foi inferido.
O reconhecimento bruto de urgência é calculado antes desses vetos, mesmo que
o caso inteiro vá para revisão por problema de categoria.

## 5. Contrato experimental e fronteira com Rails

SF2-00 congela um contrato de pesquisa `sf2-ipc/1.0` e schemas próprios, sem
editar os contratos históricos IPC/relatórios v1.1–1.6. Entrada traz ID de
correlação, texto, campos recebidos e catálogo; wrapper valida e calcula
`missing_fields`. Os especialistas recebem **somente o texto**, apenas para
os campos necessários. Não recebem gold nem máscara declarada pelo produtor
sem conferência contra os campos realmente ausentes.

Resultado por campo registra rótulo bruto, scores não calibrados, margem,
cortes usados, decisão e motivo. Resultado do caso traz `complete|review|error`,
campos recebidos preservados, complementos aplicáveis, contagem de chamadas,
hash do pacote/modelo/política e tempo total. Gold, justificativas e métricas
ficam exclusivamente no avaliador, fora do adaptador e do processo do modelo.
Erro de candidato nunca vira `complete`; controle que injeta aplicação parcial
deve ser reprovado pelo avaliador, sem “consertar” o resultado na auditoria.

Este adaptador experimental é local. A integração Rails continua C06 e só é
implementada após qualificação e decisão de adoção. O futuro job reutiliza
idempotência, correção humana, catálogo/versão, auditoria e descarte tardio já
existentes, com origem SetFit verdadeira, sem gravá-lo como Jev.

## 6. Métricas, gates e custos

Preservam-se os limites do protocolo vigente; mudam os dados/denominadores,
não o rigor. No final há 96 casos classificáveis, 24 de revisão, 80 alvos de
categoria e 80 de prioridade. Campo válido do canal não conta como acerto de
modelo. Reportar precisão/recall/F1/suporte por classe, matriz de confusão,
revisão por campo/caso, cobertura correta e scores brutos versus decisões aplicadas.

| Gate | Validação | Final |
| --- | --- | --- |
| Preservação dos campos recebidos | 100% | 100% |
| Inferências em entradas completas/inválidas | 0 | 0 |
| Aplicação parcial após revisão/erro | 0 | 0 |
| Conclusões automáticas em casos de revisão esperada | 0/18 | 0/24 |
| Prioridade não urgente aplicada quando gold é urgente | 0 | 0 |
| Acerto por campo aplicado | ≥90%, denominador >0 | ≥90%, denominador >0 |
| Cobertura automática dos casos classificáveis | ≥51/72 (70%) | ≥68/96 (70%) |
| Urgentes brutos reconhecidos | ≥11/13 (80%) | ≥14/17 (80%) |
| Tempo total p95 do adaptador | Diagnóstico medido; não seleciona cortes | ≤3.000 ms, 120 durações observadas |

Acerto aplicado = acertos / todos os alvos efetivamente aplicados daquele campo;
abstenções/erros são separados, não somem da cobertura. Cobertura automática
inclui casos aplicados errados, penalizados pelo acerto; reportar também
cobertura de casos **completamente corretos**. Completos e inválidos usam
controles adicionais, sem entrar nas 360 narrativas, acertos ou percentis.

Os controles de SF2-00 devem cobrir valores completos/invalidade (zero chamadas),
ausência omitida/nula/vazia, cada especialista isolado, ambos, preservação,
recusa de parcial, erro/timeout e score inválido. Fixtures apenas verificam
contratos: nunca entram como evidência de qualidade/tempo de SetFit real.

Execução final: concorrência 1; uma tentativa por caso; timeout de 5.000 ms;
arquivo de saída novo e append-only. Carregar modelos antes de sinalizar READY;
sem forward de aquecimento artificial antes do final. Medir monotonicamente
desde antes de validar/enviar a entrada até validar a decisão: transporte local,
ambos os especialistas quando necessários, política e validação. Incluir erros
e timeouts observados; não contar controles ou replay offline da grade.
Reportar startup frio antes de READY, download, treino, pico de RAM/CPU,
p50/p95/máximo separadamente. p95 por posto mais próximo: item 114 de 120.
Fila Rails e tempo até resposta Kafka são medidos separadamente na C06/C07.

Falha com durações ou casos faltantes é inconclusiva. Se o worker morrer ou
travar, registrar a interrupção; não reiniciá-lo para repetir casos/ocultar o
custo de recuperação. Não preencher previsões ausentes, excluir casos difíceis,
trocar rótulos ou afrouxar critérios após medir. Relatar intervalos de Wilson
95% para proporções como diagnóstico, sem criar novo gate estatístico.
Dados sintéticos e esse tamanho não comprovam qualidade em produção.

Nenhuma chamada a API de inferência do projeto. Registrar consumo local e
ausência de chamadas externas do classificador,
sem converter CPU/RAM em “custo zero” de operação ou em preço fictício em dólares.

## 7. Congelamento e decisão

1. Aprovar esta proposta; SF2-00 fixa schemas/fixtures/validador sem mudar regras.
2. Concluir revisão dos 150+90 dados e selar os 120 finais **antes do treino**.
3. Revisar código/ambiente com fixtures; congelar fontes, contratos, argumentos
   e dados públicos antes de treinar uma vez cada especialista.
4. Extrair scores de validação uma vez; selecionar a política pela ordem fixa.
5. Auditar a seleção; congelar pesos, classes, adaptador, política, comando,
   versões, hashes dos três conjuntos e gate de desenvolvimento aprovado.
6. Só então o executor independente abre o final. Não manda gold ao candidato;
   sela previsões dos 120 antes de computar métricas com os rótulos.
7. Auditar evidências e registrar elegível/reprovado/inconclusivo. Um resultado
   incompleto ou uma métrica ausente não é aprovação. Responsável decide adoção.
8. Se o final não foi aberto, arquivar publicamente somente selo, resultados
   de desenvolvimento e motivo do bloqueio; manter textos/gold/anotações sob
   custódia. Se foi aberto, arquivar o pacote final, anotações e trilha de
   exposição em evidências versionadas, sem pesos grandes/ambiente. Em execução
   parcial, distinguir IDs executados e não executados, sem fabricar previsões.
   Repetição idêntica pode ser reprodução técnica identificada; nunca novo
   teste independente.

Exposição prematura do final ao autor do modelo invalida sua independência e
impede qualificá-lo com aquele conjunto. Se o final reprovar, preservá-lo como
histórico: outra candidata exige outro final prospectivo. Se desenvolvimento
reprovar sem abrir o final, uma nova proposta pode manter o pacote ainda fechado.
Correções mecânicas de implementação anteriores à abertura do final são
rastreáveis e exigem novo congelamento, sem mudar dados/hiperparâmetros pelo acerto.

## 8. Entrega e aprendizagem

Entregar especificação e contratos; dados/anotações/selos; fontes e ambiente
fixados; dois modelos recarregáveis e manifesto; tabela das 225 políticas;
congelamento; previsões finais, métricas e auditoria; decisão de adoção.
C06/C07 continuam condicionadas e a [F10 fixture aceita](../../../f10-aceite-integrado.md)
permanece válida como evidência histórica. Atendente real E01 e dez mil
conexões são evoluções opcionais, fora da SF2.

Exercício: antes do treino, discutir um relato público de treino com categoria
clara e prioridade insuficiente. Identificar por que conhecer o assunto não
autoriza inventar urgência. Depois, acompanhar preservação → escolha bruta →
regra de revisão → aplicação atômica no relatório, sem consultar o final.

Referências primárias: [SetFit](https://huggingface.co/docs/setfit/en/quickstart),
[regressão logística 1.8](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html),
[calibração](https://scikit-learn.org/stable/modules/calibration.html).
Versões executáveis são os pins locais; documentação não autoriza atualizá-los.
