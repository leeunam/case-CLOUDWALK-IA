# Pares de diagnóstico R4

A Task3-D2 preparou 16 relatos sintéticos inéditos, organizados em oito pares,
para desenvolvimento. O conjunto v1.0.0 usa o contrato IPC 1.1.0,
a rubrica comum v1.0.0 e o catálogo v1.0.0. O bloco `metadata` em
[annotations.json](annotations.json) registra os caminhos, versões, hashes
SHA-256 e contagens.

- [inputs.jsonl](inputs.jsonl) contém uma entrada por linha, com identificador
  opaco, texto, campos recebidos, campos ausentes, marca sintética, catálogo e
  versão do contrato.
- [annotations.json](annotations.json) guarda, por ID, a expectativa para cada
  campo ausente, a justificativa, o fato distintivo e a relação dentro do par.
  A direção de cada relação é a ordem dos dois registros em `cases`.
  `preservada` refere-se a uma prioridade recebida. `mantem` indica que a
  classificação pedida é a mesma nos dois relatos.

Para a rotulação cega, o integrador entrega somente `inputs.jsonl` e a
[rubrica comum](../../rubrica-comum.md) à pessoa ou agente independente. O
leitor devolve um arquivo de rótulos por ID, com respostas apenas para
`missing` e uma justificativa curta, antes de conhecer os pares e as
expectativas. Em seguida, o integrador compara os rótulos cegos com as
anotações e registra divergências para revisão. Os campos fornecidos em
`received` continuam válidos mesmo quando o caso segue para revisão.
Uma abstenção em qualquer campo pedido impede a aplicação do complemento.

Proveniência: relatos e anotações redigidos por IA na Task3-D2. A verificação
desta entrega é estrutural e a rotulação cega fica pendente. Estes são dados de
desenvolvimento e não integram o conjunto final nem registram resultados do
Luna.
