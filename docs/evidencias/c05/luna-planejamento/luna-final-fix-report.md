# C05-R3 · Interrupção após resposta sem custo original

Commit `aafc8ce7f3059afa3fb4800620dbd4469247c920`, base `3c3131991152e49b4c3e98aff0ee69b39b2a4324`. Branch `feat/avaliador-luna`, worktree `.worktrees/r3-luna-avaliador` limpa.

O executor fecha financeiramente o caso pelo mecanismo existente. Para a rodada Luna, a continuação também exige a presença de custo observado na resposta original. A checagem usa apenas a presença do valor, inclusive zero. A contabilização continua baseada no Decimal extraído do corpo original e nos recibos do ledger. Um recibo manual mantém seu efeito financeiro mesmo quando o lote é interrompido.

O teste focal usa uma segunda conexão à conta temporária para conciliar o primeiro caso depois de o transporte registrar uso vazio e antes de o executor fechar o caso. Na base, duas reservas chegaram a ser abertas e o teste falhou com `2 != 1`. Após a correção, houve uma reserva e um despacho. A decisão permaneceu semanticamente válida. O prefixo passou pelo checker Luna com elegibilidade inconclusiva, um caso concluído e custo original ausente. A execução ficou interrompida, sem prova de desenvolvimento. O ledger preservou o recibo manual de US$ 0,0017 como settled.

Na worktree, o comando abaixo retornou zero, com três testes aprovados. Os cenários técnicos cobriram HTTP 500 e saída inválida com custo conhecido liquidado, custo ausente, timeout e prazo expirado. No fluxo normal, o teste confirmou 6 + 44 chamadas sintéticas, 50 reservas liquidadas e p95 sem medição.

```sh
rtk proxy env PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna.test_round.LunaTest.test_manual_receipt_cannot_continue_after_missing_gateway_cost luna.test_round.LunaTest.test_technical_stop_and_financial_prefix luna.test_round.LunaTest.test_cli_two_stages_and_replay
```

`rtk git diff --cached --check` passou. O diff contém apenas a decisão de continuar no executor e o teste. A re-revisão é dirigida a esse diff. A verificação usa exclusivamente fixtures e contas temporárias. Qualidade, custo e latência reais continuam pendentes de autorização e execução.

Exercício de leitura: compare, no teste focal, o saldo da conta com o custo exibido na observação. O saldo inclui o recibo manual, enquanto a observação preserva o dado que veio do fornecedor.
