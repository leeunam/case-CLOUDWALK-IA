from argparse import Namespace
from copy import deepcopy
import json
from pathlib import Path
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

import execute
import gate
import seal
from adapters.qwen.adapter import choice, request_body
from budget import Account, BudgetError, cap_usd
from common import c01, decide, decode, encode, injected_observation
from plan import C05, HERE, PROFILE, SCOPE, Plan, gate_reference
from run import run, write_json, write_report
from settings import Settings

FIXTURE = HERE / "config-fixture.json"
REAL_EXAMPLE = HERE / "config-real-exemplo.json"
CAP = cap_usd("10")


class R2Test(TestCase):
    def setUp(self):
        scratch = self.enterContext(TemporaryDirectory(dir=c01.ROOT, prefix="r2-test-"))
        finance = self.enterContext(TemporaryDirectory(prefix="r2-account-"))
        self.scratch = Path(scratch)
        self.account_path = Path(finance) / "account.sqlite"

    def args(self, name, account, *, stage="development", proof=None, config=FIXTURE):
        return Namespace(stage=stage, mode="fixture", config=config, output=self.scratch / name,
                         development_gate=proof, account=account.path, account_id=account.id,
                         cap_usd=CAP, confirm_execution=True, dry_run=False, manifest=None)

    def init_account(self):
        return Account.initialize(self.account_path, scope="fixture", cap=CAP, previous_spend="0")

    def create_manifest(self, args):
        dry = Namespace(**vars(args))
        dry.dry_run = True
        dry.output = self.scratch / (args.output.name + "-dry")
        execute.run_evaluation(dry)
        template = c01.read(dry.output / "manifest-template.json")
        self.assertIs(template["enabled"], False)
        template["enabled"] = True
        args.manifest = dry.output / "manifest-fixture.json"
        args.manifest.write_text(encode(template), encoding="utf-8")
        return template

    def cli(self, *args):
        command = [sys.executable, "-B", str(HERE / "execute.py"), *map(str, args)]
        return subprocess.run(command, cwd=c01.ROOT, capture_output=True, text=True, check=True).stdout

    def test_cli_runs_both_stages_on_one_persistent_account(self):
        account_info = decode(self.cli("init-account", "--mode", "fixture", "--account", self.account_path,
                                       "--cap-usd", 10, "--previous-spend-usd", 0))
        account = Account(self.account_path, account_info["account_id"], "fixture")
        options = ["--mode", "fixture", "--config", FIXTURE, "--account", account.path,
                   "--account-id", account.id, "--cap-usd", CAP]
        proof_args = []
        for stage, dimensions in (("development", (6, 0, 6)), ("final", (36, 13, 44))):
            dry = self.scratch / (stage + "-dry")
            output = self.scratch / stage
            self.cli("run", "--stage", stage, *options, *proof_args, "--dry-run", "--output", dry)
            template = c01.read(dry / "manifest-template.json")
            self.assertIs(template["enabled"], False)
            template["enabled"] = True
            manifest = dry / "manifest-fixture.json"
            manifest.write_text(encode(template), encoding="utf-8")
            self.cli("run", "--stage", stage, *options, *proof_args, "--manifest", manifest,
                     "--confirm-execution", "--output", output)
            report = c01.read(output / "report.json")
            self.assertEqual(c01.verify_report(output / "report.json", c01.R2), PROFILE)
            self.assertEqual((len(report["completed_ids"]), len(report["control_ids"]),
                              report["usage"]["requests"]["value"]), dimensions)
            self.assertEqual(report["eligibility"], "inconclusive")
            self.assertEqual(report["gates"][c01.OBSERVED_GATE]["state"], "unmeasured")
            if stage == "development":
                proof = output / gate.FILENAME
                proof_args = ["--development-gate", proof]
                result = c01.read(proof)
                self.assertEqual(result["status"], "fixture_ready")
                self.assertEqual((result["correct_targets"], result["preserved_fields"], result["correct_completions"],
                                  result["integral_reviews"], result["raw_urgent"]), (8, 4, 3, 3, 1))
                self.assertEqual(result["observed_usd"], "0.003282")
            else:
                self.assertEqual(template["binding"]["development_gate"], gate_reference(proof))
                self.assertEqual(report["injected_controls"]["count"], 1)
                self.assertEqual(report["gates"]["complete_or_invalid_controls_model_calls"]["numerator"], 0)
                self.assertEqual(report["gates"]["partial_application_after_abstention_or_error"]["numerator"], 0)
        status = decode(self.cli("status", "--mode", "fixture", "--account", account.path, "--account-id", account.id))
        self.assertEqual(status, Account(account.path, account.id, "fixture").status())
        self.assertEqual([run["state"] for run in status["runs"]], ["finished", "finished"])
        self.assertEqual(len(status["reservations"]), 50)
        self.assertEqual({row["state"] for row in status["reservations"]}, {"settled"})
        self.assertEqual(status["accounted_usd"], "0.027350")

    def test_replay_rejected_even_with_new_fixture_config_binding(self):
        account = self.init_account()
        original = self.args("initial", account)
        old_template = self.create_manifest(original)
        execute.run_evaluation(original)
        amended_config = self.scratch / "config-alterada.json"
        amended_config.write_bytes(FIXTURE.read_bytes() + b"\n")
        replacement = self.args("replacement", account, config=amended_config)
        new_template = self.create_manifest(replacement)
        self.assertEqual(old_template["manifest_id"], new_template["manifest_id"])
        self.assertNotEqual(old_template["binding"]["config_sha256"], new_template["binding"]["config_sha256"])
        with self.assertRaisesRegex(BudgetError, "vinculação já usados"):
            execute.run_evaluation(replacement)
        self.assertFalse(replacement.output.exists())
        new_template["manifest_id"] = "outro-id"
        replacement.manifest.write_text(encode(new_template), encoding="utf-8")
        with self.assertRaisesRegex(BudgetError, "manifesto R2"):
            execute.run_evaluation(replacement)
        self.assertEqual(len(account.status()["reservations"]), 6)

    def test_gate_cannot_be_repinned_with_forged_cost_or_interrupted_journal(self):
        account = self.init_account()
        args = self.args("dev", account)
        self.create_manifest(args)
        execute.run_evaluation(args)
        proof = args.output / gate.FILENAME
        original = proof.read_bytes()
        forged = dict(decode(original), observed_usd="0.000001")
        proof.write_text(encode(forged), encoding="utf-8")
        final = self.args("forged", account, stage="final", proof=proof)
        self.create_manifest(final)
        with self.assertRaisesRegex(BudgetError, "selo de development divergente"):
            execute.run_evaluation(final)
        proof.write_bytes(original)
        (args.output / "interruption.json").touch()
        final = self.args("prefix", account, stage="final", proof=proof)
        self.create_manifest(final)
        with self.assertRaisesRegex(BudgetError, "prefixo interrompido"):
            execute.run_evaluation(final)
        self.assertEqual(len(account.status()["runs"]), 1)

    def test_fixture_gate_rejected_before_account_or_network_in_real_mode(self):
        proof = self.scratch / gate.FILENAME
        proof.write_text('{"mode":"fixture","status":"fixture_ready"}', encoding="utf-8")
        settings = c01.read(REAL_EXAMPLE)
        settings.update(billable_limits_confirmed=True, tariff_verified=True)
        config = self.scratch / "real-sintetico.json"
        config.write_text(encode(settings), encoding="utf-8")
        account = Account(self.account_path, "conta-inexistente", "real")
        args = self.args("real", account, stage="final", proof=proof, config=config)
        args.mode = "real"
        self.create_manifest(args)
        with mock.patch.object(Account, "status", side_effect=AssertionError("conta não deve ser aberta")), \
                mock.patch.object(execute, "run_batch", side_effect=AssertionError("não deve iniciar subprocesso")):
            with self.assertRaisesRegex(BudgetError, "outro modo"):
                execute.run_evaluation(args)
        self.assertFalse(self.account_path.exists())
        self.assertFalse(args.output.exists())

    def scenario_command(self, scenario):
        child = self.scratch / f"{scenario}.py"
        child.write_text(f'''
import sys
sys.path.insert(0, {str(HERE)!r})
import execute
from common import decode, encode

original = execute.development_fixture
def altered(plan):
    synthetic = original(plan)
    def gateway(body, deadline, dispatched):
        if {scenario!r} == "timeout":
            dispatched()
            raise TimeoutError
        status, raw = synthetic(body, deadline, dispatched)
        response = decode(raw)
        if {scenario!r} == "unknown":
            del response["usage"]
        if {scenario!r} == "wrong":
            answer = response["choices"][0]["message"]
            if "payouts" in answer["content"]:
                answer["content"] = '{{"category":"pix"}}'
        return status, encode(response).encode("utf-8")
    return gateway
execute.development_fixture = altered
execute.main()
''', encoding="utf-8")
        return [sys.executable, "-B", str(child), "_adapter"]

    def test_finished_wrong_classification_retains_known_cost_and_does_not_release_final(self):
        account = self.init_account()
        args = self.args("wrong", account)
        self.create_manifest(args)
        self.assertEqual(execute.run_evaluation(args, fixture_command=self.scenario_command("wrong")), "failed")
        proof = args.output / gate.FILENAME
        self.assertEqual(c01.read(proof)["observed_usd"], "0.003282")
        final = self.args("final", account, stage="final", proof=proof)
        self.create_manifest(final)
        with self.assertRaisesRegex(BudgetError, "gate de development falhou"):
            execute.run_evaluation(final)
        self.assertEqual([row["state"] for row in account.status()["runs"]], ["finished"])

    def rewrite_wrong_outputs(self, output, development):
        bundle = c01.load_bundle(development.validation, output / "report.json")
        obs = bundle["observations"][0]
        first = bundle["inputs"][0]
        self.assertEqual((obs["id"], obs["choices"]["category"]["raw"]), ("jev-004", "pix"))
        obs["choices"]["category"]["raw"] = "payouts"
        bundle["decisions"][0] = decide(first, obs, development.catalog, bundle["report"]["run_id"])
        for name in ("observations", "decisions"):
            (output / f"{name}.jsonl").write_text("".join(encode(row) + "\n" for row in bundle[name]), encoding="utf-8")
        write_report(output, bundle["report"], bundle["inputs"], bundle["observations"], bundle["decisions"],
                     development.validation, development.protocol, development.split, development.catalog,
                     development.cases, development.control_policy, False)

    def test_regenerated_proof_from_failed_development_cannot_replace_original_outputs(self):
        account = self.init_account()
        args = self.args("wrong", account)
        self.create_manifest(args)
        self.assertEqual(execute.run_evaluation(args, fixture_command=self.scenario_command("wrong")), "failed")
        original_ledger = account.status()
        development = Plan("development", "fixture", "proof-check", FIXTURE)
        private = seal.path_for(development, account)
        original_seal = private.read_bytes()
        self.assertEqual(stat.S_IMODE(private.stat().st_mode), 0o600)
        self.assertEqual(private.parent, account.path.parent)

        output = args.output
        self.rewrite_wrong_outputs(output, development)
        regenerated = gate.collect(output, development, account, CAP)
        self.assertEqual((regenerated["status"], regenerated["correct_targets"]), ("fixture_ready", 8))
        proof = output / gate.FILENAME
        write_json(proof, regenerated)
        final = self.args("final", account, stage="final", proof=proof)
        self.create_manifest(final)
        with self.assertRaisesRegex(BudgetError, "selo de development divergente"):
            execute.run_evaluation(final)
        self.assertEqual(private.read_bytes(), original_seal)
        self.assertEqual(account.status(), original_ledger)
        self.assertFalse(final.output.exists())

    def test_rewrite_after_financial_close_cannot_become_the_original_seal(self):
        account = self.init_account()
        args = self.args("wrong-before-seal", account)
        self.create_manifest(args)
        development = Plan("development", "fixture", "proof-check", FIXTURE)
        private = seal.path_for(development, account)
        close = Account.close_run
        snapshots = []

        def close_then_rewrite(active, run_id, *, finished):
            close(active, run_id, finished=finished)
            self.assertTrue(finished)
            self.assertFalse(private.exists())
            snapshots.append(active.status())
            self.rewrite_wrong_outputs(args.output, development)

        with mock.patch.object(Account, "close_run", close_then_rewrite):
            with self.assertRaisesRegex(BudgetError, "saídas publicadas divergem dos bytes produzidos"):
                execute.run_evaluation(args, fixture_command=self.scenario_command("wrong"))
        proof = args.output / gate.FILENAME
        self.assertFalse(proof.exists())
        self.assertFalse(private.exists())
        self.assertEqual(account.status(), snapshots[0])
        self.assertEqual([row["state"] for row in snapshots[0]["runs"]], ["finished"])
        self.assertEqual({row["state"] for row in snapshots[0]["reservations"]}, {"settled"})
        self.assertEqual(len(snapshots[0]["reservations"]), 6)

        regenerated = gate.collect(args.output, development, account, CAP)
        self.assertEqual(regenerated["status"], "fixture_ready")
        write_json(proof, regenerated)
        final = self.args("final", account, stage="final", proof=proof)
        self.create_manifest(final)
        with self.assertRaisesRegex(BudgetError, "selo de development ausente"):
            execute.run_evaluation(final)
        retry = self.args("retry-original", account)
        self.create_manifest(retry)
        with self.assertRaisesRegex(BudgetError, "vinculação já usados"):
            execute.run_evaluation(retry)
        self.assertFalse(private.exists())
        self.assertEqual(account.status(), snapshots[0])

    def test_gate_proof_bytes_are_committed_at_publication(self):
        account = self.init_account()
        args = self.args("proof-publication", account)
        self.create_manifest(args)
        development = Plan("development", "fixture", "proof-check", FIXTURE)
        private = seal.path_for(development, account)

        def write_then_alter(path, value):
            written = write_json(path, value)
            if path.name == gate.FILENAME:
                path.write_bytes(path.read_bytes() + b"\n")
            return written

        with mock.patch.object(execute, "write_json", write_then_alter):
            with self.assertRaisesRegex(BudgetError, "prova publicada diverge dos bytes produzidos"):
                execute.run_evaluation(args)
        self.assertFalse(private.exists())
        self.assertEqual([row["state"] for row in account.status()["runs"]], ["finished"])

    def test_missing_or_corrupt_seal_is_never_recreated(self):
        account = self.init_account()
        args = self.args("dev", account)
        self.create_manifest(args)
        self.assertEqual(execute.run_evaluation(args), "fixture_ready")
        development = Plan("development", "fixture", "proof-check", FIXTURE)
        private = seal.path_for(development, account)
        final = self.args("final", account, stage="final", proof=args.output / gate.FILENAME)
        self.create_manifest(final)
        private.unlink()
        with self.assertRaisesRegex(BudgetError, "selo de development ausente ou corrompido"):
            execute.run_evaluation(final)
        self.assertFalse(private.exists())
        private.touch(mode=0o600)
        private.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(BudgetError, "selo de development ausente ou corrompido"):
            execute.run_evaluation(final)
        self.assertEqual(private.read_text(encoding="utf-8"), "{")
        self.assertEqual(len(account.status()["reservations"]), 6)
        self.assertFalse(final.output.exists())

    def test_unknown_or_timeout_interrupts_and_retains_reservation(self):
        for scenario in ("unknown", "timeout"):
            with self.subTest(scenario=scenario):
                account = Account.initialize(self.account_path.with_name(scenario + ".sqlite"), scope="fixture",
                                             cap=CAP, previous_spend="0")
                args = self.args(scenario, account)
                self.create_manifest(args)
                with self.assertRaisesRegex(BudgetError, "inconciliável"):
                    execute.run_evaluation(args, fixture_command=self.scenario_command(scenario))
                ledger = Account(account.path, account.id, "fixture").status()
                self.assertEqual([row["state"] for row in ledger["runs"]], ["interrupted"])
                self.assertEqual(len(ledger["reservations"]), 1)
                reservation = ledger["reservations"][0]
                self.assertEqual(ledger["accounted_usd"], reservation["reserved"])
                self.assertEqual(bool(reservation["financial_expired"]), scenario == "timeout")
                self.assertFalse((args.output / gate.FILENAME).exists())
                self.assertEqual(c01.verify_report(args.output / "prefix-report.json", c01.R2), PROFILE)
                retry = self.args(scenario + "-retry", account)
                self.create_manifest(retry)
                with self.assertRaisesRegex(BudgetError, "vinculação já usados"):
                    execute.run_evaluation(retry)

    def test_scope_and_legacy_cli_are_distinct(self):
        historic = C05 / "config-fixture.json"
        self.assertEqual(Settings.load(historic, "fixture").reservation,
                         Settings.load(FIXTURE, "fixture", expected_scope=SCOPE).reservation)
        with self.assertRaisesRegex(BudgetError, "escopo"):
            Settings.load(FIXTURE, "fixture")
        with self.assertRaisesRegex(BudgetError, "escopo"):
            Settings.load(historic, "fixture", expected_scope=SCOPE)
        with self.assertRaisesRegex(ValueError, "r2/execute.py"):
            run(Namespace(profile=c01.R2))

    def test_r2_package_lock_is_checked_before_planning_and_request_has_no_labels(self):
        original_digest = c01.digest
        review = c01.PLAN / "r2/data-review.json"
        with mock.patch.object(c01, "digest", side_effect=lambda path:
                               "0" * 64 if path == review else original_digest(path)):
            with self.assertRaisesRegex(c01.ContractError, "artifact_hash.*data-review"):
                Plan("development", "fixture", "teste-pin", FIXTURE)
        plan = Plan("development", "fixture", "teste-req", FIXTURE)
        item = plan.inputs[0]
        self.assertEqual(set(item), {"id", "text", "received", "missing", "brand", "catalog", "contract_version"})
        payload = decode(request_body(item, item["received"], "instruções", 128, {"enabled": False}))
        context = decode(payload["messages"][1]["content"])
        expected_fields = {"text", "brand", "catalog", "missing", "received"}
        self.assertEqual(set(context), expected_fields)
        self.assertEqual(payload["response_format"]["json_schema"]["schema"]["required"], item["missing"])
        self.assertEqual(payload["max_tokens"], 128)
        self.assertEqual(payload["reasoning"], {"enabled": False})
        self.assertEqual(set(plan.split["model_visible_fields"]), set(context))
        self.assertEqual(set(plan.split["ipc_projection_fields"]), set(item))
        data = c01.read(c01.source_path(plan.protocol["source_dataset"]))
        historic = dict(plan.split, source_dataset_version="1.1.0")
        with self.assertRaisesRegex(c01.ContractError, "r2_split_source"):
            c01.verify_r2_package(plan.protocol, historic, data)
        leaked = dict(plan.split, model_visible_fields=["id", *plan.split["model_visible_fields"]])
        with self.assertRaisesRegex(c01.ContractError, "r2_split_projection"):
            c01.verify_r2_package(plan.protocol, leaked, data)

    def test_r2_checker_derives_final_gates_and_rejects_forged_pass(self):
        plan = Plan("final", "fixture", "synthetic-final", FIXTURE)
        original = c01.load_bundle(plan.validation, PROFILE.golden_path)
        identity = c01.read(c01.source_path(plan.sources["candidate"]))["identity"]
        plan.report["identity"] = identity
        template = next(obs for obs in original["observations"] if obs["origin"] == "candidate")
        observations, decisions = [], []
        for item in plan.inputs:
            case_id = item["id"]
            obs = None
            if case_id in plan.injections["ids"]:
                obs = injected_observation(item, plan.report["run_id"], plan.control_policy)
            elif case_id in plan.candidates:
                targeted = case_id in plan.cases
                # Força conclusão justamente em um caso com revisão obrigatória.
                if targeted and case_id != "r2-011":
                    targets = plan.cases[case_id]["expected"]
                else:
                    targets = {field: next(iter(item["catalog"][field])) for field in item["missing"]}
                obs = dict(template, id=case_id, run_id=plan.report["run_id"], identity=identity,
                           returned_model=identity["expected_returned_model"], questions=len(item["missing"]),
                           elapsed_ms=100 if targeted else None, choices={
                               field: (choice("abstained", code, "explicit") if code == c01.ABSTENTION
                                       else choice("predicted", code)) for field, code in targets.items()})
            if obs is not None:
                observations.append(obs)
            decisions.append(decide(item, obs, plan.catalog, plan.report["run_id"]))
        for name, rows in (("inputs", plan.inputs), ("observations", observations), ("decisions", decisions)):
            (self.scratch / f"{name}.jsonl").write_text("".join(encode(row) + "\n" for row in rows), encoding="utf-8")
        write_report(self.scratch, plan.report, plan.inputs, observations, decisions, plan.validation,
                     plan.protocol, plan.split, plan.catalog, plan.cases, plan.control_policy, False)
        path = self.scratch / "report.json"
        c01.verify_report(path, c01.R2)
        report = c01.read(path)
        metric = report["gates"]["automatic_completion_on_expected_review_cases"]
        self.assertEqual((report["eligibility"], metric["numerator"]), ("fail", 1))
        metric.update(value=0, numerator=0)
        report["eligibility"] = "pass"
        write_json(path, report)
        with self.assertRaisesRegex(c01.ContractError, "r2_metrics: gates"):
            c01.verify_report(path, c01.R2)

    def test_real_gate_requires_six_measured_durations_inclusive_limit(self):
        account = self.init_account()
        args = self.args("measure", account)
        self.create_manifest(args)
        execute.run_evaluation(args)
        fixture = Plan("development", "fixture", "test", FIXTURE)
        bundle = c01.load_bundle(fixture.validation, args.output / "report.json")
        costs = c01.read(args.output / gate.FILENAME)["costs"]
        self.assertEqual(gate.assess(fixture, bundle, costs)["status"], "fixture_ready")
        synthetic_real = deepcopy(bundle)
        fixture.mode = "real"
        for observation in synthetic_real["observations"]:
            observation["elapsed_ms"] = 3000
        self.assertEqual(gate.assess(fixture, synthetic_real, costs)["status"], "pass")
        for duration in (3000.001, None):
            with self.subTest(duration=duration):
                synthetic_real["observations"][-1]["elapsed_ms"] = duration
                self.assertEqual(gate.assess(fixture, synthetic_real, costs)["status"], "failed")
