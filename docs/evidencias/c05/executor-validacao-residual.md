# C05-E · Validação da adjudicação residual

**Os dois resíduos foram resolvidos (ADDRESSED).** A especificação e a qualidade estão aprovadas para o escopo desta adjudicação. A leitura dos quatro arquivos do diff e as contraprovas dirigidas não revelaram regressão introduzida pela correção. A validação é offline e não avalia a qualidade do modelo.

Branch `feat/executor-qwen-final`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao`. Base `20610ca3b431158767e3eaf6d136aca5e48087f3`, commit revisado `e4ce14c95a4a59737b000bcc8dfa21009a1d566d`.

1. **P1 · Expiração financeira e divergência de modelo — ADDRESSED.** Na contraprova independente, o parse de um corpo válido ultrapassou o prazo interno normal em dois milissegundos. A observação validada pela C02 manteve `version_mismatch` e custo de US$ 0,000547. Apenas `jev-001` foi despachado. `jev-016` permaneceu na lista dos casos não iniciados. O SQLite registrou `staged`, `financial_expired=1` e a reserva integral de US$ 1,4004736. Com US$ 8,50 anteriores, o total contabilizado foi US$ 9,9004736. Após reabrir a conta, uma chamada de conclusão com `timed_out=False` foi recusada. O adaptador grava a expiração antes de enviar a observação e o SQLite só permite promover a marca a 1. O diff deixa a C02 e o IPC intactos. Referências: `script/classification_comparison/c05/final_adapter.py:188` e `script/classification_comparison/c05/budget.py:353`.
2. **P2 · Conta legada subcontabilizada — ADDRESSED pela recusa antes da escrita.** A versão 4 é a primeira aceita. Reabri uma conta fixture criada com o código histórico v2 e contendo o caso original de US$ 2,25. A validação, a consulta, a tentativa de registrar outra execução, a marcação de prazo e a conclusão de caso foram bloqueadas. A inicialização no mesmo caminho também foi recusada. Os bytes e a listagem do diretório ficaram idênticos. O teste parametrizado verificou ainda versões 0, 1, 2, 3 e 5, com preservação dos bytes nas tentativas de conciliação e reserva. O teste da conta nova v4 confirmou a conciliação explícita da reserva órfã após queda e o bloqueio do replay. A verificação inicial de versão abre o SQLite em modo somente leitura e imutável, e a transação verifica novamente a versão. Referências: `script/classification_comparison/c05/budget.py:129`, `:140`, `:151` e `:161`. A documentação orienta preservar os arquivos de protótipo. A escolha exclui migração automática.

## Verificações

O corpo do pacote de revisão coincidiu byte a byte com o diff Git de dez linhas de contexto. A verificação de espaços passou. As duas contraprovas independentes e os dois testes de regressão abaixo passaram. O implementador registrou separadamente 3 testes dirigidos e 37 da C05 aprovados. Esta validação usou somente SQLite temporário e transporte simulado.

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B /tmp/c05-residual-timeout.py
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B /tmp/c05-residual-unsupported.py
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY PYTHONPATH=script/classification_comparison/c05 python3 -B -m unittest -v \
  test_qwen_final.AccountTest.test_incompatible_accounts_are_refused_without_modifying_bytes \
  test_qwen_final.ExecutorTest.test_crash_keeps_third_reservation_and_verified_prefix_after_restart
rtk proxy git diff --check 20610ca..e4ce14c
```
