# C05-E · Revisão independente da Task 1

- Branch `feat/executor-qwen-final`.
- Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/c05-comparacao`.
- Base `10dbd6f2ec18f0fc44dd3b4cfe60d79f04fa9e48` e entrega `24da473a4a20775d495775b2ee578d7df3afede3`.

## Veredito de especificação

**Alterações necessárias.** Os achados 1 e 2 impedem o congelamento obrigatório quando surge evidência de custo acima da reserva. O achado 3 permite atribuir um recibo duas vezes. Isso contraria os itens 5 e 6 da Task 1 e compromete o teto cumulativo.

O pré-voo usa o perfil e a projeção congelados. Autorizações desabilitadas ou divergentes são barradas antes do transporte. A reserva e a marcação de despacho precedem a chamada. A interrupção por custo desconhecido mantém a reserva e é conservadora. O caso de violação após o 44º despacho ainda precede o controle injetado e tem teste específico no pacote.

## Veredito de qualidade

**Alterações necessárias.** A estrutura reaproveita a C02 e o adaptador Qwen, e a transação imediata protege a disputa por saldo. Os três cenários abaixo passam por caminhos que os testes existentes não cobrem. Recomendo regressões dirigidas para a cobrança conhecida sem contadores, a divergência acima da reserva após liquidação e a normalização de recibos.

## Achados

### 1. P1 — Preservar custo atribuído mesmo sem contador de tokens

[final_adapter.py:92](https://github.com/leeunam/case-CLOUDWALK-IA/blob/24da473a4a20775d495775b2ee578d7df3afede3/script/classification_comparison/c05/final_adapter.py#L92)

O extrator só considera custo USD ou créditos quando os dois contadores de tokens existem. O IPC admite contadores e custo independentes. Com US$ 7,10 já gastos, uma resposta fixture HTTP 200 atribuiu US$ 2,25 ao primeiro caso e omitiu apenas `completion_tokens`. O prefixo da C02 passou no verificador, porém `observed_api_usd`, `gateway_usage` e `frozen_reason` ficaram nulos. O saldo contabilizado permaneceu em US$ 8,5004736. A guarda financeira aceitou outra reserva sintética de US$ 1,4004736, embora o gasto comprovado de US$ 9,35 mais essa nova reserva somasse US$ 10,7504736.

Validar contadores e extrair valores monetários separadamente, preservando unidade, referência e atribuição. A ausência de contadores pode deixar as métricas correspondentes nulas. O valor comprovado acima da reserva precisa ser preservado e congelar o saldo antes do próximo despacho.

Também reproduzi o mesmo resultado com ambos os contadores em uma resposta fixture HTTP 500. O filtro de status descarta o corpo antes da análise financeira ([final_adapter.py:151](https://github.com/leeunam/case-CLOUDWALK-IA/blob/24da473a4a20775d495775b2ee578d7df3afede3/script/classification_comparison/c05/final_adapter.py#L151)). Se a resposta de erro traz evidência financeira que satisfaz a validação de unidade, atribuição e fonte, preserve ao menos o excesso para congelamento. A falha de classificação e a reserva em situação de cobrança desconhecida mantêm a semântica atual. A fixture não demonstra o formato real dos erros do fornecedor.

### 2. P1 — Registrar violação comprovada após liquidação anterior

[budget.py:290](https://github.com/leeunam/case-CLOUDWALK-IA/blob/24da473a4a20775d495775b2ee578d7df3afede3/script/classification_comparison/c05/budget.py#L290)

A conciliação rejeita o estado `settled` antes de avaliar o valor do novo recibo. Na conta fixture com US$ 8 de gasto anterior, o primeiro caso reservou US$ 1,4004736 e liquidou US$ 0,001 pelo gateway. Um segundo recibo atribuído ao mesmo caso informou US$ 2,25. O comando retornou “já conciliada”, o saldo continuou em US$ 8,001, `frozen_reason` ficou nulo e a próxima reserva foi aceita. O custo informado implicava US$ 10,25 já gastos.

A duplicação de liquidação deve continuar bloqueada. Para um recibo posterior válido acima da reserva, registrar uma violação e preservar o recibo e o valor anteriores. A contabilização deve refletir o maior custo comprovado como valor total do caso. Essa operação altera a evidência financeira e deixa o relatório de classificação preservado.

### 3. P2 — Normalizar margem em referências de recibos

[budget.py:80](https://github.com/leeunam/case-CLOUDWALK-IA/blob/24da473a4a20775d495775b2ee578d7df3afede3/script/classification_comparison/c05/budget.py#L80), [budget.py:236](https://github.com/leeunam/case-CLOUDWALK-IA/blob/24da473a4a20775d495775b2ee578d7df3afede3/script/classification_comparison/c05/budget.py#L236)

A validação usa `.strip()` para excluir texto vazio, mas retorna o valor original. O índice e a verificação de unicidade tratam `synthetic invoice` e `synthetic invoice ` como recibos distintos. Na reprodução, os dois liquidaram reservas de casos diferentes. Normalize a referência na entrada antes de comparar, persistir e verificar atribuição duplicada, inclusive contra a referência anterior preservada.

## Verificações executadas

Comandos executados na worktree indicada.

```sh
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git worktree list
rtk git diff --check 10dbd6f..HEAD
rtk proxy git diff --name-only 10dbd6f..24da473
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B /tmp/c05-executor-review-probes.py
```

Verifiquei byte a byte que a seção de diff do pacote equivale à saída de `rtk proxy git diff -U10 10dbd6f..24da473`. O checkout estava limpo e a verificação de espaços do Git passou. Os nomes alterados confirmam o escopo no executor C05, documentação e dois callbacks opcionais da C02. As contraprovas usaram apenas transporte fixture e arquivos SQLite temporários e verificaram o relatório de prefixo da C02 nos cenários de resposta. O script em `/tmp` reproduz os três achados. As suítes amplas da entrega foram consultadas no relatório de implementação. Não houve chamadas externas, acesso à chave ou criação de conta real.
