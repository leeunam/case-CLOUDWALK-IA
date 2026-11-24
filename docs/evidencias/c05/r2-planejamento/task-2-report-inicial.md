# C05-R2 · Task 2 · autoria dos casos finais

- **Status** — concluída a autoria, com revisão independente e conferência de similaridade pendentes.
- **Branch** — `docs/r2-protocolo-dados`.
- **Worktree** — `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-dados`.
- **Base** — `c00ac5431630c92d30349c13529d5071ad9879b4`.
- **Commit de entrega** — `29973d74209796c54076fcaf9348c14a37ab1743`.

Foram adicionados somente `final-cases.json` e `data-authorship.json` em
`docs/planejamento/classificacao-comparativa/r2/`. O primeiro reúne relatos
sintéticos em português brasileiro, com alvos normalizáveis e justificativas
que apontam os fatos usados na rotulação. O segundo registra a origem dos
rótulos, o método, as referências, as contagens e as etapas de revisão
pendentes.

## Contagens verificadas

| Máscara | Casos | Classificáveis | Revisão | Urgentes com prioridade ausente |
| --- | ---: | ---: | ---: | ---: |
| Categoria | 12 | 10 | 2 | 0 |
| Prioridade | 12 | 10 | 2 | 3 |
| Dupla | 12 | 9 | 3 | 3 |
| Total | 36 | 29 | 7 | 6 |

- Há cinco categorias insuficientes, três prioridades insuficientes e uma sobreposição.
- Os três casos duplos para revisão têm categoria insuficiente. Suas prioridades são uma urgente, uma básica e uma insuficiente.
- Dos seis urgentes com prioridade ausente, dois são duplos classificáveis e um é duplo para revisão. O estrato `ambiguo` prevalece quando há abstenção em qualquer alvo. A composição final é de 24 `rotina`, cinco `urgente` e sete `ambiguo`.
- As 48 ausências recebidas incluem 17 chaves omitidas, 15 valores nulos, sete strings vazias e nove strings de espaços. As 24 chaves fornecidas têm códigos válidos.
- Entre os alvos de categoria há sete `terminal`, seis `payouts`, seis `pix` e cinco insuficientes. Entre os alvos de prioridade há cinco `basic`, seis `intermediate`, quatro `advanced`, seis `urgent` e três insuficientes.

## Verificações

1. Revisão de autoria das 36 justificativas com o brief, a rubrica comum e o catálogo fixado. Os textos e os rótulos antigos, as saídas dos candidatos e as instruções novas ficaram fora das fontes de autoria. As marcas e as situações foram criadas para este conjunto.
2. Conferência offline em Python com saída zero. Conferidos JSON sem chaves duplicadas, UTF-8 sem BOM, texto em NFC, caracteres de controle, unicidade de IDs, textos e justificativas, máscaras e ordem dos alvos, formação da ausência, catálogo, estratos, quotas e hash declarado da fonte.
3. `rtk git diff --cached --check` e `rtk git diff --check HEAD^ HEAD` retornaram zero. A lista do commit confirma somente os dois novos arquivos e o estado da worktree após o commit está limpo.

| Arquivo | SHA-256 |
| --- | --- |
| `final-cases.json` | `de29a2de28e9b643dfe82eff97ef54263afa3eca7ad0b8642f5c3fc4ee22d4b8` |
| `data-authorship.json` | `e52d30e64d6579f8893d7625fea6d0b02ba758b5bf6454d19d4ae689e1ddc2eb` |

Na worktree da tarefa, é possível repetir a conferência de arquivos, codificação,
contagens e integridade com os comandos abaixo.

```sh
rtk git diff --check c00ac54 29973d7
rtk git diff --name-status c00ac54 29973d7
rtk proxy sha256sum docs/planejamento/classificacao-comparativa/r2/{final-cases,data-authorship}.json
rtk proxy python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path

root = Path("docs/planejamento/classificacao-comparativa/r2")
cases = json.loads((root / "final-cases.json").read_text(encoding="utf-8"))["cases"]
catalog = json.loads(Path("script/f08/jev/catalog.json").read_text(encoding="utf-8"))
unknown = "informacao_insuficiente"
fields = ("category", "priority")
masks = Counter()
missing_fields = Counter()
urgents = Counter()
texts = set()

for index, case in enumerate(cases, start=1):
    assert case["id"] == f"r2-{index:03d}"
    text = " ".join(case["text"].casefold().split())
    assert text and text not in texts
    texts.add(text)
    missing = []
    for field in fields:
        value = case["received"].get(field)
        if value is None or not value.strip():
            missing.append(field)
        else:
            assert value in catalog[field]
    mask = ("category", "priority", "both")[(index - 1) // 12]
    assert missing == list(case["expected"]) == case["missing"]
    assert missing == (list(fields) if mask == "both" else [mask])
    for field, label in case["expected"].items():
        assert label == unknown or label in catalog[field]
        if label == unknown:
            missing_fields[field] += 1
    review = unknown in case["expected"].values()
    masks[(mask, review)] += 1
    if case["expected"].get("priority") == "urgent":
        urgents[(mask, review)] += 1

assert masks == {
    ("category", False): 10, ("category", True): 2,
    ("priority", False): 10, ("priority", True): 2,
    ("both", False): 9, ("both", True): 3,
}
assert missing_fields == {"category": 5, "priority": 3}
assert urgents == {("priority", False): 3, ("both", False): 2, ("both", True): 1}
print("36 casos, máscaras e quotas conferidos")
PY
```

## Pendências para a integração

A revisão exploratória independente dos 36 rótulos e a conferência de
similaridade por um terceiro papel seguem pendentes. A unicidade verificada
localmente cobre os textos dentro do novo conjunto. Os vereditos externos e
suas referências devem ser registrados antes de considerar a revisão concluída.
Divergências persistentes vão para o responsável. Houve zero inferências.

Para praticar a regra de aplicação após o fechamento da revisão, escolha um
caso duplo em que só a prioridade seja determinável. Leia o relato e identifique
quais fatos sustentam a prioridade e qual informação ainda falta para reconhecer
a categoria. O atendimento segue para revisão sem aplicar a prioridade inferida.
