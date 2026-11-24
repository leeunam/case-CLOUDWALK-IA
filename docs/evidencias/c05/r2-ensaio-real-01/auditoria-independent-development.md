# Auditoria do development real da C05-R2

**SPEC — conforme para a execução e seu bloqueio.** O ensaio fez os seis despachos previstos em série, com uma tentativa por caso e sem controles. A execução terminou em `interrupted`; o pré-requisito operacional do final falhou. O relatório de prefixo permanece `inconclusive` para a elegibilidade do modelo. O final R2 de 36 relatos e 13 controles ficou sem execução, portanto está sem medição de qualidade.

**QUALITY — evidência local consistente.** O checker oficial aprovou a consistência do prefixo e a recontagem independente confirmou as métricas e os cinco custos liquidados. O resultado negativo decorre do comportamento e dos tempos observados na amostra e da interrupção financeira prevista no protocolo.

Tarefa `C05-R2 / development`. Branch `feat/r2-avaliador`. Commit-base e HEAD auditado `4d94094672f7170248ca083bbf0572c21c3494f5`. Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-avaliador`. Os arquivos reais novos estavam sem commit. As referências aos registros do ensaio abaixo partem de `docs/evidencias/c05/r2-ensaio-real-01/` na worktree.

## Escopo e integridade

- A autorização cobriu seis chamadas development e até 44 chamadas finais condicionadas à aprovação, sob o teto cumulativo de US$ 10. O plano, o manifesto e a invocação real vinculam a mesma revisão do Git, o mesmo Qwen `qwen/qwen3.8-27b`, os seis IDs congelados, concorrência um, uma tentativa e zero controles. O pré-voo registrou a conta v4 existente com 44 reservas liquidadas e US$ 0,02300927 contabilizados. O plano preliminar e o manifesto-modelo conferem com a vinculação real. (`autorizacao.md`, linhas 3–9. `preflight.json`, linhas 27–34. `development-manifest.json`, linhas 4–19, 69–96 e 116–122. `development/plan.json` e `development/invocation.json`.)
- O diário tem seis sequências de despacho e encerramento do caso, seguidas de `interrupted` por `BudgetError` em `jev-039`. A linha `completed` do sexto caso confirma que a observação local de timeout e a decisão de revisão foram persistidas. A liquidação ocorre depois desse registro e interrompeu o lote. A exportação confirma `interrupted`, sem repetição, reinicialização ou início do final. Ausência de gate no diretório e controle de fluxo anterior à criação do selo são consistentes com a interrupção. O selo privado e a conta privada ficaram fora da inspeção. (`development/journal.jsonl`, linhas 2–20. `development/interruption.json`, linha 1. `financeiro-apos-development.json`, linhas 78–91. `script/classification_comparison/run.py`, linhas 144–155. `script/classification_comparison/r2/execute.py`, linhas 115–137.)
- Conferi 39 referências SHA-256, incluindo sobreposições entre manifesto, relatório e interrupção, além da correspondência de config e manifesto com a invocação. As três séries JSONL originais coincidem byte a byte com as verificadas, e os inputs também com a projeção do plano seco. A revisão citada contém o perfil `observed-total-r2` e o schema de relatório 1.3.0, com IPC 1.1.0. O checker oficial aceitou o relatório com as próprias fontes. (`development-manifest.json`, linhas 20–73 e 97–114. `development/interruption.json`, linha 1. `development/prefix-report.json`, linhas 1–96 e 750. `script/check_classification_contracts.py`, linhas 25 e 69–71. `docs/planejamento/classificacao-comparativa/contratos/relatorio-1.3/report.schema.json`.)

## Métricas recalculadas

Comparei os oito alvos ausentes com o gabarito congelado por ID. No quadro, **abstenção** representa o rótulo `informacao_insuficiente`.

| Caso | Alvos esperados | Saída local e decisão | Latência total |
| --- | --- | --- | ---: |
| `jev-004` | Categoria `payouts` | `payouts`, concluiu corretamente | 4.234,344 ms |
| `jev-013` | Abstenção na categoria | Aplicou `payouts` e concluiu indevidamente | 2.750,435 ms |
| `jev-002` | Prioridade `urgent` | `urgent`, concluiu corretamente | 2.755,233 ms |
| `jev-023` | Abstenção na prioridade | Absteve-se, revisão integral | 3.920,852 ms |
| `jev-006` | Categoria `terminal`, prioridade `basic` | `terminal` e `basic`, concluiu corretamente | 4.066,946 ms |
| `jev-039` | Abstenção nos dois campos | Timeout nos dois campos, revisão integral | 4.995,002 ms |

Fontes do quadro e dos denominadores em `docs/planejamento/classificacao-comparativa/r2/dataset.json`, linhas 6, 8, 10, 15, 20 e 27, e em `development/{inputs,observations,decisions}.jsonl`, linhas 1–6 de cada arquivo.

| Condição congelada para development | Recontagem | Exigência |
| --- | ---: | ---: |
| Alvos corretos, incluindo abstenção explícita | 5/8 | 8/8 |
| Campos do canal preservados | 4/4 | 4/4 |
| Conclusões corretas entre os classificados pelo gabarito | 3/3 | 3/3 |
| Revisões integrais entre os casos esperados em revisão | 2/3 | 3/3 |
| Urgente reconhecido na saída bruta | 1/1 | 1/1 |
| Campos-alvo inválidos ou com erro | 2/8, ambos no mesmo caso | 0 |
| Despachos liquidados na execução | 5/6 | 6/6 |
| p95 observado | 4.995,002 ms | até 3.000 ms |

Os acertos brutos foram **2/4 em categoria** e **3/4 em prioridade**. Entre os alvos efetivamente aplicados, foram **2/3 em categoria** e **2/2 em prioridade**. A cobertura automática e a cobertura de conclusão correta foram **3/3** nos classificáveis. Houve quatro conclusões e duas revisões em seis casos, com **1/3** de conclusão indevida entre as revisões esperadas. Houve **1/4** de abstenções explícitas corretas nos campos em que elas eram esperadas, **0/2** aplicações parciais após erro ou abstenção e **0/1** urgentes com prioridade menor aplicada. O denominador de controles é zero nesta etapa. O timeout produziu uma revisão integral, dois erros de campo e zero acertos brutos. (`development/prefix-report.json`, linhas 92–159 e 159–254. `development/prefix-report.md`, tabela por campo e indicadores. `docs/planejamento/classificacao-comparativa/r2/protocol.json`, linhas 140–149. `script/classification_comparison/r2/gate.py`, linhas 17–49.)

O p50 e o p95 têm seis amostras, pelo método nearest-rank. O p50 é a terceira duração ordenada, **3.920,852 ms**, e o p95 é a sexta, **4.995,002 ms**. Quatro casos superaram 3.000 ms. A soma dos seis tempos de caso é **22.722,811 ms**. A inicialização local prévia levou **641,792 ms**, dando **23.364,603 ms** em soma simples, com outros intervalos do processo fora dessa conta. Nas cinco respostas anteriores ao timeout, o p95 descritivo já seria **4.234,344 ms**. (`development/observations.jsonl`, linhas 1–6. `development/prefix-report.json`, linhas 15–23, 140–145 e 699–705. `docs/planejamento/classificacao-comparativa/r2/protocol.json`, critério de latência em `metric_semantics`.)

## Financeiro

Os cinco valores em USD liquidados coincidem em ordem entre observações e exportação, com conversão de `usage.credits` a US$ 0,01 por crédito. São US$ 0,00063325, US$ 0,00063070, US$ 0,00063113, US$ 0,00063495 e US$ 0,00065875. A soma observada é **US$ 0,00318878**, com 7.047 tokens de entrada e 76 de saída em 5/6 amostras. As seis tentativas e requisições locais cobriram oito perguntas. O total estimado separado foi US$ 0,003188775 para as cinco amostras. (`development/observations.jsonl`, linhas 1–6. `development/prefix-report.json`, linhas 706–748. `financeiro-apos-development.json`, linhas 13–77.)

- **Contabilização exportada:** US$ 0,02300927 anteriores + US$ 0,00318878 liquidados + US$ 1,7837 retidos = **US$ 1,80989805** sob o teto de US$ 10. O acumulado conhecido é US$ 0,02619805, e a margem contábil sob o teto é US$ 8,19010195. A reserva decorre dos limites e tarifas configurados, incluindo cache, e representa exposição conservadora no ledger experimental. (`config.json`, linhas 8–27. `preflight.json`, linhas 20–34. `financeiro-apos-development.json`, linhas 3–11 e 78–95. `script/classification_comparison/c05/settings.py`, linhas 102–105.)
- **Atribuição tardia:** o integrador registrou seis novas linhas consecutivas do mesmo modelo na janela da execução e informou o mesmo recorte de chave. O horário inicial convertido é 15h21min46s em São Paulo. Para as cinco primeiras linhas, conferi custo conhecido arredondado a seis casas e tokens **de saída** na mesma ordem. A sexta linha é a única restante e aparece às 15h22min09s, coerente com a soma de 23,365 s da inicialização e dos casos. Ela traz a referência `gen-6kYWzvWhoR5dAc875soXz1rw`, HTTP 200, uma tentativa, 1.421 tokens de entrada, 28 de saída e **US$ 0,000675** exibidos. A cópia filtra detalhes privados, portanto a chave é uma constatação do integrador e a ligação do ID de provedor ao caso é inferida da sequência, moeda e janela. O timeout local ficou sem ID de provedor, tokens ou valor observado. (`cobranca-tardia-observada.json`, linhas 4–61. `development/observations.jsonl`, linha 6.)
- **Parecer:** evidência suficiente para o integrador contabilizar **US$ 0,000676** em `jev-039` como limite conservador, um passo de US$ 0,000001 acima do valor exibido. O valor exato continua indisponível. A atribuição deve usar a execução e o caso explícitos, unidade USD e referência única do provedor. A checagem de duplicidade cabe à operação no ledger. Se a origem monetária em USD ou a correspondência da linha com a execução deixar de se sustentar, manter a reserva. A proposta segue pendente e o estado observado desta auditoria é o da exportação. (`cobranca-tardia-observada.json`, linhas 7–25 e 58–61. `script/classification_comparison/c05/budget.py`, linhas 381–408.)
- **Projeção se aplicada:** custo contabilizado conservador do development **US$ 0,00386478**, acumulado **US$ 0,02687405** e redução da exposição reservada **US$ 1,783024**. A margem contábil passaria a US$ 9,97312595. `reconcile()` atualiza a reserva individual e preserva `financial_expired=1` e a execução `interrupted`. As métricas e a decisão local continuam as do prefixo. O caminho do gate rejeita prefixo interrompido, exige execução concluída sem expiração financeira e condiciona o final a prova e selo originais. O HTTP 200 tardio não fornece observação local utilizável. O resultado continua operacionalmente reprovado também por qualidade e latência. (`script/classification_comparison/c05/budget.py`, linhas 176–190, 294–310 e 353–408. `script/classification_comparison/r2/gate.py`, linhas 52–77 e 116–144.)

## Verificação executada

- Estado e fonte via `rtk proxy git status --short --branch`, `rtk proxy git worktree list`, `rtk proxy git rev-parse HEAD`, `rtk proxy git show --stat --oneline 4d94094`, `rtk proxy git ls-tree -r --name-only 4d94094` nos caminhos de perfil/schema e `rtk proxy git show 4d94094:script/check_classification_contracts.py`. Leituras locais com `rtk proxy cat`, `rg`, `nl` e `sed`.
- Na worktree, `rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-r2 --report docs/evidencias/c05/r2-ensaio-real-01/development/prefix-report.json` retornou `OK: observed-total-r2`.
- Na worktree, `rtk proxy python3 -B /tmp/cloudwalk-c05-r2-real-audit.py` conferiu hashes, cruzou os seis inputs/observações/decisões com o gabarito, comparou as cinco linhas da cobrança e refez as somas com decimais. A primeira tentativa de cálculo leu a chave incorreta do split e parou antes de calcular. A execução após ajuste do script temporário concluiu com todas as asserções.
- Auditoria sem chamadas de rede, consultas à conta privada, acesso a credenciais, edição dos artefatos originais ou repetição das suítes.

**Exercício.** Abra a segunda linha de `development/decisions.jsonl` e compare com a linha 15 do gabarito. Conte o efeito de aplicar `payouts` em `jev-013` sobre o acerto aplicado de categoria e sobre as revisões esperadas.
