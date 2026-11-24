# C05-R3 Task3-B · Correção dirigida 1

Commit `3b085fcbbf62fdaee8fe74fabad5416c0aa374a7`, base `85803430f17d5f582b26890e621746412a85db66`. Branch `feat/avaliador-luna`, worktree `.worktrees/r3-luna-avaliador` limpa.

A CLI resolve o destino e aplica a guarda da rodada antes de inicializar, consultar ou conciliar uma conta. O comando de inicialização entrega o caminho resolvido à criação exclusiva existente. O Git comum e as contas no teste focal são temporários. O teste recusa o caminho reservado ausente e um alias por link de diretório sem criar arquivo. Com arquivo já presente, verifica a recusa pela guarda e a preservação dos bytes. Em um caminho comum, confirma a criação e a leitura da identidade sintética.

Antes da mudança, a regressão reproduziu a criação indevida. Depois da mudança, este comando passou nos dois testes, incluindo as seis chamadas de desenvolvimento e 44 finais por fixture, com 50 reservas liquidadas.

```sh
rtk proxy env PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna.test_round.LunaTest.test_init_account_guards_reserved_path_before_creation luna.test_round.LunaTest.test_cli_two_stages_and_replay
```

O smoke do wrapper histórico também passou. Dentro de um `TemporaryDirectory`, executei `rtk proxy python3 -B script/classification_comparison/r2/execute.py init-account --mode fixture --account CAMINHO_TEMPORARIO/fixture.sqlite --cap-usd 10 --previous-spend-usd 0`. Verifiquei a existência do arquivo, o escopo fixture, a identidade e o saldo contabilizado zero. `rtk git diff --cached --check` passou. A alteração alcança apenas o dispatcher e o teste, preservando o ledger e as fontes congeladas.

O aceite desta correção cobre a criação de fixtures. As verificações amplas anteriores permanecem no relatório da Task3-B. A re-revisão independente do diff e o pré-voo real permanecem com o integrador. Esta rodada usou somente fixtures, sem abrir a conta real ou consultar a rede.
