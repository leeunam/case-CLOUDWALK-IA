# C02 · Contratos 1.1.0 para controles injetados

Base `e5404a5038a8bc28007e0bcb8d7fcba0c5b58997`, branch
`feat/contratos-controles`, worktree `.worktrees/c02-contratos`.
A revisão técnica de 23 de novembro de 2026 encontrou uma dependência das
respostas naturais do candidato para exercer a regra de aplicação parcial.
O contrato reserva uma entrada sintética adicional para essa verificação.
[Decisão do integrador](../ajuste-de-proveniencia-c02.md)

## Passagem para C02

1. No preflight, verificar a versão 1.1.0 dos quatro envelopes, o protocolo
   e a política de controles pelos hashes congelados na base integrada.
   O SHA-256 do protocolo é `eb9bdbb786037bac864f3155ff6dfbb45feb83dfdb99958f463b6896a614dced`.
   `protocol.control_policy` fixa caminho, versão e SHA-256. O checker confere
   os bytes da política antes de interpretar seu conteúdo e exige que o
   inventário da injeção repita a referência aprovada. [Formato do lote](README.md#origem-e-controle-de-aplicação-parcial)
2. Reservar os IDs de `policy.controls` ao avaliador. Usar o catálogo e a
   máscara comuns. Entregar os demais controles aptos ao adaptador e esperar
   `origin: "candidate"` e a identidade do candidato. O controle reservado
   segue direto para a validação e a decisão comuns.
3. Persistir o resultado de cada origem. Ao fechar o lote ou o prefixo,
   montar `control_ids` e `injected_controls` na ordem das evidências
   concluídas. Em um prefixo anterior à injeção, usar `{"ids":[],"count":0}`.
   Registrar o controle injetado no gate de aplicação parcial e excluir sua
   observação ao calcular `usage`. Emitir as métricas do teste a partir dos
   IDs concluídos do dataset.
4. Para um processo interrompido sem observação válida, registrar despacho e
   uso desconhecido no diário/manifesto da C02. O relatório comum descreve o
   prefixo validado. A revisão independente e a integração precedem o consumo
   desta representação pelos adaptadores.

Na raiz da worktree, este exemplo constrói a observação a partir da política,
usa os mesmos validadores de qualquer candidato e confere a decisão
persistida. No runner, a função comum de decisão deve produzir essa decisão.

```sh
rtk proxy python3 -B - <<'PY'
import sys
sys.path.insert(0, "script")
import check_classification_contracts as c

v = c.validators()
bundle = c.load_bundle(v)
report = bundle["report"]
inventory = report["injected_controls"]
approved = c.read(c.PLAN / "protocolo-comparacao.json")["control_policy"]
assert inventory["policy"] == approved
policy = c.read(c.source_path(approved))
case_id, = inventory["ids"]
spec = policy["controls"][case_id]
entry = next(item for item in bundle["inputs"] if item["id"] == case_id)
decision = next(row for row in bundle["decisions"] if row["id"] == case_id)
assert (entry["text"], entry["received"]) == (spec["text"], spec["received"])
obs = dict(contract_version="1.1.0", run_id=report["run_id"], id=case_id, attempt=1,
           origin="injected_control", identity=policy["identity"], choices=spec["choices"],
           returned_model=None, weights_revision=None, temperature_state="unknown",
           elapsed_ms=None, load_ms=None, inference_ms=None,
           requests=0, questions=0, request_usage=[])
c.structure(v, "observation", obs)
c.verify_case(entry, obs, decision, report, c.read(c.source_path(report["sources"]["catalog"])))
assert obs == next(row for row in bundle["observations"] if row["id"] == case_id)
print(case_id, decision["outcome"], [f["applied"] for f in decision["fields"].values()])
PY
```

Resultado esperado: `ctl-injetado-aplicacao-parcial review [None, None]`.
O contrato compara o inventário ao ID reservado, à origem observada, às
escolhas, ao conteúdo dos três arquivos e aos hashes de origem. Para validar
outro lote salvo, usar `load_bundle(validators, Path(".../report.json"))`
e `verify_run` com o protocolo, a divisão, o catálogo e o dataset congelados.

## Correções da revisão de `509c0fa`

A população do gate de aplicação parcial contém todos os relatos observados
com alguma escolha abstida, inválida ou com erro. Cada ID conta uma vez.
Na fixture são `ctl-sem-assunto`, `ctl-saida-invalida`, `ctl-timeout`,
`ctl-saida-ausente`, `ctl-versao`, `ctl-politica` e a injeção reservada.
Os sete retêm todos os campos originalmente ausentes. O gate guarda
`{"state":"measured","numerator":0,"denominator":7,"value":0}`.
A execução mínima do teste com todas as previsões naturais válidas guarda
zero violações em um relato. Omitir a injeção somente dessa contagem quebra
a verificação. Entradas bloqueadas antes da tentativa ficam fora do gate.

Reproduzimos os dois aceites indevidos na base anterior. A métrica com uma
violação e denominador mil era aceita. Uma política com um LF acrescentado
e um novo SHA no manifesto também era aceita em uma cópia temporária. Os
testes agora exigem a rejeição das contagens, estados e bytes divergentes
e exercitam a leitura do relatório salvo com o protocolo aprovado.

## Verificação realizada

| Verificação offline | Resultado |
| --- | --- |
| `rtk proxy python3 -B script/check_classification_contracts.py` | 5 schemas, 13 entradas/13 decisões, 9 observações, 64 rejeições esperadas |
| `rtk proxy python3 -B docs/planejamento/classificacao-comparativa/contratos/test_regressions.py -v` | 11 testes aprovados |
| Exemplo mínimo acima | Escolha bruta `pix`, abstenção na prioridade, ambos os valores aplicados nulos |
| `rtk git diff --check` | Sem erros de formatação |

Uma regressão usa somente respostas naturais com códigos válidos e confirma
a presença do controle misto. Outra remove a injeção e conserva uma resposta
natural mista. O lote de fixture continua válido e a pré-condição de controles
para a elegibilidade fica pendente. Os exemplos negativos cobrem troca de
origem, ID do dataset, política, identidade, custos, scores, tempos, uso
contaminado e diferença entre registros declarados e persistidos.

Todos os resultados são de fixtures. O protocolo continua com 24/36 casos,
critérios e orçamento inalterados. A execução não fez chamadas a modelos.
Como exercício, localize `ctl-injetado-aplicacao-parcial` nos três arquivos
JSONL e reconcilie as nove observações com as oito tentativas em `usage`.
