# SF2 — modelos de passagem para os agentes

Os prompts abaixo são **templates do integrador**, não autorizações de execução.
Antes de enviá-los, o chat central registra a aprovação da especificação, integra
essa aprovação e substitui `{{COMMIT_BASE}}` pelo SHA concreto correspondente.
Nunca enviar um prompt com esse marcador sem preencher nem usar HEAD móvel.
A base de 00/01/02 é comum; bases de ondas posteriores contêm seus aceites
integrados. Consulte [tarefas](tarefas.md) para escopo, propriedade e bloqueios.

## Primeira onda — após aprovação da proposta

### SF2-00 · Astra, alto

```text
Leia AGENTS.md, CONTEXT.md e /home/inteli/.codex/RTK.md e use RTK.
Tarefa SF2-00. Commit-base: {{COMMIT_BASE}}.
Repositório principal: /home/inteli/Documents/projetos/case-CLOUDWALK-IA.
Branch feat/sf2-contratos, worktree .worktrees/sf2-contratos na raiz.
Confira se já existem e a quem pertencem; reutilize se esta tarefa já começou.
Leia docs/planejamento/classificacao-comparativa/sf2/especificacao.md,
protocolo.json e o card SF2-00 em tarefas.md na base fornecida.
Implemente somente contratos/validadores/fixtures do card, sem alterar os
contratos históricos, dados, treino, regras ou demonstração. Coordene qualquer
ambiguidade de interface com o integrador antes de outros agentes consumirem.
Sem subagentes, API do classificador, .env, credenciais, treino, merge ou push.
Entregue commits, verificações realmente executadas, limitações e exercício.
A integração fica no chat central.
```

### SF2-01 · Sol, alto

```text
Leia AGENTS.md, CONTEXT.md e /home/inteli/.codex/RTK.md e use RTK.
Tarefa SF2-01. Commit-base: {{COMMIT_BASE}}.
Repositório principal: /home/inteli/Documents/projetos/case-CLOUDWALK-IA.
Branch feat/sf2-dados-publicos, worktree .worktrees/sf2-dados-publicos na raiz.
Confira e reutilize apenas o ambiente que pertença a esta tarefa.
Leia docs/planejamento/classificacao-comparativa/sf2/especificacao.md,
protocolo.json e o card SF2-01 em tarefas.md.
Produza somente os 150 relatos de treino e 90 de validação e os registros de
autoria/anotação/quotas, nos arquivos do card. Não crie os 120 finais.
Não leia o pacote final, previsões de modelos, .env ou contas financeiras.
Sua anotação inicial não substitui a segunda anotação independente que o
integrador atribuirá a outro agente. Não dispare subagentes nem faça treino.
A autoria pode começar junto de SF2-00; validação final e selo dos dados
esperam o validador aceito/integrado, em nova base fornecida pelo integrador.
Não altere contratos/gates/rubrica para fazer seus dados passarem.
Sem API do classificador, merge, push ou alterações na demonstração.
Entregue commits, verificações reais, dúvidas de rótulo e exercício público.
```

### SF2-02 · Sol, alto, pessoa/instância distinta da candidata

```text
Leia AGENTS.md, CONTEXT.md e /home/inteli/.codex/RTK.md e use RTK.
Tarefa SF2-02. Commit-base: {{COMMIT_BASE}}.
Repositório principal: /home/inteli/Documents/projetos/case-CLOUDWALK-IA.
Branch feat/sf2-dados-finais, worktree .worktrees/sf2-dados-finais na raiz.
Confira e reutilize apenas o ambiente que pertença a esta tarefa.
Leia docs/planejamento/classificacao-comparativa/sf2/especificacao.md,
protocolo.json e o card SF2-02 em tarefas.md.
Você é custodiante do final; não treina modelos nem escolhe limiares.
Prepare 120 relatos finais novos com as quotas, revisão e auditoria de
semelhança previstas. Textos, gold e anotações ficam somente em
/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.superpowers/sdd/conclusao-projeto/sf2-final/.
Não varra outras pastas privadas. Não publique casos/justificativas em chat,
Git, relatório compartilhado ou saída de terminal. Entregue publicamente
apenas hashes, contagens e recibo nos dois arquivos do card.
O integrador atribuirá o anotador independente; não dispare subagentes.
A autoria pode começar junto de 00/01, mas auditoria e selo esperam dados
públicos e validador aceitos em nova base fornecida pelo integrador.
Selo fechado antes do primeiro treino, sem usar previsões para corrigir gold.
Sem API do classificador, .env, credenciais, merge, push ou demo.
Entregue commits de metadados, localização privada do pacote, verificações
executadas e limitações, sem expor o conteúdo reservado.
```

## Anotação independente — instância fresca designada pelo integrador

O integrador entrega ao anotador somente textos, IDs e rubrica, sem rótulos,
justificativas ou decisões do primeiro anotador. A passagem identifica qual
partição pode ser lida e o caminho de entrega reservado. Para finais, nem a
anotação nem os casos vão ao chat compartilhado. As duas anotações são lacradas
antes da conciliação, que registra versões, motivos e eventual substituição.
O agente que viu o final não pode assumir posteriormente treino/política.

## Segunda onda — templates para bases posteriores

03 e 04 usam o mesmo início de mensagem acima com seu ID, SHA integrado de
00, branch/worktree e card correspondentes. Acrescentar literalmente:

```text
Trabalhe somente nos arquivos do seu card em tarefas.md.
Não leia o pacote final, não altere dados/rótulos, contratos, protocolo,
limiares ou métricas fora do seu escopo. Primeiro implemente com fixtures.
Não rode treino real, scores de validação ou teste final enquanto o chat
central não fornecer a base com 00–04 aceitas e os dados/selos revisados.
Sua worktree não pode consumir alterações não commitadas de outra frente.
Sem subagentes, API do classificador, .env, credenciais, merge ou push.
```

Para 05, o integrador prepara um único ambiente integrado e agenda as medições.
06 só recebe prompt após qualificação elegível, decisão de adoção e contrato de
proveniência. 07 só recebe prompt após C06 aceita. Não preencher esses SHAs
antecipadamente com a base de planejamento, pois isso omite dependências reais.
