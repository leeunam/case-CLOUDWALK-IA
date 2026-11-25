"""Verificação offline pelo CLI e pelo mesmo transporte sintético de um lote por etapa."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import json
from io import BytesIO
import os
import time
from types import SimpleNamespace
from unittest.mock import Mock
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from luna_r5.round_spec import LUNA_R5
from luna import test_round as historic
from luna_r5.audit import FILENAME, completed_timings
from r2 import execute, gate, seal
from r2.plan import Plan, gate_reference
from budget import Account, BudgetError
from common import c01, decode, encode
from run import exchange


def faulty_fixture(kind, plan):
    gateway = LUNA_R5.fixture_for(plan)

    def intercepted(body, deadline, dispatched):
        if kind == "before_post":
            raise ConnectionError("fixture indisponível antes do POST")
        if kind == "timeout":
            dispatched()
            raise TimeoutError
        status, raw = gateway(body, deadline, dispatched)
        result = decode(raw)
        if kind == "invalid":
            result["choices"][0]["message"]["content"] = "{"
        elif kind == "model":
            result["model"] = "modelo-sintetico-incompativel"
        elif kind == "429":
            status = 429
        elif kind == "unknown":
            del result["usage"]["cost"]
        elif kind == "wrong":
            fields = decode(result["choices"][0]["message"]["content"])
            for value in fields.values():
                value.update(code=c01.ABSTENTION, criterion="none", quote="")
            result["choices"][0]["message"]["content"] = encode(fields)
        return status, encode(result).encode()

    return intercepted


class R5Test(unittest.TestCase):
    round = LUNA_R5
    fixture = LUNA_R5.entrypoint.with_name("config-fixture.json")
    setUp = historic.LunaTest.setUp
    account = historic.LunaTest.account
    args = historic.LunaTest.args
    cli = historic.LunaTest.cli
    test_financial_sources_must_cover_cache_long_context_and_usage = historic.LunaTest.test_financial_sources_must_cover_cache_long_context_and_usage
    test_profile_binding_and_generic_cli = historic.LunaTest.test_profile_binding_and_generic_cli

    def scenario(self, kind):
        return [sys.executable, "-B", str(Path(__file__).resolve()), kind, "_adapter"]

    def test_cli_development_final_and_original_receipts(self):
        path = self.finance / "fixture.sqlite"
        created = decode(self.cli("init-account", "--mode", "fixture", "--account", path, "--cap-usd", "10",
                                  "--previous-spend-usd", "0").stdout)
        account = Account(path, created["account_id"], "fixture")
        options = ["--mode", "fixture", "--config", self.fixture, "--account", path,
                   "--account-id", account.id, "--cap-usd", "10"]
        proof = []
        for stage, selected, controls, calls in (("development", 6, 0, 6), ("final", 36, 13, 44)):
            args = ["--stage", stage, *options, *proof]
            dry = self.output / (stage + "-dry")
            output = self.output / stage
            self.cli("run", *args, "--dry-run", "--output", dry)
            manifest = dry / "manifest-template.json"
            template = c01.read(manifest)
            self.assertFalse(template["enabled"])
            binding = template["binding"]
            self.assertEqual(binding["profile"], c01.LUNA_R5)
            self.assertEqual(binding["evidence_schema"]["version"], "1.0.0")
            self.assertEqual(binding["max_requests"], calls)
            self.assertEqual(binding["scope"], "c05-feita-luna-r5")
            self.assertTrue(template["manifest_id"].startswith("luna-r5-"))
            manifest.write_text(encode(dict(template, enabled=True)))
            self.cli("run", *args, "--manifest", manifest, "--confirm-execution", "--output", output)
            report_path = output / "report.json"
            c01.verify_report(report_path, c01.LUNA_R5)
            report = c01.read(report_path)
            self.assertEqual([len(report["completed_ids"]), len(report["control_ids"]),
                              report["luna_evidence"]["count"], report["usage"]["requests"]["value"]],
                             [selected, controls, calls, calls])
            self.assertEqual(report["eligibility"], "inconclusive")
            self.assertEqual(report["gates"][c01.OBSERVED_GATE],
                             dict(state="unmeasured", numerator=None, denominator=selected, value=None))
            if stage == "development":
                dev_file = output / gate.FILENAME
                result = c01.read(dev_file)
                self.assertEqual([result[k] for k in ("status", "correct_targets", "preserved_fields",
                                 "correct_completions", "integral_reviews", "raw_urgent", "errors")],
                                 ["fixture_ready", 8, 4, 3, 3, 1, 0])
                proof = ["--development-gate", dev_file]
                self.check_tamper(output, report)
            else:
                self.cli("verify-final", *args, "--output", output)
                receipt_path = output / gate.FINAL_RECEIPT
                receipt = c01.read(receipt_path)
                self.assertEqual((receipt["status"], receipt["luna_evidence"]), ("inconclusive", report["luna_evidence"]))
                observations = c01.read_records(c01.source_path(report["artifacts"]["observations"]))
                self.assertTrue(all(ch["reason"] == "explicit" for obs in observations if obs["origin"] == "candidate"
                                    for ch in obs["choices"].values()))
                receipt_path.write_text(encode(receipt, indent=2) + "\n\n")
                final = Plan("final", "fixture", "check", self.fixture, round_spec=LUNA_R5)
                with self.assertRaisesRegex(BudgetError, "selo"):
                    gate.verify_final(output, final, account, historic.CAP, gate_reference(dev_file))
        snapshot = account.status()
        self.assertEqual([row["state"] for row in snapshot["reservations"]], ["settled"] * 50)
        self.assertEqual(Decimal(snapshot["accounted_usd"]), Decimal("0.02735"))

    def check_tamper(self, output, report):
        path = output / FILENAME
        original = path.read_bytes()
        report_path = output / "report.json"
        original_report = report_path.read_bytes()
        rows = original.splitlines(keepends=True)

        def modified(*keys, value):
            entry = json.loads(rows[0])
            target = entry
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = value
            return (encode(entry) + "\n").encode() + b"".join(rows[1:])

        corruptions = {
            "missing": b"".join(rows[1:]), "extra": original + rows[0], "duplicate": rows[1] + b"".join(rows[1:]),
            "order": rows[1] + rows[0] + b"".join(rows[2:]), "truncated": original[:-1],
            "quote": modified("audit", "fields", "category", "quote", value="citação inexistente"),
            "choice": modified("observation", "choices", "category", "raw", value="pix"),
            "input": modified("audit", "input_sha256", value="a"*64),
            "model": modified("observation", "returned_model", value="modelo-diferente"),
            "provider": modified("observation", "identity", "provider", value="feita"),
        }
        try:
            for name, content in corruptions.items():
                with self.subTest(name=name):
                    path.write_bytes(content)
                    forged = deepcopy(report)
                    forged["luna_evidence"]["sha256"] = c01.digest(path)
                    report_path.write_text(encode(forged))
                    with self.assertRaisesRegex(c01.ContractError, "luna_evidence"):
                        c01.verify_report(report_path)
            path.write_bytes(original)
            for field, value in (("count", 0), ("sha256", "0"*64), ("schema_version", "1.1.0")):
                forged = deepcopy(report)
                forged["luna_evidence"][field] = value
                report_path.write_text(encode(forged))
                with self.assertRaises(ValueError):
                    c01.verify_report(report_path)
        finally:
            path.write_bytes(original)
            report_path.write_bytes(original_report)

    def test_external_time_requires_exact_completed_event(self):
        report = dict(run_id="luna-r5-tempo-sintetico", identity={"mode": "real"})
        candidates = [{"id": "sintetico"}]
        path = self.output / FILENAME
        journal = self.output / "journal.jsonl"
        event = dict(event="completed", run_id=report["run_id"], id="sintetico", elapsed_ms=24.75)
        journal.write_text(encode(event) + "\n")
        self.assertEqual(completed_timings(path, report, candidates), {"sintetico": 24.75})
        for records in ([], [event, event], [dict(event, run_id="outra")], [dict(event, elapsed_ms=None)]):
            with self.subTest(events=records):
                journal.write_text("".join(encode(record) + "\n" for record in records))
                with self.assertRaises(ValueError):
                    completed_timings(path, report, candidates)

    def test_wire_rejects_crossed_profiles(self):
        golden = c01.read(self.round.profile.golden_path)
        inputs = {row["id"]: row for row in c01.read_records(c01.source_path(golden["artifacts"]["inputs"]))}
        envelope = c01.read_records(c01.source_path(golden["luna_evidence"]))[0]
        obs = envelope["observation"]
        item = inputs[obs["id"]]
        read_fd, write_fd = os.pipe()
        with os.fdopen(read_fd, "rb") as reader, os.fdopen(write_fd, "wb"):
            process = SimpleNamespace(stdin=BytesIO(), stdout=reader)
            responses = Mock(pending=False)
            responses.record.return_value = envelope
            with self.assertRaisesRegex(ValueError, "ID de resposta"):
                exchange(process, item, responses, Mock(), time.monotonic() + 5)
            responses.record.return_value = obs
            with self.assertRaises(ValueError):
                exchange(process, item, responses, Mock(), time.monotonic() + 5,
                         evidence_policy=golden["sources"]["policy"]["sha256"])

    def test_failure_cost_prefix_and_replay(self):
        states = {"invalid": "settled", "model": "settled", "429": "settled",
                  "unknown": "staged", "timeout": "dispatched", "before_post": "dispatched"}
        for kind, expected_state in states.items():
            with self.subTest(kind=kind):
                account = self.account(kind)
                args = self.args(kind, account)
                with self.assertRaises(BudgetError):
                    execute.run_evaluation(args, fixture_command=self.scenario(kind), round_spec=LUNA_R5)
                state = account.status()
                row, = state["reservations"]
                self.assertEqual(row["state"], expected_state)
                self.assertEqual(bool(row["financial_expired"]), kind == "timeout")
                self.assertEqual(state["runs"][0]["state"], "interrupted")
                self.assertFalse((args.output / gate.FILENAME).exists())
                self.assertFalse((args.output / gate.FINAL_RECEIPT).exists())
                prefix = args.output / "prefix-report.json"
                c01.verify_report(prefix)
                self.assertEqual(c01.read(prefix)["luna_evidence"]["count"], 1)
                path = args.output / FILENAME
                envelope, = c01.read_records(path)
                self.assertEqual(envelope["observation"]["requests"], 0 if kind == "before_post" else 1)
                path.write_bytes(path.read_bytes().rstrip(b"\n"))
                with self.assertRaisesRegex(c01.ContractError, "luna_evidence"):
                    c01.verify_report(prefix)

    def test_failed_gate_then_tamper_rejected(self):
        historic.LunaTest.test_failed_gate_then_tamper_rejected(self)


if __name__ == "__main__":
    kind = sys.argv.pop(1)
    if kind not in ("wrong", "invalid", "model", "429", "unknown", "timeout", "before_post"):
        raise ValueError("cenário de fixture desconhecido")
    execute.main(replace(LUNA_R5, fixture_for=lambda plan: faulty_fixture(kind, plan)))
