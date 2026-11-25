# C05-E · Revisão dirigida da correção 1/5

- Branch `feat/executor-qwen-final`.
- Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao`.
- Base `24da473a4a20775d495775b2ee578d7df3afede3` e correção `aee264c2d1b38344bc9b41c7d5b84f03c8941b80`.

## Veredito de especificação

**Aprovada na revisão dirigida.** A correção atende aos três achados do parecer anterior. Os cenários verificados mantêm a cobrança independente da classificação, congelam a conta quando a evidência demonstra violação e impedem atribuição dupla de recibo.

## Veredito de qualidade

**Aprovada na revisão dirigida.** A correção preserva a evidência original e aplica a revisão financeira atomicamente. A migração da conta legada preserva o estado no caso de recibos ambíguos. Sem nova quebra identificada no diff da correção.

## Achados anteriores

1. **P1 · Cobrança com contador ausente ou HTTP de erro · ADDRESSED.** O extrator valida o custo independentemente dos contadores. Os dois vetores originais, resposta HTTP 200 sem `completion_tokens` e resposta HTTP 500 com uso USD válido, conservaram US$ 2,25 no SQLite e na observação C02, contabilizaram US$ 9,35 e congelaram a conta. Os dois prefixos passaram no verificador. O erro HTTP manteve a escolha com motivo `transport`. [Extração financeira](/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao/script/classification_comparison/c05/final_adapter.py:71) · [Captura da resposta](/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao/script/classification_comparison/c05/final_adapter.py:148)
2. **P1 · Recibo tardio acima da reserva · ADDRESSED.** O recibo de US$ 2,25 elevou o total a US$ 10,25, conservou os US$ 0,001 originais e bloqueou a próxima reserva após reabertura. No vetor adicional, a correção de US$ 1,00 permaneceu abaixo da reserva original do caso, mas elevou a conta a US$ 10,4004736 com outra reserva pendente. A guarda bloqueou inclusive a marcação de despacho dessa reserva já existente. A reapresentação do mesmo recibo continuou recusada. [Conciliação](/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao/script/classification_comparison/c05/budget.py:330) · [Correção e congelamento](/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao/script/classification_comparison/c05/budget.py:357)
3. **P2 · Recibos duplicados por espaços nas extremidades · ADDRESSED.** Espaços, tabulação e espaço não separável nas extremidades resultaram na mesma chave. A segunda reserva permaneceu íntegra. O código também compara recibos atuais, anteriores e de correção. Uma colisão legada entre dois casos bloqueou a migração. A transação desfez a criação da tabela e preservou a versão e valores originais. [Normalização](/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao/script/classification_comparison/c05/budget.py:96) · [Migração](/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao/script/classification_comparison/c05/budget.py:155) · [Verificação de atribuição](/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao/script/classification_comparison/c05/budget.py:268)

## Verificação

```sh
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git diff --check 24da473..aee264c
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B /tmp/c05-executor-re-review-probes.py
```

O diff do pacote equivale byte a byte à saída de `rtk proxy git diff -U10 24da473..aee264c`. A worktree estava limpa. As contraprovas passaram com simulação e SQLite temporário. Consultei o registro do implementador para os sete testes dirigidos e a suíte de 28 testes da C05. Esta revisão executou somente as contraprovas próprias, sem rede, credenciais ou conta real.
