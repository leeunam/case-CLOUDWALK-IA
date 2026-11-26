# SF2-R1 · Revisão da correção 1

**P2 — ADDRESSED. SPEC e QUALITY aprovados.** A correção fecha a divergência possível entre os bytes autenticados e os usados no replay. A Task 1 está aprovada para integração pelo responsável.

Revisão delimitada ao diff de `7ae98ff129ce9058f7ff1ec2c471bbdaafea8396` até `99cf2f33e1803838e33813d5c4ff46971181ce4e`, na branch `feat/sf2-revisao-grade`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-revisao-grade`. Os caminhos abaixo partem de `script/classification_comparison/setfit_sf2/revision_r1/`.

## SPEC

Em `cli.py:112`, o inicializador retém os bytes conferidos e cruza os recursos compartilhados pelos inventários. Em `cli.py:166`, retém também o stderr autenticado pelo selo. Em `cli.py:224`, a árvore privada recebe esses bytes, inclusive os do protocolo, schema, catálogo, validação, decisões, tempos, scores e recibos. Em `cli.py:230`, o motor recebe a nova raiz para resolver os arquivos que abre por caminho. O carregador continua executando o código Python que passou pela verificação. A grade arquivada continua em memória.

A fixture de `test_replay.py:263` altera oito entradas depois da atestação. No score 03, muda os bytes preservando o conteúdo JSON. Durante o replay, a fixture bloqueia leituras da origem via `Path.open`, observa o digest do score efetivamente aberto e o confronta com o valor publicado. As asserções das linhas 291 e 292 distinguem igualdade de objetos de igualdade dos bytes consumidos.

## QUALITY

O diretório temporário tem ciclo de vida delimitado. A reserva exclusiva em `cli.py:236` e a publicação do resultado ainda usam o destino da worktree oficial. A reserva ocorre depois da paridade das 225 e antes das novas políticas. O diff altera apenas o inicializador, sua entrada no inventário, a documentação e a fixture. Nenhuma regressão identificada na correção.

Conferi o pai Git, a limpeza da worktree, os quatro arquivos modificados e o resultado de `rtk git diff --check 7ae98ff 99cf2f3`, que passou. Os digests lidos nesta revisão foram:

- Emenda — `c3a6db8134f71491c1e743ddf6d57a400bba6449017b336e0a311c02f4eb07b3`.
- Inventário — `f9199e3535f5504df2a1c9f11b317b526920d643a2653328fd5012f61eb8739e`.
- Inicializador — `ef8a233923e01c7e7ad6ddb40c80e7c75de38530f5d85d882d9b949583ae1b81`, correspondente à entrada no inventário.

O autor registrou sete testes R1 aprovados em 7,500 s e a verificação focal reforçada aprovada em 1,651 s. A revisão verificou o código e as asserções sem repetir a execução. A paridade e o resultado da captura real continuam pendentes da Task 2. Nenhuma política real, modelo ou dado final foi utilizado nesta revisão.
