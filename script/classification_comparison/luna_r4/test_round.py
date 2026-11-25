"""Contratos fixos das duas rodadas e isolamento da prova de desenvolvimento."""
from contextlib import redirect_stderr
from io import StringIO
import subprocess
import sys
from unittest.mock import patch

from luna import test_round
from luna.round_spec import ACCOUNT_ID, ACCOUNT_RELATIVE, LUNA
from luna_r4.round_spec import LUNA_R4
from r2 import execute, gate
from r2.plan import Plan, gate_reference
from budget import Account, BudgetError
from common import c01, encode


class R4Test(test_round.LunaTest):
    round = LUNA_R4
    round_name = "LUNA_R4"
    scope = "c05-feita-luna-r4"
    prefix = "luna-r4-"
    previous_spend = "0.02869232"
    expected_total = "0.05604232"

    def test_failed_r3_never_authorizes_r4(self):
        account = self.account("development")
        # Produz a reprovação pela CLI/IPC da R3 e mantém seu selo original.
        with patch.object(self, "round", LUNA), patch.object(self, "round_name", "LUNA"):
            args = self.args("r3", account)
            status = execute.run_evaluation(args, fixture_command=self.scenario("wrong"), round_spec=LUNA)
            self.assertEqual(status, "failed")
        proof = args.output / gate.FILENAME
        original = c01.read(proof)
        final = Plan("final", "fixture", "test", self.fixture, round_spec=LUNA_R4)
        other = self.account("outra")
        for target in (account, other):
            with self.assertRaisesRegex(BudgetError, "falhou"):
                gate.verify(gate_reference(proof), final, target, test_round.CAP)
        proof.write_text(encode(dict(original, status="fixture_ready")))
        for target in (account, other):
            with self.assertRaisesRegex(BudgetError, "selo"):
                gate.verify(gate_reference(proof), final, target, test_round.CAP)
        self.assertEqual(len(account.status()["runs"]), 1)
        self.assertEqual(other.status()["runs"], [])

    def test_only_r4_prompt_and_historical_official_populations(self):
        r3 = Plan("development", "fixture", "test", LUNA.entrypoint.with_name("config-fixture.json"), round_spec=LUNA)
        r4 = Plan("development", "fixture", "test", self.fixture, round_spec=LUNA_R4)
        final = Plan("final", "fixture", "test", self.fixture, round_spec=LUNA_R4)
        self.assertEqual(r4.round.profile.name, "observed-total-luna-r4")
        self.assertEqual((r4.round.profile.quality_version, r4.round.profile.report_version,
                          r4.round.profile.ipc_version), ("1.4.0", "1.5.0", "1.1.0"))
        self.assertEqual(r4.inputs, r3.inputs)
        self.assertEqual(r4.report["sources"]["prompt"]["sha256"],
                         "026c70c89da05102f9c6b84c87ba8e2c522d8d77cd2405403849d6823b7e2741")
        self.assertEqual(r4.sources["candidate"]["sha256"],
                         "ba0701bd3b003cb146f8212bef1753d45c9a2ef8d548472ffe3d04d83cced888")
        self.assertEqual(r4.sources["operational"], r3.sources["operational"])
        self.assertEqual(r4.sources["final_cases"], r3.sources["final_cases"])
        self.assertEqual(final.binding["max_requests"], 44)
        self.assertEqual(r4.binding["max_requests"], 6)
        self.assertEqual(r4.protocol["gates"], r3.protocol["gates"])
        account = self.account("isolamento")
        self.assertNotEqual(r4.manifest_id(account), r3.manifest_id(account))
        with self.assertRaisesRegex(BudgetError, "configuração"):
            Plan("development", "fixture", "test", r3.config, round_spec=LUNA_R4)

    def test_real_cli_checks_account_before_open_or_key(self):
        git_dir = self.finance / ".git"
        git_dir.mkdir()
        canonical = self.finance / ACCOUNT_RELATIVE
        canonical.parent.mkdir(parents=True)
        canonical.touch()
        other = self.finance / "outra.sqlite"
        def git_output(command, **kwargs):
            return {"HEAD": "a" * 40, "--git-common-dir": str(git_dir)}[command[-1]]

        with patch.object(subprocess, "check_output", side_effect=git_output), \
                patch.object(Account, "transaction", side_effect=AssertionError("acesso à conta")):
            for account, account_id in ((canonical, "id-distinto"), (other, ACCOUNT_ID)):
                common = ["--mode", "real", "--account", str(account), "--account-id", account_id]
                for command in (["status"], ["reconcile", "--receipt", str(self.finance / "ausente")],
                                ["run", "--stage", "development", "--cap-usd", "10", "--dry-run",
                                 "--config", str(self.round.entrypoint.with_name("config-real-exemplo.json")),
                                 "--output", str(self.output / "rejeitado")]):
                    argv = [str(self.round.entrypoint), *command, *common]
                    with self.subTest(command=command[0], account=account), patch.object(sys, "argv", argv):
                        with redirect_stderr(StringIO()) as message, self.assertRaises(SystemExit):
                            execute.main(self.round)
                        self.assertIn("conta global existente", message.getvalue())
        self.assertFalse((self.output / "rejeitado").exists())
        self.assertFalse(other.exists())
