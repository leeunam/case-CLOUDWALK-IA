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

## Revisão 1 de autoria após triagem de similaridade

- **Base da revisão** — `29973d74209796c54076fcaf9348c14a37ab1743`.
- **Commit da revisão** — `96b9dfa920756236b5e81a08e04df2a3e71a4acf`.
- **Origem** — feedback de similaridade consolidado pelo integrador para autoria. A revisão de rótulos anterior registrou 48 de 48 alvos aprovados para a base.
- **Escopo** — dez situações e justificativas substituídas. Os outros 26 objetos coincidem com a base. Máscaras, valores recebidos, rótulos e estratos coincidem nos 36 casos.
- **Status** — reavaliação independente de rótulos e similaridade pendente para o recorte alterado. A autoria usou somente o feedback delimitado, o brief, a rubrica comum e o catálogo. Houve zero inferências.

A comparação dos dois JSONs com a base, a conferência de codificação e unicidade,
a validação de máscaras, catálogo e todas as cotas e `git diff --check`
retornaram zero. O commit modifica apenas os dois JSONs previstos e a worktree
ficou limpa. Mantiveram-se 36 casos, 29 classificáveis, sete de revisão e seis
urgentes com prioridade ausente.

| Arquivo | SHA-256 após a revisão |
| --- | --- |
| `final-cases.json` | `4f1d712b87bbee326e3602b3fb74398558f929b08c1709b11407676869a21145` |
| `data-authorship.json` | `2236559d41cf1f1a50b09e961fd6797bb83e0f71578e9fc217b8c6dd195b2b7a` |

Use os comandos abaixo nesta worktree para repetir a conferência do recorte.
O comando de máscaras e cotas acima também passou novamente com o conjunto
deste commit.

```sh
rtk git diff --check 29973d7 96b9dfa
rtk git diff --name-status 29973d7 96b9dfa
rtk proxy python3 - <<'PY'
import hashlib
import json
from pathlib import Path
from subprocess import check_output

root = Path("docs/planejamento/classificacao-comparativa/r2")
base = "29973d74209796c54076fcaf9348c14a37ab1743"
current = "96b9dfa920756236b5e81a08e04df2a3e71a4acf"

def blob(revision, name):
    return check_output(["rtk", "proxy", "git", "show", f"{revision}:{root / name}"])

old_bytes = blob(base, "final-cases.json")
new_bytes = blob(current, "final-cases.json")
old = json.loads(old_bytes)
new = json.loads(new_bytes)
authorship = json.loads(blob(current, "data-authorship.json"))
changed = []

for before, after in zip(old["cases"], new["cases"], strict=True):
    assert list(before) == list(after)
    fields = {key for key in before if before[key] != after[key]}
    if fields:
        assert fields == {"text", "rationale"}
        changed.append(after["id"])
        after.update(before)

expected_ids = [f"r2-{i:03d}" for i in (1, 7, 14, 19, 20, 22, 23, 30, 31, 33)]
assert changed == expected_ids == authorship["revision_history"][-1]["changed_case_ids"]
assert hashlib.sha256(new_bytes).hexdigest() == authorship["dataset_sha256"]
assert (json.dumps(new, ensure_ascii=False, indent=2) + "\n").encode("utf-8") == old_bytes
print("10 situações e justificativas substituídas, 26 objetos e todos os demais campos conferidos")
PY
```

## Revisão 2 de autoria após triagem de similaridade

- **Base da revisão** — `96b9dfa920756236b5e81a08e04df2a3e71a4acf`.
- **Commit da revisão** — `9648208b47112fa87a8e584bb30e2779f2449ed8`.
- **Origem** — feedback do integrador sobre o único caso ainda sinalizado na triagem de similaridade. A autoria usou o feedback delimitado, o brief, a rubrica comum e o catálogo.
- **Escopo** — situação e justificativa de `r2-014` substituídas. Os outros 35 objetos coincidem com a base. Os campos recebidos, máscaras, rótulos e estratos coincidem nos 36 casos.
- **Status** — nova revisão independente de rótulo e similaridade pendente para o recorte. Houve zero inferências.

A conferência de JSON, UTF-8/NFC, unicidade, escopo e hashes passou. A
verificação de máscaras, catálogo e cotas voltou a passar com 36 casos, 29
classificáveis, sete de revisão e seis urgentes com prioridade ausente.
O commit modifica somente os dois JSONs previstos.

| Arquivo | SHA-256 após a revisão |
| --- | --- |
| `final-cases.json` | `17f5bae372983f90aa1956d0d583db25483a77a3ff35e4f1041ad4d51b897af9` |
| `data-authorship.json` | `e4ee3ff880c230dff7b53136c64e6db30b4c96e774d3f695663786793f3495bc` |

```sh
rtk git diff --check 96b9dfa 9648208
rtk git diff --name-status 96b9dfa 9648208
rtk proxy python3 - <<'PY'
import hashlib
import json
from subprocess import check_output

root = "docs/planejamento/classificacao-comparativa/r2"
base = "96b9dfa920756236b5e81a08e04df2a3e71a4acf"
current = "9648208b47112fa87a8e584bb30e2779f2449ed8"

def blob(revision, name):
    return check_output(["rtk", "proxy", "git", "show", f"{revision}:{root}/{name}"])

def encode(document):
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

old_bytes = blob(base, "final-cases.json")
new_bytes = blob(current, "final-cases.json")
old = json.loads(old_bytes)
new = json.loads(new_bytes)
old_authorship_bytes = blob(base, "data-authorship.json")
new_authorship = json.loads(blob(current, "data-authorship.json"))
changed = []

for before, after in zip(old["cases"], new["cases"], strict=True):
    assert list(before) == list(after)
    fields = {key for key in before if before[key] != after[key]}
    if fields:
        assert fields == {"text", "rationale"}
        changed.append(after["id"])
        after.update(before)

revision = new_authorship["revision_history"].pop()
assert changed == ["r2-014"] == revision["changed_case_ids"]
assert revision["round"] == 2 and revision["base_commit"] == base
assert hashlib.sha256(new_bytes).hexdigest() == new_authorship["dataset_sha256"]
new_authorship["dataset_sha256"] = json.loads(old_authorship_bytes)["dataset_sha256"]
assert encode(new_authorship) == old_authorship_bytes
assert encode(new) == old_bytes
print("1 caso substituído, 35 objetos e todos os outros campos conferidos")
PY
```
