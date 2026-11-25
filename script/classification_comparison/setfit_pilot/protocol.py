"""Seleção, divisões e medidas do piloto C05-SF1."""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from unicodedata import normalize

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
R2 = ROOT / "docs/planejamento/classificacao-comparativa/r2"
REVIEW = "informacao_insuficiente"
LABELS = ("pix", "payouts", "terminal", REVIEW)
SEED = 42
FOLD_COUNT = 4


def write_json(destination, value):
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(destination)


def normalized(text):
    return " ".join(normalize("NFKC", text).casefold().split())


def select_data():
    paths = (R2 / "dataset.json", R2 / "split.json")
    dataset_bytes, split_bytes = (path.read_bytes() for path in paths)
    dataset, split = json.loads(dataset_bytes), json.loads(split_bytes)
    hashes = [hashlib.sha256(blob).hexdigest() for blob in (dataset_bytes, split_bytes)]
    if (
        dataset["version"] != "2.0.0"
        or split["version"] != "2.0.0"
        or split["source_dataset_version"] != dataset["version"]
        or split["source_dataset_sha256"] != hashes[0]
    ):
        raise ValueError("As fontes devem corresponder ao dataset e split R2 2.0.0")

    development = {key for group in split["development"].values() for key in group}
    final = {key for group in split["final_test"].values() for key in group}
    if development & final:
        raise ValueError("IDs compartilhados entre development e final")
    development_cases = [row for row in dataset["cases"] if row["id"] in development]
    if Counter(row["id"] for row in development_cases) != Counter(development):
        raise ValueError("IDs de development ausentes ou duplicados")

    records = {
        row["id"]: {"text": row["text"], "label": row["expected"]["category"]}
        for row in sorted(development_cases, key=lambda row: row["id"])
        if "category" in row["missing"]
    }
    counts = Counter(row["label"] for row in records.values())
    if counts != Counter(dict.fromkeys(LABELS, 4)):
        raise ValueError(f"Distribuição esperada: quatro registros por rótulo. Encontrada: {counts}")
    texts = [normalized(row["text"]) for row in records.values()]
    if "" in texts or len(set(texts)) != len(records):
        raise ValueError("Textos vazios ou duplicados após normalização")

    ids = list(records)
    labels = [records[key]["label"] for key in ids]
    stratified = StratifiedKFold(n_splits=FOLD_COUNT, shuffle=True, random_state=SEED)
    folds = []
    for fold, (train, validation) in enumerate(stratified.split(ids, labels), start=1):
        train_ids = [ids[i] for i in train]
        validation_ids = [ids[i] for i in validation]
        if set(train_ids) & set(validation_ids) or set(train_ids + validation_ids) != set(ids):
            raise ValueError(f"Partição inválida na divisão {fold}")
        for group, per_label in ((train_ids, 3), (validation_ids, 1)):
            if Counter(records[key]["label"] for key in group) != Counter(dict.fromkeys(LABELS, per_label)):
                raise ValueError(f"Distribuição de rótulos inválida na divisão {fold}")
        folds.append({"fold": fold, "train_ids": train_ids, "validation_ids": validation_ids})
    if Counter(key for fold in folds for key in fold["validation_ids"]) != Counter(ids):
        raise ValueError("Cada texto precisa aparecer exatamente uma vez em validação")

    manifest = {
        "dataset_version": dataset["version"],
        "reference_review": dataset["review"],
        "synthetic": True,
        "sources_sha256": {str(path.relative_to(ROOT)): sha for path, sha in zip(paths, hashes, strict=True)},
        "split": "development",
        "selection": "category in missing",
        "ids": ids,
        "label_counts": {label: counts[label] for label in LABELS},
        "splitter": {"class": "StratifiedKFold", "n_splits": FOLD_COUNT, "shuffle": True, "seed": SEED},
        "id_order": "ascending",
        "text_normalization_for_duplicate_check": "NFKC, casefold, collapse whitespace",
        "folds": folds,
    }
    return records, manifest


def summarize(predictions):
    expected = [row["expected_label"] for row in predictions]
    observed = [row["predicted_label"] for row in predictions]
    matrix = confusion_matrix(expected, observed, labels=LABELS)
    correct_reviews = int(matrix[-1, -1])
    expected_reviews = expected.count(REVIEW)
    expected_categories = len(expected) - expected_reviews
    latencies = sorted(row["inference_ms"] for row in predictions)
    return {
        "n": len(predictions),
        "correct": int(matrix.trace()),
        "classification": classification_report(expected, observed, labels=LABELS, output_dict=True, zero_division=0),
        "confusion": {"labels": LABELS, "rows_expected_columns_predicted": matrix.tolist()},
        "review": {
            "correct": correct_reviews,
            "expected": expected_reviews,
            "incorrect_category_given_expected_review": expected_reviews - correct_reviews,
            "predicted": observed.count(REVIEW),
        },
        "category_coverage": {
            "categories_predicted": len(observed) - observed.count(REVIEW),
            "total": len(predictions),
            "classifiable_categories_predicted": int(matrix[:-1, :-1].sum()),
            "classifiable_total": expected_categories,
            "correct_categories": int(matrix[:-1, :-1].trace()),
        },
        "latency": {
            "n": len(latencies),
            "method": "nearest-rank",
            "p50_ms": latencies[math.ceil(0.50 * len(latencies)) - 1],
            "p95_ms": latencies[math.ceil(0.95 * len(latencies)) - 1],
        },
    }
