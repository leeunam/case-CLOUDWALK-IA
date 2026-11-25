# Task3-D1 · Revisão antes do congelamento

## SPEC · Aprovada

- A mudança de categoria distingue a demanda do cliente de operações mencionadas como contexto. Uma consulta clara continua classificável em linguagem comum, inclusive antes de executar a operação ou com resultado desconhecido. `script/classification_comparison/adapters/luna/r4/prompt.txt:5`.
- A instrução distingue relações afirmadas, negadas e hipotéticas. Uma falha de operação identificada pode definir o assunto. Descartar uma operação não determina outra. A abstenção se aplica quando o objeto segue indefinido ou quando escolher entre categorias exige presumir um fato. O critério é semântico e o prompt dispensa atalhos por texto ou ID. `script/classification_comparison/adapters/luna/r4/prompt.txt:11`.
- A comparação independente dos bytes do pacote com a base confirmou a abertura e todo o trecho de prioridade até a saída JSON idênticos. O manifesto preserva contrato, identidade, política e rubrica nas mesmas cinco chaves. O pacote acrescenta apenas o prompt, o manifesto e a nota, preservando os arquivos operacionais e congelados da R3. `script/classification_comparison/adapters/luna/r4/prompt.txt:20` e `script/classification_comparison/adapters/luna/r4/candidate.json:2`.
- Os SHA-256 da instrução e do manifesto reconstruídos do pacote conferem. Os hashes das fontes de política e rubrica também conferem com o manifesto. `script/classification_comparison/adapters/luna/r4/candidate.json:11`.

## QUALITY · Aprovada para congelamento

- **Críticos, importantes e menores** — nenhum achado.
- A rubrica continua responsável pelos significados das categorias. A instrução explica como avaliar a suficiência do relato e a nota delimita o que a verificação observou. `script/classification_comparison/adapters/luna/r4/prompt.txt:1` e `docs/evidencias/c05/r4-instrucao/nota.md:17`.
- O autor relata que o construtor real do corpo JSON foi verificado localmente nas três combinações de campos ausentes. O teste relatado cobre parâmetros, projeção, schema e conteúdo da mensagem de sistema. A revisão independente conferiu a integridade do pacote por comparação e hashes, sem repetir esse teste. `.superpowers/sdd/conclusao-projeto/r4-instrucao-report.md`.

## Limites

- Acerto, cobertura, latência e custo R4 seguem sem medição. O efeito da instrução sobre a cobertura em relatos novos exige avaliação posterior. A revisão usou o material autorizado, sem dados de diagnóstico novos, conjuntos finais ou chamadas externas. `docs/evidencias/c05/r4-instrucao/nota.md:25`.
- Base `3e59f4ad80536b5586e91c89a2ea157bebbcb442`, candidata `2f6698495577ec9064f7020d2e0f0825bcc3a74f`, branch `feat/luna-instrucao-r4`, worktree `.worktrees/r4-luna-instrucao`.
