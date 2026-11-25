"""Vínculo texto/anotação e contagens por partição, antes de qualquer treino."""
from collections import Counter
import re
import unicodedata

from .core import CATALOG, FIELDS, LABELS, PROTOCOL, REVIEW, channel, require, structure, text_hash


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def validate_record(row):
    structure("record", row)
    if row["partition"] != "train":
        missing, invalid, valid = channel(row["received"], CATALOG)
        require(missing and set(missing) == set(row["missing_fields"]), "missing_fields diverge do canal")
        require(not invalid, "canal inválido no conjunto anotado")
        require(all(row["gold"][k] == v for k, v in valid.items()), "gold diverge do canal")


def validate_annotation(row, entry, stage):
    validate_record(row)
    structure("annotationRecord", entry)
    require(stage in ("draft", "accepted"), "estágio desconhecido")
    require(entry["id"] == row["id"] and entry["text_sha256"] == text_hash(row["text"]),
            "anotação pertence a outro relato ou texto")
    annotations = entry["annotations"]
    reconciliation = entry["reconciliation"]
    if stage == "draft":
        require(len(annotations) == 1 and reconciliation is None, "draft exige exatamente a anotação autoral")
        require(annotations[0]["labels"] == row["gold"] and annotations[0]["annotator"] == row["author"],
                "gold/autoria do draft diverge da anotação")
    else:
        identities = {normalize(a["annotator"]) for a in annotations}
        require(len(identities) == 2 and normalize(row["author"]) in identities,
                "exige a anotação autoral e uma segunda identidade distinta")
        require(reconciliation is not None and reconciliation["labels"] == row["gold"],
                "conciliação ausente ou incompatível com gold")
    for annotation in annotations:
        for field in FIELDS:
            pieces = annotation["evidence"][field]
            require(all(piece in row["text"] for piece in pieces), "trecho não consta no relato")
            require(pieces or annotation["labels"][field] == REVIEW, "rótulo claro exige trecho de evidência")


def validate_isolation(partitions):
    families, texts, ids = {}, set(), set()
    for partition, rows in partitions.items():
        for row in rows:
            family = normalize(row["family_id"])
            require(row["partition"] == partition, "registro na partição errada")
            require(row["id"] not in ids, "ID duplicado")
            require(families.setdefault(family, partition) == partition, "família em partições distintas")
            normalized = normalize(row["text"])
            require(normalized not in texts, "texto normalizado duplicado")
            ids.add(row["id"])
            texts.add(normalized)


def _validate_train(rows, quota):
    pairs = Counter((r["gold"]["category"], r["gold"]["priority"]) for r in rows)
    for field in FIELDS:
        require(Counter(row["gold"][field] for row in rows) == quota[field + "_support"],
                "suporte incorreto: " + field)
    for category in LABELS["category"][:-1]:
        for priority in LABELS["priority"][:-1]:
            require(pairs[category, priority] == quota["per_clear_category_priority_pair"], "par de treino incorreto")
    require(pairs[REVIEW, REVIEW] == quota["both_insufficient"], "quota de dupla insuficiência")


def _validate_masked(rows, quota):
    urgent = 0
    targets = Counter()
    for name in quota["masks"]:
        fields = set(FIELDS) if name == "both" else {name}
        group = [r for r in rows if set(r["missing_fields"]) == fields]
        clear = [r for r in group if all(r["gold"][f] != REVIEW for f in fields)]
        require(len(group) == quota["per_mask"] and len(clear) == quota["classifiable_per_mask"], "quota por máscara")
        require(Counter(r["gold"]["category"] for r in clear) == quota["classifiable_category_support_per_mask"],
                "suporte de categoria por máscara")
        if "priority" in fields:
            support = quota["clear_priority_support_per_" + name + "_mask"]
            require(Counter(r["gold"]["priority"] for r in clear) ==
                    {p: support for p in LABELS["priority"] if p != REVIEW}, "suporte de prioridade por máscara")
            urgent += sum(r["gold"]["priority"] == "urgent" for r in group)
        if name == "category":
            require(all(r["gold"]["priority"] != "urgent" for r in group if r["gold"]["category"] == REVIEW),
                    "prioridade clara em revisão fora de both deve ser não urgente")
        if name == "both":
            reviews = Counter(("both" if r["gold"]["priority"] == r["gold"]["category"] == REVIEW
                               else "category_only" if r["gold"]["category"] == REVIEW else "priority_only")
                              + "_insufficient" for r in group if REVIEW in r["gold"].values())
            require(reviews == quota["both_mask_review"], "composição das revisões em both")
        for field in fields:
            targets[field] += len(group)
    require(urgent == quota["urgent_target_cases"] and targets == quota["target_fields"], "suporte dos alvos")


def validate_dataset(partitions, annotations, stage):
    require(stage in ("draft", "accepted") and partitions, "estágio ou conjunto inválido")
    for partition, rows in partitions.items():
        require(partition in ("train", "validation", "final"), "partição inválida")
        for row in rows:
            validate_record(row)
    validate_isolation(partitions)
    by_id = {a["id"]: a for a in annotations}
    expected_ids = {r["id"] for rows in partitions.values() for r in rows}
    require(len(by_id) == len(annotations) and set(by_id) == expected_ids, "IDs de anotações divergentes")
    for name, rows in partitions.items():
        quota = PROTOCOL["data"][name]
        require(len(rows) == quota["total"], "total de relatos incorreto")
        for row in rows:
            validate_annotation(row, by_id[row["id"]], stage)
        if name == "train":
            _validate_train(rows, quota)
        else:
            _validate_masked(rows, quota)
    return {"stage": stage, "accepted": stage == "accepted", "counts": {p: len(r) for p, r in partitions.items()}}


def novelty_candidates(row, other_records):
    """Apenas sugere pares à revisão semântica pelo custodiante autorizado."""
    def tokens(text):
        return set(re.findall(r"[^\W_]+", normalize(text)))
    own = tokens(row["text"])
    scores = []
    for other in other_records:
        theirs = tokens(other["text"])
        union = own | theirs
        score = len(own & theirs) / len(union) if union else 1.0
        scores.append((other["id"], score))
    scores.sort(key=lambda item: (-item[1], item[0]))
    rule = PROTOCOL["data"]["annotation"]
    cutoff = rule["token_jaccard_review_threshold"]
    k = rule["cross_partition_lexical_neighbors_reviewed_per_record"]
    return {"short_text": len(re.findall(r"[^\W_]+", normalize(row["text"]))) < rule["short_text_review_token_count_lt"],
            "neighbors": [pair for i, pair in enumerate(scores) if i < k or pair[1] >= cutoff]}
