# Re-revisão independente da SF2-04 · correção 2

**Achado Important de integração — ADDRESSED.** Branch `feat/sf2-avaliador`, worktree `.worktrees/sf2-avaliador`, base `237df80b4d27229fe79456f943cc11dc2b31f066`, entrega `2a24f0d0ed6b29d2263450ddeb416af19a49111c`. As referências abaixo partem de `script/classification_comparison/setfit_sf2/`.

## SPEC — compliant

- `evaluation/workflow.py:32` valida a estrutura dos índices do adaptador e do treino. Em `evaluation/workflow.py:37` exige caminhos POSIX canônicos e relativos, sem travessia nem resolução para fora da raiz. Em `evaluation/workflow.py:40` exige o conjunto completo de nomes do inventário congelado de treino acrescido de `adapter/__main__.py`.
- `evaluation/workflow.py:43` compara cada SHA declarado com os bytes do arquivo na worktree. Depois da conferência, `evaluation/workflow.py:48` exige igualdade do mapa de nomes e hashes do adaptador, retirado o ponto de entrada adicional, com o mapa recalculado pelo helper aceito de 03. O helper inclui `adapter/decide.py` e `contracts/__init__.py` em `training/fit.py:21`. O entrypoint também passa pela verificação individual dos bytes. O valor devolvido em `evaluation/workflow.py:51` identifica os bytes exatos do próprio índice.
- O pré-voo chama essa verificação em `evaluation/workflow.py:113` e `evaluation/workflow.py:137`, antes do início do worker. A reauditoria recalcula o recibo em `evaluation/workflow.py:151`. Ela é exigida para emitir o freeze e para conferir uma liberação existente, antes de registrar a exposição e abrir o inventário reservado em `evaluation/workflow.py:214` e `evaluation/workflow.py:218`. A nova interface de `c910ba8` atribui ao operador a custódia do argv e do intérprete que resolvem o worker nessa mesma worktree. O README documenta essa condição em `evaluation/README.md:27`.

## QUALITY — approved

O teste de `evaluation/test_workflow.py:99` usa processos novos no espelho de fontes. Confere uma captura e um freeze íntegros, inclusive o digest do índice nos dois recibos em `evaluation/test_workflow.py:143`. Em `evaluation/test_workflow.py:149`, altera separadamente decisão, entrypoint e inicialização dos contratos, mantendo fixos o índice, o argv e a configuração. A cada alteração, exige recusa nas três fases, identifica o membro divergente e verifica que não houve início da coleta, emissão de release ou exposição. A mesma regressão cobre omissão do entrypoint, omissão simultânea de um módulo do índice e do espelho, travessia e symlink externo em `evaluation/test_workflow.py:103`.

O implementador registrou três testes de fluxo aprovados, incluindo as nove recusas entre três fontes e três fases. Esta revisão examinou o diff, o helper de inventário, as chamadas da cadeia e a interface aprovada. A leitura não deixou dúvida que justificasse repetir os testes. Nenhum novo achado no diff. A rechecagem independente da integração com a fixture de 03 permanece pendente. O conjunto reservado permaneceu fechado.
