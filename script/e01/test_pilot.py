"""Exercita orquestração e falhas sem conectar ao provedor."""
import copy
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

import pilot as p


def uid():
    return str(uuid.uuid4())


class FakeProject:
    project = "e01-test"
    base = "http://127.0.0.1:43309"

    def __init__(self):
        self.active = False
        self.sent = self.dispatches = self.stops = 0
        self.record = None
        self.records = {}
        self.fixed_response = None
        self.account = "fixture-account"
        self.cached = 2
        self.captures = {}
        self.next_charge = {"credits": "0.01"}
        self.rate = "0.50"
        self.holds = 0
        self.reservation = "0.755400000000"

    def stopped(self):
        return not self.active

    def start(self):
        self.active = True
        self.dispatches += 1

    def stop(self):
        self.stops += 1
        self.active = False

    def copy_receipts(self, directory):
        assert self.stopped()
        for filename, capture in self.captures.values():
            p.write_json(Path(directory) / filename, capture)

    def budget(self):
        return {"dispatches": self.dispatches, "entries": self.sent, "accounted_usd": str(self.dispatches * p.Decimal("0.001")),
                "holds": self.holds, "open_turns": 0, "database": "example", "oid": "1", "cluster": "example"}

    def tariff(self):
        return {"account_ref": self.account, "model": p.MODEL, "input_rate_usd_per_million": self.rate}

    def candidate(self):
        return {"source_commit": "a" * 40, "image": "sha256:" + "b" * 64}

    def turn(self, case, seq):
        return copy.deepcopy(self.records.get((case, seq)))


class FakeSimulator:
    def __init__(self, project, directory):
        self.project = project
        self.directory = directory
        self.lose_receipt = False
        self.delay = False
        self.channel_id = uid()
        self.fail_at = None
        self.capture_prefix = ""

    def prepare(self):
        pass

    def channel(self, brand, kind):
        return self.channel_id

    def send(self, channel, body, key):
        journal = json.loads((self.directory / "journal.json").read_bytes())
        label, index = next(k.split(".") for k, v in journal["turns"].items() if v["key"] == key and v["status"] == "intent")
        n = int(index)
        spec = p.MATRIX[label]
        assert spec.turns[n-1][0] == body["text"]
        self.project.sent += 1
        if self.lose_receipt:
            raise OSError("perda do 202")
        if n == 1:
            self.receipt = {"case_id": uid(), "correlation_id": uid(), "channel_id": channel,
                            "external_conversation_id": "simulator-private-" + uid()}
            self.messages = []
        else:
            assert body["external_conversation_id"] == self.receipt["external_conversation_id"]
        action, reply, refs, rule = p.expectation(spec, n)
        customer = {"id": uid(), "text": body["text"], "author": "customer", "created_at": p.now(), "sequence": 2*n-1}
        ai = {"id": uid(), "text": reply, "author": "ai", "created_at": p.now(), "sequence": 2*n}
        self.messages.extend((customer, ai))
        payload = {"text": reply, "request_event_id": uid()}
        handoff = None
        if rule:
            handoff = {"summary": customer["text"], "message_ids": [customer["id"]]}
            payload.update(handoff)
        brand = p.frozen(f"brands/{spec.brand}.json")
        proposal = {"case_id": self.receipt["case_id"], "correlation_id": self.receipt["correlation_id"],
                    "brand_id": brand["brand_id"], "event_id": uid(), "event_type": f"agent.{action}.proposed",
                    "payload": payload}
        self.project.record = None if self.delay else {
            **{k: self.receipt[k] for k in ("channel_id", "case_id", "correlation_id")}, "brand_id": brand["brand_id"],
            "category": spec.category, "priority": "basic", "state": "published", "request_ok": True, "result_ok": True, "on_time": True,
            "request_sha256": p.digest(json.dumps(payload).encode()), "request_id": payload["request_event_id"], "result_id": proposal["event_id"],
            "result_sha256": p.digest(json.dumps(proposal).encode()), "disposition": "applied", "proposal": proposal,
            "metadata": {"source_refs": refs, "ontology_version": "1.0.0", "knowledge_version": "1.0.0",
                         "policy_version": "e01-v1", "handoff_rule": {"id":rule["id"], "reason":rule["reason"]} if rule else None},
            "handoff": handoff, "integration": "idle", "status": {"reply":"ai_active","resolve":"resolved",
                                                                  "handoff":"waiting_human"}[action],
            "account_ref": self.project.account, "mode": "feita_bounded_public", "accounted_usd":"0.001",
            "reserved_usd":self.project.reservation,
            "usage":{"input_tokens":10,"cached_input_tokens":self.project.cached,"output_tokens":3,
                     "provider_response_id":self.project.fixed_response or "gen-" + uid()},
            "started_at": p.now(), "pilot_id": 1, "tariff_sha256": p.document_digest(self.project.tariff()),
        }
        if self.fail_at == f"{label}.{n}":
            self.project.record.update(state="failed", reason="invalid_decision", integration="failed",
                                       proposal=None, result_id=None, result_sha256=None, disposition=None, metadata=None)
        self.project.records[(self.receipt["case_id"],2*n-1)] = self.project.record
        if self.project.record:
            response = self.project.record["usage"]["provider_response_id"]
            counts = {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13,
                      "prompt_tokens_details": {"cached_tokens": self.project.cached}}
            if label != "P1":
                counts.update(self.project.next_charge)
            self.project.captures[f"{self.capture_prefix}{label}.{n}"] = ("receipt-" + uid() + ".json", {
                "id": response, "model": p.MODEL, "status": 200, "usage": counts, "request_sha256": "0"*64,
                "started_at": p.now(), "finished_at": p.now()})
        return self.receipt

    def history(self, case):
        return list(self.messages)


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.project = FakeProject()
        self.sim = FakeSimulator(self.project, self.dir)
        self.runner = p.Pilot(self.project, self.sim, self.dir, timeout=.03)

    def approval(self, turn="P1.1", source="provider_portal", directory=None):
        directory = directory or self.dir
        directory.mkdir(mode=0o700, exist_ok=True)
        row = self.runner.journal["turns"][turn]["ledger"]
        resp = row["usage"]["provider_response_id"]
        capture_key = self.sim.capture_prefix + turn
        filename, original_capture = self.project.captures[capture_key]
        capture = {**original_capture, "usage": {
            "prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13,
            "prompt_tokens_details": {"cached_tokens": row["usage"]["cached_input_tokens"]}}}
        self.project.captures[capture_key] = filename, capture
        record = {"id":resp, "source":"extrato de teste", "precision":"exact", "amount":"0.01", "unit":"credits",
                  "usd_per_credit":"0.01","conversion_source":"exemplo de teste","observed_at":p.now()}
        original = directory / "portal.txt"
        original.write_text("Relatório individual de teste em créditos " + resp)
        record.update(source_type=source, account_ref=row["account_ref"], conversion_account_ref=row["account_ref"],
                      original={"file":original.name,"sha256":p.digest(original.read_bytes())})
        if source == "provider_api_receipt":
            capture["usage"]["credits"] = record["amount"]
            record["field"] = "credits"
        approval = {"approved":True,"reviewer":"Teste offline","reviewed_at":p.now(), "binding":self.runner.journal["binding"],
                    "request_id":row["request_id"],"result_sha256":row["result_sha256"]}
        for name, data in (("capture", capture), ("provider_record", record)):
            if name == "provider_record" and source == "provider_api_receipt":
                data["original"] = approval["capture"]
            file = directory / (name + ".json")
            p.write_json(file, data)
            approval[name] = {"file":file.name, "sha256":p.digest(file.read_bytes())}
        dest = directory / "approval.json"
        p.write_json(dest, approval)
        return dest

    def prepare_parent(self):
        self.runner.run("canary")
        approval = self.approval(source="provider_api_receipt", directory=self.dir / "primeiro-p1")
        self.sim.fail_at = "P3.2"
        with self.assertRaisesRegex(p.Stop, "terminal_sem_resultado"):
            self.runner.run("remaining", approval)
        failed = self.approval("P3.2", source="provider_api_receipt", directory=self.dir / "primeiro-p32")
        self.runner.reconcile_turn("P3.2", failed)
        # O journal já gravado pelo runner original antecede a inclusão destes dois campos na consulta SQL.
        parent = json.loads(self.runner.path.read_bytes())
        for entry in parent["turns"].values():
            del entry["ledger"]["tariff_sha256"], entry["ledger"]["pilot_id"]
        p.write_json(self.runner.path, parent)
        self.sim = FakeSimulator(self.project, self.dir / p.ADDITIONAL)
        self.sim.capture_prefix = "adicional-"
        return approval

    def additional(self, approval=None):
        return p.Pilot(self.project, self.sim, self.dir, timeout=.1, attempt=p.ADDITIONAL, parent_approval=approval)

    def test_additional_five_plus_nine_preserves_failure_and_original_bytes(self):
        parent_approval = self.prepare_parent()
        original = self.runner.path.read_bytes()
        self.runner = self.additional(parent_approval)
        self.runner.run("canary")
        with self.assertRaisesRegex(p.Stop, "conciliacao_de_outra_rodada"):
            self.runner.run("remaining", parent_approval)
        self.runner = self.additional()
        approval = self.approval(source="provider_api_receipt", directory=self.dir / "novo-p1")
        new_evidence = json.loads(approval.read_bytes())
        p.write_json(approval, {**new_evidence, "prior_orientation_approval_sha256": "0" * 64})
        with self.assertRaisesRegex(p.Stop, "orientacao_original_divergente"):
            self.runner.run("remaining", approval)
        p.write_json(approval, {**new_evidence, "prior_orientation_approval_sha256": p.digest(parent_approval.read_bytes())})
        self.runner.run("remaining", approval)
        report = json.loads((self.runner.dir / "public.json").read_bytes())
        self.assertEqual((self.project.sent, self.project.dispatches, len(self.project.captures)), (14, 14, 14))
        self.assertEqual(self.runner.parent_path.read_bytes(), original)
        self.assertEqual(report["previous_attempt"]["statuses"]["P3.2"], "failed")
        self.assertEqual(report["cumulative_provider_observed_usd"], "0.0014")
        self.assertEqual((report["attempt_dispatches"], report["receipts_reconciled"],
                          report["cumulative_receipts_reconciled"]), (9, 9, 14))
        self.assertEqual(report["ledger_last_read"]["accounted_usd"], "0.014")
        self.assertEqual(report["attempt_accounted_usd"], "0.009")
        self.assertFalse(report["rows"][0]["human_reviewed"])
        self.assertTrue(report["rows"][0]["prior_identical_orientation_approved"])
        self.assertNotIn(self.project.account, json.dumps(report))
        self.assertNotIn("gen-", json.dumps(report))
        self.assertEqual(report["source_commit"], self.project.candidate()["source_commit"])
        with self.assertRaisesRegex(p.Stop, "original_congelado"):
            p.Pilot(self.project, self.sim, self.dir)
        with self.assertRaisesRegex(p.Stop, "ensaio_desconhecido"):
            p.Pilot(self.project, self.sim, self.dir, attempt="e01-q2")
        with self.assertRaisesRegex(p.Stop, "ja_iniciado"):
            self.additional().run("canary")
        with self.assertRaisesRegex(p.Stop, "ja_iniciado"):
            self.additional().run("remaining", parent_approval)
        self.assertEqual(self.project.sent, 14)

    def test_additional_requires_actual_receipts_and_original_approval(self):
        approval = self.prepare_parent()
        with self.assertRaisesRegex(p.Stop, "indique_aprovacao_original"):
            self.additional()
        approval_bytes = approval.read_bytes()
        approval.write_bytes(approval_bytes + b" ")
        with self.assertRaisesRegex(p.Stop, "aprovacao_original_divergente"):
            self.additional(approval)
        approval.write_bytes(approval_bytes)
        name, capture = self.project.captures.pop("P2.2")
        with self.assertRaisesRegex(p.Stop, "quantidade_de_capturas_divergente"):
            self.additional(approval).run("canary")
        self.project.captures["P2.2"] = name, {**capture, "id": "alterado"}
        with self.assertRaisesRegex(p.Stop, "capturas_do_piloto_divergentes"):
            self.additional(approval).run("canary")
        self.assertEqual(self.project.sent, 5)

    def test_additional_validates_database_global_balance_holds_rows_and_tariff(self):
        approval = self.prepare_parent()
        budget = self.project.budget
        for changed, reason in [({"cluster":"other"}, "banco"), ({"entries":6}, "atividade"),
                                ({"holds":1}, "atividade"), ({"accounted_usd":"0.1"}, "provisao")]:
            with self.subTest(changed=changed):
                self.project.budget = lambda: {**budget(), **changed}
                with self.assertRaisesRegex(p.Stop, reason):
                    self.additional(approval).run("canary")
        self.project.budget = budget
        self.project.rate = "1.00"
        with self.assertRaisesRegex(p.Stop, "tarifario"):
            self.additional(approval).run("canary")
        self.project.rate = "0.50"
        last = list(self.project.records.values())[-1]
        last["reason"] = "outro"
        with self.assertRaisesRegex(p.Stop, "rodada_duravel_divergente"):
            self.additional(approval).run("canary")
        self.assertEqual(self.project.sent, 5)

    def test_additional_lost_202_never_reposts_even_in_another_directory(self):
        approval = self.prepare_parent()
        self.sim.lose_receipt = True
        self.runner = self.additional(approval)
        with self.assertRaises(OSError):
            self.runner.run("canary")
        self.assertEqual(self.runner.journal["turns"]["P1.1"]["status"], "inconclusive")
        with self.assertRaisesRegex(p.Stop, "ja_iniciado"):
            self.additional().run("canary")
        other = self.dir / "outra-saida"
        other.mkdir()
        (other / "journal.json").write_bytes(self.runner.parent_path.read_bytes())
        for path in self.dir.glob("receipt-*.json"):
            (other / path.name).write_bytes(path.read_bytes())
        with self.assertRaisesRegex(p.Stop, "atividade_nao_conciliada"):
            p.Pilot(self.project, self.sim, other, attempt=p.ADDITIONAL, parent_approval=approval).run("canary")
        self.assertEqual((self.project.sent, self.project.dispatches), (6, 5))

    def test_archived_child_pre_ingress_intent_still_blocks_purchase(self):
        approval = self.prepare_parent()
        self.runner = self.additional(approval)
        with patch.object(self.sim, "send", side_effect=OSError("sem confirmação de ingresso")) as send:
            with self.assertRaises(OSError):
                self.runner.run("canary")
            send.assert_called_once()
        first = self.runner.journal["turns"]["P1.1"]
        self.assertEqual(first["status"], "inconclusive")
        self.runner.dir.rename(self.dir / "filho-arquivado")
        with self.assertRaisesRegex(p.Stop, "intencao_adicional_ja_registrada"):
            self.additional(approval).run("canary")
        self.assertEqual((self.project.sent, self.project.dispatches), (5, 5))
        marker = self.runner.marker
        self.assertEqual(marker.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(marker.read_bytes())["p1_key"], first["key"])
        with self.assertRaisesRegex(p.Stop, "ensaio_original_congelado"):
            p.Pilot(self.project, self.sim, self.dir)

    def test_cli_serializes_same_uid_with_different_home_environments(self):
        tmp = self.dir
        system_home, other_home = tmp / "usuario", tmp / "outro-home"
        state = Path(".local/state/cloudwalk-e01") / self.project.project
        self.dir = system_home / state
        self.dir.mkdir(mode=0o700, parents=True)
        self.sim = FakeSimulator(self.project, self.dir)
        self.runner = p.Pilot(self.project, self.sim, self.dir)
        approval = self.prepare_parent()
        other_dir = other_home / state
        shutil.copytree(self.dir, other_dir)
        other_sim = FakeSimulator(self.project, other_dir / p.ADDITIONAL)
        other_sim.capture_prefix = "outro-"
        original_send = self.sim.send
        second = []

        def interleave(channel, body, key):
            errors = io.StringIO()
            with patch.dict(os.environ, HOME=str(other_home)), redirect_stderr(errors):
                second.append((p.main(), errors.getvalue().strip()))
            return original_send(channel, body, key)

        argv = ["pilot.py", "canary", "--attempt", p.ADDITIONAL, "--project", self.project.project,
                "--base-url", self.project.base, "--parent-approval", str(approval)]
        with (patch.dict(os.environ, HOME=str(system_home)), patch.object(p.sys, "argv", argv),
              patch("pwd.getpwuid", return_value=SimpleNamespace(pw_dir=str(system_home))) as user,
              patch.object(p.signal, "signal"), patch.object(p, "LocalProject", return_value=self.project),
              patch.object(p, "Simulator", side_effect=[self.sim, other_sim]),
              patch.object(self.sim, "send", side_effect=interleave), redirect_stdout(io.StringIO())):
            result = p.main()
        self.assertEqual((self.project.sent, self.project.dispatches), (6, 6))
        self.assertEqual(result, 0)
        self.assertEqual(second, [(1, "piloto_em_uso")])
        self.assertEqual([args.args for args in user.call_args_list], [(os.getuid(),), (os.getuid(),)])
        self.assertFalse((other_dir / p.ADDITIONAL).exists())

    def test_additional_reentry_checks_parent_digest_and_candidate(self):
        approval = self.prepare_parent()
        self.runner = self.additional(approval)
        self.runner.run("canary")
        original = self.runner.parent_path.read_bytes()
        self.runner.parent_path.write_bytes(original + b" ")
        with self.assertRaisesRegex(p.Stop, "journal_original_divergente"):
            self.additional()
        self.runner.parent_path.write_bytes(original)
        self.project.candidate = lambda: {"source_commit":"other", "image":"other"}
        with self.assertRaisesRegex(p.Stop, "baseline_ou_candidata_divergente"):
            self.additional()
        self.assertEqual(self.project.sent, 6)

    def test_additional_rejects_old_provider_id(self):
        approval = self.prepare_parent()
        self.runner = self.additional(approval)
        self.runner.run("canary")
        original_id = self.project.captures["P2.2"][1]["id"]
        self.project.fixed_response = original_id
        with self.assertRaisesRegex(p.Stop, "id_do_provedor_ausente_ou_duplicado"):
            self.runner.run("remaining", self.approval(directory=self.dir / "novo-p1"))
        report = p.public_report(self.runner.journal)
        self.assertEqual(report["ambiguous_provider_ids"], 1)
        self.assertIsNone(report["cumulative_provider_observed_usd"])
        self.assertEqual(self.project.sent, 7)

    def test_additional_financial_conflict_stops_before_p22(self):
        approval = self.prepare_parent()
        self.runner = self.additional(approval)
        self.runner.run("canary")
        self.project.next_charge = {"credits": "0.01", "cost":"0.50", "cost_unit":"USD"}
        with self.assertRaisesRegex(p.Stop, "valores_da_captura_divergentes"):
            self.runner.run("remaining", self.approval(directory=self.dir / "novo-p1"))
        self.assertEqual(self.project.sent, 7)
        self.assertNotIn("P2.2", self.runner.journal["turns"])

    def test_additional_checks_money_before_post_and_uses_the_same_project_lock(self):
        self.project.reservation = "0.999"
        approval = self.prepare_parent()
        with p.exclusive(self.dir):
            with self.assertRaisesRegex(p.Stop, "piloto_em_uso"), p.exclusive(self.dir):
                pass
            with self.assertRaisesRegex(p.Stop, "limite_do_piloto"):
                self.additional(approval).run("canary")
        self.assertEqual(self.project.sent, 5)

    def test_additional_checks_active_tariff_again_immediately_before_post(self):
        approval = self.prepare_parent()
        self.runner = self.additional(approval)
        self.sim.prepare = lambda: setattr(self.project, "rate", "0.80")
        with self.assertRaisesRegex(p.Stop, "tarifario_divergente"):
            self.runner.run("canary")
        self.assertEqual(self.project.sent, 5)

    def test_canary_stops_reentry_and_missing_approval(self):
        self.runner.run("canary")
        self.assertEqual(self.project.sent, 1)
        self.assertTrue(self.project.stopped())
        other = p.Pilot(self.project, self.sim, self.dir)
        with self.assertRaises(p.Stop):
            other.run("canary")
        with self.assertRaises(p.Stop):
            other.run("remaining")
        self.assertEqual(self.project.sent, 1)

    def test_uncertain_receipt_persists_and_never_reposts(self):
        self.sim.lose_receipt = True
        with self.assertRaises(OSError):
            self.runner.run("canary")
        self.assertEqual(self.runner.journal["turns"]["P1.1"]["status"], "inconclusive")
        with self.assertRaises(p.Stop):
            p.Pilot(self.project, self.sim, self.dir).run("canary")
        self.assertEqual((self.project.sent, self.project.dispatches), (1,0))

    def test_timeout_stops_without_new_attempt(self):
        self.sim.delay = True
        with self.assertRaisesRegex(p.Stop, "timeout"):
            self.runner.run("canary")
        self.assertEqual(self.project.stops, 1)
        self.assertEqual(json.loads((self.dir / "public.json").read_bytes())["timeouts"], 1)
        with self.assertRaises(p.Stop):
            self.runner.run("remaining")
        self.assertEqual(self.project.dispatches, 1)

    def test_private_receipt_and_cache_mismatch_fail_closed(self):
        self.runner.run("canary")
        path = self.approval()
        self.edit_evidence(path, "capture", lambda cap: cap["usage"].pop("prompt_tokens_details"))
        with self.assertRaisesRegex(p.Stop, "desconto_cache_divergente"):
            self.runner.run("remaining", path)
        path = self.approval()
        for name, field in (("capture", "usage"), ("provider_record","id")):
            approval = json.loads(path.read_bytes())
            file = self.dir / approval[name]["file"]
            original = file.read_bytes()
            data = json.loads(original)
            if field == "id":
                data[field] = "other"
            else:
                del data["usage"]["prompt_tokens_details"]["cached_tokens"]
            p.write_json(file, data)
            approval[name]["sha256"] = p.digest(file.read_bytes())
            p.write_json(path, approval)
            with self.assertRaises((KeyError,p.Stop)):
                self.runner.run("remaining", path)
            self.assertEqual(self.project.dispatches, 1)
            file.write_bytes(original)
            path = self.approval()

    def test_rounded_individual_record_keeps_interval_and_stops_if_uncertain(self):
        self.runner.run("canary")
        path = self.approval()
        approval = json.loads(path.read_bytes())
        record_path = self.dir / "provider_record.json"
        record = json.loads(record_path.read_bytes())
        record.update(precision="nearest", quantum="0.01", precision_source="regra declarada pela fonte de teste")
        def check_record():
            p.write_json(record_path, record)
            approval["provider_record"]["sha256"] = p.digest(record_path.read_bytes())
            p.write_json(path, approval)
            return p.reconcile(self.runner.journal["turns"]["P1.1"], path, self.runner.journal["binding"])
        result = check_record()
        self.assertEqual((result["provider_usd_min"], result["provider_usd_max"]), ("0.00005", "0.00015"))
        record["amount"] = "0.10"
        with self.assertRaisesRegex(p.Stop, "supera"):
            check_record()

    def test_changed_database_is_blocked(self):
        self.runner.run("canary")
        path = self.approval()
        self.project.project = "e01-other"
        with self.assertRaisesRegex(p.Stop, "banco"):
            self.runner.run("remaining", path)
        self.assertEqual(self.project.sent, 1)

    def test_all_nine_turns_sanitized_report(self):
        self.runner.run("canary")
        self.runner.run("remaining", self.approval())
        self.assertEqual((self.project.stops, self.project.sent), (9,9))
        report = (self.dir / "public.json").read_text()
        public = json.loads(report)
        self.assertEqual(public["receipts_reconciled"], 9)
        self.assertEqual([r["human_reviewed"] for r in public["rows"]], [True] + [False] * 8)
        self.assertTrue(all(r["financially_reconciled"] for r in public["rows"]))
        row = self.runner.journal["turns"]["P2.1"]["reconciliation"]
        saved = self.dir / row["capture_file"]
        self.assertEqual(row["capture_sha256"], p.digest(saved.read_bytes()))
        self.assertEqual(saved.stat().st_mode & 0o777, 0o600)
        self.assertEqual((public["dispatch_authorizations"], public["distinct_provider_ids_in_ledger_usage"]), (9, 9))
        for private in ("simulator-private", "gen-", "fixture-account", "Onde consulto", "secret", "message_ids", "summary"):
            self.assertNotIn(private, report)
        with self.assertRaises(p.Stop):
            self.runner.run("remaining", self.approval())
        self.assertEqual(self.project.sent, 9)

    def edit_evidence(self, approval_path, field, change):
        approval = json.loads(approval_path.read_bytes())
        path = self.dir / approval[field]["file"]
        data = json.loads(path.read_bytes())
        change(data)
        if field == "capture":
            filename, _ = self.project.captures["P1.1"]
            self.project.captures["P1.1"] = filename, data
        p.write_json(path, data)
        approval[field]["sha256"] = p.digest(path.read_bytes())
        p.write_json(approval_path, approval)

    def test_conflicting_cost_unknown_unit_or_credits_blocks_p2(self):
        self.runner.run("canary")
        for fields, reason in [
            ({"cost":"0.90","cost_unit":"USD"}, "valor_do_provedor_divergente"),
            ({"cost":"0.0001"}, "custo_sem_unidade_documentada"),
            ({"credits":"0.01","cost":"0.002","cost_unit":"USD"}, "valores_da_captura_divergentes"),
        ]:
            with self.subTest(fields=fields):
                path = self.approval()
                self.edit_evidence(path, "capture", lambda cap: cap["usage"].update(fields))
                with self.assertRaisesRegex(p.Stop, reason):
                    self.runner.run("remaining", path)
                self.assertEqual(set(self.runner.journal["turns"]), {"P1.1"})

    def test_invalid_filtered_field_blocks_even_with_valid_credits_and_documented_unit(self):
        self.runner.run("canary")
        for marker in ("cost", "credits", "cost_unit"):
            with self.subTest(marker=marker):
                path = self.approval(source="provider_api_receipt")
                self.edit_evidence(path, "capture", lambda cap: cap["usage"].update(invalid_fields=[marker]))
                approval = json.loads(path.read_bytes())
                self.edit_evidence(path, "provider_record", lambda row: row.update(
                    original=approval["capture"], cost_unit="USD", cost_unit_source="documento de teste"))
                with self.assertRaisesRegex(p.Stop, "campo_financeiro_invalido"):
                    self.runner.run("remaining", path)
                self.assertEqual(self.project.sent, 1)

    def test_p21_missing_charge_stops_before_p22_post_and_persists_journal(self):
        self.project.next_charge = {}
        self.runner.run("canary")
        with self.assertRaisesRegex(p.Stop, "valor_ausente_no_recibo_da_api"):
            self.runner.run("remaining", self.approval())
        saved = json.loads((self.dir / "journal.json").read_bytes())
        self.assertEqual(list(saved["turns"]), ["P1.1", "P2.1"])
        self.assertEqual((self.project.sent, self.project.dispatches), (2, 2))
        self.assertTrue(self.project.stopped())

    def test_p21_conflicting_credits_and_cost_stops_before_p22(self):
        self.project.next_charge = {"credits": "0.01", "cost": "0.50", "cost_unit": "USD"}
        self.runner.run("canary")
        with self.assertRaisesRegex(p.Stop, "valores_da_captura_divergentes"):
            self.runner.run("remaining", self.approval())
        self.assertEqual((self.project.sent, self.project.dispatches), (2, 2))
        with self.assertRaises(p.Stop):
            p.Pilot(self.project, self.sim, self.dir).run("remaining", self.approval())
        self.assertEqual(self.project.sent, 2)

    def test_p21_over_provision_stops_before_p22(self):
        self.project.next_charge = {"credits": "0.9"}
        self.runner.run("canary")
        with self.assertRaisesRegex(p.Stop, "gasto_supera_valor_contabilizado"):
            self.runner.run("remaining", self.approval())
        self.assertEqual((self.project.sent, self.project.dispatches), (2, 2))

    def test_prior_capture_blocks_first_dispatch(self):
        self.project.captures["unknown"] = "receipt-" + uid() + ".json", {"id": "unexpected"}
        with self.assertRaisesRegex(p.Stop, "quantidade_de_capturas_divergente"):
            self.runner.run("canary")
        self.assertEqual((self.project.sent, self.project.dispatches), (0, 0))

    def test_approved_p1_must_match_original_in_consumer_before_p2(self):
        self.runner.run("canary")
        approval = self.approval()
        self.project.captures["P1.1"][1]["id"] = "other"
        with self.assertRaisesRegex(p.Stop, "capturas_do_piloto_divergentes"):
            self.runner.run("remaining", approval)
        self.assertEqual(self.project.sent, 1)

    def test_unknown_without_usage_has_authorization_outside_ledger_id_coverage(self):
        def unknown(case, seq):
            row = copy.deepcopy(self.project.record)
            row.update(state="unknown", usage=None)
            return row
        self.project.turn = unknown
        with self.assertRaisesRegex(p.Stop, "terminal_sem_resultado"):
            self.runner.run("canary")
        report = p.public_report(self.runner.journal)
        self.assertEqual(report["dispatch_authorizations"], 1)
        self.assertTrue(self.project.captures["P1.1"][1]["id"])
        self.assertEqual(report["distinct_provider_ids_in_ledger_usage"], 0)
        self.assertFalse(report["rows"][0]["provider_id_in_ledger_usage"])

    def test_metric_rounding_and_documented_unit_in_capture(self):
        self.runner.run("canary")
        path = self.approval()
        self.edit_evidence(path, "capture", lambda cap: cap["usage"].update(cost="0.000", credits="0.01"))
        self.edit_evidence(path, "provider_record", lambda row: row.update(
            cost_unit="USD", cost_unit_source="unidade declarada no documento de teste",
            capture_precision={"cost":{"precision":"nearest", "quantum":"0.001","precision_source":"fonte de teste"}}))
        self.runner.reconcile_turn("P1.1", path)
        self.assertEqual(p.public_report(self.runner.journal)["rows"][0]["provider_observed_usd"],"0.0001")

    def test_truncation_excludes_upper_endpoint_for_portal_and_capture(self):
        self.runner.run("canary")
        truncated = {"precision": "truncated", "quantum": "0.0001", "precision_source": "regra de teste"}
        for location, reason in (("portal", "valor_do_provedor_divergente"), ("capture", "valores_da_captura_divergentes")):
            with self.subTest(location=location):
                path = self.approval()
                raw = {"cost": "0.0001", "cost_unit": "USD"}
                if location == "capture":
                    raw["credits"] = "0.02"
                self.edit_evidence(path, "capture", lambda cap: cap["usage"].update(raw))
                self.edit_evidence(path, "provider_record", lambda row: row.update(
                    unit="USD", amount="0.0002", capture_precision={"cost": truncated}))
                with self.assertRaisesRegex(p.Stop, reason):
                    self.runner.run("remaining", path)
                self.assertEqual(self.project.sent, 1)
                self.assertNotIn("P2.1", self.runner.journal["turns"])

        path = self.approval()
        self.edit_evidence(path, "capture", lambda cap: cap["usage"].update(cost="0.0001", cost_unit="USD"))
        for compatible in ("0.0001", "0.00019999"):
            self.edit_evidence(path, "provider_record", lambda row: row.update(
                unit="USD", amount=compatible, capture_precision={"cost": truncated}))
            self.runner.reconcile_turn("P1.1", path)
            self.assertEqual(p.public_report(self.runner.journal)["rows"][0]["provider_observed_usd"], compatible)

    def test_api_receipt_validates_actual_monetary_field(self):
        self.runner.run("canary")
        path = self.approval(source="provider_api_receipt")
        self.edit_evidence(path, "provider_record", lambda r: r.update(field="cost"))
        with self.assertRaisesRegex(p.Stop, "valor_ausente"):
            self.runner.run("remaining", path)
        path = self.approval(source="provider_api_receipt")
        self.runner.run("remaining", path)
        self.assertEqual(self.runner.journal["turns"]["P1.1"]["reconciliation"]["source_type"], "provider_api_receipt")

    def test_mismatched_account_conversion_original_and_identical_evidence(self):
        self.runner.run("canary")
        for change, reason in [
            (lambda r: r.update(account_ref="other"), "conta_divergente"),
            (lambda r: r.update(conversion_account_ref="other"), "conversao_sem_vinculo"),
            (lambda r: r["original"].update(sha256="0"*64), "evidencia_alterada"),
        ]:
            with self.subTest(reason=reason):
                path = self.approval()
                self.edit_evidence(path, "provider_record", change)
                with self.assertRaisesRegex(p.Stop, reason):
                    self.runner.run("remaining", path)
        approval = json.loads(path.read_bytes())
        approval["provider_record"] = approval["capture"]
        p.write_json(path, approval)
        with self.assertRaisesRegex(p.Stop,"extracao_igual"):
            self.runner.run("remaining",path)
        self.assertEqual(self.project.sent,1)

    def test_durable_same_database_same_totals_but_changed_p1(self):
        self.runner.run("canary")
        row = self.project.record
        for field in ("request_id", "request_sha256", "result_sha256", "account_ref", "usage", "accounted_usd"):
            with self.subTest(field=field):
                path = self.approval()
                old = row[field]
                row[field] = "other"
                with self.assertRaisesRegex(p.Stop, "rodada_duravel_divergente"):
                    self.runner.run("remaining", path)
                self.assertNotIn("P2.1",self.runner.journal["turns"])
                row[field] = old

    def test_reconcile_failed_billed_turn_without_proposal(self):
        def failed(case, seq):
            row = copy.deepcopy(self.project.record)
            row.update(state="failed", result_id=None, result_sha256=None, result_ok=None,
                       disposition=None, integration="failed", reason="invalid_decision")
            return row
        self.project.turn = failed
        with self.assertRaisesRegex(p.Stop,"terminal_sem_resultado"):
            self.runner.run("canary")
        path = self.approval()
        self.runner.reconcile_turn("P1.1", path)
        self.runner.reconcile_turn("P1.1", path)
        report = p.public_report(self.runner.journal)
        self.assertEqual(report["receipts_reconciled"],1)
        self.assertTrue(report["rows"][0]["financially_reconciled"])
        self.assertFalse(report["rows"][0]["human_reviewed"])
        self.assertEqual(report["rows"][0]["status"], "failed")
        with self.assertRaises(p.Stop):
            self.runner.run("remaining",path)
        self.assertEqual(self.project.sent,1)

    def test_factual_failure_can_be_reconciled_without_releasing_p2(self):
        self.sim.history = lambda case: []
        with self.assertRaisesRegex(p.Stop, "sequencias_divergentes"):
            self.runner.run("canary")
        path = self.approval(source="provider_api_receipt")
        self.runner.reconcile_turn("P1.1", path)
        self.assertEqual(self.runner.journal["turns"]["P1.1"]["status"], "failed")
        with self.assertRaises(p.Stop):
            self.runner.run("remaining", path)
        self.assertEqual(self.project.sent,1)

    def test_duplicate_provider_id_stops_and_prevents_double_counting(self):
        self.project.fixed_response = "gen-same"
        self.runner.run("canary")
        with self.assertRaisesRegex(p.Stop, "duplicado"):
            self.runner.run("remaining", self.approval())
        self.assertEqual(self.project.sent,2)
        self.assertNotIn("P2.2",self.runner.journal["turns"])
        report = p.public_report(self.runner.journal)
        self.assertEqual((report["receipts_reconciled"],report["distinct_provider_ids_in_ledger_usage"],
                          report["ambiguous_provider_ids"]), (0,1,1))
        self.assertIsNone(report["sum_of_reconciled_receipts_usd"])
        with self.assertRaisesRegex(p.Stop,"duplicado"):
            self.runner.reconcile_turn("P1.1",self.approval())

    def test_omitted_cache_keeps_observation_null_and_discount_zero(self):
        self.project.cached = 0
        self.runner.run("canary")
        for invalid in (None, {}, {"cached_tokens":False}, {"cached_tokens":-1}):
            path = self.approval()
            self.edit_evidence(path, "capture", lambda cap: cap["usage"].update(prompt_tokens_details=invalid))
            with self.assertRaisesRegex(p.Stop, "cache_invalido"):
                self.runner.run("remaining",path)
        path = self.approval()
        self.edit_evidence(path, "capture", lambda cap: cap["usage"].pop("prompt_tokens_details"))
        self.runner.run("remaining",path)
        row = p.public_report(self.runner.journal)["rows"][0]
        self.assertTrue(row["cache_capture_reviewed"])
        self.assertIsNone(row["cached_tokens_observed"])
        self.assertEqual(row["usage"]["cached_input_tokens"],0)

    def test_wrong_case_brand_source_resolution_and_handoff(self):
        self.runner.run("canary")
        self.runner.run("remaining", self.approval())
        for key, mutation in [
            ("P1.1", lambda e: e["ledger"].update(case_id=uid())),
            ("P1.1", lambda e: e["ledger"].update(brand_id=uid())),
            ("P2.1", lambda e: e["ledger"]["metadata"]["source_refs"][0].update(id="aurora.manual")),
            ("P2.1", lambda e: e["ledger"].update(status="resolved")),
            ("P2.2", lambda e: e["history"][-2].update(text="Ainda não resolveu.")),
            ("P3.2", lambda e: e["ledger"]["proposal"]["payload"].update(message_ids=[])),
            ("P3.2", lambda e: e["ledger"]["handoff"].update(summary="resumo inventado")),
            ("P4.1", lambda e: e["ledger"]["metadata"]["handoff_rule"].update(reason="no_guidance")),
        ]:
            with self.subTest(key=key):
                item = copy.deepcopy(self.runner.journal["turns"][key])
                mutation(item)
                label, number = key.split(".")
                with self.assertRaises(p.Stop):
                    p.evaluate(label, int(number), item["receipt"], item["history"], item["ledger"])


class CandidateTests(unittest.TestCase):
    def test_consumer_must_contain_committed_q1_code_and_graceful_signal(self):
        project = p.LocalProject.__new__(p.LocalProject)
        project.ids = {"mock": "fixture"}
        project.stopped = lambda: True
        name = "integration/e01_backend.py"
        commit = "b" * 40
        changed = b""
        image_source = b"codigo antigo"
        signal = "SIGINT"

        def git(argv, timeout):
            command = argv[3]
            return {"rev-parse": commit.encode(), "diff": changed, "ls-tree": name.encode(),
                    "show": b"codigo revisado"}[command]

        def docker(*args):
            if args[0] == "cp":
                Path(args[-1]).write_bytes(image_source)
                return ""
            return signal if args[2] == "{{.Config.StopSignal}}" else "imagem-de-teste"

        project.docker = docker
        with patch.object(p.subprocess, "check_output", side_effect=git):
            with self.assertRaisesRegex(p.Stop, "candidata_sem_ajuste_q1"):
                project.candidate()
            changed = name.encode()
            with self.assertRaisesRegex(p.Stop, "codigo_do_consumer_divergente"):
                project.candidate()
            image_source = b"codigo revisado"
            self.assertEqual(project.candidate(), {"source_commit":commit, "image":"imagem-de-teste"})
            signal = "SIGTERM"
            with self.assertRaisesRegex(p.Stop, "consumer_sem_sigint"):
                project.candidate()


class HttpSessionTests(unittest.TestCase):
    def test_real_cookie_csrf_and_identity_headers(self):
        calls = []
        class Rails(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, value, cookie=False):
                self.send_response(200)
                if cookie:
                    self.send_header("Set-Cookie","test=session; Path=/")
                self.end_headers()
                self.wfile.write(json.dumps(value).encode())

            def do_GET(self):
                calls.append(self.path)
                if self.path.endswith("/session"):
                    self.reply({"csrf_token":"fresh"}, cookie=True)
                else:
                    self.reply({"items":[],"next_cursor":None})

            def do_POST(self):
                calls.append((self.path, self.headers.get("Cookie"), self.headers.get("X-CSRF-Token"),
                              self.headers.get("X-Simulator-Session-Id"), self.headers.get("Idempotency-Key")))
                self.reply({"user":{"role":"simulator","id":"synth"}} if self.path.endswith("/session") else {"ok":True})

        with HTTPServer(("127.0.0.1",0), Rails) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                sim = p.Simulator("http://127.0.0.1:" + str(server.server_port))
                sim.prepare()
                sim.send("channel", {"text":"teste"}, "key")
            finally:
                server.shutdown()
                thread.join()
        self.assertEqual(calls[-1], ("/api/v1/simulator/channels/channel/messages","test=session","fresh","synth","key"))
        self.assertEqual(len([r for r in calls if isinstance(r,tuple)]),2)


if __name__ == "__main__":
    unittest.main()
