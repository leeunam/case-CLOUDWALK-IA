"""Exercita a C05 com SQLite temporário e sem transporte real."""
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
from argparse import Namespace
from decimal import Decimal
from unittest import TestCase, main, mock

sys.dont_write_bytecode = True
from budget import Account, BudgetError, cap_usd, usd
from execute import run_evaluation
from final_adapter import fixture_gateway, main as adapter_main, observed_cost
from settings import HERE, Plan, VERSIONS
from common import c01, decode, encode

FIXTURE = HERE / "config-fixture.json"
REAL_EXAMPLE = HERE / "config-real-exemplo.json"
PER_REQUEST = Decimal("1.4004736")
CREDIT_CONVERSION = {"confirmed": True, "reference": "synthetic fixture credits",
                     "usd_per_credit": "0.01"}


def reserve_worker(path, account_id, run_id, start, results):
    account = Account(path, account_id, "fixture")
    start.wait(10)
    try:
        account.reserve(run_id, "case-a", PER_REQUEST)
    except BudgetError as exc:
        results.put((run_id, str(exc)))
    else:
        results.put((run_id, "reserved"))


def claim(account, run_id, candidate_ids=("case-a",), value=PER_REQUEST):
    manifest, pin, binding = (f"{run_id}-{name}" for name in ("manifest", "pin", "binding"))
    account.claim(run_id, manifest, pin, binding,
                  {"candidate_ids": list(candidate_ids), "reservation_usd": str(value)})
    account.activate(run_id, pin)


def run_scenario(scenario):
    calls = 0

    def transport(body, deadline, dispatched):
        nonlocal calls
        calls += 1
        request = decode(body)
        assert request["max_tokens"] == 128 and request["reasoning"] == {"enabled": False}
        if scenario == "timeout":
            dispatched()
            raise TimeoutError
        if scenario == "crash" and calls == 3:
            dispatched()
            os._exit(9)
        status, response = fixture_gateway(body, deadline, dispatched)
        if scenario == "no-usage":
            obj = decode(response)
            del obj["usage"]
            response = encode(obj).encode("utf-8")
        if scenario == "over-cap" or (scenario == "over-cap-last" and calls == 44):
            obj = decode(response)
            obj["usage"]["cost"] = "1.500000000000000000000000000001"
            response = encode(obj).encode("utf-8")
        if scenario == "credits":
            obj = decode(response)
            obj["usage"]["credits"] = "0.075"
            response = encode(obj).encode("utf-8")
        if scenario == "wrong-unit":
            obj = decode(response)
            obj["usage"]["cost_unit"] = "credits"
            response = encode(obj).encode("utf-8")
        return status, response

    adapter_main(transport)


class AccountTest(TestCase):
    def setUp(self):
        self.scratch = self.enterContext(tempfile.TemporaryDirectory())
        self.path = Path(self.scratch) / "budget.sqlite3"

    def account(self, *, previous="0", cap="10"):
        return Account.initialize(self.path, scope="fixture", cap=cap, previous_spend=previous)

    def test_exact_currency_validation_and_existing_file(self):
        for invalid in ("NaN", "-0.01", "Infinity", "invalid", 0.5, False, None):
            with self.subTest(invalid=invalid), self.assertRaises(BudgetError):
                usd(invalid)
        for invalid in ("0", "10.0000000001"):
            with self.subTest(cap=invalid), self.assertRaises(BudgetError):
                cap_usd(invalid)
        with self.assertRaises(BudgetError):
            self.account(previous="10.1")
        self.assertFalse(self.path.exists())
        account = self.account(previous="0.000519")
        with self.assertRaises(FileExistsError):
            self.account()
        self.assertEqual(account.status()["available_usd"], "9.999481")

    def test_missing_corrupt_and_wrong_identity_block(self):
        with self.assertRaises(BudgetError):
            Account(self.path, "any", "fixture").validate(Decimal(10))
        self.assertFalse(self.path.exists())
        self.path.write_text("not SQLite")
        with self.assertRaises(BudgetError):
            Account(self.path, "any", "fixture").validate(Decimal(10))
        self.path.unlink()
        account = self.account()
        for owner in (Account(self.path, "other", "fixture"), Account(self.path, account.id, "real")):
            with self.assertRaises(BudgetError):
                owner.validate(Decimal(10))

    def test_two_processes_contend_for_last_reservation(self):
        account = self.account(previous="8.5995264")
        for run in ("first", "second"):
            claim(account, run)
        ctx = multiprocessing.get_context("spawn")
        start = ctx.Event()
        results = ctx.Queue()
        children = [ctx.Process(target=reserve_worker, args=(self.path, account.id, run, start, results))
                    for run in ("first", "second")]
        try:
            for child in children:
                child.start()
            start.set()
            outcomes = dict(results.get(timeout=10) for child in children)
            self.assertCountEqual(outcomes.values(), ["reserved", "saldo global insuficiente para a reserva"])
            for child in children:
                child.join(10)
                self.assertEqual(child.exitcode, 0)
        finally:
            for child in children:
                if child.is_alive():
                    child.kill()
                    child.join()
        reopened = Account(self.path, account.id, "fixture")
        self.assertEqual(Decimal(reopened.status()["available_usd"]), 0)
        self.assertEqual(len(reopened.status()["reservations"]), 1)

    def test_duplicate_manifest_binding_activation_and_case_after_reopen(self):
        account = self.account()
        claim(account, "run")
        account.reserve("run", "case-a", PER_REQUEST)
        reopened = Account(self.path, account.id, "fixture")
        with self.assertRaisesRegex(BudgetError, "vinculação já usados"):
            reopened.claim("new", "different", "different", "run-binding", {})
        with self.assertRaisesRegex(BudgetError, "vinculação já usados"):
            reopened.claim("new", "run-manifest", "different", "different", {})
        with self.assertRaisesRegex(BudgetError, "já iniciada"):
            reopened.activate("run", "run-pin")
        with self.assertRaisesRegex(BudgetError, "já reservado"):
            reopened.reserve("run", "case-a", PER_REQUEST)
        with self.assertRaisesRegex(BudgetError, "fora da execução"):
            reopened.reserve("run", "development", PER_REQUEST)
        reopened.mark_dispatched("run", "case-a")
        with self.assertRaisesRegex(BudgetError, "já registrado"):
            reopened.mark_dispatched("run", "case-a")

    def test_reconcile_explicit_receipt_once_exactly(self):
        account = self.account(previous="2.4")
        claim(account, "run", ("case-a", "case-b"))
        for case in ("case-a", "case-b"):
            account.reserve("run", case, PER_REQUEST)
            account.mark_dispatched("run", case)
        receipt = {"unit": "USD", "cost_usd": "0.000123456789012345678901234567",
                   "run_id": "run", "case_id": "case-a", "reference": "synthetic invoice/01"}
        for altered in ({"unit": "credits"}, {"cost_usd": "-1"}, {"cost_usd": "NaN"}, {"reference": ""}):
            with self.assertRaises(BudgetError):
                account.reconcile(dict(receipt, **altered))
        self.assertEqual(account.status()["accounted_usd"], "5.2009472")
        account.reconcile(receipt)
        self.assertEqual(account.status()["accounted_usd"], "3.800597056789012345678901234567")
        self.assertEqual(account.status()["available_usd"], "6.199402943210987654321098765433")
        with self.assertRaisesRegex(BudgetError, "já conciliada"):
            account.reconcile(receipt)
        with self.assertRaisesRegex(BudgetError, "já atribuído"):
            account.reconcile(dict(receipt, case_id="case-b"))


    def test_dashboard_receipt_preserves_original_gateway_attribution(self):
        account = self.account()
        claim(account, "run", ("case-a", "case-b"))
        for case in ("case-a", "case-b"):
            account.reserve("run", case, PER_REQUEST)
            account.mark_dispatched("run", case)
        account.stage("run", "case-a", amount=Decimal("0.25"), evidence="gateway:one")
        account.reconcile({"unit": "USD", "cost_usd": "0.26", "run_id": "run",
                           "case_id": "case-a", "reference": "synthetic dashboard:one"})
        row = account.status()["reservations"][0]
        self.assertEqual((row["prior_observed"], row["prior_receipt"]), ("0.25", "gateway:one"))
        with self.assertRaisesRegex(BudgetError, "já atribuído"):
            account.stage("run", "case-b", amount=Decimal("0.25"), evidence="gateway:one")

    def test_over_reservation_reconciliation_ledgers_cost_and_freezes_after_restart(self):
        account = self.account(previous="8")
        claim(account, "run", ("case-a", "case-b"))
        account.reserve("run", "case-a", PER_REQUEST)
        account.mark_dispatched("run", "case-a")
        with self.assertRaisesRegex(BudgetError, "acima da reserva"):
            account.reconcile({"unit": "USD", "cost_usd": "2.25", "run_id": "run",
                               "case_id": "case-a", "reference": "synthetic above cap"})
        reopened = Account(self.path, account.id, "fixture")
        status = reopened.status()
        self.assertEqual(status["accounted_usd"], "10.25")
        self.assertEqual(status["available_usd"], "-0.25")
        self.assertEqual(status["reservations"][0]["state"], "violation")
        with self.assertRaisesRegex(BudgetError, "conta congelada"):
            reopened.reserve("run", "case-b", PER_REQUEST)


class ExecutorTest(TestCase):
    def setUp(self):
        self.output = Path(self.enterContext(tempfile.TemporaryDirectory(prefix=".c05-test-", dir=c01.ROOT)))
        self.scratch = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.db = self.scratch / "budget.sqlite3"

    def setup_run(self, *, previous="0.000519", config=FIXTURE):
        account = Account.initialize(self.db, scope="fixture", cap="10", previous_spend=previous)
        args = Namespace(mode="fixture", config=config, output=self.output / "plan", account=self.db,
                         account_id=account.id, cap_usd=Decimal(10), dry_run=True,
                         manifest=None, confirm_execution=False)
        run_evaluation(args)
        template = c01.read(args.output / "manifest-template.json")
        self.assertIs(template["enabled"], False)
        manifest = self.scratch / "manifest.json"
        template["enabled"] = True
        manifest.write_text(encode(template), encoding="utf-8")
        args.dry_run = False
        args.confirm_execution = True
        args.manifest = manifest
        args.output = self.output / "run"
        return account, args

    def command(self, scenario):
        return [sys.executable, "-B", str(Path(__file__).resolve()), "--scenario", scenario]

    def test_dry_run_final_versions_no_adapter_no_account_access(self):
        args = Namespace(mode="real", config=REAL_EXAMPLE, output=self.output / "plan",
                         account=self.db, account_id="nonexistent", cap_usd=Decimal("10"),
                         dry_run=True, manifest=None, confirm_execution=False)
        with mock.patch("execute.run_batch") as batch, mock.patch.object(Account, "transaction") as database:
            run_evaluation(args)
        batch.assert_not_called()
        database.assert_not_called()
        self.assertFalse(self.db.exists())
        stored = c01.read(args.output / "plan.json")
        self.assertEqual({v: stored[v] for v in VERSIONS}, {
            "profile": "observed-total-1.1", "protocol_version": "1.1.0",
            "report_version": "1.2.0", "ipc_contract_version": "1.1.0"})
        self.assertEqual(stored["identity"]["adapter_version"], "1.1.0")
        self.assertEqual(len(stored["final_ids"]), 36)
        self.assertEqual(len(stored["control_ids"]), 13)
        self.assertEqual(len(stored["candidate_ids"]), 44)
        self.assertEqual(stored["reservation_usd"], str(PER_REQUEST))
        self.assertEqual(stored["input"]["sha256"], c01.digest(args.output / "inputs.jsonl"))
        self.assertEqual(len(stored["git_revision"]), 40)
        self.assertFalse((args.output / "observations.jsonl").exists())

    def test_full_fixture_can_complete_with_per_case_reservation_and_retains_c02_decisions(self):
        account, args = self.setup_run()
        run_evaluation(args)
        report_path = args.output / "report.json"
        c01.verify_report(report_path, "observed-total-1.1")
        report = c01.read(report_path)
        self.assertEqual(report["identity"]["mode"], "fixture")
        self.assertEqual(report["eligibility"], "inconclusive")
        self.assertEqual((len(report["completed_ids"]), len(report["control_ids"])), (36, 13))
        status = account.status()
        self.assertEqual(len(status["reservations"]), 44)
        self.assertEqual({row["state"] for row in status["reservations"]}, {"settled"})
        self.assertEqual(status["accounted_usd"], "0.024587")
        inputs = {row["id"]: row for row in c01.read_records(args.output / "inputs.jsonl")}
        decisions = c01.read_records(args.output / "decisions.jsonl")
        abstentions = []
        retained = []
        for decision in decisions:
            item = inputs[decision["id"]]
            for field, evidence in decision["fields"].items():
                if evidence["status"] == "provided":
                    self.assertEqual(evidence["applied"], item["received"][field])
                    retained.append(field)
                if evidence["status"] == "abstained":
                    self.assertIsNone(evidence["applied"])
                    self.assertEqual(decision["outcome"], "review")
                    abstentions.append(field)
        self.assertTrue(retained)
        self.assertTrue(abstentions)
        args.output = self.output / "repeat"
        with mock.patch("execute.run_batch") as batch, self.assertRaisesRegex(BudgetError, "já usados"):
            run_evaluation(args)
        batch.assert_not_called()
        self.assertEqual(len(account.status()["reservations"]), 44)

    def test_authorization_rejects_before_adapter_for_pilot_disabled_and_modified_pins(self):
        account, args = self.setup_run()
        template = c01.read(args.manifest)
        for alteration in ({"candidate_ids": ["jev-003"]}, {"concurrency": 2}, {"attempts": 2},
                           {"inputs_sha256": "tampered"}, {"config_sha256": "tampered"},
                           {"sources": {}}, {"account": {"id": "tampered"}}, {"identity": {}}):
            with self.subTest(alteration=alteration), mock.patch("execute.run_batch") as batch:
                wrong = dict(template, binding=dict(template["binding"], **alteration))
                args.manifest.write_text(encode(wrong), encoding="utf-8")
                with self.assertRaisesRegex(BudgetError, "manifesto"):
                    run_evaluation(args)
                batch.assert_not_called()
        for wrong in (dict(template, enabled=False), {"authorized": True, "scope": "pilot"}):
            args.manifest.write_text(encode(wrong), encoding="utf-8")
            with self.assertRaisesRegex(BudgetError, "manifesto"):
                run_evaluation(args)
        args.confirm_execution = False
        with self.assertRaisesRegex(BudgetError, "confirm-execution"):
            run_evaluation(args)
        self.assertFalse(args.output.exists())
        self.assertEqual(account.status()["runs"], [])

    def test_real_limits_need_confirmation_before_transport(self):
        with mock.patch("execute.run_batch") as batch:
            plan = Plan("real", "c05-offline", REAL_EXAMPLE)
            with self.assertRaisesRegex(BudgetError, "confirmação"):
                plan.authorize(self.scratch / "absent", None, Decimal(10), confirmed=True)
        batch.assert_not_called()

    def prefix(self, args, *, completed):
        interruption = c01.read(args.output / "interruption.json")
        self.assertEqual(interruption["eligibility"], "inconclusive")
        self.assertEqual(len(interruption["completed_ids"]), completed)
        c01.verify_report(args.output / "prefix-report.json", "observed-total-1.1")
        self.assertFalse((args.output / "report.json").exists())
        return interruption

    def test_stops_before_post_when_next_case_cannot_be_reserved(self):
        account, args = self.setup_run(previous="8.5993")
        with self.assertRaisesRegex(BudgetError, "saldo global insuficiente"):
            run_evaluation(args)
        interrupted = self.prefix(args, completed=1)
        self.assertEqual(interrupted["delivery"], "not_sent")
        self.assertEqual(len(interrupted["dispatched_ids"]), 1)
        rows = account.status()["reservations"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["state"], "settled")

    def test_estimated_cost_keeps_reservation_and_stops_after_verified_first_case(self):
        config = self.scratch / "unknown.json"
        config.write_text(encode(dict(c01.read(FIXTURE), usage_cost_unit=None, usage_cost_reference=None)),
                          encoding="utf-8")
        account, args = self.setup_run(config=config)
        with self.assertRaisesRegex(BudgetError, "USD inconciliável"):
            run_evaluation(args)
        self.prefix(args, completed=1)
        status = account.status()
        self.assertEqual(status["accounted_usd"], "1.4009926")
        self.assertIsNone(status["reservations"][0]["observed"])
        observation, = c01.read_records(args.output / "verified_observations.jsonl")
        usage, = observation["request_usage"]
        self.assertIsNotNone(usage["estimated_api_usd"])
        self.assertIsNone(usage["observed_api_usd"])

    def test_absent_usage_or_wrong_currency_keeps_reservation(self):
        for scenario in ("no-usage", "wrong-unit"):
            with self.subTest(scenario=scenario):
                self.db = self.scratch / f"{scenario}.sqlite3"
                self.output = self.output / scenario
                self.output.mkdir()
                account, args = self.setup_run()
                with self.assertRaisesRegex(BudgetError, "USD inconciliável"):
                    run_evaluation(args, fixture_command=self.command(scenario))
                self.prefix(args, completed=1)
                self.assertEqual(account.status()["accounted_usd"], "1.4009926")

    def test_timeout_is_journaled_and_retains_reservation(self):
        account, args = self.setup_run()
        with self.assertRaisesRegex(BudgetError, "USD inconciliável"):
            run_evaluation(args, fixture_command=self.command("timeout"))
        self.prefix(args, completed=1)
        observation, = c01.read_records(args.output / "verified_observations.jsonl")
        self.assertEqual({choice["reason"] for choice in observation["choices"].values()}, {"timeout"})
        row, = account.status()["reservations"]
        self.assertEqual(row["state"], "dispatched")
        self.assertEqual(row["reserved"], str(PER_REQUEST))

    def test_crash_keeps_third_reservation_and_verified_prefix_after_restart(self):
        account, args = self.setup_run()
        with self.assertRaisesRegex(ValueError, "EOF"):
            run_evaluation(args, fixture_command=self.command("crash"))
        interrupted = self.prefix(args, completed=2)
        self.assertEqual(interrupted["delivery"], "stdin_flushed")
        reopened = Account(self.db, account.id, "fixture")
        status = reopened.status()
        self.assertEqual(status["accounted_usd"], "1.4020866")
        self.assertEqual([row["state"] for row in status["reservations"]], ["settled", "settled", "dispatched"])
        args.output = self.output / "retry"
        with self.assertRaisesRegex(BudgetError, "já usados"):
            run_evaluation(args, fixture_command=self.command("crash"))

    def test_observed_violation_retains_cost_and_freezes_before_next_dispatch(self):
        account, args = self.setup_run()
        with self.assertRaisesRegex(BudgetError, "acima da reserva"):
            run_evaluation(args, fixture_command=self.command("over-cap"))
        interrupted = self.prefix(args, completed=1)
        self.assertEqual(len(interrupted["dispatched_ids"]), 1)
        status = account.status()
        self.assertIn("acima da reserva", status["frozen_reason"])
        self.assertEqual(status["accounted_usd"], "1.500519000000000000000000000001")


    def test_last_dispatch_violation_cannot_publish_complete_evidence(self):
        account, args = self.setup_run()
        with self.assertRaisesRegex(BudgetError, "acima da reserva"):
            run_evaluation(args, fixture_command=self.command("over-cap-last"))
        interrupted = self.prefix(args, completed=48)
        self.assertEqual(len(interrupted["dispatched_ids"]), 44)
        self.assertEqual(interrupted["not_started_ids"], ["ctl-injetado-aplicacao-parcial"])
        status = account.status()
        self.assertEqual(status["runs"][0]["state"], "interrupted")
        self.assertIsNotNone(status["frozen_reason"])

    def test_invalid_tariff_limits_and_cap_are_blocked_before_adapter(self):
        account, args = self.setup_run()
        settings = c01.read(FIXTURE)
        args.config = self.scratch / "modified-settings.json"
        for alteration in ({"tariff": dict(settings["tariff"], output="NaN")},
                           {"tariff": dict(settings["tariff"], unit="credits")},
                           {"billable_output_token_ceiling": 127}, {"usage_cost_reference": None},
                           {"usage_credits": dict(CREDIT_CONVERSION, reference="")},
                           {"usage_credits": dict(CREDIT_CONVERSION, usd_per_credit="0.001")}):
            with self.subTest(alteration=alteration), mock.patch("execute.run_batch") as batch:
                args.config.write_text(encode(dict(settings, **alteration)), encoding="utf-8")
                with self.assertRaises(BudgetError):
                    run_evaluation(args)
                batch.assert_not_called()
        args.config = FIXTURE
        args.cap_usd = Decimal("10.01")
        with mock.patch("execute.run_batch") as batch, self.assertRaisesRegex(BudgetError, "teto global"):
            run_evaluation(args)
        batch.assert_not_called()
        self.assertEqual(account.status()["runs"], [])

    def test_observed_cost_retains_exact_numeric_json_and_flags_token_limit(self):
        raw = (b'{"id":"abc","usage":{"prompt_tokens":1024001,"completion_tokens":20,'
               b'"cost":0.123456789012345678901234567891}}')
        observed = observed_cost(raw, c01.read(FIXTURE), "run", "case", PER_REQUEST)
        self.assertEqual(observed.amount, Decimal("0.123456789012345678901234567891"))
        self.assertEqual(observed.receipt, "gateway:abc")
        self.assertIn("prompt_tokens=1024001", observed.violation)


    def test_confirmed_credit_conversion_can_reconcile_without_cost_unit(self):
        config = self.scratch / "credits.json"
        settings = dict(c01.read(FIXTURE), usage_credits=CREDIT_CONVERSION,
                        usage_cost_unit=None, usage_cost_reference=None)
        config.write_text(encode(settings), encoding="utf-8")
        account, args = self.setup_run(config=config)
        run_evaluation(args, fixture_command=self.command("credits"))
        self.assertEqual(account.status()["accounted_usd"], "0.033519")
        usage = account.status()["reservations"][0]["gateway_usage"]
        self.assertEqual(usage, {"credits": "0.075", "converted_credits_usd": "0.00075"})
        c01.verify_report(args.output / "report.json", "observed-total-1.1")

    def test_dual_verified_sources_keep_larger_exact_cost_and_both_evidences(self):
        settings = dict(c01.read(FIXTURE), usage_credits=CREDIT_CONVERSION)
        raw = (b'{"usage":{"prompt_tokens":1024,"completion_tokens":20,'
               b'"cost":0.123456789012345678901234567891,"credits":12.34567890123456789012345679}}')
        observed = observed_cost(raw, settings, "run", "case", PER_REQUEST)
        self.assertEqual(observed.amount, Decimal("0.1234567890123456789012345679"))
        self.assertEqual(observed.evidence, {
            "cost_usd": "0.123456789012345678901234567891",
            "credits": "12.34567890123456789012345679",
            "converted_credits_usd": "0.1234567890123456789012345679",
        })

    def test_unconfirmed_missing_or_invalid_credits_never_supply_a_cost(self):
        settings = dict(c01.read(FIXTURE), usage_credits=CREDIT_CONVERSION,
                        usage_cost_unit=None, usage_cost_reference=None)
        usage = {"prompt_tokens": 1000, "completion_tokens": 20, "cost": "0.01"}
        for extra in ({}, {"credits": False}, {"credits": "NaN"}, {"credits": "-1"},
                      {"credits": "0.5", "credits_unit": "USD"}):
            with self.subTest(extra=extra):
                raw = encode({"usage": dict(usage, **extra)}).encode("utf-8")
                observed = observed_cost(raw, settings, "run", "case", PER_REQUEST)
                self.assertIsNone(observed.amount)
        unconfirmed = dict(settings, usage_credits=dict(CREDIT_CONVERSION, confirmed=False))
        raw = encode({"usage": dict(usage, credits="0.5")}).encode("utf-8")
        self.assertIsNone(observed_cost(raw, unconfirmed, "run", "case", PER_REQUEST).amount)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--scenario"]:
        scenario = sys.argv.pop(2)
        sys.argv.pop(1)
        run_scenario(scenario)
    else:
        main()
