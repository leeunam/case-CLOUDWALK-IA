"""Contract vectors only; every duration and candidate response in these tests is synthetic."""
import json
from copy import deepcopy
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "script"))
import check_classification_contracts as c


def metric(state, n, value=None):
    return dict(state=state, numerator=None, denominator=n, value=value)


class ObservedLatencyProfile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = c.get_profile(c.OBSERVED)
        cls.context = c.profile_context(cls.profile.name)
        cls.validation, cls.protocol, cls.split, cls.catalog, cls.dataset = cls.context
        cls.golden = c.load_bundle(cls.validation, cls.profile.golden_path)

    def test_only_latency_changes_in_frozen_quality_rules(self):
        original = c.read(c.get_profile().protocol_path)
        self.assertEqual({k: v for k, v in self.protocol["gates"].items() if k != c.OBSERVED_GATE},
                         {k: v for k, v in original["gates"].items() if k != c.WARM_GATE})
        self.assertEqual(self.protocol["gates"][c.OBSERVED_GATE], 3000)
        for key in ("source_dataset", "source_catalog", "data_split_file", "data_split_sha256", "control_policy",
                    "rubric", "exact_test_denominators", "provenance", "decision"):
            self.assertEqual(self.protocol[key], original[key], key)
        for key in ("timeout_ms_per_case", "attempts_per_case", "concurrency", "full_test_cases_per_candidate"):
            self.assertEqual(self.protocol["execution"][key], original["execution"][key], key)
        self.assertEqual(self.protocol["ipc_contract_version"], self.profile.ipc_version)
        self.assertEqual(self.protocol["contract_version"], self.profile.report_version)

    def test_report_pins_and_ipc_are_distinct(self):
        self.assertEqual(c.verify_report(self.profile.golden_path), self.profile)
        with self.assertRaisesRegex(c.ContractError, "profile_mismatch"):
            c.verify_report(self.profile.golden_path, c.LEGACY)
        for stream, schema in c.KINDS.items():
            row = self.golden[stream][0]
            self.assertEqual(row["contract_version"], "1.1.0")
            with self.assertRaises(c.ContractError):
                c.structure(self.validation, schema, dict(row, contract_version="1.2.0"))
        for changed in ({"version": "1.0.0"}, {"sha256": "0"*64}, {"path": "../untrusted.json"}):
            report = deepcopy(self.golden["report"])
            report["sources"]["protocol"].update(changed)
            with self.assertRaisesRegex(c.ContractError, "profile_protocol"):
                c.profile_for_report(report)
        forged = deepcopy(self.protocol)
        forged["gates"][c.OBSERVED_GATE] = 10000
        with self.assertRaisesRegex(c.ContractError, "profile_protocol"):
            c.verify_sources(self.golden["report"], forged, self.split)

    def synthetic_sample(self, durations):
        report = deepcopy(self.golden["report"])
        report["identity"]["mode"] = "real"
        ids = [f"synthetic-{index}" for index in range(len(durations))]
        report.update(run_id="synthetic-unit-test", split="final_test", planned_ids=ids, completed_ids=ids.copy())
        observations = {}
        outcomes = ("predicted", "abstained", "invalid", "error")
        for index, (case_id, duration) in enumerate(zip(ids, durations)):
            status = outcomes[index % len(outcomes)]
            observations[case_id] = dict(origin="candidate", elapsed_ms=duration,
                                         temperature_state=("warm", "unknown", "cold")[index % 3],
                                         choices={"category": {"status": status}, "priority": {"status": status}})
        observations["ctl-duplo"] = dict(origin="candidate", elapsed_ms=60000, temperature_state="warm")
        return report, observations

    def test_complete_sample_and_inclusive_gate(self):
        decisions = {row["id"]: row for row in self.golden["decisions"]}
        for boundary, verdict in ((3000, "pass"), (3001, "fail")):
            with self.subTest(boundary=boundary):
                report, observations = self.synthetic_sample([1500] * 34 + [boundary, 5000])
                observations["synthetic-35"]["choices"] = {"category": {"status": "error", "reason": "timeout"}}
                report["gates"] = {c.OBSERVED_GATE: metric("measured", 36, boundary)}
                report.update(latency_p50_ms=metric("measured", 36, 1500), eligibility=verdict,
                              by_field={}, by_mask={}, by_stratum={}, urgent_outcomes={})
                samples = c.verify_observed_latency(report, observations, 36)
                full = c.has_complete_evidence(report, observations, decisions, samples)
                self.assertTrue(full)
                c.verify_metrics(report, self.protocol, full, {}, {}, c.OBSERVED_GATE)
                report["eligibility"] = "fail" if verdict == "pass" else "pass"
                with self.assertRaisesRegex(c.ContractError, "eligibility"):
                    c.verify_metrics(report, self.protocol, full, {}, {}, c.OBSERVED_GATE)
                for case_id in report["completed_ids"]:
                    observations[case_id]["choices"] = {"category": {"status": "error"}}
                self.assertFalse(c.has_complete_evidence(report, observations, decisions, samples))

    def test_nearest_rank_and_forged_complete_percentiles(self):
        report, obs = self.synthetic_sample(list(reversed(range(1, 37))))
        report["latency_p50_ms"] = metric("measured", 36, 18)
        report["gates"][c.OBSERVED_GATE] = metric("measured", 36, 35)
        self.assertEqual(c.verify_observed_latency(report, obs, 36), 36)
        for target, bad in ((report["latency_p50_ms"], {"value": 18.5}),
                            (report["gates"][c.OBSERVED_GATE], {"value": 36}),
                            (report["gates"][c.OBSERVED_GATE], {"denominator": 35}),
                            (report["gates"][c.OBSERVED_GATE], {"state": "partial"})):
            with self.subTest(bad=bad):
                original = target.copy()
                target.update(bad)
                with self.assertRaisesRegex(c.ContractError, "observed_latency"):
                    c.verify_observed_latency(report, obs, 36)
                target.update(original)

    def test_mixed_development_sample_excludes_slow_candidate_control(self):
        vectors = [(900, "unknown", "predicted"), (1100, "warm", "predicted"),
                   (1400, "cold", "abstained"), (2400, "unknown", "invalid"),
                   (3200, "warm", "error"), (5000, "cold", "error")]
        report, obs = self.synthetic_sample([duration for duration, _, _ in vectors])
        report["split"] = "development"
        for case_id, (_, thermal, status) in zip(report["completed_ids"], vectors):
            obs[case_id].update(temperature_state=thermal, choices={"category": {"status": status}})
        obs["synthetic-0"]["choices"]["priority"] = {"status": "predicted"}
        obs["synthetic-5"]["choices"]["category"]["reason"] = "timeout"
        obs["ctl-duplo"]["elapsed_ms"] = 5200
        report["latency_p50_ms"] = metric("measured", 6, 1400)
        report["gates"][c.OBSERVED_GATE] = metric("measured", 6, 5000)
        self.assertEqual(c.verify_observed_latency(report, obs, 6), 6)
        self.assertFalse(c.has_complete_evidence(report, obs, {}, 6))
        for bad in (metric("partial", 2, 3200), metric("measured", 7, 5200),
                    metric("partial", 4, 2400)):
            report["gates"][c.OBSERVED_GATE] = bad
            with self.assertRaisesRegex(c.ContractError, "observed_latency"):
                c.verify_observed_latency(report, obs, 6)

    def test_missing_durations_prefix_fixture_and_zero_samples(self):
        report, obs = self.synthetic_sample([0, None, 5020])
        decisions = {row["id"]: row for row in self.golden["decisions"]}
        report["planned_ids"] = report["completed_ids"] + ["synthetic-pending"]
        report["latency_p50_ms"] = metric("partial", 2, 0)
        report["gates"][c.OBSERVED_GATE] = metric("partial", 2, 5020)
        self.assertEqual(c.verify_observed_latency(report, obs, 36), 2)
        self.assertFalse(c.has_complete_evidence(report, obs, decisions, 2))
        for state, count, value in (("measured", 2, 5020), ("partial", 3, 5020), ("partial", 2, 5000)):
            report["gates"][c.OBSERVED_GATE] = metric(state, count, value)
            with self.assertRaisesRegex(c.ContractError, "observed_latency"):
                c.verify_observed_latency(report, obs, 36)
        for mode in ("fixture", "real"):
            if mode == "real":
                for row in obs.values():
                    row["elapsed_ms"] = None
            report["identity"]["mode"] = mode
            report["latency_p50_ms"] = metric("unmeasured", 36)
            report["gates"][c.OBSERVED_GATE] = metric("unmeasured", 36)
            self.assertEqual(c.verify_observed_latency(report, obs, 36), 0)
        report["gates"][c.OBSERVED_GATE]["denominator"] = 0
        with self.assertRaisesRegex(c.ContractError, "observed_latency"):
            c.verify_observed_latency(report, obs, 36)

    def test_saved_synthetic_development_report_uses_authenticated_elapsed(self):
        # A complete file/IPC round trip with one invented reply, no executable adapter.
        report = deepcopy(self.golden["report"])
        case_id = self.split["development"]["category"][0]
        case = self.dataset[case_id]
        identity = dict(report["identity"], mode="real", provider="synthetic-unit-test")
        report.update(run_id="synthetic-development", identity=identity, split="development",
                      planned_ids=[case_id], completed_ids=[case_id], control_ids=[],
                      injected_controls={"ids": [], "count": 0}, latency_p50_ms=metric("measured", 1, 123))
        report["gates"][c.OBSERVED_GATE] = metric("measured", 1, 123)
        report["gates"]["partial_application_after_abstention_or_error"] = metric("unmeasured", 0)
        item = dict(self.golden["inputs"][1], id=case_id, text=case["text"], received=case["received"])
        obs = dict(self.golden["observations"][0], id=case_id, run_id=report["run_id"],
                   identity=identity, elapsed_ms=123, temperature_state="unknown")
        decision = deepcopy(self.golden["decisions"][1])
        decision.update(id=case_id, run_id=report["run_id"])
        decision["fields"]["priority"]["applied"] = case["received"]["priority"]
        for name in report["usage"]:
            counted = name in ("attempts", "requests", "questions")
            report["usage"][name] = dict(state="measured" if counted else "unmeasured", value=1 if counted else None,
                                         samples=int(counted), expected_samples=1)
        with TemporaryDirectory(dir=c.ROOT, prefix="synthetic-contract-") as folder:
            directory = Path(folder)
            for stream, row in (("inputs", item), ("observations", obs), ("decisions", decision)):
                path = directory / f"{stream}.jsonl"
                path.write_text(json.dumps(row) + "\n", encoding="utf-8")
                report["artifacts"][stream] = dict(path=path.relative_to(c.ROOT).as_posix(), sha256=c.digest(path))
            manifest = directory / "report.json"
            manifest.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(c.verify_report(manifest).name, c.OBSERVED)
            report["gates"][c.OBSERVED_GATE]["value"] = 122
            manifest.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(c.ContractError, "observed_latency"):
                c.verify_report(manifest)


if __name__ == "__main__":
    unittest.main()
