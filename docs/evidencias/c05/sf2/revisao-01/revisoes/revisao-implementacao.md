# Revisão independente da Task 1 · SF2-R1

**Parecer sobre `7ae98ff129ce9058f7ff1ec2c471bbdaafea8396`** — Solicito uma correção na ligação entre os bytes atestados e os bytes usados pela auditoria. A rodada real de 45 permanece pendente.

Base `290dee316c6fde2414f414dcfcb81a72b39daf18`, branch `feat/sf2-revisao-grade`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-revisao-grade`. Os caminhos Python abaixo são relativos a `script/classification_comparison/setfit_sf2/`.

## SPEC

**Pendência de integridade, P2 — `revision_r1/cli.py:168` e `revision_r1/engine.py:75`.** O pré-voo lê e confere os bytes dos insumos em `cli.py:112`, mas devolve os caminhos ao motor. Esse motor abre novamente validação, política, pacote, selo, scores e recibos. O código Python é importado dos bytes retidos, mas `contracts/core.py:71`, `:89` e `:91` também abrem de novo o schema, o protocolo e o catálogo no disco. Uma alteração do arquivo entre as duas leituras deixa a auditoria consumir bytes diferentes daqueles associados ao hash no relatório. Basta considerar o score 03 reformatado nesse intervalo. A igualdade de objetos da linha 75 continua verdadeira, o recibo da linha 79 vincula apenas o score 04 e a paridade das 225 usa os scores derivados dos frames. A divergência do SHA do score 03 pode chegar silenciosamente à extensão. A condição é uma alteração enquanto a CLI está em execução. Não há evidência de que isso tenha ocorrido.

**Correção mínima sugerida.** Disponibilizar ao motor os bytes atestados de todos os recursos que ele reabre, incluindo os JSON usados por `contracts/core.py`. Uma opção que preserva as APIs SF2 é montar uma árvore temporária privada somente com os insumos necessários, preenchida com os bytes já verificados, e resolver nela os caminhos usados pelo motor. Manter o destino oficial da rodada na worktree de execução. Uma fixture focal entre a atestação e a importação/auditoria pode demonstrar que alterações posteriores na árvore de origem são ignoradas ou recusadas antes da avaliação nova.

Os demais pontos do aceite estão cobertos pelo diff e pela evidência de fixtures:

- O inventário atual tem conjunto de membros exigido no inicializador e digest externo. O pré-voo confere a emenda, os caminhos públicos fixos, a captura histórica, os 17 membros do adaptador e os índices públicos. Os hashes do seletor histórico `634d5d89…` e do atual `5c189760…` foram conferidos nesta revisão. A configuração antiga é autenticada pelo digest. A CLI obtém os arquivos pela correspondência canônica de papéis. A saída informa que os pesos físicos não foram verificados novamente.
- O subcontrato limita categoria a 0,95 com três margens e prioridade aos cinco limiares e três margens originais. As 225 políticas preservam o tipo `sf2-ipc/1.0`. As 45 recebem `sf2-r1-offline/1.0`. O relatório vincula a candidata, quando houver, aos digests da emenda, grade original, grades derivadas, insumos e fontes em ambas as versões.
- A auditoria verifica a política mínima de coleta, o selo e os frames dos 90 casos, dos cinco controles e das 95 tentativas ordenadas. Reconstrói o pacote de scores e exige igualdade de objeto com 03 e 04. As quotas preservam 72 classificáveis, 18 revisões esperadas, 60 alvos por campo e 13 urgentes. As funções originais preservam precisão aplicada por campo ≥90% com denominador positivo, cobertura automática ≥51/72, urgente bruto ≥11/13 e os vetos operacionais.
- A API histórica continua a selecionar pela grade antiga. A paridade em `revision_r1/engine.py:92` exige 225, seleção nula e igualdade de objetos e bytes de todo o arquivo, inclusive a baseline. A extensão só é avaliada após a prova e a contagem de 270 chaves distintas. A união usa a ordenação original, inclusive os quatro cortes no desempate.

## QUALITY

**Aprovação pendente da correção P2 acima.** O núcleo de decisão foi extraído sem duplicar as regras. O diff preserva margens estritas, empate no limiar de confiança, veto da classe de revisão e aplicação atômica dos campos. As métricas, intervalos, matrizes e razões de veto são rastreáveis às mesmas funções da SF2.

A CLI reserva o diretório por criação exclusiva antes da primeira política nova e publica o resultado completo sem sobrescrever o destino. Uma interrupção depois da reserva pode deixar esse diretório para investigação. Os caminhos normais retornam 0 para elegibilidade em validação, 1 para resultado negativo e 2 para insumo ou execução inválidos. O tempo informado mede o cálculo da extensão. O resultado declara o bloqueio do final, da adoção e de C06/C07. O README explica a escolha do corte após observar a validação.

## Evidência e limites

Revisei o brief, relatório do autor, pacote de diff integral, protocolo, sete arquivos alterados e as dependências locais pertinentes. Confirmei o pai do commit, os sete caminhos, a limpeza da worktree, os dois digests do seletor e os digests conferidos de emenda `c3a6db8134f71491c1e743ddf6d57a400bba6449017b336e0a311c02f4eb07b3` e inventário `f459a21a4fea1a78ab2b65c6df71a697dbb4666adb5d50ce8ff0cb4f7999475d`. `rtk git diff --check 290dee3 7ae98ff` passou.

Os 11 testes aprovados em 7,051 s são evidência registrada pelo autor. Inspecionei as fixtures, as asserções e o bloqueio de recursos externos sem repetir a suíte. As verificações de adulteração preexistente e de semântica separadas deixam descoberto o intervalo descrito no achado. A paridade real, o resultado das 45 e sua elegibilidade cabem à Task 2 depois do aceite. Nenhum modelo, chamada externa, dado final reservado ou política real foi usado nesta revisão.

Para acompanhar a regra na fixture, siga Pix 0,92 com margem 0,84 e delta zero. O corte 0,90 aceita categoria. Em 0,95 o caso entra em revisão e, quando categoria e prioridade estão ausentes, a aplicação de prioridade também fica suspensa.
