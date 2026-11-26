# Task 4 · Auditoria independente da SF2-FINAL-R1

**SPEC PASS · QUALITY PASS.** Em 26/11/2026, a auditoria independente confirmou `eligible`, com aprovação nos 10 critérios congelados. O parecer cobre a especificação, a qualidade da evidência e a execução registrada.

## Reprodução e integridade

O controlador estava em `main`, commit `6f9cc850bf4cc237b6307f7eca9d213d00638b47`. A auditoria usou uma vez o vetor [task-4-audit-command.json](task-4-audit-command.json), com Python `-I -B -S` e a operação `audit`, a partir de `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-ajustes`, branch `feat/sf2-final-ajustes`, commit `486d55c76d6a2436826364f01057dc0436247216`. Retornou código 0, com saída de erro vazia. O [resultado independente](task-4-publico/audit-independent.json) é idêntico ao oficial em valores e bytes. A reprodução ocorreu sem iniciar o worker ou fazer inferência.

Os oito arquivos do manifesto público conferiram. A autorização do usuário vinculava a execução única e a adoção condicional ao digest da liberação. A autorização operacional conferiu com sua cópia pública. As três reservas continham os mesmos bytes e registraram uma única exposição em 26/11/2026 às 13:37:30 UTC. O marcador de início do worker vinculou a liberação ao PID registrado no selo. O recibo da execução vinculou a mesma reserva ao selo.

| Vínculo | SHA-256 verificado |
| --- | --- |
| Liberação autorizada | `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a` |
| Selo público do conjunto final | `71bea26395321246ef00c4374465c6cd8bd3320252a7729429cfad5e3c2263a4` |
| Reserva de exposição | `c63b2c394a859acec07abf88db0985c386020861583c3ccf57b17b85f3ceb4d4` |
| Recibo da execução | `f3116bb82d03e268386873f9006465328f7092b55674667ead8b85db62060911` |
| Selo da execução | `022f1ebc20daa58c8ac9941390b31fecef056b0cad33d0700b19df46e0eab67a` |
| Resultado das duas auditorias | `f2da03afdadbddfe3cd86a776cdca318dcff4883b9723f03c2e465e5c7e30f40` |

Após verificar o selo da execução, o auditor conferiu os quatro papéis da custódia e as quotas. Foram 40 casos por máscara de campos ausentes, 80 alvos de cada campo, 96 casos classificáveis, 24 com revisão esperada e 17 com alvo urgente. O auditor confrontou a agenda de IDs únicos com os tempos, as 125 unidades atômicas e as decisões brutas e R1. Verificou a reconstrução da R1 por ID com a política congelada e o cálculo pelo avaliador original. Os artefatos registram 120 decisões e cinco controles, uma observação válida por ID, zero IDs faltantes, zero interrupções e zero falhas de integridade.

## Critérios congelados

| Critério | Observado | Limite |
| --- | --- | --- |
| Categoria aplicada correta | 40/40 (100%) | ≥90% |
| Prioridade aplicada correta | 47/48 (97,92%) | ≥90% |
| Cobertura automática nos classificáveis | 69/96 (71,88%) | ≥68/96 |
| Reconhecimento bruto de alvos urgentes | 17/17 (100%) | ≥14/17 |
| Preservação dos campos do canal | 80/80 (100%) | 100% |
| Conclusões indevidas em revisões esperadas | 0/24 | 0 |
| Prioridade inferior aplicada em urgentes | 0/17 | 0 |
| Aplicações parciais | 0/120 | 0 |
| Chamadas aos especialistas nos controles completo e inválido | 0 em 2 controles | 0 |
| Latência total p95 dos casos | 71,96 ms | ≤3.000 ms |

A cobertura correta foi 68/96 (70,83%). Uma das 69 conclusões automáticas teve prioridade incorreta. A política aplicou urgente a 13/17 alvos (76,47%) e encaminhou os outros quatro para revisão. Ao todo, 51/120 casos ficaram em revisão.

A mediana foi 38,46 ms e o máximo foi 110,90 ms. O p95 correspondeu à 114ª posição das 120 durações ordenadas, com inicialização e controles medidos à parte. A inicialização levou 19.381,06 ms.

| Processo | PID | Pico de CPU | Pico de RAM |
| --- | --- | --- | --- |
| Worker | 214 | 198,80% | 1.708.331.008 bytes |
| Supervisor | 84 | 79,36% | 529.989.632 bytes |

## Limites do parecer

As métricas e o uso de recursos descrevem a coleta e o ambiente registrados. A auditoria reconstruiu as decisões e verificou a integridade dos registros da execução única a partir dos artefatos selados. A validação do fluxo Rails e da demonstração pertence às etapas de integração e aceite.
