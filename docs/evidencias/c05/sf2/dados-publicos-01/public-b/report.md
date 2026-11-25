# SF2-01 · Anotação pública B

O anotador de IA `sf2-public-b-astra-01` classificou os 240 textos da projeção recebida usando a rubrica fornecida. Cada texto recebeu uma decisão de categoria e uma de prioridade, ambas com justificativa e trecho literal. O verificador confirmou os 240 IDs únicos na ordem original, os códigos de catálogo e a presença de todas as evidências nos respectivos textos.

| Arquivo | SHA-256 |
| --- | --- |
| input.jsonl | `6bc4e53562cd243b67eb53267206cdb8ff9a72e176c266741e6f713948f5f621` |
| annotations-b.jsonl | `f17c8515f903706191ec45c34a5b7c07db02423f83c015da6accc33c110059a8` |

Esta entrega registra uma interpretação independente por IA. Relatos com vários assuntos de igual relevância ou sem fatos suficientes sobre impacto podem ter abstenção em apenas uma dimensão. A verificação automática cobre estrutura, cobertura e literalidade. A qualidade semântica permanece sujeita a revisão.

## Verificação executada na raiz do repositório

```sh
rtk proxy python3 - <<'PY'
from pathlib import Path
import json, hashlib
d=Path('.superpowers/sdd/tarefas/public-b')
raw=(d/'input.jsonl').read_bytes()
out=(d/'annotations-b.jsonl').read_bytes()
records=[json.loads(x) for x in raw.splitlines()]
annotations=[json.loads(x) for x in out.splitlines()]
assert len(records)==len(annotations)==len(set(r['id'] for r in records))==240
cats={'pix','payouts','terminal','informacao_insuficiente'}
prios={'basic','intermediate','advanced','urgent','informacao_insuficiente'}
for r,a in zip(records,annotations):
    assert r['id']==a['id'] and set(a)=={'id','annotator','origin','labels','rationale','evidence'}
    assert a['annotator']=='sf2-public-b-astra-01' and a['origin']=='ai'
    assert a['labels']['category'] in cats and a['labels']['priority'] in prios
    for field in ('category','priority'):
        assert a['rationale'][field].strip()
        excerpts=a['evidence'][field]
        assert excerpts and all(fragment and fragment in r['text'] for fragment in excerpts)
print(len(annotations),hashlib.sha256(raw).hexdigest(),hashlib.sha256(out).hexdigest())
PY
```
