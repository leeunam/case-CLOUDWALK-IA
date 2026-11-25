# SF2-03/04 — interface de implementação

Esta passagem concretiza o contrato `sf2-ipc/1.0` já aprovado. Os formatos de
entrada, decisão, scores, política e congelamentos continuam em
[contratos](contratos/README.md). Dados, receita de treino e critérios de
qualificação permanecem os do protocolo.

## Transporte local

O worker de 03 recebe a localização do pacote e da política por argumentos de
inicialização documentados no seu README. O avaliador de 04 recebe o comando
completo do worker como uma lista de argumentos; não monta comandos de shell.
Assim, não depende do nome das opções internas escolhidas por 03.

- Após verificar e carregar os artefatos, o worker escreve uma linha JSON
  `{"type":"ready"}` em stdout e a descarrega imediatamente. Não executa um
  forward para aquecimento. O tempo até esse sinal é registrado separadamente.
- Depois, cada linha de stdin contém um `input` do contrato. Cada resposta é
  uma única linha `decision`, na mesma ordem e com o mesmo ID, seguida de flush.
- Stdout contém somente esses frames. Logs e diagnósticos usam stderr. EOF
  encerra o worker. Falha que impede resposta válida encerra o processo e é
  registrada pelo executor, sem reinício ou repetição de casos no ensaio final.
- 04 valida o comando como argv, o sinal de readiness, o contrato das decisões
  e a correspondência com a entrada. Aplica o prazo aprovado por caso e mede
  monotonicamente o tempo total, incluindo transporte e validações.

O sinal de prontidão é enquadramento do processo, não uma decisão de atendimento
nem um novo campo do contrato. Fixtures de processo devem ser identificadas
como controles de implementação, sem resultados atribuídos ao SetFit real.

## Propriedade e independência

03 possui provisionamento, supervisão externa do limite de treino, artefatos,
reload e worker do adaptador. 04 possui métricas, seleção offline da política,
execução supervisionada do worker durante o ensaio e congelamento da avaliação.
São supervisores de etapas diferentes; não há importação obrigatória entre os
dois módulos para aceitar suas implementações na mesma base.

04 pode testar com um worker de fixture que implemente esse transporte.
03 testa o próprio worker e seus artefatos com fixtures identificadas. Depois
dos aceites individuais, o integrador verifica os dois juntos com fixtures,
antes de qualquer execução com os dados da pesquisa.

A seleção das 225 políticas reaproveita os mesmos scores. Seu replay offline
é separado da decisão recebida do candidato: o auditor verifica a resposta
original e rejeita inconsistências, sem corrigir uma aplicação parcial ou um
score inválido. Tempos de replay não são latência observada de classificação.
Qualquer ambiguidade sobre cronologia ou medição deve ser resolvida pelo
integrador antes de liberar a execução real em 05.

## Coleta da validação e política selecionada

A validação faz uma única passagem pelo worker. Antes dessa passagem, fixa
uma política de coleta com os menores cortes de score e margem da grade
aprovada, nos dois campos. O executor de 04 preserva um JSONL com as decisões
originais e um journal separado com tempos externos observados, IDs, erros e
origem. O `elapsed_ms` emitido pelo worker não é sobrescrito para acrescentar
transporte: o journal registra a duração total externa usada no relatório.

O extrator `scores` de 03 consome o JSONL original já selado, a política de
coleta e as identidades/hash do pacote. Confere cada decisão contra o contrato
e extrai os mesmos vetores, sem carregar o modelo para novos forwards. 04
também pode derivar o pacote desses frames; a integração confere a igualdade
das extrações. Não há uma segunda execução dos 90 relatos para extrair scores.

A grade usa esses scores para calcular os resultados de cada política. As
métricas aplicadas do relatório de validação correspondem à política vencedora.
A latência de validação é diagnóstico da coleta real, identificada como tal;
não é uma medição da execução com a política vencedora, nem tempo de replay.

No congelamento, `validation_predictions` continua sendo o JSONL original da
coleta e `policy` é a política selecionada. A auditoria de 04 deve verificar
essa distinção: decisões originais contra a política de coleta, scores contra
seus vetores originais e métricas/cortes contra o replay da vencedora.
`freeze.files.command` deve vincular por hash o descritor da execução, que
por sua vez vincula política de coleta, journal de tempos, scores e recibo da
seleção com a tabela das 225 políticas. Todos esses bytes são conferidos pelo
comando de auditoria/congelamento antes de autorizar a abertura do final.
O validador mínimo de 00, sozinho, não substitui essa auditoria de cronologia,
seleção e medição.

O ensaio final inicia outro worker com a política vencedora. Suas 120 decisões
e durações são observadas nessa execução, uma tentativa por caso, sem forward
artificial de aquecimento. A latência final usa o total externo observado.

## Limites desta onda

03 e 04 implementam e verificam código. Não treinam os especialistas, não
extraem scores dos 90 relatos, não acessam os finais reservados, não alteram
os dados ou parâmetros e não usam API de classificador. Instalação e imports
seguem os pins locais de SF1; ambiente e cache já disponíveis podem ser
reutilizados somente após conferir os arquivos e versões. Artefatos grandes e
ambientes permanecem ignorados. A F10 aceita continua preservada.
