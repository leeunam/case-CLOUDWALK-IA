"""Exercita orquestração e falhas sem conectar ao provedor."""
import copy
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
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

    def stopped(self):
        return not self.active

    def start(self):
        self.active = True
        self.dispatches += 1

    def stop(self):
        self.stops += 1
        self.active = False

    def budget(self):
        return {"dispatches": self.dispatches, "entries": self.sent, "accounted_usd": str(self.dispatches * .001),
                "holds": 0, "open_turns": 0, "database": "example", "oid": "1", "cluster": "example"}

    def turn(self, case, seq):
        return copy.deepcopy(self.records.get((case, seq)))


class FakeSimulator:
    def __init__(self, project, directory):
        self.project = project
        self.directory = directory
        self.lose_receipt = False
        self.delay = False
        self.channel_id = uid()

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
            "account_ref": self.project.account, "mode": "feita_bounded_public", "accounted_usd":"0.001", "reserved_usd":"0.755400000000",
            "usage":{"input_tokens":10,"cached_input_tokens":self.project.cached,"output_tokens":3,
                     "provider_response_id":self.project.fixed_response or "gen-" + uid()},
            "started_at": p.now(),
        }
        self.project.records[(self.receipt["case_id"],2*n-1)] = self.project.record
        return self.receipt

    def history(self, case):
        return self.messages


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.project = FakeProject()
        self.sim = FakeSimulator(self.project, self.dir)
        self.runner = p.Pilot(self.project, self.sim, self.dir, timeout=.03)

    def approval(self, turn="P1.1", source="provider_portal"):
        row = self.runner.journal["turns"][turn]["ledger"]
        resp = row["usage"]["provider_response_id"]
        capture = {"id":resp, "model":p.MODEL, "status":200, "usage":{"prompt_tokens":10,
                   "completion_tokens":3, "total_tokens":13, "prompt_tokens_details":{"cached_tokens":row["usage"]["cached_input_tokens"]}}, "request_sha256":"0"*64,
                   "started_at":p.now(), "finished_at":p.now()}
        record = {"id":resp, "source":"extrato de teste", "precision":"exact", "amount":"0.01", "unit":"credits",
                  "usd_per_credit":"0.01","conversion_source":"exemplo de teste","observed_at":p.now()}
        original = self.dir / "portal.txt"
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
            file = self.dir / (name + ".json")
            p.write_json(file, data)
            approval[name] = {"file":file.name, "sha256":p.digest(file.read_bytes())}
        dest = self.dir / "approval.json"
        p.write_json(dest, approval)
        return dest

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
        self.assertEqual(public["receipts_reconciled"], 1)
        self.assertEqual((public["dispatch_authorizations"], public["provider_calls_observed_distinct"]), (9, 9))
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

    def test_metric_rounding_and_documented_unit_in_capture(self):
        self.runner.run("canary")
        path = self.approval()
        self.edit_evidence(path, "capture", lambda cap: cap["usage"].update(cost="0.000", credits="0.01"))
        self.edit_evidence(path, "provider_record", lambda row: row.update(
            cost_unit="USD", cost_unit_source="unidade declarada no documento de teste",
            capture_precision={"cost":{"precision":"nearest", "quantum":"0.001","precision_source":"fonte de teste"}}))
        self.runner.reconcile_turn("P1.1", path)
        self.assertEqual(p.public_report(self.runner.journal)["rows"][0]["provider_observed_usd"],"0.0001")

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
        self.assertEqual((report["receipts_reconciled"],report["provider_calls_observed_distinct"],
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
