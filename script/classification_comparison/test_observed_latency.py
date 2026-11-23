"""Cenários sintéticos de latência. Nenhuma resposta vem de um fornecedor."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from common import HERE, c01, decide, encode, preflight, project
from run import write_report


ABSTAIN = dict(status="abstained", raw=c01.ABSTENTION, reason="explicit")
TIMEOUT = dict(status="error", raw=None, reason="timeout")


class ObservedLatencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observed = preflight(c01.OBSERVED)
        cls.warm = preflight()

    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)

    def synthetic_report(self, name, partition, scenarios, *, fixture=False, profile=c01.OBSERVED):
        # Persist only in a disposable test directory, including when exercising
        # the contract's real-mode requirements with invented responses.
        validation, protocol, split, catalog, cases, golden = self.observed if profile == c01.OBSERVED else self.warm
        planned = [i for group in split[partition].values() for i in group] if partition != "control" else []
        ids = [i for i in planned if i in scenarios]
        report = dict(golden["report"], split=partition, completed_ids=ids, planned_ids=planned,
                      identity=dict(golden["report"]["identity"], mode="fixture" if fixture else "real"))
        template = next(o for o in golden["observations"] if o["id"] == "ctl-simples")
        inputs = [project(cases[i], catalog) for i in ids] + golden["inputs"]
        observations = []
        for i in ids:
            elapsed, temperature, outcome = scenarios[i]
            choices = {f: outcome if outcome is not None else ABSTAIN if raw == c01.ABSTENTION else
                       dict(status="predicted", raw=raw, reason=None) for f, raw in cases[i]["expected"].items()}
            observations.append(dict(template, id=i, elapsed_ms=elapsed, temperature_state=temperature,
                                     choices=choices, questions=len(choices), identity=report["identity"]))
        for control in golden["observations"]:
            if control["origin"] == "candidate":
                control = dict(control, identity=report["identity"])
                if control["id"] == "ctl-timeout":
                    control.update(elapsed_ms=5200, temperature_state="warm")
            observations.append(control)
        observed = {o["id"]: o for o in observations}
        decisions = [decide(item, observed.get(item["id"]), catalog, report["run_id"]) for item in inputs]
        output = self.path / name
        output.mkdir()
        for kind, rows in (("inputs", inputs), ("observations", observations), ("decisions", decisions)):
            (output / f"{kind}.jsonl").write_text("".join(encode(row) + "\n" for row in rows), encoding="utf-8")
        policy = c01.read(c01.source_path(protocol["control_policy"]))
        write_report(output, report, inputs, observations, decisions, validation, protocol, split, catalog, cases,
                     policy, prefix=False)
        self.assertEqual(c01.verify_report(output / "report.json", profile).name, profile)
        return c01.read(output / "report.json")

    def assert_latency(self, report, state, denominator, p50, p95, *, gate=c01.OBSERVED_GATE):
        for metric, value in ((report["latency_p50_ms"], p50), (report["gates"][gate], p95)):
            self.assertEqual(metric, dict(state=state, numerator=None, denominator=denominator, value=value))

    def test_development_latency_includes_all_outcomes_and_excludes_controls(self):
        split = self.observed[2]["development"]
        ids = split["category+priority"][:1] + split["category"][:5]
        scenarios = dict(zip(ids, [
            (900, "unknown", None),
            (1100, "warm", None),
            (1400, "cold", ABSTAIN),
            (2400, "unknown", dict(status="invalid", raw="fora-do-catalogo", reason="invalid_output")),
            (3200, "warm", dict(status="error", raw=None, reason="transport")),
            (5130, "cold", TIMEOUT),
        ]))
        observed = self.synthetic_report("observed", "development", scenarios)
        self.assert_latency(observed, "measured", 6, 1400, 5130)
        self.assertEqual(observed["eligibility"], "inconclusive")
        observations = c01.read_records(self.path / "observed" / "observations.jsonl")
        two_fields = next(o for o in observations if o["id"] == ids[0])
        self.assertEqual(two_fields["questions"], 2)
        self.assertEqual(next(o for o in observations if o["id"] == "ctl-timeout")["elapsed_ms"], 5200)
        warm = self.synthetic_report("warm", "development", scenarios, profile=c01.LEGACY)
        self.assert_latency(warm, "partial", 2, 1100, 3200, gate=c01.WARM_GATE)
        fixture = self.synthetic_report("fixture", "development", scenarios, fixture=True)
        self.assert_latency(fixture, "unmeasured", 6, None, None)
        control = self.synthetic_report("controls", "control", {})
        self.assert_latency(control, "unmeasured", 0, None, None)

    def final_scenarios(self, p95):
        _, _, split, _, cases, _ = self.observed
        ids = [i for group in split["final_test"].values() for i in group]
        timeout = next(i for i in ids if cases[i]["missing"] == ["category"] and
                       c01.ABSTENTION not in cases[i]["expected"].values())
        scenarios = {i: (1500, "unknown", None) for i in ids}
        p95_id = next(i for i in ids if i != timeout)
        scenarios[p95_id] = p95, "cold", None
        scenarios[timeout] = 5000, "cold", TIMEOUT
        return scenarios, timeout

    def test_final_gate_is_inclusive_at_35th_rank(self):
        for p95, eligibility in ((3000, "pass"), (3001, "fail")):
            with self.subTest(p95=p95):
                scenarios, _ = self.final_scenarios(p95)
                report = self.synthetic_report(str(p95), "final_test", scenarios)
                self.assert_latency(report, "measured", 36, 1500, p95)
                self.assertEqual(report["eligibility"], eligibility)
                self.assertEqual(report["gates"]["automatic_coverage_on_fully_classifiable_cases_min"]["denominator"], 29)
                self.assertEqual(report["gates"]["raw_urgent_recognition_min"]["denominator"], 6)

    def test_final_missing_time_and_incomplete_reports(self):
        scenarios, timeout = self.final_scenarios(3000)
        for name, entries in (("no-elapsed", dict(scenarios, **{timeout: (None, "cold", TIMEOUT)})),
                              ("not-completed", {i: sample for i, sample in scenarios.items() if i != timeout})):
            with self.subTest(name=name):
                report = self.synthetic_report(name, "final_test", entries)
                self.assert_latency(report, "partial", 35, 1500, 1500)
                self.assertEqual(report["eligibility"], "inconclusive")
                self.assertEqual(len(report["planned_ids"]), 36)

    def test_final_zero_samples_and_complete_operational_failure(self):
        scenarios, _ = self.final_scenarios(3000)
        for name, entries, fixture in (("no-completed", {}, False),
                                       ("all-elapsed-missing", {i: (None, "unknown", None) for i in scenarios}, False),
                                       ("fixture", scenarios, True)):
            with self.subTest(name=name):
                report = self.synthetic_report(name, "final_test", entries, fixture=fixture)
                self.assert_latency(report, "unmeasured", 36, None, None)
                self.assertEqual(report["eligibility"], "inconclusive")
        all_timeout = {i: (800, "unknown", TIMEOUT) for i in scenarios}
        report = self.synthetic_report("all-timeout", "final_test", all_timeout)
        self.assert_latency(report, "measured", 36, 800, 800)
        self.assertEqual(report["eligibility"], "inconclusive")

    def test_cli_profile_versions_and_dry_run(self):
        command = [sys.executable, "-B", str(HERE / "run.py"), "--profile", c01.OBSERVED,
                   "--split", "final_test", "--limit", "2"]
        metadata = dict(profile=c01.OBSERVED, protocol_version="1.1.0", contract_version="1.2.0",
                        ipc_contract_version="1.1.0")
        for name, options in (("dry", ["--dry-run"]), ("fixture", [])):
            with self.subTest(name=name):
                output = self.path / name
                subprocess.run([*command, "--output", str(output), *options], cwd=c01.ROOT, check=True,
                               capture_output=True, text=True, timeout=20)
                for artifact in ("plan.json", "invocation.json"):
                    content = c01.read(output / artifact)
                    self.assertEqual({k: content[k] for k in metadata}, metadata)
                plan = c01.read(output / "plan.json")
                self.assertEqual(len(plan["planned_ids"]), 36)
                self.assertEqual(len(plan["selected_ids"]), 2)
                self.assertEqual(plan["sources"]["protocol"], c01.get_profile(c01.OBSERVED).protocol_source())
                self.assertIn(f"--profile {c01.OBSERVED}", c01.read(output / "invocation.json")["command"])
                if options:
                    self.assertFalse((output / "journal.jsonl").exists())
                    self.assertFalse((output / "report.json").exists())
                else:
                    planned = c01.read_records(output / "journal.jsonl")[0]
                    self.assertEqual({k: planned[k] for k in metadata}, metadata)
                    self.assertEqual(planned["event"], "planned")
                    self.assertEqual(c01.verify_report(output / "report.json").name, c01.OBSERVED)
                    report = c01.read(output / "report.json")
                    self.assert_latency(report, "unmeasured", 36, None, None)
                    self.assertEqual(report["eligibility"], "inconclusive")
                    self.assertIn(c01.OBSERVED, (output / "report.md").read_text(encoding="utf-8"))
                for kind in ("inputs",) if options else c01.KINDS:
                    self.assertEqual({r["contract_version"] for r in c01.read_records(output / f"{kind}.jsonl")}, {"1.1.0"})

        config = dict(c01.read(HERE / "fixture.json"), contract_version="1.2.0")
        config_path = self.path / "bad-config.json"
        config_path.write_text(encode(config), encoding="utf-8")
        output = self.path / "rejected"
        refuse = subprocess.run([*command, "--output", str(output), "--config", str(config_path)], cwd=c01.ROOT,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(refuse.returncode, 2)
        self.assertIn("configuração incompatível", refuse.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
