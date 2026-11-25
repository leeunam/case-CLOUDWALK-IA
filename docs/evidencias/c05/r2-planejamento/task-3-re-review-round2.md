# C05-R2 · Re-revisão da correção 2

- **SPEC · Aprovada.** O compromisso do selo deriva dos bytes originais produzidos pela execução. A substituição dos arquivos públicos no intervalo identificado é rejeitada.
- **QUALITY · Aprovada.** P1 fechado. P2 e Minor permanecem fechados conforme a primeira re-revisão. Nenhum achado aberto no escopo desta rodada.
- Base `9dfbc0d0fe1a981946e2e05e41395b6146b77d05`, commit `3f66bec2e6ac89c03ffd298fbfb9d5fcc5e428e5`, branch `feat/r2-avaliador`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-avaliador`.

## P1 · Fechado

O executor conserva em memória os hashes do plano, da invocação, das entradas, do relatório e das três sequências do diário. Os escritores de JSON retornam o hash do conteúdo que serializaram. O diário atualiza seus hashes com as linhas efetivamente produzidas e sincronizadas, com rastreamento habilitado só no desenvolvimento R2. Referências em `script/classification_comparison/run.py:21`, `script/classification_comparison/journal.py:57` e `:76` e `script/classification_comparison/r2/execute.py:34` e `:121`.

Depois de fechar o lote, `gate.collect` compara os sete arquivos publicados aos hashes originais, antes de calcular a prova com os mesmos bytes lidos e conferidos. O executor verifica a publicação da prova contra o hash devolvido pelo escritor e usa esse hash no selo privado. O coletor pode recalcular uma prova, mas somente o caminho de conclusão original cria o selo exclusivo que o final exige. Permanecem as guardas do selo, da conta v4 e da unicidade de etapa. Referências em `script/classification_comparison/r2/gate.py:75` e `:134`, `script/classification_comparison/r2/execute.py:128` e `script/classification_comparison/r2/seal.py:24`.

## Evidência

Executei os dois testes dirigidos da correção. Ambos passaram em 2,821 s.

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY PYTHONPATH=script/classification_comparison/r2 python3 -B -m unittest -v \
  test_r2.R2Test.test_rewrite_after_financial_close_cannot_become_the_original_seal \
  test_r2.R2Test.test_gate_proof_bytes_are_committed_at_publication
```

- Na intervenção após o fechamento financeiro, a substituição coordenada da observação, decisão e relatório foi rejeitada antes da primeira prova ou selo. O ledger fixture manteve o lote `finished` e as seis reservas conciliadas. O final recusou a prova regenerada e o replay do desenvolvimento foi bloqueado.
- Na intervenção após a gravação da prova, a alteração de seus bytes bloqueou a criação do selo. Os ganchos dos testes reproduzem a ordem das operações. A janela em processos independentes segue sem medição.
- `git diff --check 9dfbc0d HEAD` e a comparação dos caminhos protegidos com `9dfbc0d` retornaram código zero. O diff preserva fontes, contratos, candidata e orçamento. As suítes de R2, C02, C05 e Qwen constam do apêndice da implementação e foram consideradas como evidência registrada. A worktree permaneceu limpa.

A aprovação é do aceite offline, dentro do modelo que preserva o programa, a conta e seu armazenamento privado. A avaliação real permanece pendente.
