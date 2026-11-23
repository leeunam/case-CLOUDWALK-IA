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
                  "gates": {"channel_field_preservation_ratio": metric("measured", 1, 1, 1)},
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

    def test_applied_accuracy_matches_its_gate_for_both_fields(self):
        for field in contract.FIELDS:
            with self.subTest(field=field):
                ids = [f"controle-{i}" for i in range(19)]
                dataset = {i: {"missing": [field], "expected": {field: "codigo"}} for i in ids}
                decisions = {i: {"fields": {field: {"applied": "codigo"}}} for i in ids}
                gate = f"applied_{field}_accuracy"
                summary = {"applied_accuracy": metric("measured", 0, 19, 0)}
                report = {"run_id": "controle", "completed_ids": ids, "eligibility": "pass",
                          "gates": {gate: metric("measured", 1, 1, 1)}, "by_field": {field: summary},
                          "by_mask": {}, "by_stratum": {}, "urgent_outcomes": {},
                          "latency_p50_ms": metric("measured", None, 19, 10)}
                with self.assertRaisesRegex(contract.ContractError, "applied_accuracy_mismatch"):
                    contract.verify_metrics(report, self.protocol, True, dataset, decisions)
                for correct, outcome in ((0, "fail"), (17, "fail"), (18, "pass")):
                    summary["applied_accuracy"] = metric("measured", correct, 19, correct / 19)
                    report["gates"][gate] = dict(summary["applied_accuracy"])
                    report["eligibility"] = outcome
                    contract.verify_metrics(report, self.protocol, True, dataset, decisions)

                for key, value in (("state", "partial"), ("value", 18 / 19 + 1e-12)):
                    with self.subTest(key=key):
                        report["gates"][gate] = dict(summary["applied_accuracy"], **{key: value})
                        with self.assertRaisesRegex(contract.ContractError, "applied_accuracy_mismatch"):
                            contract.verify_metrics(report, self.protocol, True, dataset, decisions)

                for decision in decisions.values():
                    decision["fields"][field]["applied"] = None
                summary["applied_accuracy"] = metric("unmeasured", None, 0, None)
                report["gates"][gate] = dict(summary["applied_accuracy"])
                with self.assertRaisesRegex(contract.ContractError, "eligibility"):
                    contract.verify_metrics(report, self.protocol, True, dataset, decisions)
                report["eligibility"] = "inconclusive"
                contract.verify_metrics(report, self.protocol, True, dataset, decisions)

    def test_urgent_outcomes_and_percentiles_use_the_full_sample(self):
        ids = [i for group in self.split["final_test"].values() for i in group]
        urgent_outcomes = {k: metric("measured", 0, 6, 0) for k in self.bundle["report"]["urgent_outcomes"]}
        urgent_outcomes.update(applied_urgent=metric("measured", 5, 6, 5 / 6),
                               review=metric("measured", 1, 6, 1 / 6))
        report = {"run_id": "controle", "completed_ids": ids, "eligibility": "pass",
                  "gates": {"raw_urgent_recognition_min": metric("measured", 5, 6, 5 / 6),
                            "warm_total_latency_p95_ms_max": metric("measured", None, 36, 3000)},
                  "by_field": {}, "by_mask": {}, "by_stratum": {}, "urgent_outcomes": urgent_outcomes,
                  "latency_p50_ms": metric("measured", None, 36, 100)}
        contract.verify_metrics(report, self.protocol, True, {}, {})
        for name in (*urgent_outcomes, "latency_p50_ms"):
            with self.subTest(metric=name):
                latency = name == "latency_p50_ms"
                target = report[name] if latency else urgent_outcomes[name]
                original = dict(target)
                population = 36 if latency else 6
                error = "latency_denominator" if latency else "urgent_denominator"
                for n in (1, population - 1, population + 1):
                    target.update(metric("measured", None if latency else 1, n, 100 if latency else 1 / n))
                    with self.assertRaisesRegex(contract.ContractError, error):
                        contract.verify_metrics(report, self.protocol, True, {}, {})
                target["state"] = "partial"  # Above population is still impossible.
                with self.assertRaisesRegex(contract.ContractError, error):
                    contract.verify_metrics(report, self.protocol, True, {}, {})
                n = population - 1
                target.update(metric("partial", None if latency else 1, n, 100 if latency else 1 / n))
                with self.assertRaisesRegex(contract.ContractError, "eligibility"):
                    contract.verify_metrics(report, self.protocol, True, {}, {})
                report["eligibility"] = "inconclusive"
                contract.verify_metrics(report, self.protocol, True, {}, {})
                target.update(original)
                report["eligibility"] = "pass"

    def test_final_manifest_cannot_claim_samples_before_the_first_case(self):
        bundle = deepcopy(self.bundle)
        report = bundle["report"]
        report["split"] = "final_test"
        report["planned_ids"] = [i for group in self.split["final_test"].values() for i in group]
        catalog = contract.read(contract.ROOT / self.protocol["source_catalog"]["path"])
        args = self.validation, self.protocol, self.split, catalog, self.dataset
        contract.verify_run(bundle, *args)
        for target, error, population, numerator in (
                (report["urgent_outcomes"]["review"], "urgent_denominator", 6, 1),
                (report["latency_p50_ms"], "latency_denominator", 36, None),
                (report["gates"]["warm_total_latency_p95_ms_max"], "latency_denominator", 36, None)):
            original = dict(target)
            for state, n in (("measured", population), ("partial", 1)):
                with self.subTest(error=error, state=state):
                    target.update(metric(state, numerator, n, 100 if numerator is None else numerator / n))
                    with self.assertRaisesRegex(contract.ContractError, error):
                        contract.verify_run(bundle, *args)
            target.update(original)

    def test_card_distinguishes_quality_approval_from_pending_spend(self):
        card = (contract.PLAN / "cards/C01-protocolo.md").read_text(encoding="utf-8")
        approved = next(item for item in card.split("\n- ") if item.startswith("[x] Aprovar "))
        self.assertIn("latência", approved)
        self.assertNotRegex(approved, r"custo|orçamento|teto")
        self.assertIn("autorização pendente", card)
        execution = self.protocol["execution"]
        self.assertFalse(execution["paid_execution_authorized"])
        self.assertIsNone(execution["budget_cap_usd"])

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
