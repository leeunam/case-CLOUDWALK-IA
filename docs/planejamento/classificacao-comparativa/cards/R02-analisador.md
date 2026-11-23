# R02 — Preservar provas de atraso e atribuir escritas de chat após timeout

Issue publicada: [#9](https://github.com/leeunam/case-CLOUDWALK-IA/issues/9). Consulte a issue para progresso e comentários atuais.

## Parent e especificação

[Quadro CLASS-001](../README.md). Pendências do instrumento F08 de carga,
independentes do avaliador de classificação e da correção R01.

## O que construir

Como leitor do experimento, receber um relatório que conserva uma falha de prazo
positivamente demonstrada mesmo com outro horário ausente, e reconhece uma
escrita de chat persistida apesar de resposta HTTP ambígua. Corrigir as duas
reproduções residuais da revisão final sem editar os dados históricos.

## Critérios de aceite

- [ ] Com `completed_ms=null` e `published_ms=end_ms+1`, conservar a lacuna do
  carimbo e marcar drenagem falsa, com falha observada de prazo. Uma prova
  disponível não é apagada por outra informação ausente no mesmo turno.
- [ ] Se todos os horários disponíveis estiverem no prazo e faltar um obrigatório,
  a meta pode continuar indeterminada e a medição bloqueada, sem inventar atraso.
- [ ] Atribuir a escrita de chat por canal e `source_event_id` no índice SQL,
  conferindo separadamente caso/correlação do recibo quando presentes.
- [ ] Uma escrita persistida com timeout e `case_id=null` não vira automaticamente
  entrada não planejada/mensagens sem atribuição. O erro HTTP continua contado.
- [ ] Ausência de escrita ou múltiplas correspondências SQL não são resolvidas
  escolhendo silenciosamente um caso. Distinguir ambiguidade e efeito excedente.
- [ ] Testes dirigidos cobrem as duas reproduções e contrapontos. Reanálise dos
  sete históricos preserva seus estados/contagens/latências ou explica qualquer
  divergência real em um novo artefato, sem sobrescrever originais.
- [ ] Conferir o confronto de efeitos nos dois sentidos e a distinção entre
  cópias em offsets diferentes e reprocessamento do mesmo offset.

## Fora do escopo

Corrigir consumidores, modificar produto para atingir meta, repetir a matriz
longa ou alterar o conjunto/modelos da comparação de classificação.

## Bloqueado por

Nenhum card de classificação. Pode iniciar em paralelo com R01 ou com as
frentes de classificação, com propriedade de arquivos separada.

## Execução e retorno

Papel: agente do analisador de carga. Ler AGENTS.md e relatório F08; o integrador
informa a base. Usar branch/worktree próprias; editar somente o instrumento e
seus testes/guia. Entregar commits, verificações e comparação analítica versionada.
Qualquer execução real é coordenada para não concorrer com outro benchmark.

## Exercício de aprendizagem

Comparar um timeout de HTTP com o snapshot SQL e explicar por que a falta do
recibo não comprova ausência da mensagem.
