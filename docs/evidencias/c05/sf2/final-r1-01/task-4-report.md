# Task 4 · Teste independente SF2-FINAL-R1

**Resultado elegível em 26/11/2026.** A auditoria confirmou os 120 casos, os cinco controles e os dez critérios congelados. A execução única terminou normalmente, com todos os casos e controles observados. A auditoria verificou o mesmo recibo e reconstruiu as decisões R1 sem iniciar o modelo.

| Critério congelado | Resultado observado | Limite |
| --- | --- | --- |
| Categoria aplicada correta | 40/40 (100%) | ≥90% |
| Prioridade aplicada correta | 47/48 (97,92%) | ≥90% |
| Cobertura automática em classificáveis | 69/96 (71,88%) | ≥68/96 |
| Reconhecimento bruto de urgentes | 17/17 (100%) | ≥14/17 |
| Preservação dos campos recebidos pelo canal | 80/80 (100%) | 100% |
| Conclusões indevidas em revisões esperadas | 0/24 | 0 |
| Prioridade inferior aplicada em urgentes | 0/17 | 0 |
| Aplicações parciais | 0 em 120 casos | 0 |
| Chamadas de especialistas nos controles completo e inválido | 0 em 2 controles | 0 |
| Latência total p95 dos casos | 71,96 ms | ≤3.000 ms |

O selo e as quotas conferidas na carga cobriram 40 casos com apenas categoria ausente, 40 com apenas prioridade ausente e 40 com ambos ausentes. Cada campo teve 80 alvos. Dos 120 casos, 96 eram classificáveis, 24 exigiam revisão e 17 tinham alvo urgente. Entre os classificáveis, a cobertura automática correta foi 68/96 (70,83%). Um dos 69 casos concluídos teve prioridade incorreta. A política aplicou a prioridade urgente a 13/17 alvos (76,47%) e encaminhou os quatro restantes para revisão. Houve 51 revisões no total.

A mediana foi 38,46 ms. O p95 foi a 114ª das 120 durações ordenadas, com máximo de 110,90 ms. A inicialização levou 19.381,06 ms e foi medida separadamente. Os cinco controles também ficaram fora da distribuição de latência dos casos.

| Processo observado | Pico de CPU | Pico de RAM |
| --- | --- | --- |
| Worker | 198,80% | 1.708.331.008 bytes |
| Supervisor | 79,36% | 529.989.632 bytes |

Os dois processos tiveram medições válidas e identificadores distintos. A auditoria registrou zero casos ou controles sem início, zero interrupções e zero falhas de integridade. As proporções descrevem esta amostra selada e seus intervalos de Wilson de 95% constam em `task-4-publico/audit.json`.

## Reprodução da auditoria

A execução usou o comando registrado em `task-4-command.json`, na worktree `.worktrees/sf2-final-ajustes`, branch `feat/sf2-final-ajustes`, commit-base `486d55c76d6a2436826364f01057dc0436247216`. O controlador estava em `main` no commit `6f9cc850bf4cc237b6307f7eca9d213d00638b47`. Para verificar esta coleta, use a operação `audit` do mesmo CLI, com `--run` apontando para o destino registrado e `--execution-sha256` igual ao SHA-256 do recibo abaixo. A execução e a auditoria retornaram código 0.

| Evidência | SHA-256 |
| --- | --- |
| Liberação autorizada | `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a` |
| Recibo da execução | `f3116bb82d03e268386873f9006465328f7092b55674667ead8b85db62060911` |
| Selo da execução | `022f1ebc20daa58c8ac9941390b31fecef056b0cad33d0700b19df46e0eab67a` |
| Saída da auditoria | `f2da03afdadbddfe3cd86a776cdca318dcff4883b9723f03c2e465e5c7e30f40` |

As saídas dos comandos, o recibo, a cópia do selo e o relatório do avaliador estão em `task-4-publico/`. As observações individuais permanecem no diretório reservado `final-run`. A coleta utilizou o pacote local, sem chamadas a APIs ou novo treinamento.
