# C05-R4 · Auditoria do desenvolvimento real da Luna

**Qualidade reprovada. Financeiro conciliado pelos registros exportados. Integridade dos artefatos confirmada.** O lote real concluiu os seis casos previstos. `jev-013` foi concluído automaticamente, quando a referência exigia revisão. O gate reprovou e bloqueou o final.

- Execução `luna-r4-83a0e8fc7c794b3184f3d9b8f534aa93`, realizada na noite de 24/11/2026 no horário de São Paulo. Segundo o registro do integrador, iniciou às 02:42:44 UTC e terminou às 02:42:52 UTC de 25/11/2026, com saída 2 da CLI. O código encerra com esse status quando o gate falha.
- Base `1c89c264ca7cba4e8cde72ec9098181435def74d`, branch `feat/luna-executor-r4`, worktree `.worktrees/r4-luna-executor`. Evidências em `docs/evidencias/c05/luna-r4-ensaio-real-01/`.
- Perfil `observed-total-luna-r4`, protocolo 1.4.0, relatório 1.5.0 e IPC 1.1.0. As seis observações registraram `openai/gpt-5.6-luna` como modelo solicitado e retornado via Feita. O candidato manteve o prompt 1.2.0 e a política 1.1.0 congelados.
- O registro `autorizacao-continuacao.json` documenta a interpretação do integrador do pedido «termine o que falta do projeto» sob o teto cumulativo existente de US$ 10. Limitou o desenvolvimento a seis requisições, condicionou as até 44 finais à aprovação desse gate e excluiu sondas, repetições e o uso dos 16 relatos diagnósticos.

## Qualidade

| Critério de desenvolvimento | Exigido | Observado |
| --- | ---: | ---: |
| Alvos corretos | 8/8 | **7/8** |
| Campos válidos recebidos e preservados | 4/4 | 4/4 |
| Conclusões corretas em casos classificáveis | 3/3 | 3/3 |
| Revisões integrais em casos que exigiam revisão | 3/3 | **2/3** |
| Reconhecimento bruto de urgente | 1/1 | 1/1 |
| Erros técnicos ou saídas inválidas | 0 | 0 |
| Requisições com custo conciliado | 6/6 | 6/6 |
| p95 do tempo total | ≤ 3.000 ms | 1.762,223 ms (n=6) |

| Caso | Alvos corretos | Decisão esperada | Decisão aplicada | Tempo total (ms) | Custo (US$) |
| --- | ---: | --- | --- | ---: | ---: |
| `jev-004` | 1/1 | Concluir | Concluído | 1.762,223 | 0,00037015 |
| `jev-013` | 0/1 | Revisar | Concluído | 1.400,647 | 0,00036840 |
| `jev-002` | 1/1 | Concluir | Concluído | 1.028,431 | 0,00036950 |
| `jev-023` | 1/1 | Revisar | Em revisão | 705,391 | 0,00037080 |
| `jev-006` | 2/2 | Concluir | Concluído | 792,615 | 0,00037855 |
| `jev-039` | 2/2 | Revisar | Em revisão | 1.160,077 | 0,00038540 |

A referência congelada de `jev-013` esperava `informacao_insuficiente` no campo `category`. Luna retornou `payouts` com status `predicted`. A decisão aplicou essa categoria, preservou a prioridade `basic` fornecida e concluiu o caso. O relatório registrou 2/3 categorias aplicadas corretas e 1/3 conclusões indevidas nos casos de revisão. O mesmo caso e a mesma escolha haviam reprovado a R3. O p95 usa o método *nearest-rank* e corresponde ao maior dos seis tempos totais. O p50 foi 1.028,431 ms.

`finished` no diário indica que o lote produziu as seis decisões. `failed` na prova indica a reprovação do desenvolvimento. O relatório mantém `inconclusive` para elegibilidade. O conjunto sintético é uma referência exploratória. Entre os seis casos executados, `jev-002` tem aprovação humana direta e os outros cinco tiveram revisão delegada à IA. Os 36 casos finais congelados têm zero aprovações humanas individuais. Os 16 relatos diagnósticos estão fora das etapas oficiais. Os resultados e a latência desta amostra se restringem ao desenvolvimento.

## Integridade e bloqueio da etapa final

O verificador canônico aceitou o relatório e suas fontes. A reconstrução local produziu os mesmos bytes de entrada do planejamento e da execução. Conferi SHA-256 de 47 arquivos vinculados aos registros contra a base, incluindo os 23 arquivos de execução. Os sete arquivos fixados no congelamento da candidata também conferiram com o commit de congelamento `2f6698495577ec9064f7020d2e0f0825bcc3a74f`. A conferência cobriu ainda os sete artefatos da prova. O manifesto habilitado coincide com o molde salvo após a mudança de `enabled` de `false` para `true`. A vinculação canônica, o identificador do manifesto, a configuração e a invocação correspondem ao plano salvo e à prova.

Cada um dos seis relatos do desenvolvimento teve o corpo de requisição reconstruído localmente. A entrada usa os campos da projeção IPC e o corpo do modelo contém `text`, `brand`, `catalog`, `missing` e `received`. O esquema restringe a saída aos campos ausentes. As decisões preservam os quatro valores válidos recebidos. O diário reúne 20 eventos para o mesmo `run_id`, com planejamento, seis sequências de início de envio, envio e conclusão e fechamento com seis decisões. Entradas, observações, decisões, diário e recibos têm os seis IDs autorizados na mesma ordem. Cada caso tem uma tentativa e um POST registrado. O pré-voo registra zero sondas de inferência.

O verificador da etapa final rejeitou a prova original com `gate de development falhou ou pertence a outro modo`, antes de consultar selo ou conta. A prova é do modo `real` e as duas métricas abaixo do exigido explicam o bloqueio. O pacote contém apenas diretórios de desenvolvimento e de planejamento do desenvolvimento. O diário e os extratos registram somente o acréscimo desse lote. Nenhum envio final consta no pacote. A C05-R4 permanece sem qualificação final ou adoção.

## Financeiro

Os seis recibos distintos de `financial-receipts.json` correspondem ao gate e aos valores observados. Recalculei cada conversão usando US$ 0,01 por crédito. Os **0,224280 créditos** exportados somam **US$ 0,00224280** no lote. Todas as seis reservas de **US$ 1,239 por requisição** foram liquidadas sem expiração. A estimativa por tarifa somou US$ 0,00357720. A reserva por requisição é o limite conservador aplicado antes da chamada. Os recibos mostram o custo observado.

Os extratos da mesma conta real, identificada como schema 4 na exportação, mostram o acumulado de **US$ 0,02869232 → US$ 0,03093512** sob o teto interno de US$ 10. A diferença coincide com os seis recibos. Foram de 56 a 62 reservas liquidadas, zero pendências registradas e três para quatro lotes, dos quais três concluídos e um interrompido no histórico. O motivo de congelamento consta como nulo. A margem restante sob o teto interno é de **US$ 9,96906488**. A conferência cobre os registros exportados da conta e os valores de uso registrados pelo gateway. O saldo junto ao fornecedor e o selo privado ficaram fora do escopo.

## Verificações executadas

Na worktree indicada, o comando retornou `OK` para o relatório real salvo.

```sh
rtk proxy python3 -B script/check_classification_contracts.py \
  --profile observed-total-luna-r4 \
  --report docs/evidencias/c05/luna-r4-ensaio-real-01/development/report.json
```

Executei também um script local de leitura dos JSONs publicados. Usei `Plan` para reconstruir a vinculação e as entradas a partir da configuração e dos arquivos fixados. Usei `r2.gate.assess` para recompor o gate, conferi p95 pelo *nearest-rank* e somei os recibos com `Decimal`. Testei `r2.gate.verify` com a prova original e verificações de selo e conta instrumentadas para interromper a reprodução se alcançadas. A rejeição ocorreu antes de ambas. A reconstrução usou somente a identidade registrada da conta. A auditoria não acessou o banco financeiro, a credencial ou o fornecedor e não repetiu o lote.

**Exercício.** Siga `jev-013` de `inputs.jsonl` a `observations.jsonl` e `decisions.jsonl`. Identifique o campo autorizado para complementação e confira como a categoria aplicada alterou as duas contagens do gate.
