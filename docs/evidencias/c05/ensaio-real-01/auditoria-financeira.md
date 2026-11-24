# C05 · Auditoria financeira do lote final

Execução `c05-58e8f0b5c64547b98d6f5ca738bf2c6e`, revisão `19a56fe3dc4fb80a48122182fcc6bcdf1d9855d7`, branch `feat/executor-qwen-final`. A conta SQLite v4 foi aberta em modo somente leitura, passou no teste de integridade e manteve o mesmo SHA-256 antes e depois. A conta tem uma única execução `finished`.

## Despachos e integridade

- 44 despachos, com 44 casos e recibos distintos. A ordem coincide no plano, no diário, no IPC e no SQLite. Todos os candidatos tiveram uma tentativa.
- Foram concluídos 36 relatos e 13 controles. Houve 36 despachos de relatos e oito de controles. Quatro controles de entrada e um controle injetado passaram sem requisição HTTP.
- O IPC registra 44 requisições, 59 perguntas, 47.557 tokens de entrada e 690 de saída.
- O registro de execução terminou com código 0. O lançador registrou ausência da sequência literal da credencial nos artefatos e no log. A revisão Git, o SHA-256 do manifesto e a configuração coincidem com o lançamento, o diário da conta e o plano realizado. Os hashes dos três arquivos de evidência conferem com o relatório.

## Contabilidade em USD

| Medida | Resultado |
| --- | ---: |
| Teto cumulativo autorizado | US$ 10 |
| Pilotos anteriores contabilizados conservadoramente | US$ 0,001038 |
| Reserva por despacho | US$ 1,5032 |
| Reservas liquidadas / pendentes | 44 / 0 |
| Custo exato conciliado do lote | US$ **0,02197127** |
| Custo observado no IPC | US$ 0,02197127 |
| Estimativa por tokens no IPC | US$ 0,021971225 |
| Diferença entre custo conciliado e estimado | US$ 0,000000045 |
| **Total contabilizado, incluindo pilotos** | **US$ 0,02300927** |
| Maior exposição local reconstituída | US$ 1,52572095 |

A conciliação soma 2,197127 créditos a US$ 0,01 por crédito. Cada valor convertido coincide exatamente com o custo observado correspondente no IPC. Não há expiração financeira, correção posterior, reserva pendente ou congelamento. A maior exposição reconstituída soma os pilotos, 43 custos já conciliados e a reserva do último despacho.

A auditoria usou a contabilidade local e as respostas registradas pelo executor. O custo conciliado não foi comparado com extrato posterior do fornecedor nesta etapa. Os hashes e os totais exatos estão no arquivo JSON.
