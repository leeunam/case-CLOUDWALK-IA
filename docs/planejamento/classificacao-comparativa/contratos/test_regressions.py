"""Directed contract checks with static data, without invoking an evaluator or model."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "script"))
import check_classification_contracts as contract


def metric(state, numerator, denominator, value):
    return dict(state=state, numerator=numerator, denominator=denominator, value=value)


class ContractRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = contract.read(contract.PLAN / "protocolo-comparacao.json")
        cls.split = contract.read(contract.PLAN / cls.protocol["data_split_file"])
        rows = contract.read(contract.ROOT / cls.protocol["source_dataset"]["path"])["cases"]
        cls.dataset = {row["id"]: row for row in rows}
        cls.validation = contract.validators()
        cls.bundle = contract.load_bundle(cls.validation)

    def test_frozen_slices_cannot_claim_zero_denominators(self):
        report = deepcopy(self.bundle["report"])
        report["completed_ids"] = [i for ids in self.split["final_test"].values() for i in ids]
        report["eligibility"] = "pass"
        # For a targeted completeness check the decisions only supply application status.
        decisions = {i: {"fields": {f: {"applied": None} for f in contract.FIELDS}} for i in report["completed_ids"]}
        for dimension, group, name, population in [
                ("by_field", "category", "raw_accuracy", 24),
                ("by_mask", "category+priority", "review", 12),
                ("by_stratum", "rotina", "review", 22)]:
            with self.subTest(dimension=dimension, group=group):
                candidate = deepcopy(report)
                m = candidate[dimension][group][name]
                m["denominator"] = 0
                with self.assertRaisesRegex(contract.ContractError, "slice_denominator"):
                    contract.verify_metrics(candidate, self.protocol, True, self.dataset, decisions)
                m.update(metric("measured", 0, population, 0))
                candidate["eligibility"] = "inconclusive"  # Other required evidence remains missing.
                contract.verify_metrics(candidate, self.protocol, True, self.dataset, decisions)

    def test_only_proven_empty_slice_is_exempt(self):
        # Isolate the eligibility predicate. Partial dictionaries here are not reports
        # for a candidate. Schema and end-to-end checks use the full fixture bundle.
        report = {"run_id": "controle", "completed_ids": ["synthetic"], "eligibility": "pass",
                  "gates": {"applied_category_accuracy": metric("measured", 1, 1, 1)},
                  "latency_p50_ms": metric("measured", None, 1, 3), "urgent_outcomes": {},
                  "by_mask": {}, "by_stratum": {}, "by_field": {"priority": {
                      "raw_accuracy": metric("measured", 0, 1, 0),
                      "applied_accuracy": metric("unmeasured", None, 0, None)}}}
        dataset = {"synthetic": {"missing": ["priority"], "expected": {"priority": "urgent"}}}
        decisions = {"synthetic": {"fields": {"priority": {"applied": None}}}}
        contract.verify_metrics(report, self.protocol, True, dataset, decisions)
        report["by_field"]["priority"]["raw_accuracy"] = metric("unmeasured", None, None, None)
        with self.assertRaisesRegex(contract.ContractError, "eligibility"):
            contract.verify_metrics(report, self.protocol, True, dataset, decisions)
        report["eligibility"] = "inconclusive"
        contract.verify_metrics(report, self.protocol, True, dataset, decisions)

    def test_zero_attempts_have_measured_counters_and_unknown_charges(self):
        catalog = contract.read(contract.ROOT / self.protocol["source_catalog"]["path"])
        bundle = deepcopy(self.bundle)
        ids = ["ctl-completo", "ctl-invalido"]
        bundle["report"]["control_ids"] = ids
        for stream in contract.KINDS:
            bundle[stream] = [r for r in bundle[stream] if r["id"] in ids]
        for name, total in bundle["report"]["usage"].items():
            counter = name in ("requests", "attempts", "questions")
            total.update(state="measured" if counter else "unavailable", value=0 if counter else None,
                         samples=0, expected_samples=0)
        contract.verify_run(bundle, self.validation, self.protocol, self.split, catalog, self.dataset)
        for name in ("requests", "attempts", "questions", "observed_api_usd"):
            with self.subTest(name=name):
                report = deepcopy(bundle["report"])
                total = report["usage"][name]
                if name == "observed_api_usd":
                    total.update(state="measured", value=0)
                else:
                    total.update(state="unavailable", value=None)
                with self.assertRaisesRegex(contract.ContractError, "usage_state"):
                    contract.verify_usage(report, [])

    def test_partial_request_cost_and_unicode_survive_the_exchange(self):
        row = next(o for o in self.bundle["observations"] if o["id"] == "ctl-duplo")
        self.assertEqual([r["observed_api_usd"] for r in row["request_usage"]], [0.01, None])
        subset = {"usage": {"observed_api_usd": {"state": "partial", "value": 0.01, "samples": 1, "expected_samples": 2}}}
        contract.verify_usage(subset, [row])
        item = next(i for i in self.bundle["inputs"] if i["id"] == "ctl-simples")
        self.assertEqual(item["text"], "Onde vejo\u2028o comprovante\u2029do Pix?\u0085Preciso da via.")


if __name__ == "__main__":
    unittest.main()
