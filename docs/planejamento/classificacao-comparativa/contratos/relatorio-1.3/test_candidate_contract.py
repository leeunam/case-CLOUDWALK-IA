import sys
from copy import deepcopy
from pathlib import Path
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "script"))
import check_classification_contracts as c01


class CandidateContractTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validation, cls.protocol, cls.split, cls.catalog, cls.cases = c01.profile_context(c01.R2)
        cls.golden = c01.load_bundle(cls.validation, c01.get_profile(c01.R2).golden_path)
        cls.dataset = c01.read(c01.source_path(cls.protocol["source_dataset"]))

    def test_golden_counts_one_request_for_each_candidate_control(self):
        c01.verify_run(self.golden, self.validation, self.protocol, self.split, self.catalog, self.cases)
        candidates = [row for row in self.golden["observations"] if row["origin"] == "candidate"]
        self.assertEqual(len(candidates), 8)
        self.assertTrue(all(row["requests"] == len(row["request_usage"]) == 1 for row in candidates))
        self.assertTrue(all(choice.get("score") is None for row in candidates for choice in row["choices"].values()))
        double = next(row for row in candidates if row["id"] == "ctl-duplo")
        self.assertEqual(double["questions"], 2)
        self.assertEqual(self.golden["report"]["usage"]["requests"]["value"], 8)

    def test_error_before_dispatch_preserves_zero_requests(self):
        obs = deepcopy(next(row for row in self.golden["observations"] if row["id"] == "ctl-timeout"))
        item = next(row for row in self.golden["inputs"] if row["id"] == obs["id"])
        decision = next(row for row in self.golden["decisions"] if row["id"] == obs["id"])
        obs.update(requests=0, questions=0, returned_model=None, request_usage=[])
        c01.structure(self.validation, "observation", obs)
        c01.verify_case(item, obs, decision, self.golden["report"], self.catalog)

    def test_metadata_rejects_historical_approval_and_paid_authorization(self):
        historical = dict(self.split, approved_on="2026-11-23")
        with self.assertRaisesRegex(c01.ContractError, "r2_offline_approval"):
            c01.verify_r2_package(self.protocol, historical, self.dataset)
        paid = deepcopy(self.protocol)
        paid["approval"]["paid_execution_authorized"] = True
        with self.assertRaisesRegex(c01.ContractError, "r2_offline_approval"):
            c01.verify_r2_package(paid, self.split, self.dataset)

    def test_metadata_rejects_attributing_final_labels_to_the_responsible_human(self):
        protocol = deepcopy(self.protocol)
        protocol["provenance"]["final"].update(human_direct_cases=1, agent_delegated_cases=35)
        with self.assertRaisesRegex(c01.ContractError, "r2_label_provenance"):
            c01.verify_r2_package(protocol, self.split, self.dataset)
