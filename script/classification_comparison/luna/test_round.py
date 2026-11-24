"""Verifica os dois processos Luna com um ledger temporário e transporte sintético."""
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest
from unittest.mock import patch

from luna.round_spec import ACCOUNT_ID, ACCOUNT_RELATIVE, HERE, LUNA, LunaSettings, check_account
from r2 import execute, gate, seal
from r2.plan import Plan, gate_reference
from budget import Account, BudgetError, cap_usd
from common import c01, decode, encode
from run import run

FIXTURE = HERE / "config-fixture.json"
CAP = cap_usd("10")


def cli(*args, check=True):
    return subprocess.run([sys.executable, "-B", str(HERE / "execute.py"), *map(str, args)],
                          cwd=c01.ROOT, capture_output=True, text=True, check=check)


class LunaTest(unittest.TestCase):
    def setUp(self):
        self.output = Path(self.enterContext(TemporaryDirectory(dir=c01.ROOT)))
        self.finance = Path(self.enterContext(TemporaryDirectory()))

    def account(self, name):
        return Account.initialize(self.finance / name, scope="fixture", cap=CAP, previous_spend="0")

    def args(self, name, account, *, stage="development", gate_file=None, config=FIXTURE):
        args = Namespace(mode="fixture", stage=stage, development_gate=gate_file, config=config,
                         account=account.path, account_id=account.id, cap_usd=CAP, confirm_execution=True,
                         manifest=None, output=self.output / (name + "-dry"), dry_run=True)
        execute.run_evaluation(args, round_spec=LUNA)
        template = c01.read(args.output / "manifest-template.json")
        self.assertFalse(template["enabled"])
        template["enabled"] = True
        args.manifest = args.output / "fixture-enabled.json"
        args.manifest.write_text(encode(template))
        args.output = self.output / name
        args.dry_run = False
        return args

    def scenario(self, kind):
        script = self.output / (kind + ".py")
        script.write_text(f"""
import sys
sys.path.insert(0, {str(HERE.parent)!r})
from luna.round_spec import LUNA
from r2 import execute
from common import decode, encode
if {kind!r} == "expired":
    from adapters.luna.adapter import LunaAdapter
    from pathlib import Path
    import os
    classify = LunaAdapter.classify
    def after_deadline(self, item):
        clock = Path(os.environ["CLASSIFICATION_READY_FILE"]).with_name("case-deadline.json")
        clock.write_text(encode([item["id"], 0]))
        return classify(self, item)
    LunaAdapter.classify = after_deadline
original = execute.development_fixture
def fixture(plan):
    gateway = original(plan)
    def intercept(body, deadline, dispatched):
        if {kind!r} == "expired":
            raise AssertionError("gateway chamado após prazo externo")
        if {kind!r} == "timeout":
            dispatched()
            raise TimeoutError()
        status, raw = gateway(body, deadline, dispatched)
        response = decode(raw)
        if {kind!r} == "unknown":
            del response["usage"]
        elif {kind!r} == "invalid":
            response["choices"][0]["message"]["content"] = "?"
        elif {kind!r} == "http_error":
            status = 500
        elif {kind!r} == "wrong":
            answer = response["choices"][0]["message"]["content"]
            response["choices"][0]["message"]["content"] = answer.replace("payouts", "pix")
        return status, encode(response).encode()
    return intercept
execute.development_fixture = fixture
execute.main(LUNA)
""")
        return [sys.executable, "-B", str(script), "_adapter"]

    def test_init_account_guards_reserved_path_before_creation(self):
        git_dir = self.finance / ".git"
        git_dir.mkdir()
        reserved = self.finance / ACCOUNT_RELATIVE
        reserved.parent.mkdir(parents=True)
        alias = self.finance / "alias"
        alias.symlink_to(reserved.parent, target_is_directory=True)

        def initialize(path):
            argv = ["luna/execute.py", "init-account", "--mode", "fixture", "--account", str(path),
                    "--cap-usd", "10", "--previous-spend-usd", "0"]
            stdout = StringIO()
            with patch.object(sys, "argv", argv), redirect_stdout(stdout):
                execute.main(LUNA)
            return decode(stdout.getvalue())

        with patch.object(subprocess, "check_output", return_value=str(git_dir)):
            for path in (reserved, alias / reserved.name):
                with self.subTest(path=path):
                    with redirect_stderr(StringIO()) as err, self.assertRaises(SystemExit) as failure:
                        initialize(path)
                    self.assertEqual(failure.exception.code, 2)
                    self.assertIn("conta sintética separada", err.getvalue())
                    self.assertFalse(reserved.exists())

            reserved.write_bytes(b"arquivo historico simulado")
            with redirect_stderr(StringIO()) as err, self.assertRaises(SystemExit):
                initialize(reserved)
            self.assertIn("conta sintética separada", err.getvalue())
            self.assertEqual(reserved.read_bytes(), b"arquivo historico simulado")
            allowed = self.finance / "permitida.sqlite"
            result = initialize(allowed)
            self.assertEqual(Account(allowed, result["account_id"], "fixture").status(), result)

    def test_cli_two_stages_and_replay(self):
        path = self.finance / "fixture.sqlite"
        info = decode(cli("init-account", "--mode", "fixture", "--account", path, "--cap-usd", 10,
                          "--previous-spend-usd", "0.02687405").stdout)
        account = Account(path, info["account_id"], "fixture")
        options = ["--mode", "fixture", "--config", FIXTURE, "--account", path, "--account-id", account.id,
                   "--cap-usd", 10]
        proof = []
        for stage, n, controls, calls in (("development", 6, 0, 6), ("final", 36, 13, 44)):
            args = ["run", "--stage", stage, *options, *proof]
            dry = self.output / (stage + "-dry")
            out = self.output / stage
            cli(*args, "--dry-run", "--output", dry)
            manifest = dry / "manifest-template.json"
            template = c01.read(manifest)
            self.assertFalse(template["enabled"])
            self.assertTrue(template["manifest_id"].startswith("luna-"))
            binding = template["binding"]
            self.assertEqual(binding["scope"], "c05-feita-luna")
            self.assertEqual(binding["operational"]["sha256"], "0666cdd1c99f58c52512681563b72ddcaf4f97593071a1797104526d062678da")
            self.assertIn(str(HERE.relative_to(c01.ROOT) / "execute.py"), binding["executor_sha256"])
            manifest.write_text(encode(dict(template, enabled=True)))
            cli(*args, "--manifest", manifest, "--confirm-execution", "--output", out)
            c01.verify_report(out / "report.json", c01.LUNA)
            report = c01.read(out / "report.json")
            self.assertEqual((len(report["completed_ids"]), len(report["control_ids"]),
                              report["usage"]["requests"]["value"]), (n, controls, calls))
            self.assertEqual(report["eligibility"], "inconclusive")
            self.assertEqual(report["gates"][c01.OBSERVED_GATE], dict(state="unmeasured", denominator=n,
                                                                     value=None, numerator=None))
            self.assertIn("luna/execute.py", c01.read(out / "invocation.json")["command"])
            if stage == "development":
                result = c01.read(out / gate.FILENAME)
                self.assertEqual([result[k] for k in ("status", "correct_targets", "preserved_fields",
                                 "correct_completions", "integral_reviews", "raw_urgent", "errors")],
                                 ["fixture_ready", 8, 4, 3, 3, 1, 0])
                proof = ["--development-gate", out / gate.FILENAME]
        status = decode(cli("status", "--mode", "fixture", "--account", path, "--account-id", account.id).stdout)
        self.assertEqual([r["state"] for r in status["runs"]], ["finished", "finished"])
        self.assertEqual([r["state"] for r in status["reservations"]], ["settled"] * 50)
        self.assertEqual(status["accounted_usd"], "0.05422405")
        amended = self.output / "another.json"
        amended.write_bytes(FIXTURE.read_bytes() + b"\n")
        retry = self.args("replay", account, config=amended)
        with self.assertRaisesRegex(BudgetError, "já usados"):
            execute.run_evaluation(retry, round_spec=LUNA)

    def test_technical_stop_and_financial_prefix(self):
        for scenario in ("invalid", "http_error", "unknown", "timeout", "expired"):
            with self.subTest(scenario=scenario):
                account = self.account(scenario)
                args = self.args(scenario, account)
                with self.assertRaises(BudgetError):
                    execute.run_evaluation(args, fixture_command=self.scenario(scenario), round_spec=LUNA)
                status = account.status()
                self.assertEqual([r["state"] for r in status["runs"]], ["interrupted"])
                self.assertEqual(len(status["reservations"]), 1)
                row = status["reservations"][0]
                if scenario in {"invalid", "http_error"}:
                    self.assertEqual((row["state"], row["observed"]), ("settled", "0.000547"))
                else:
                    self.assertNotEqual(row["state"], "settled")
                    self.assertEqual(status["accounted_usd"], row["reserved"])
                    self.assertEqual(bool(row["financial_expired"]), scenario in {"timeout", "expired"})
                c01.verify_report(args.output / "prefix-report.json", c01.LUNA)
                self.assertFalse((args.output / gate.FILENAME).exists())

    def test_failed_gate_then_tamper_rejected(self):
        account = self.account("wrong")
        args = self.args("wrong", account)
        self.assertEqual(execute.run_evaluation(args, fixture_command=self.scenario("wrong"), round_spec=LUNA), "failed")
        proof = args.output / gate.FILENAME
        development = Plan("development", "fixture", "check", FIXTURE, round_spec=LUNA)
        final = Plan("final", "fixture", "check", FIXTURE, round_spec=LUNA)
        self.assertTrue(seal.path_for(development, account).exists())
        with self.assertRaisesRegex(BudgetError, "falhou"):
            gate.verify(gate_reference(proof), final, account, CAP)
        failed = c01.read(proof)
        proof.write_text(encode(dict(failed, status="fixture_ready")))
        with self.assertRaisesRegex(BudgetError, "selo"):
            gate.verify(gate_reference(proof), final, account, CAP)
        with self.assertRaisesRegex(BudgetError, "selo"):
            gate.verify(gate_reference(proof), final, self.account("other"), CAP)
        snapshots = account.status()
        args = self.args("manifest", account, stage="final", gate_file=proof)
        manifest = c01.read(args.manifest)
        manifest["binding"]["candidate"] = c01.read(c01.get_profile(c01.R2).protocol_path)["r2"]["candidate"]
        args.manifest.write_text(encode(manifest))
        with self.assertRaisesRegex(BudgetError, "manifesto LUNA"):
            execute.run_evaluation(args, round_spec=LUNA)
        self.assertEqual(account.status(), snapshots)
        final.mode = "real"
        with self.assertRaisesRegex(BudgetError, "outro modo"):
            gate.verify(gate_reference(proof), final, account, CAP)

    def test_financial_sources_must_cover_cache_long_context_and_usage(self):
        config = c01.read(FIXTURE)
        model = "openai/gpt-5.6-luna"
        url = "https://feita.ai/models/" + model
        record = self.output / "evidence.json"
        snapshot = self.output / "snapshot.txt"
        snapshot.write_text("Documento sintético de teste. Nenhuma consulta externa.")
        def pin(path):
            return {"path": str(path.relative_to(c01.ROOT)), "sha256": c01.digest(path)}
        config.update(mode="real", billable_limits_reference=url, usage_cost_reference=url)
        config["tariff"]["source"] = url
        prices = {k: config["tariff"][k] for k in ("input", "output", "cache_read", "cache_write")}
        evidence = dict(provider="feita", model=model, unit="USD/Mtoken", date=config["tariff"]["date"],
                        limits=[1050000, 140000], tiers={"standard": prices.copy(), "long_context": prices.copy()},
                        usage_cost_unit="USD", usage_credits=None,
                        sources={k: dict(url=url, snapshot=pin(snapshot)) for k in ("limits", "route", "tariff", "usage")})
        path = self.output / "settings.json"
        def load():
            record.write_text(encode(evidence))
            config["financial_evidence"] = pin(record)
            path.write_text(encode(config))
            return LunaSettings.load(path, "real")
        load().verify_execution()
        evidence["tiers"]["long_context"]["cache_write"] = "100"
        with self.assertRaisesRegex(BudgetError, "cache"):
            load()
        evidence["tiers"]["long_context"] = prices.copy()
        config["billable_output_token_ceiling"] = 32000
        with self.assertRaisesRegex(BudgetError, "limites faturáveis"):
            load()
        config["billable_output_token_ceiling"] = 140000
        snapshot.write_text("Fonte alterada")
        with self.assertRaisesRegex(c01.ContractError, "artifact_hash"):
            load()

    def test_profile_binding_and_generic_cli(self):
        with self.assertRaisesRegex(ValueError, "luna/execute.py"):
            run(Namespace(profile=c01.LUNA))
        example = HERE / "config-real-exemplo.json"
        with self.assertRaisesRegex(BudgetError, "pendente"):
            LunaSettings.load(example, "real").verify_execution()
        altered = dict(c01.read(example), tariff_verified=True, billable_limits_confirmed=True)
        bogus = self.output / "flags.json"
        bogus.write_text(encode(altered))
        with self.assertRaises(BudgetError):
            LunaSettings.load(bogus, "real")
        with self.assertRaisesRegex(BudgetError, "conta global"):
            check_account(Account(self.finance / "other.sqlite", ACCOUNT_ID, "real"))
        with self.assertRaisesRegex(c01.ContractError, "profile_mismatch"):
            c01.verify_report(LUNA.profile.golden_path, c01.R2)
        protected = HERE.parent / "adapters/luna/transport.py"
        original = c01.digest
        with patch.object(c01, "digest", side_effect=lambda path: "0"*64 if path == protected else original(path)):
            with self.assertRaisesRegex(c01.ContractError, "artifact_hash"):
                Plan("development", "fixture", "check", FIXTURE, round_spec=LUNA)
