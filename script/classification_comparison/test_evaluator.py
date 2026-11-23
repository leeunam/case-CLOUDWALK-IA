import copy
from pathlib import Path
import tempfile
import unittest

from common import HERE, c01, decide, decode, encode, preflight, project
from metrics import eligibility, percentile, summarize, usage
from run import run
from argparse import Namespace


def predicted(raw):
    return dict(status="predicted", raw=raw, reason=None)


ABSTAIN = dict(status="abstained", raw=c01.ABSTENTION, reason="explicit")
ERROR = dict(status="error", raw=None, reason="timeout")


class EvaluatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validation, cls.protocol, cls.split, cls.catalog, cls.cases, cls.example = preflight()

    def score(self, scenarios):
        items, observations, decisions, ids = [], [], [], []
        for case_id, choices in scenarios.items():
            item = project(self.cases[case_id], self.catalog)
            obs = dict(self.example["observations"][0], id=case_id, choices=choices, questions=len(choices))
            d = decide(item, obs, self.catalog, obs["run_id"])
            c01.structure(self.validation, "observation", obs)
            c01.verify_case(item, obs, d, self.example["report"], self.catalog)
            items.append(item)
            observations.append(obs)
            decisions.append(d)
            ids.append(case_id)
        return summarize(self.cases, items, observations, decisions, self.catalog, ids)

    def test_field_mask_stratum_and_urgent(self):
        r = self.score({"jev-003": dict(category=predicted("pix"), priority=predicted("basic")),
                        "jev-027": dict(category=ABSTAIN, priority=predicted("urgent")),
                        "jev-005": dict(priority=predicted("basic"))})
        self.assertEqual(r["by_field"]["category"]["raw_accuracy"]["numerator"], 2)
        self.assertEqual(r["by_field"]["category"]["applied_accuracy"]["denominator"], 1)
        self.assertEqual(r["by_field"]["priority"]["applied_accuracy"]["value"], .5)
        self.assertEqual(r["by_mask"]["category+priority"]["raw_accuracy"]["denominator"], 4)
        self.assertEqual(r["by_stratum"]["ambiguo"]["correct_abstention"]["value"], .5)
        self.assertEqual(r["by_field"]["priority"]["unapplied_choices"]["numerator"], 1)
        self.assertEqual(r["gates"]["raw_urgent_recognition_min"]["value"], .5)
        self.assertEqual(r["urgent_outcomes"]["applied_lower"]["value"], .5)
        self.assertEqual(r["urgent_outcomes"]["review"]["value"], .5)
        self.assertEqual(r["gates"]["automatic_coverage_on_fully_classifiable_cases_min"]["value"], 1)
        self.assertEqual(r["by_field"]["priority"]["correct_completion_coverage"]["value"], .5)

    def test_abstention_and_operational_failure(self):
        for choice, counter in [(ABSTAIN, "undue_abstention"), (ERROR, "operational_error")]:
            r = self.score({"jev-003": dict(category=choice, priority=choice)})
            self.assertEqual(r["by_mask"]["category+priority"][counter]["numerator"], 2)
            self.assertIsNone(r["gates"]["applied_priority_accuracy"]["value"])
            self.assertEqual(r["gates"]["applied_priority_accuracy"]["denominator"], 0)
            self.assertEqual(r["urgent_outcomes"]["review"]["value"], 1)
            self.assertEqual(r["gates"]["raw_urgent_recognition_min"]["numerator"], 0)

    def test_partial_field_failure_and_partial_usage(self):
        r = self.score({"jev-003": dict(category=ERROR, priority=predicted("urgent"))})
        self.assertEqual(r["by_field"]["priority"]["raw_accuracy"]["value"], 1)
        self.assertEqual(r["by_field"]["priority"]["unapplied_choices"]["numerator"], 1)
        self.assertEqual(r["gates"]["partial_application_after_abstention_or_error"]["value"], 0)
        self.assertEqual(r["urgent_outcomes"]["operational_error"]["numerator"], 0)
        o = copy.deepcopy(next(o for o in self.example["observations"] if o["id"] == "ctl-duplo"))
        u = usage([o])
        self.assertEqual(u["observed_api_usd"], dict(state="partial", value=.01, samples=1, expected_samples=2))
        self.assertEqual(u["input_tokens"]["value"], 10)
        self.assertIsNone(u["output_tokens"]["value"])
        o["request_usage"][0]["observed_api_usd"] = 0
        self.assertEqual(usage([o])["observed_api_usd"]["value"], 0)
        self.assertEqual(usage([])["questions"], dict(state="measured", value=0, samples=0, expected_samples=0))

    def test_unicode_strict_json_masks_and_invalid_types(self):
        text = "relato\u2028parte\u2029fim\u0085!"
        self.assertEqual(decode(encode(dict(text=text)) + "\r\n")["text"], text)
        for line in ('{"x":1,"x":2}', "NaN", "1e500", ""):
            with self.assertRaises(ValueError):
                decode(line)
        item = dict(self.example["inputs"][0], received=dict(category={}, priority=" \t "), missing=["priority"])
        d = decide(item, None, self.catalog, "controle")
        self.assertEqual((d["attempts"], d["reason"]), (0, "invalid_input"))
        self.assertEqual(d["fields"]["priority"]["status"], "not_requested")
        with self.assertRaises(c01.ContractError):
            c01.normalize_input(dict(item, missing=[]), self.catalog)
        with self.assertRaises(c01.ContractError):
            c01.structure(self.validation, "input", dict(item, expected={"priority": "urgent"}))

    def test_unavailable_latency_and_nearest_rank(self):
        self.assertIsNone(percentile([], 36, .95)["value"])
        m = percentile([2, 12, 100], 36, .95)
        self.assertEqual((m["state"], m["denominator"], m["value"]), ("partial", 3, 100))
        self.assertEqual(percentile(range(1, 37), 36, .95)["value"], 35)

    def test_dry_run_never_starts_process_and_rejects_hash_before_output(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            path = Path(d)
            cfg = c01.read(HERE / "fixture.json")
            cfg["command"] = ["missing-c02-executable"]
            config = path / "config.json"
            config.write_text(encode(cfg))
            args = Namespace(config=config, split="development", limit=2, mode="fixture", output=path/"dry",
                             attempts=1, concurrency=1, dry_run=True)
            run(args)
            self.assertFalse((args.output / "observations.jsonl").exists())
            with (args.output / "inputs.jsonl").open(encoding="utf-8", newline="\n") as stream:
                rows = list(map(decode, stream))
            self.assertEqual(len(rows), 14)
            self.assertTrue(all(set(row) == {"id","text","brand","catalog","missing","received","contract_version"}
                                for row in rows))
            args.output = path / "invalid"
            args.dry_run = False
            cfg["policy"]["sha256"] = "0"*64
            config.write_text(encode(cfg))
            with self.assertRaisesRegex(c01.ContractError, "artifact_hash"):
                run(args)
            self.assertFalse(args.output.exists())

    def test_real_gate_arithmetic_with_constructed_metrics_only(self):
        # Isolated arithmetic, with an invented report in memory.
        r = copy.deepcopy(self.example["report"])
        r.update(split="final_test", completed_ids=["synthetic"], planned_ids=["synthetic"])
        for key in r["gates"]:
            threshold = ("applied_accuracy_per_field_min" if key.endswith("_accuracy") else key)
            r["gates"][key] = dict(state="measured", value=self.protocol["gates"][threshold])
        for m in [r["latency_p50_ms"], *r["urgent_outcomes"].values()]:
            m["state"] = "measured"
        obs = [dict(id="synthetic", choices={"category": predicted("pix")})]
        ds = self.example["decisions"]
        self.assertEqual(eligibility(r, self.protocol, obs, ds), "inconclusive")
        r["identity"]["mode"] = "real"
        # Supply the full frozen population, as the runner would.
        r["planned_ids"] = r["completed_ids"] = [i for ids in self.split["final_test"].values() for i in ids]
        obs = [dict(id=i, choices={"category": predicted("pix")}) for i in r["completed_ids"]]
        self.assertEqual(eligibility(r, self.protocol, obs, ds), "pass")
        r["gates"]["automatic_non_urgent_applied_when_expected_urgent"]["value"] = 1
        self.assertEqual(eligibility(r, self.protocol, obs, ds), "fail")
        r["gates"]["applied_priority_accuracy"]["state"] = "unmeasured"
        self.assertEqual(eligibility(r, self.protocol, obs, ds), "inconclusive")

    def test_ruby_adapter_and_mismatched_response_id(self):
        # The Ruby process uses only the envelope and the public configuration.
        ruby = """
require 'json'
identity = JSON.parse(ENV.fetch('CLASSIFICATION_IDENTITY'))
ready = ENV.fetch('CLASSIFICATION_READY_FILE')
File.write(ready + '.tmp', JSON.generate(runtime: RUBY_VERSION, hardware: RUBY_PLATFORM))
File.rename(ready + '.tmp', ready)
STDOUT.sync = true
STDIN.each_line do |line|
  item = JSON.parse(line)
  missing = item.fetch('missing')
  choices = missing.to_h { |f| [f, {status: 'error', raw: nil, reason: 'adapter_error'}] }
  puts JSON.generate(contract_version: '1.0.0', id: ARGV.empty? ? item.fetch('id') : 'wrong-id',
    attempt: 1, run_id: ENV.fetch('CLASSIFICATION_RUN_ID'), identity: identity,
    returned_model: nil, weights_revision: nil, choices: choices, temperature_state: 'unknown',
    elapsed_ms: nil, load_ms: nil, inference_ms: nil, requests: 0, questions: 0, request_usage: [])
end
"""
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            path = Path(d)
            config = c01.read(HERE/"fixture.json")
            config["command"] = ["ruby", "-e", ruby]
            args = Namespace(config=path/"config.json", split="development", limit=2, mode="fixture",
                             output=path/"valid", attempts=1, concurrency=1, dry_run=False)
            args.config.write_text(encode(config))
            run(args)
            r = c01.read(args.output/"report.json")
            self.assertEqual(r["eligibility"], "inconclusive")
            self.assertEqual(r["usage"]["requests"]["value"], 0)
            self.assertEqual(r["usage"]["attempts"]["value"], 10)
            self.assertEqual(r["by_field"]["category"]["operational_error"]["value"], 1)
            self.assertIsNone(r["usage"]["observed_api_usd"]["value"])
            args.output = path/"invalid"
            config["command"].append("wrong")
            args.config.write_text(encode(config))
            with self.assertRaisesRegex(ValueError, "ID"):
                run(args)
            self.assertFalse((args.output/"report.json").exists())

    def test_fixture_full_and_partial_plans(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            for index, (split, limit) in enumerate([("control", None), ("final_test", 3), ("final_test", None)]):
                args = Namespace(config=HERE/"fixture.json", split=split, limit=limit, mode="fixture",
                                 output=Path(d)/str(index), attempts=1, concurrency=1, dry_run=False)
                run(args)
                r = c01.read(args.output/"report.json")
                self.assertEqual(r["eligibility"], "inconclusive")
                self.assertIsNone(r["usage"]["observed_api_usd"]["value"])
                self.assertIsNone(r["latency_p50_ms"]["value"])
                self.assertEqual(r["gates"]["complete_or_invalid_controls_model_calls"]["value"], 0)
                if split == "final_test":
                    self.assertEqual(len(r["planned_ids"]), 36)
                    if limit is None:
                        self.assertEqual(r["gates"]["automatic_coverage_on_fully_classifiable_cases_min"]["denominator"], 29)
                        self.assertEqual(r["urgent_outcomes"]["review"]["denominator"], 6)
                        self.assertEqual(r["by_field"]["category"]["raw_accuracy"]["denominator"], 24)
                        self.assertEqual(r["by_field"]["priority"]["raw_accuracy"]["denominator"], 24)


if __name__ == "__main__":
    unittest.main()
