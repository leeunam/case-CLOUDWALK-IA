# Revisão independente da C05-R2 — Task 1

- Branch `feat/r2-instrucoes-qwen`
- Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-qwen`
- Base `c00ac5431630c92d30349c13529d5071ad9879b4`
- Candidata `262d51cc85e377a6a7649d906ae6a8ac8c704c0a`
- Veredito de especificação **APROVADO**
- Veredito de qualidade **APROVADO**

## Achados

Nenhum achado acionável. A recomendação de aceite para congelamento vale para o commit revisado e para o escopo offline da Task 1.

## Evidência da revisão

- O pacote de revisão `review-c00ac54..262d51c.diff` contém somente os três acréscimos previstos. O Git confirmou a candidata como filha direta da base, na branch e worktree indicadas, com a worktree limpa.
- `r2/candidate.json:1–21` tem os quatro campos previstos, IPC `1.1.0`, modo `real`, provedor `feita`, modelo solicitado e esperado `qwen/qwen3.8-27b`, adaptador `1.2.0` e política `1.1.0`. As duas referências apontam para os novos textos, com versão `1.1.0` e hashes iguais aos registrados na autoverificação. O manifesto não inclui comando nem autorização.
- `r2/prompt.txt:1–23` preserva `received`, limita a classificação a `missing` e pede suporte separado para categoria e prioridade. Para a categoria, liga o assunto ao objeto do pedido e exige fato discriminante. Para a prioridade, usa funcionamento, impacto, alternativas e prazo, inclusive circunstâncias que indiquem intervenção imediata. A leitura do relato inteiro, das negações e de expressões equivalentes segue `rubrica-comum.md`, sem adicionar critérios ou depender de palavra específica. Se um dos campos for insuficiente, o outro continua sendo avaliado.
- `r2/prompt.txt:25–27` restringe a saída ao objeto JSON e às chaves obrigatórias, com códigos do catálogo ou `informacao_insuficiente`. `adapter.py:77–92` confirma que o schema estrito pede apenas os campos ausentes e restringe os valores a essas opções. O prompt contém zero exemplos. Nenhum dos três artefatos contém exemplos de casos, exceções por ID ou confiança numérica.
- `r2/politica.txt:3–16` descreve elegibilidade, preservação, abstenção por campo e revisão sem aplicação parcial. A descrição da recusa documentada e das saídas inválidas é compatível com `adapter.py:96–126` e com a rubrica. O adaptador legado também mantém `score` nulo em `adapter.py:36–37`.

## Limites da verificação

A revisão foi estática, com conferência do diff, do contrato, do catálogo e da rubrica. A execução de JSON, hashes e `request_body` para as três máscaras consta no relatório do autor e não foi repetida. Não houve chamada ao fornecedor, acesso a credenciais ou uso de casos finais e saídas de inferência como evidência. Obediência do modelo, acerto, abstenções, preservação no fluxo integrado, custo e latência observados seguem pendentes da validação correspondente. O texto maior e o schema estrito, isoladamente, não permitem estimar esses resultados.
