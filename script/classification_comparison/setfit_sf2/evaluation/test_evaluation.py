import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from ..contracts.core import FIELDS, REVIEW, VERSION, ContractError, read_lines, sha256
from ..contracts.test_contracts import fixture, quota_rows
from .audit import derive, originals
from .workflow import digest
from ..contracts.artifacts import validate_report
from ..contracts.test_artifacts import write_rows
from .metrics import metrics, percentiles, quality_gates, ratio
from .runner import controls, save, supervise
from .selection import rank_key, scored_rows, select


POLICY = dict(contract_version=VERSION, **{f: dict(tau=.5, delta=0.) for f in FIELDS})
WORKER = Path(__file__).with_name("fixture_worker.py")


def records(part):
    result = []
    for i, case in enumerate(quota_rows(part)):
        key = f"{part}-{i}"
        result.append(dict(**case, id=key, family_id=key, text=key, author="A", partition=part,
                           received={f: case["gold"][f] for f in FIELDS if f not in case["missing_fields"]}))
    return result


def templates(rows, *, weak=False):
    kinds = {k: fixture(k)["decision"] for k in ("category-only", "priority-only", "both", "complete-channel", "invalid-channel")}
    choices = {}
    for row in rows:
        mask = row["missing_fields"]
        d = deepcopy(kinds["both" if len(mask) == 2 else mask[0]+"-only"])
        d.update(id=row["id"], received=row["received"])
        accepted = {}
        for f in mask:
            field = d["fields"][f]
            raw = row["gold"][f]
            ambiguous = weak and row["id"] == "validation-24" and f == "category"
            if ambiguous:
                raw = "pix"
            classes = field["vector"]["classes"]
            field["vector"]["scores"] = [(.55 if c == raw else .15) if ambiguous else int(c == raw) for c in classes]
            field.update(raw=raw, margin=.4 if ambiguous else 1, cut=POLICY[f])
            if raw == REVIEW:
                field.update(decision="review", reason="raw_review")
            else:
                accepted[f] = raw
        complete = len(accepted) == len(mask)
        d.update(outcome="complete" if complete else "review", applied=accepted if complete else {})
        choices[row["id"]] = d
    for row, kind in zip(controls(), ("complete-channel", "invalid-channel", "category-only", "priority-only", "both"), strict=True):
        d = deepcopy(kinds[kind])
        d.update(id=row["id"], received=row["received"])
        if kind == "invalid-channel":
            d["fields"]["priority"], d["fields"]["category"] = d["fields"]["category"], d["fields"]["priority"]
        choices[row["id"]] = d
    return choices


class MathTest(unittest.TestCase):
    def test_applied_and_raw_urgent_have_distinct_numerators(self):
        for part, raw, applied, clear, review in (("validation", 13, 12, 72, 18), ("final", 17, 16, 96, 24)):
            rows = records(part)
            originals = templates(rows)
            results = [originals[r["id"]] for r in rows]
            totals = metrics(rows, results, 0)
            self.assertEqual(totals["raw_urgent"], ratio(raw, raw))
            self.assertEqual(totals["applied_urgent"], ratio(applied, raw))
            self.assertEqual(totals["review_by_case"], ratio(review, len(rows)))
            self.assertEqual(totals["correct_coverage"], ratio(clear, clear))
            self.assertEqual(totals["applied_accuracy"]["priority"], ratio(clear*2//3, clear*2//3))
            veto = next(d for r,d in zip(rows, results) if r["gold"] == dict(category=REVIEW, priority="urgent")
                        and len(r["missing_fields"]) == 2)
            self.assertEqual(veto["fields"]["priority"]["raw"], "urgent")
            self.assertEqual(veto["applied"], {})
            self.assertTrue(all(quality_gates(totals, part).values()))
            for d in results:
                d.update(outcome="review", applied={})
            abstention = metrics(rows, results, 0)
            self.assertEqual(abstention["applied_accuracy"]["priority"], ratio(0, 0))
            self.assertFalse(quality_gates(abstention, part)["priority_accuracy"])
            self.assertFalse(quality_gates(abstention, part)["automatic_coverage"])

    def test_percentiles_and_wilson(self):
        self.assertEqual(percentiles(list(range(120, 0, -1))), dict(n=120, p50=60, p95=114, maximum=120))
        self.assertAlmostEqual(ratio(11, 13)["wilson95"][0], .57765, places=4)
        self.assertAlmostEqual(ratio(11, 13)["wilson95"][1], .95674, places=4)

    def test_asymmetric_confusion_and_wrong_applied_urgent(self):
        rows = records("validation")
        decisions = list(templates(rows).values())[:90]
        urgent = next(i for i,r in enumerate(rows) if r["missing_fields"] == ["priority"] and r["gold"]["priority"] == "urgent")
        decisions[urgent]["fields"]["priority"]["raw"] = "basic"
        decisions[urgent]["applied"]["priority"] = "basic"
        m = metrics(rows, decisions, 0)
        self.assertEqual(m["confusion"]["priority"]["urgent"]["basic"], 1)
        self.assertEqual(m["by_class"]["priority"]["urgent"]["precision"], ratio(12,12))
        self.assertEqual(m["by_class"]["priority"]["urgent"]["recall"], ratio(12,13))
        self.assertAlmostEqual(m["by_class"]["priority"]["urgent"]["f1"], 24/25)
        self.assertEqual(m["applied_accuracy"]["priority"], ratio(47,48))
        self.assertEqual(m["automatic_coverage"], ratio(72,72))
        self.assertEqual(m["correct_coverage"], ratio(71,72))
        gates = quality_gates(m, "validation")
        self.assertTrue(gates["raw_urgent"])
        self.assertFalse(gates["nonurgent_on_urgent"])

    def test_gate_boundaries_and_order(self):
        totals = metrics(records("validation"), list(templates(records("validation")).values())[:90], 0)
        for gate, n, d, limit in (("automatic_coverage",51,72,"automatic_coverage"), ("raw_urgent",11,13,"raw_urgent")):
            totals[gate] = ratio(n,d)
            self.assertTrue(quality_gates(totals,"validation")[limit])
            totals[gate] = ratio(n-1,d)
            self.assertFalse(quality_gates(totals,"validation")[limit])
        totals.update(correct_coverage=ratio(48,72), applied_urgent=ratio(8,13))
        row = dict(policy=POLICY, metrics=totals)
        self.assertEqual(rank_key(row), (-48, -8, 2, -50, .5, 0., .5, 0.))

    def test_grid_selects_winner_without_model_calls_or_rewriting_scores(self):
        rows = records("validation")
        decisions = list(templates(rows, weak=True).values())[:90]
        bundle = dict(partition="validation", rows=scored_rows(rows, decisions), class_order=fixture("both")["class_order"])
        saved = deepcopy(bundle)
        grid = select(rows, bundle, 0)
        self.assertEqual(bundle, saved)
        self.assertEqual(len(grid["policies"]), 225)
        self.assertEqual(grid["selected"], {**POLICY, "category": {"tau": .6, "delta": 0.}})
        self.assertEqual(grid["baseline_argmax"]["wrong_expected_review"]["numerator"], 1)
        self.assertIsNone(select(rows, bundle, 1)["selected"])


class TransportTest(unittest.TestCase):
    def test_observed_external_latency_including_timeout_and_no_filled_predictions(self):
        rows = records("final")
        model = {"class_order": fixture("both")["class_order"], "model_sha256": fixture("both")["identities"]["model_sha256"]}
        ids = fixture("both")["identities"]
        costs = dict(download_ms=0, training_ms=1, classifier_api_calls=0)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for n, value in (("choices", templates(rows)), ("identity", ids), ("policy", POLICY)):
                save(root/n,value)
            ids["policy_sha256"] = sha256(root/"policy")
            cmd = [sys.executable, str(WORKER), *(str(root/n) for n in ("choices", "identity", "policy"))]
            interrupted = root/"interrupted"
            supervise(rows, cmd + ["hang"], POLICY, model, ids, interrupted, 5, timeout_ms=100)
            scores, grid, report = derive(rows,"b"*64,interrupted,POLICY,model,ids,costs)
            self.assertIsNone(grid)
            self.assertEqual(scores["rows"], [])
            self.assertEqual(report["status"], "inconclusive")
            self.assertEqual(report["unexecuted_ids"], [r["id"] for r in rows[1:]])
            self.assertEqual(report["counts"], dict(planned=120, observed=1))
            self.assertGreaterEqual(report["latency_ms"]["p95"], 100)
            self.assertIsNone(report["metrics"])
            validate_report(dict(**report, score_package_sha256=digest(scores)))

            # Fixture matemática independente: durações controladas, nunca medidas de SetFit.
            for boundary, status in ((3000, "eligible"), (3001, "failed")):
                run = root/str(boundary)
                seal = supervise(rows, cmd + ["ok"], POLICY, model, ids, run, 5)
                timings = read_lines(run/"timings.jsonl")
                for i, timing in enumerate(timings):
                    timing["elapsed_ms"] = 10 if i < 113 else boundary
                write_rows(run/"timings.jsonl", timings)
                seal["files"]["timings.jsonl"] = sha256(run/"timings.jsonl")
                from ..contracts.test_artifacts import write
                write(run/"seal.json",seal)
                scores, _, report = derive(rows,"b"*64,run,POLICY,model,ids,costs)
                self.assertEqual(report["latency_ms"], dict(n=120, p50=10, p95=boundary, maximum=boundary))
                self.assertEqual(report["status"], status)
                validate_report(dict(**report,score_package_sha256=digest(scores)))

    def test_original_decisions_timeout_and_protocol_failures(self):
        rows = records("validation")[:2]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ids, model = fixture("both")["identities"], {"class_order": fixture("both")["class_order"]}
            for n,v in (("choices", templates(rows)), ("identity", ids), ("policy", POLICY)):
                save(root/n,v)
            ids["policy_sha256"] = sha256(root/"policy")
            for mode in ("ok", "bad-ready", "partial", "invalid-score", "other-package", "die", "hang", "extra"):
                with self.subTest(mode=mode):
                    cmd = [sys.executable, str(WORKER), *(str(root/n) for n in ("choices","identity","policy")), mode]
                    seal = supervise(rows, cmd, POLICY, model, ids, root/mode, 5, timeout_ms=150 if mode=="hang" else 5000)
                    checked, decisions, elapsed, calls = originals(root/mode, rows, POLICY, model, ids)
                    self.assertEqual(checked, seal)
                    self.assertEqual(calls, 0)
                    if mode == "ok":
                        self.assertEqual(len(elapsed), 2)
                        self.assertEqual(len(decisions), 2)
                        self.assertIsNone(seal["failure"])
                        self.assertEqual(len(read_lines(root/mode/"controls.jsonl")), 5)
                    else:
                        self.assertIsNotNone(seal["failure"])
                    if mode in ("hang", "partial", "invalid-score", "other-package", "die"):
                        self.assertEqual(len(elapsed), 1)
                        self.assertEqual(decisions, [])
                    if mode == "hang":
                        self.assertGreaterEqual(elapsed[0], 150)
                    if mode == "bad-ready":
                        self.assertEqual(elapsed, [])
            with (root/"ok/predictions.jsonl").open("ab") as f:
                f.write(b" ")
            with self.assertRaises(ContractError):
                originals(root/"ok", rows, POLICY, model, ids)
