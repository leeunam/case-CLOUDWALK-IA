# C05-R3 · Auditoria do desenvolvimento real da Luna

O lote de 24/11/2026 terminou com os seis casos autorizados e reprovou no gate de desenvolvimento. O caso `jev-013` explica os dois critérios que falharam. As 44 chamadas da etapa final ficaram bloqueadas e os artefatos não registram execução final.

- Branch de execução `feat/avaliador-luna`, worktree `.worktrees/r3-luna-avaliador`, commit-base `e8434bb8ed7a01ec564f8bf3b02aa35d7bde1575`.
- Execução `luna-a23fe8ecda5e4a759cc3436f95dda867`, perfil `observed-total-luna-1.0`, protocolo 1.3.0, relatório 1.4.0 e IPC 1.1.0.
- Os seis registros têm origem `candidate` e trazem `openai/gpt-5.6-luna` como modelo solicitado e retornado, via Feita. O manifesto delimita uma tentativa por caso, concorrência um, esforço `none` e máximo solicitado de 128 tokens de saída. O pré-voo público registrou zero chamadas de inferência.

## Resultado recalculado

| Critério de desenvolvimento | Exigido | Observado | Resultado |
| --- | ---: | ---: | --- |
| Alvos corretos | 8/8 | 7/8 | Reprovou |
| Campos válidos preservados | 4/4 | 4/4 | Passou |
| Conclusões corretas nos casos classificáveis | 3/3 | 3/3 | Passou |
| Revisões integrais nos casos que exigiam revisão | 3/3 | 2/3 | Reprovou |
| Reconhecimento bruto de urgente | 1/1 | 1/1 | Passou |
| Erros técnicos ou saída inválida | 0 | 0 | Passou |
| Custos conciliados | 6/6 | 6/6 | Passou |
| p95 total, seis observações | ≤ 3.000 ms | 2.635,459 ms | Passou |

| Caso | Alvos corretos | Decisão esperada | Decisão observada | Tempo total (ms) | Custo observado (US$) |
| --- | ---: | --- | --- | ---: | ---: |
| `jev-004` | 1/1 | Concluir | Concluiu | 1.282,100 | 0,00034240 |
| `jev-013` | 0/1 | Revisar | Concluiu | 1.613,341 | 0,00034060 |
| `jev-002` | 1/1 | Concluir | Concluiu | 2.635,459 | 0,00034170 |
| `jev-023` | 1/1 | Revisar | Encaminhou para revisão | 1.081,773 | 0,00034305 |
| `jev-006` | 2/2 | Concluir | Concluiu | 1.561,848 | 0,00035075 |
| `jev-039` | 2/2 | Revisar | Encaminhou para revisão | 1.383,625 | 0,00009977 |

Em `jev-013`, a referência congelada esperava `informacao_insuficiente` para a categoria ausente. Luna retornou `payouts` com status `predicted`. A decisão aplicou essa categoria, preservou a prioridade `basic` fornecida e concluiu o caso. O relatório registra uma conclusão indevida dentre três casos com revisão esperada e 2/3 categorias aplicadas corretas.

Pelo método *nearest-rank*, o p50 é a terceira duração ordenada, 1.383,625225999822 ms, e o p95 é a sexta, 2.635,458529999596 ms. A amostra contém seis durações completas, com uma observação por caso. O relatório de desenvolvimento tem elegibilidade `inconclusive`, reservando o julgamento de qualificação para o teste final completo. O estado `finished` indica que o lote foi concluído. A prova específica de desenvolvimento tem estado `failed`, e a candidata ficou sem qualificação final.

## Integridade e gate

O verificador canônico aceitou o relatório salvo, as entradas, as observações, as decisões e suas fontes. A reconstrução local do plano produziu os mesmos bytes de entrada do planejamento e da execução. O manifesto habilitado coincide com o molde, exceto pelo campo `enabled`, e corresponde à vinculação do plano, à invocação e à prova. Conferi o commit registrado e os SHA-256 de 21 arquivos de execução e 25 fontes distintas vinculadas, incluindo 12 arquivos da candidata congelada. Os hashes no checkout coincidiram com os bytes do commit-base. Os sete artefatos da prova também conferiram.

O diário contém 20 eventos para o mesmo `run_id`: planejamento, seis sequências de início de envio, envio e conclusão, e fechamento com seis decisões. As três sequências de registros, os seis recibos e o diário apresentam os mesmos seis IDs na ordem autorizada. O pré-voo marcou zero chamadas e os dois diretórios de evidência são o planejamento e o desenvolvimento.

Passei a prova original à verificação real da etapa final sem inicializar a etapa ou a conta. O verificador rejeitou a prova com `gate de development falhou ou pertence a outro modo` antes de verificar selo ou consultar finanças. O recálculo confirma que o modo é `real` e que os dois critérios reprovados justificam a rejeição. A autorização condiciona a etapa final a uma prova original real aprovada, ao selo original e a custos conciliados. A primeira condição falhou.

## Conciliação e proveniência

Os seis recibos distintos do gateway correspondem às observações, à prova e à exportação filtrada `financial-receipts.json`. A soma decimal foi 0,181827 créditos, convertidos a US$ 0,01 por crédito, totalizando **US$ 0,00181827**. As seis reservas de US$ 1,239 foram liquidadas, sem correções, expirações ou custo pendente. A estimativa por tarifa no relatório soma US$ 0,00331080.

Os snapshots da mesma conta registram 50 → 56 reservas liquidadas, zero pendências, 2 → 3 lotes e acumulado de **US$ 0,02687405 → US$ 0,02869232** sob o teto de US$ 10. A diferença entre os acumulados coincide com a soma dos recibos. A margem restante sob o teto interno é de US$ 9,97130768.

O protocolo declara uma referência sintética exploratória com seis aprovações humanas diretas e 54 casos delegados à IA. No desenvolvimento completo são 6/24 aprovações diretas e 18/24 delegadas. A interseção dos seis IDs executados com o registro histórico de aprovações mostra uma aprovação direta (`jev-002`) e cinco delegadas à IA, incluindo `jev-013`. O protocolo registra 0/36 aprovações diretas no final.

## Reprodução local

Execute a partir da worktree acima. O primeiro comando valida o relatório. O segundo recompõe o gate com os artefatos salvos, confere a conciliação por recibo e reproduz o bloqueio.

```sh
rtk proxy python3 -B script/check_classification_contracts.py \
  --profile observed-total-luna-1.0 \
  --report docs/evidencias/c05/luna-ensaio-real-01/development/report.json

rtk proxy env PYTHONPATH=script/classification_comparison python3 -B - <<'PY'
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from common import decode
from luna.round_spec import LUNA
from budget import BudgetError
from r2 import gate
from r2.plan import Plan, gate_reference

root = Path("docs/evidencias/c05")
evidence = root / "luna-ensaio-real-01"
development = evidence / "development"
proof_path = development / gate.FILENAME
proof = decode(proof_path.read_bytes())
bundle = {
    kind: [decode(line) for line in (development / f"{kind}.jsonl").read_bytes().splitlines()]
    for kind in ("inputs", "observations", "decisions")
}
bundle["report"] = decode((development / "report.json").read_bytes())
config = root / "luna-preflight-2026-11-24/config-real-planejada.json"
plan = Plan("development", "real", proof["run_id"], config, round_spec=LUNA)
export = decode((evidence / "financial-receipts.json").read_bytes())
costs = gate.settled_costs(
    {"reservations": export["rows"], "receipt_corrections": export["receipt_corrections"]},
    bundle["observations"], proof["run_id"], Decimal("1.239"),
)
assert costs == proof["costs"]
result = gate.assess(plan, bundle, costs)
assert result == {key: proof[key] for key in result}
print(result)

before, after = [
    decode((evidence / f"development-finance-{stage}.json").read_bytes())
    for stage in ("before", "after")
]
observed = sum(Decimal(cost["observed_usd"]) for cost in costs.values())
assert observed == Decimal(proof["observed_usd"])
assert observed == Decimal(after["accounted_usd"]) - Decimal(before["accounted_usd"])
print(f"US$ {observed}; {after['reservation_states']}")

with patch.object(gate.seal, "verify", side_effect=AssertionError), \
     patch.object(gate, "collect", side_effect=AssertionError):
    try:
        gate.verify(gate_reference(proof_path), SimpleNamespace(mode="real"), None, None)
    except BudgetError as error:
        assert str(error) == "gate de development falhou ou pertence a outro modo"
        print(error)
    else:
        raise AssertionError("o gate reprovado foi aceito")
PY
```

Na auditoria usei os artefatos filtrados e as fontes congeladas. A verificação financeira cobre a consistência dos registros exportados. O selo privado e a conta real ficaram fora da inspeção. A validação canônica conferiu as fontes do final, sem inspeção de seus textos ou rótulos e sem execução final. Os seis casos permitem julgar o gate de desenvolvimento e fornecem uma amostra de latência desse lote.

**Exercício.** Compare a entrada, a observação e a decisão de `jev-013`. Identifique qual campo estava autorizado para preenchimento e por que uma categoria aplicada mudou ao mesmo tempo as contagens de alvos corretos e de revisões integrais.
