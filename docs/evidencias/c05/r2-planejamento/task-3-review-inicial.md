# C05-R2 · Task 3 · Revisão independente do avaliador

- Base `b299fdd1a9bc52d45bd46cd87a4a7a9583a6d115` e revisão `e6fe31cbe4dd2c96493bf455016163c6c68ff7dc`.
- Branch `feat/r2-avaliador` e worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-avaliador`. Checkout limpo na conferência final.
- **Especificação · Reprovada.** A prova regenerada de uma etapa de desenvolvimento reprovada libera a autorização do final. O brief exige prova do resultado autêntico da etapa concluída.
- **Qualidade · Reprovada.** O gate aceita evidência de desempenho substituída e o checker final aceita um veredito incompatível com os registros originais. Nenhum achado Critical.

## Achados

### P1 · Vincular a prova do gate às saídas originais do desenvolvimento

`script/classification_comparison/r2/execute.py:119`, `script/classification_comparison/r2/gate.py:73` e `:107` e `:125`.

A conta conserva a identidade do lote, o manifesto, a configuração e o custo por caso. O diário vincula o plano e os eventos de despacho e conclusão. Os dados persistidos nesses pontos deixam sem compromisso independente os bytes das observações, decisões e relatório. Durante o pré-voo do final, `collect` calcula os hashes dos arquivos então apresentados e `verify` compara a prova com esse recálculo. Basta regenerar a prova e vincular seu novo hash no manifesto. A mesma verificação aceita um conteúdo de classificação diferente com os custos originais.

Reproduzi em uma conta fixture, com seis reservas conciliadas. O desenvolvimento concluiu com `failed` e 7/8 alvos. Substituí a categoria observada de `jev-004` de `pix` por `payouts`, derivei a decisão correspondente e regenerei o relatório e a prova. A prova passou a `fixture_ready` com 8/8 e o pré-voo do final a autorizou. Conta, diário, entradas, plano e invocação permaneceram originais. A verificação usa o mesmo mecanismo de vinculação para observações e durações reais.

Fixar o compromisso com as saídas no momento da conclusão, fora dos próprios artefatos oferecidos para validação. Fazer o final exigir esse compromisso da execução correspondente antes de abrir o adaptador. A escolha do armazenamento pertence ao integrador, pois a tarefa preserva a proteção financeira e a schema v4. Incluir regressão que regenere prova, relatório e manifesto depois de alterar uma observação, preservando a conta, e exija a rejeição.

### P2 · Reconstruir as métricas de aprovação do final a partir dos registros

`script/check_classification_contracts.py:349` e `:624`.

O checker comprova decisões por caso, a latência e a ausência de aplicação parcial. Para os outros gates, aceita numeradores compatíveis com a aritmética e aplica o limiar ao valor declarado no relatório. Em uma contraprova inteiramente sintética com formato de relatório completo real, o cálculo canônico indicou `fail` junto de uma conclusão automática em `r2-011`, caso de revisão obrigatória. Alterei somente o numerador e o valor de `automatic_completion_on_expected_review_cases` para zero e o veredito para `pass`. O checker aceitou, com os três streams originais. A lacuna é herdada na verificação de métricas e compromete a conferência do novo relatório R2.

Conferir os numeradores e demais valores de aprovação do perfil R2 contra entradas, observações, decisões e referências congeladas. Preservar a interpretação dos perfis históricos. Cobrir a alteração do numerador e do veredito com os streams intactos.

### Minor · Corrigir a origem declarada da partição nova

`docs/planejamento/classificacao-comparativa/r2/split.json:2`, `docs/planejamento/classificacao-comparativa/r2/protocol.json:6` e `script/check_classification_contracts.py:655`.

A partição R2 declara o dataset histórico 1.1.0 como seu dataset fonte, mas lista 36 casos que só existem no pacote composto 2.0.0. O protocolo aponta para o composto e os pins atuais protegem o conteúdo. O checker verifica os objetos do pacote e a partição sem verificar os campos de origem declarados no split. Usar a versão e o SHA do composto nesses campos, mantendo a referência histórica em `protocol.r2.historical_dataset`. A mesma partição descreve `id` como visível ao modelo, enquanto a projeção IPC inclui ID e o corpo Qwen o retira. A nomenclatura pode refletir a fronteira correta. Nenhuma dessas correções exige editar os casos, os pareceres ou as instruções congeladas.

## Critérios conferidos

- **Fontes, perfil e ordem.** Conferi o novo contrato 1.3.0 com `$id` próprio, o protocolo 1.2.0, o IPC 1.1.0, os 28 pins e os hashes do inventário golden. Os 24 objetos de desenvolvimento e os 36 finais do composto têm os mesmos bytes entre chaves de suas respectivas fontes. Os 12 casos por máscara e as quotas de revisão 2/2/3 conferem, com cinco categorias insuficientes, três prioridades insuficientes e uma sobreposição. A seleção explicitamente ordenada do desenvolvimento é `jev-004`, `jev-013`, `jev-002`, `jev-023`, `jev-006`, `jev-039`. O final fixa 36 relatos, 13 controles e 44 candidaturas.
- **Fronteiras de execução.** A CLI C02 exclui o perfil R2 e a função `run` o recusa antes do pré-voo. A CLI dedicada exige configuração do escopo R2, manifesto habilitado e confirmação. O adaptador verifica candidato, conteúdo e ordem, e a conta precisa estar ativa com reserva antes do despacho. A projeção Qwen contém apenas o contexto previsto e o schema dos campos ausentes, com 128 tokens e reasoning desligado. Entradas completas e inválidas seguem pelo fluxo canônico sem despacho. `decide` preserva os dados fornecidos e faz revisão integral diante de abstenção ou erro.
- **Relógio e modo.** O executor usa `run_batch`, `Journal` e o relógio total da C02. O relatório separa inicialização, controles e tempos dos casos finais. O desenvolvimento fixture permanece `inconclusive` para elegibilidade e `unmeasured` no p95. `assess` exige seis durações no modo real e toma seu máximo para o p95 n=6. O pré-voo distingue `fixture_ready` de `pass` e valida a prova antes do acesso à credencial e do transporte. Os exemplos reais estão desabilitados.
- **Conta e repetição.** A única extensão financeira é o scope esperado em `Settings.load` com padrão preservado. `c05/budget.py` e a schema ficaram intactos. O executor R2 inicializa apenas conta fixture. O manifesto usa o SHA-256 canônico de identidade da conta, candidata, casos finais e etapa. A dimensão financeira conserva o teto global real de US$ 10. A unicidade de `manifest_id` sob transação v4 impede repetir a etapa mesmo com outra configuração, revisão, manifesto ou saída. O custo independente é conservado para classificação errada. Desconhecido e timeout interrompem e retêm reserva. Prefixo, modo divergente, fontes alteradas ou custo divergente passam pelas respectivas guardas, sujeitas à lacuna de autenticação do P1.
- **Compatibilidade.** O diff preserva dataset, catálogo, rubrica, política, instruções congeladas, schemas históricos e arquivos de resultados. A seleção da família de relógio mantém `warm-1.0` e `observed-total-1.1` nos ramos anteriores. O relatório do implementador registra 134 testes nas seis suítes, três checkers, 21 relatórios históricos conferidos e a execução fixture de seis chamadas em desenvolvimento e 44 no final. Usei esses resultados como evidência registrada e executei somente as duas contraprovas novas e a conferência independente de conteúdo e hashes.

## Verificações pendentes

- A autenticação da prova e a rejeição de métricas finais adulteradas precisam de nova verificação após a correção. Os comandos abaixo isolam as duas condições.
- O funcionamento com tarifa, conta e credencial reais, a qualidade real e os tempos do Qwen continuam fora do aceite offline. Os pareceres e seu congelamento foram conferidos como artefatos e hashes. A separação operacional entre autoria e revisão depende dos registros das etapas anteriores.

## Reprodução offline do P1

Execute na raiz da worktree revisada. O script cria apenas arquivos temporários e um ledger fixture. Ele verifica a autorização do final sem executá-lo.

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B - <<'PY'
import sys

sys.path.insert(0, "script/classification_comparison/r2")
from test_r2 import CAP, FIXTURE, Plan, R2Test, c01, encode, execute, gate, gate_reference
from common import decide
from run import write_json, write_report

scenario = R2Test()
try:
    scenario.setUp()
    account = scenario.init_account()
    args = scenario.args("development", account)
    scenario.create_manifest(args)
    original_status = execute.run_evaluation(args, fixture_command=scenario.scenario_command("wrong"))
    proof = args.output / gate.FILENAME
    print("resultado original:", original_status, "alvos:", c01.read(proof)["correct_targets"])
    assert original_status == "failed"

    plan = Plan("development", "fixture", "verification", FIXTURE)
    bundle = c01.load_bundle(plan.validation, args.output / "report.json")
    observed = bundle["observations"][0]
    assert observed["id"] == "jev-004" and observed["choices"]["category"]["raw"] == "pix"
    observed["choices"]["category"]["raw"] = "payouts"
    bundle["decisions"][0] = decide(bundle["inputs"][0], observed, plan.catalog, bundle["report"]["run_id"])
    for name in ("observations", "decisions"):
        content = "".join(encode(row) + "\n" for row in bundle[name])
        (args.output / f"{name}.jsonl").write_text(content, encoding="utf-8")
    write_report(args.output, bundle["report"], bundle["inputs"], bundle["observations"], bundle["decisions"],
                 plan.validation, plan.protocol, plan.split, plan.catalog, plan.cases, plan.control_policy, False)
    regenerated = gate.collect(args.output, plan, account, CAP)
    write_json(proof, regenerated)
    final = scenario.args("final", account, stage="final", proof=proof)
    scenario.create_manifest(final)
    execute.authorize(final, Plan("final", "fixture", "verification", FIXTURE),
                      account, gate_reference(proof), True)
    print("resultado regenerado:", regenerated["status"], "alvos:", regenerated["correct_targets"])
    print("pré-voo aceitou a prova regenerada; reservas originais:", len(account.status()["reservations"]))
finally:
    scenario.doCleanups()
PY
```

Resultado em `e6fe31c`:

```text
resultado original: failed alvos: 7
resultado regenerado: fixture_ready alvos: 8
pré-voo aceitou a prova regenerada; reservas originais: 6
```

## Reprodução offline do P2

A contraprova usa registros e tempos sintéticos para exercitar a verificação do contrato de um relatório final.

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B - <<'PY'
from copy import deepcopy
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, "script/classification_comparison/r2")
from test_r2 import FIXTURE
from adapters.qwen.adapter import choice
from common import decide, encode, injected_observation
from plan import Plan, c01
from run import write_json, write_report

plan = Plan("final", "fixture", "synthetic-review-only", FIXTURE)
original = c01.load_bundle(plan.validation, c01.get_profile(c01.R2).golden_path)
identity = c01.read(c01.source_path(plan.sources["candidate"]))["identity"]
plan.report["identity"] = identity
final_ids = set(plan.binding["selected_ids"])
run_id = plan.report["run_id"]
observations, decisions = [], []
template = next(obs for obs in original["observations"] if obs["origin"] == "candidate")
for item in plan.inputs:
    case_id = item["id"]
    obs = None
    if case_id in plan.injections["ids"]:
        obs = injected_observation(item, run_id, plan.control_policy)
    elif case_id in plan.candidates:
        obs = deepcopy(template)
        obs.update(id=case_id, run_id=run_id, identity=identity,
                   returned_model=identity["expected_returned_model"], questions=len(item["missing"]),
                   elapsed_ms=100 if case_id in final_ids else None)
        targets = {field: next(iter(item["catalog"][field])) for field in item["missing"]}
        if case_id in final_ids and case_id != "r2-011":
            targets = plan.cases[case_id]["expected"]
        obs["choices"] = {
            field: (choice("abstained", code, "explicit") if code == c01.ABSTENTION else choice("predicted", code))
            for field, code in targets.items()
        }
    if obs:
        observations.append(obs)
    decisions.append(decide(item, obs, plan.catalog, run_id))

with TemporaryDirectory(dir=c01.ROOT, prefix="r2-review-") as scratch:
    output = Path(scratch)
    for name, rows in {"inputs": plan.inputs, "observations": observations, "decisions": decisions}.items():
        content = "".join(encode(row) + "\n" for row in rows)
        (output / f"{name}.jsonl").write_text(content, encoding="utf-8")
    write_report(output, plan.report, plan.inputs, observations, decisions, plan.validation,
                 plan.protocol, plan.split, plan.catalog, plan.cases, plan.control_policy, False)
    path = output / "report.json"
    report = c01.read(path)
    gate_name = "automatic_completion_on_expected_review_cases"
    assert report["eligibility"] == "fail" and report["gates"][gate_name]["value"] == 1
    print("relatório canônico:", report["eligibility"], "conclusões indevidas:", report["gates"][gate_name]["value"])
    report["gates"][gate_name].update(value=0, numerator=0)
    report["eligibility"] = "pass"
    write_json(path, report)
    print("checker aceitou relatório adulterado com streams originais:", c01.verify_report(path, c01.R2).name)
PY
```

Resultado em `e6fe31c`:

```text
relatório canônico: fail conclusões indevidas: 1
checker aceitou relatório adulterado com streams originais: observed-total-r2
```
