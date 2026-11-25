# Revisão da correção do espelho de QA da SF2, onda 2

Base `4f219583d9895332ce5511ca4d5c8b41250dd2bd`, head `9507887152b86a76901621fc38838e088ae2af82`, branch `feat/sf2-integracao`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-integracao`. As referências abaixo apontam para `docs/evidencias/c05/sf2/integracao-onda2/` nessa worktree.

## SPEC — APROVADO

O modo focal autentica o recibo histórico e seleciona seus papéis de captura após verificar a captura arquivada e os hashes de frames, journal e controles (`verificar.py:450–460`). O manifesto, o índice e o protocolo passam pela conferência de SHA-256 antes de suas chaves influenciarem os caminhos. A configuração preservada precisa coincidir com os papéis e caminhos derivados da factory e do manifesto (`verificar.py:216–237`). A comparação dos papéis aceita como única diferença o par de hashes conhecido de `evaluation/workflow.py` e precede a primeira cópia (`verificar.py:24–27,249–261`). Conferi os dois hashes do fluxo contra os commits e o hash do inicializador público.

## QUALITY — APROVADO · P2 ADDRESSED

`verificar.py:203–212,239–261` rejeita caminhos relativos não canônicos, componentes de subida, origens ausentes ou não regulares, caminhos redirecionados e destinos existentes. O roteiro monta e verifica todos os pares de origem e destino antes de iniciar as cópias. Isso cobre o índice e a configuração adulterados apontados no P2 e restringe o espelho a fontes e metadados autorizados. A revisão considera a worktree e a saída privada sob custódia do operador, como documentado no relatório.

`test_espelho.py:64–100` exige seis recusas específicas com zero chamadas ao `copyfile` e preservação do marcador inofensivo. Conferi o log arquivado dos seis testes e seu SHA-256. O recibo `passed/0` da execução focal coincide byte a byte com `recibo-custodia.json` (`0141eb2db83b00fcb8cb06a8398e8c37c26155aa1b4b246e2ae16f9ca3288e49`), com oito recusas e os dois pré-voos íntegros. O recibo da rodada original também permanece idêntico ao commit arquivado. A rechecagem focal usou o modo de custódia (`verificar.py:450–465`), com início de worker bloqueado nas sondas.

O pacote de revisão coincide byte a byte com o diff Git com dez linhas de contexto. `git diff --check` e o parse dos dois arquivos Python passaram. Nenhuma regressão nova foi identificada no escopo do diff. A revisão foi estática e usou somente o log e os recibos já produzidos, sem executar o roteiro, os testes ou nova inferência.
