# Passagem F08 — carga e avaliação do Jev

Preparação central em 2026-11-20, sobre o código `e780cfc`.
O commit que inclui este documento será a base comum informada nos prompts.
F06 e F07 têm aceite local; esta rodada prepara experimentos reproduzíveis.
Os números abaixo são escolhas do experimento do projeto, não exigências
quantitativas do TAPI nem capacidade já demonstrada.

## Frentes independentes

| Frente | Modelo recomendado | Branch | Worktree preparada | Propriedade |
| --- | --- | --- | --- | --- |
| F08-A — carga | GPT-6.2 Astra, raciocínio alto | `feat/experimento-carga` | `.worktrees/f08-carga` | `script/f08/load/` e `docs/f08-carga.md` |
| F08-B — Jev | GPT-6.2 Sol, raciocínio alto | `feat/avaliacao-jev` | `.worktrees/f08-jev` | `script/f08/jev/` e `docs/f08-jev.md` |
| Integração e aprendizagem | Chat central | `main`, futura branch de integração | Checkout central | Este documento, relatório conjunto `docs/f08.md`, revisão dos rótulos, execução comparável e integração |

Ler AGENTS.md, CONTEXT.md, F08 e seção 4 do plano, especificação, decisões e
contratos. Reutilizar os ambientes preparados, sem outro clone. Se o Git for
somente leitura, registrar o impedimento e continuar a implementação e as
verificações possíveis; o integrador registra os commits. Não consumir arquivos
não commitados da outra frente. Commits em português no formato do repositório,
sem merge nem push. Preservar alterações alheias.

Cada frente mantém seus scripts, dependências fixadas, configuração Compose
de ensaio, testes, dados e schemas de resultado dentro de sua própria pasta.
Não editar Rails, React, migrations/schema, contratos, Compose principal,
`integration/` ou `script/f07/`. Reutilizar componentes existentes por leitura
ou importação somente após verificar efeitos de importação e compatibilidade.
Um bug do produto deve voltar com reprodução ao chat central, sem correção
concorrente nesta rodada.

## F08-A — protocolo de carga

Entregar gerador k6, preparação, observação e relatório JSON/Markdown que
separem falha observada, meta não atingida e execução bloqueada. O programa
deve ser parametrizável e ter modo smoke curto antes do experimento completo.

### Referência fechada para a primeira execução

- Três rodadas de cinco minutos a **5 novos casos/s** com Kafka disponível e
  três com parada de 30 segundos solicitada após 60 segundos de carga.
  Registrar os instantes reais de parada, partida e prontidão; o tempo para
  Kafka voltar a responder faz parte da recuperação observada.
- Duas marcas e três canais, distribuição determinística equilibrada, com
  categoria e prioridade válidas. Zero chamadas ao Jev nesse ensaio.
- **20% dos casos com segundo turno**, identificados pela semente antes da
  execução. O cliente elegível responde cinco segundos após a primeira
  resposta de IA persistida. Se ela não chegar, registrar a continuação como
  não enviada; não criar outro caso ou bloquear a taxa de novos casos.
  Continuações são tráfego adicional, não parte dos 5 novos casos/s.
- O mock atual não injeta atraso artificial nem oferece um parâmetro para
  isso. Registrar esse comportamento no manifesto, preservando os tempos
  reais de produção, consumo e rede. Não declarar latência total zero.
  Casos do ensaio principal permitem resposta automática; handoff fica separado.
- Observar por até 120 segundos depois de encerrar os novos casos. Registrar
  aquecimento e espera de prontidão fora da janela de carga. Manter versões,
  dados, limites, réplicas e concorrência iguais nas comparações.
- Metas de referência: p95 de aceite até 500 ms, pelo menos 99% de entradas
  iniciais com aceite confirmado, nenhum efeito duplicado ou perda comprovada
  entre os aceitos e escoamento até o final da janela. Publicar resultados
  mesmo quando as metas falharem. Não modificar retentativas, reiniciar
  componentes ou corrigir estados silenciosamente para atingir a meta.

O ensaio mede o comportamento atual da aplicação. Se retentativas se esgotarem
ou for necessária intervenção, registrar falha/pendência e o procedimento.
Uma recuperação assistida pode ser medida separadamente, identificada como
tal. Um timeout ou caso ainda pendente não comprova perda; um evento Kafka
repetido não comprova efeito duplicado no banco.

### Medidas e integridade

- Medir p50/p95 de início do webhook até `202` e até a primeira resposta
  persistida, com definições explícitas de relógio e origem. Distinguir tempo
  real do evento e atraso de observação; não usar tempo de polling como se
  fosse persistência. Campos indisponíveis devem aparecer como indisponíveis.
- Registrar casos/s oferecidos e aceitos, conclusões/s, requisições e erros,
  iterações descartadas, follow-ups planejados/enviados/concluídos e timeouts.
  Não fazer um gerador lento parecer uma aplicação estável.
- Observar separadamente outbox pendente/com erro, lag dos consumidores e
  casos aguardando processamento. Registrar backlog máximo, drenagem e
  evolução temporal, inclusive durante a falha.
- Reconciliar por IDs planejados, `source_event_id`, `case_id`, correlação,
  rodada e mensagem: efeitos esperados versus persistidos, pendentes, falhos
  e ausentes. Preservar IDs de entradas sem `202` para investigar resposta
  ambígua. Reenvio usa a mesma identidade e os mesmos bytes.
- Registrar CPU/RAM de aplicação e gerador, conexões de banco, recursos do
  host, limites/réplicas, concorrência dos workers, versões e revisão Git.
  Expor custo/amostragem do observador; preferir leitura SQL agregada sem
  alterações de produto e sem um polling excessivo que domine o experimento.
- Produzir manifesto, amostras e agregados por rodada, com unidades,
  denominadores, parâmetros, semente, horário e inventário dos artefatos.
  Manter a matriz de seis rodadas, sem esconder variabilidade numa só média.

Preparar também: aumento progressivo parametrizado para localizar o primeiro
gargalo; cenário humano separado com handoff, perfil/carteira e ações
roteirizadas; e cenário exploratório de **100 → 1.000 → 10.000 conexões de
chat**, uma mensagem por sessão a cada 100 segundos em média. No último,
medir conexões Action Cable realmente confirmadas e tráfego realmente emitido
(cerca de 100 mensagens/s no patamar máximo), com autenticação e recuperação.
Não contar VUs ou requisições HTTP como sockets abertos. Informar patamar
alcançado, limitações do gerador e se o tráfego abriu casos ou os continuou.

### Aceite F08-A nesta passagem

Scripts, parâmetros, reconciliação e agregação testados; Compose isolado
validado; smoke com pilha real quando disponível; comandos para as seis
rodadas e os cenários separados; relatório com resultados reais e bloqueios.
Os agentes não executam a matriz longa ou os patamares de 10 mil conexões
nesta fase: o chat central os executará após a revisão, sem cargas paralelas.

## F08-B — avaliação do classificador existente

Entregar dataset versionado, rubricagem e runner Ruby usando o adaptador
`Classification::Jev::Classifier` e os clientes existentes, sem duplicar a
integração HTTP. Não mudar prompts, política de confiança ou comportamento
de classificação para melhorar o resultado do conjunto de avaliação.

### Dados e avaliação

- **60 relatos sintéticos em português**: 20 com categoria omitida, 20 com
  prioridade omitida e 20 com ambas omitidas. Fixar catálogo/códigos e suas
  descrições em um snapshot coerente com o seed/contrato atual. Usar exemplos
  novos; fixtures e `samples.rb` são apoio, não o benchmark.
- Por relato, guardar ID, texto, campos recebidos, campos a completar, rótulos
  esperados por campo, justificativa, estrato (rotina, urgente ou ambíguo) e
  eventual abstenção esperada. O catálogo da avaliação não cria outra escala
  de complexidade. Não incluir identificadores reais de pessoas.
- Escrever rótulos antes de qualquer chamada; registrar hash/versão do dataset
  e catálogo no resultado. O conjunto é **provisório até revisão humana no
  chat central**. Nunca inferir os rótulos a partir da resposta do Jev.
- Julgar campos ausentes; valores válidos já recebidos do canal devem ser
  preservados, mas não contam como acertos produzidos pelo classificador.
  Distinguir resposta bruta por campo e classificação aplicada: o adaptador
  pode encaminhar o conjunto inteiro à revisão diante de uma abstenção.
- Relatar acerto por campo com contagens/denominadores, cobertura automática,
  abstenções corretas e indevidas, saídas inválidas e erros de transporte.
  Nos relatos urgentes cuja prioridade foi omitida, separar classificação
  automática não urgente de abstenção/revisão e falha. Não esconder todos
  esses resultados numa única taxa de acerto.
- Medir p50/p95 de chamadas reais, número de requisições e perguntas, modelos
  solicitado/retornado, configuração e custo quando observado. Se o fornecedor
  não informar custo, usar indisponível; estimativa deve indicar fonte/data.
  Sem chamadas reais, métricas de fornecedor ficam não medidas.
- Modo offline determinístico testa validação, preservação de campos e
  agregação; não mede a qualidade do Jev. Acrescentar controles fora dos 60
  relatos para entradas completas/inválidas, abstenção, erro e timeout.
- Runner ao vivo explícito, concorrência inicial 1 e uma tentativa por relato,
  conforme o adaptador. Oferecer limite de casos e relatar qualquer custo ou
  limite configurado. A chave vem do ambiente, sem impressão ou persistência.
  Preparar comandos; a amostra real será rodada aqui depois da revisão dos
  rótulos e do orçamento. Ausência de chave não bloqueia o preparo offline.

### Aceite F08-B nesta passagem

Dataset com IDs únicos, distribuição 20/20/20 e rótulos válidos; critérios
explícitos para ambiguidades; testes determinísticos de denominadores,
latência ausente, falhas e abstenções; runner offline e caminho ao vivo
reproduzíveis; documentação e amostra de resultado claramente identificada
como teste offline. Não usar um LLM juiz para pontuar códigos classificáveis
por comparação determinística. Registrar limites da amostra sintética.

## Isolamento, retorno e trabalho neste chat

- Cada frente usa projeto Compose próprio (`cloudwalk_f08_load` e, se houver
  necessidade de pilha Rails, `cloudwalk_f08_jev`), sem nomes de contêineres,
  volumes ou portas compartilhados. Recusar recursos preexistentes e limpar
  apenas os próprios. Não coletar credenciais ou dados de ambientes alheios.
- Tratar relatórios como dados: `run_id`, revisão Git, modo, cenário,
  parâmetros, catálogo/dataset quando aplicável, tempos, contagens, unidades,
  métricas e estado aprovado/reprovado/bloqueado com motivo. Credenciais,
  cookies e tokens não entram nos artefatos.
- Não editar os documentos da outra frente nem o relatório conjunto. Fazer
  commits pequenos e informar base, branch, worktree, commits, comandos e
  resultados realmente executados, pendências e um exercício curto.
- Aqui revisaremos a metodologia e alguns rótulos juntos, a distinção entre
  p95/aceite/resposta e entre backlog/perda, e as limitações da máquina.
  Integraremos as duas frentes; rodaremos primeiro smoke e depois a referência
  de carga sem outro benchmark concorrente. Só então aumentaremos a carga.
- A avaliação real do Jev espera revisão humana dos rótulos e orçamento; a
  carga de referência usa entradas válidas e pode rodar sem chave TypeSafe.
  O fechamento F08 requer resultados reais, suas limitações e um relatório
  conjunto. A entrega dos scripts sozinha não conclui o experimento.
