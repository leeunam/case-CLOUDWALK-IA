import unittest
from copy import deepcopy
from itertools import product

from jsonschema import Draft202012Validator

from .artifacts import validate_manifest, validate_report
from .core import (FIELDS, LABELS, PLAN, PROTOCOL, REVIEW, SCHEMA_PATH, ContractError, decode, read,
                   verify_sources)
from .data import (novelty_candidates, validate_annotation, validate_dataset, validate_isolation,
                   validate_record, _validate_masked, _validate_train)
from .ipc import project, validate_decision, validate_scores, validate_vector

FIXTURES = PLAN / "contratos/fixtures"


def fixture(name):
    return read(FIXTURES / (name + ".json"))


def audit(packet):
    validate_decision(packet["input"], packet["decision"], packet["policy"], packet["class_order"],
                      packet["identities"], interruption=packet.get("interruption"))


def quota_rows(partition):
    # Somente contadores sem texto/gold real, para testar as restrições cruzadas.
    categories, priorities = LABELS["category"][:-1], LABELS["priority"][:-1]
    if partition == "train":
        pairs = list(product(categories, priorities)) * 10
        pairs += [(c, REVIEW) for c in categories] * 4 + [(REVIEW, p) for p in priorities] * 3
        pairs += [(REVIEW, REVIEW)] * 6
        return [{"gold": {"category": c, "priority": p}} for c, p in pairs]
    rows = []
    quota = PROTOCOL["data"][partition]
    cats = [c for c, n in quota["classifiable_category_support_per_mask"].items() for _ in range(n)]
    for name in quota["masks"]:
        mask = list(FIELDS) if name == "both" else [name]
        pairs = [(c, priorities[i % 4]) for i, c in enumerate(cats)]
        if name == "both":
            n = quota["both_mask_review"]["category_only_insufficient"]
            pairs += [(REVIEW, "urgent")] + [(REVIEW, "basic")] * (n - 1)
            pairs += [("pix", REVIEW)] * n + [(REVIEW, REVIEW)] * 2
        else:
            pair = (REVIEW, "basic") if name == "category" else ("pix", REVIEW)
            pairs += [pair] * quota["review_per_mask"]
        rows.extend({"gold": {"category": c, "priority": p}, "missing_fields": mask} for c, p in pairs)
    return rows


class DataTest(unittest.TestCase):
    def test_contract_and_sources(self):
        Draft202012Validator.check_schema(read(SCHEMA_PATH))
        verify_sources()
        for bad in ('{"x":1,"x":2}', 'NaN', '1e999'):
            with self.assertRaises(ValueError):
                decode(bad)

    def test_record_mask_and_channel(self):
        record = fixture("record")
        validate_record(record)
        with self.assertRaisesRegex(ContractError, "missing_fields"):
            validate_record(fixture("invalid-mask"))
        record["received"]["priority"] = "urgent"
        with self.assertRaisesRegex(ContractError, "gold"):
            validate_record(record)
        record["received"]["priority"] = REVIEW
        with self.assertRaises(ContractError):
            validate_record(record)

    def test_annotation_stages_and_text_binding(self):
        record, draft, accepted = (fixture(name) for name in ("record", "annotation-draft", "annotation-accepted"))
        validate_annotation(record, draft, "draft")
        validate_annotation(record, accepted, "accepted")
        with self.assertRaises(ContractError):
            validate_annotation(record, draft, "accepted")
        for mutate in (lambda a: a.update(text_sha256="0" * 64),
                       lambda a: a.update(reconciliation=None),
                       lambda a: a["annotations"][1].update(annotator="AUTOR-Fixture"),
                       lambda a: a["annotations"][1]["evidence"].update(category=["trecho inexistente"]),
                       lambda a: a["reconciliation"]["labels"].update(priority="urgent"),
                       lambda a: a["catalog"].update(sha256="0" * 64)):
            bad = deepcopy(accepted)
            mutate(bad)
            with self.assertRaises(ContractError):
                validate_annotation(record, bad, "accepted")

    def test_quota_mutations(self):
        for part in ("train", "validation", "final"):
            rows = quota_rows(part)
            check = _validate_train if part == "train" else _validate_masked
            q = PROTOCOL["data"][part]
            self.assertEqual(len(rows), q["total"])
            check(rows, q)
            # Conserva o total e os suportes marginais no treino, altera pares.
            if part == "train":
                rows[0]["gold"]["priority"], rows[5]["gold"]["priority"] = "intermediate", "basic"
            else:
                target = next(r for r in rows if r["gold"] == {"category": REVIEW, "priority": "urgent"})
                target["gold"]["priority"] = "advanced"
            with self.assertRaises(ContractError):
                check(rows, q)

    def test_isolation_normalization_and_neighbors(self):
        a = fixture("record")
        b = {**a, "partition": "final", "id": "b", "family_id": "outra", "text": a["text"].upper()}
        for field, value in (("text", a["text"].upper()), ("family_id", a["family_id"]), ("id", a["id"])):
            other = {**b, "text": "Outro exemplo", field: value}
            with self.assertRaises(ContractError):
                validate_isolation({"validation": [a], "final": [other]})
        candidates = [{"text": "fala pix", "id": c} for c in "dcba"]
        result = novelty_candidates({"text": "FALA  PIX"}, candidates)
        self.assertTrue(result["short_text"])
        self.assertEqual([v[0] for v in result["neighbors"]], list("abcd"))
        with self.assertRaises(ContractError):
            validate_dataset({"validation": [a]}, [fixture("annotation-draft")], "draft")


class IPCTest(unittest.TestCase):
    def test_positive_negative_controls(self):
        for name in ("complete-channel", "invalid-channel", "category-only", "priority-only", "both", "timeout"):
            with self.subTest(name=name):
                audit(fixture(name))
        for name in ("invalid-partial", "invalid-score"):
            with self.assertRaises(ContractError):
                audit(fixture(name))

    def test_cuts_ties_catalog_and_uninvoked_heads(self):
        p = fixture("category-only")
        f = p["decision"]["fields"]["category"]
        f["vector"]["scores"] = [0, 0.4, 0.6, 0]  # ['informacao_insuficiente','payouts','pix','terminal']
        f["margin"] = 0.2
        audit(p)  # tau inclusivo
        p["policy"]["category"]["delta"] = f["cut"]["delta"] = 0.2
        f.update(decision="review", reason="low_margin")
        p["decision"].update(outcome="review", applied={})
        audit(p)
        f["vector"]["scores"] = [0, 0.5, 0.5, 0]
        f.update(raw="payouts", margin=0)
        f["cut"]["tau"] = p["policy"]["category"]["tau"] = 0.5
        audit(p)
        p["input"]["catalog"]["category"].pop("payouts")
        f.update(reason="inactive_label")
        audit(p)
        for change in (lambda x: x["decision"]["calls"].update(priority=1),
                       lambda x: x["decision"]["received"].update(priority="urgent"),
                       lambda x: x["decision"].update(package_sha256="f" * 64),
                       lambda x: x["input"].update(gold={}),
                       lambda x: x["input"].update(missing_fields=[])):
            bad = deepcopy(p)
            change(bad)
            with self.assertRaises(ContractError):
                audit(bad)

    def test_interruption_and_errors(self):
        p = fixture("category-only")
        f = p["decision"]["fields"]["category"]
        f.update(vector=None, raw=None, margin=None, decision="error", reason="invalid_score")
        p["decision"].update(outcome="error", applied={})
        audit(p)
        f.update(reason="too_long")
        p["decision"]["calls"]["category"] = 0
        with self.assertRaises(ContractError):
            audit(p)
        p["decision"]["outcome"] = f["decision"] = "review"
        p["interruption"] = "too_long"
        audit(p)
        bad = fixture("invalid-channel")
        bad["decision"]["received"]["category"] = 0
        with self.assertRaises(ContractError):
            audit(bad)

    def test_vectors_and_scores_inventory(self):
        p = fixture("category-only")
        record = fixture("record")
        self.assertNotIn("gold", project(record))
        identity = {k: p["identities"][k] for k in ("model_sha256", "package_sha256")}
        identity.update(dataset_sha256="0" * 64, class_order=p["class_order"])
        vector = p["decision"]["fields"]["category"]["vector"]
        row = dict(id=record["id"], heads={"category": vector}, errors={})
        bundle = dict(contract_version="sf2-ipc/1.0", partition="validation", rows=[row], **identity)
        validate_scores(bundle, [record], **identity)
        for scores in ([0, 0, float("nan"), 0], [0, 0, 1.01, 0], [0.1, 0.5, 0.3, 0], [1]):
            with self.assertRaises(ContractError):
                validate_vector({**vector, "scores": scores}, p["class_order"]["category"])
        with self.assertRaises(ContractError):
            validate_vector(vector, list(reversed(vector["classes"])))
        with self.assertRaises(ContractError):
            validate_scores(bundle, [record], **{**identity, "package_sha256": "1" * 64})
        row["errors"]["category"] = "timeout"
        with self.assertRaises(ContractError):
            validate_scores(bundle, [record], **identity)
