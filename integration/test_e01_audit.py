import hashlib
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from e01_audit import AuditedPost
from e01_backend import InferenceFailure, LunaBackend


class E01AuditTest(unittest.TestCase):
    def test_captures_only_financial_fields_and_preserves_decimal_precision(self):
        raw = b'''{"id":"response-e01","model":"openai/gpt-5.6-luna","usage":{
          "prompt_tokens":80,"completion_tokens":22,"credits":0.12345678901234567890123456,
          "cost":"0.00034","cost_unit":"USD","prompt_tokens_details":{"cached_tokens":0,
          "cache_creation_input_tokens":1,"content":"FORBIDDEN"},"private":"FORBIDDEN"},
          "choices":[{"message":{"content":"FORBIDDEN"}}],"error":{"message":"FORBIDDEN"}}'''
        post = Mock(return_value=(200, raw))
        body = b"PRIVATE-INPUT"
        with tempfile.TemporaryDirectory() as directory:
            audited = AuditedPost(post, directory)
            self.assertEqual(audited("/route", {"Authorization": "SECRET"}, body, deadline=4.0), (200, raw))
            files = list(Path(directory).iterdir())
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].stat().st_mode & 0o777, 0o600)
            proof = files[0].read_text()
        for forbidden in ("FORBIDDEN", "SECRET", "PRIVATE-INPUT", "choices", "error", "content"):
            self.assertNotIn(forbidden, proof)
        report = json.loads(proof, parse_float=Decimal)
        self.assertEqual(report["status"], 200)
        self.assertEqual(report["id"], "response-e01")
        self.assertEqual(report["model"], "openai/gpt-5.6-luna")
        self.assertEqual(report["request_sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(report["usage"], {
            "prompt_tokens": 80, "completion_tokens": 22,
            "credits": Decimal("0.12345678901234567890123456"), "cost": "0.00034", "cost_unit": "USD",
            "prompt_tokens_details": {"cached_tokens": 0, "cache_creation_input_tokens": 1},
        })
        self.assertTrue(report["started_at"].endswith("+00:00"))
        self.assertGreaterEqual(report["finished_at"], report["started_at"])

    def test_marks_invalid_present_cost_credits_and_unit_without_saving_external_values(self):
        for raw_usage, invalid in [
            ({"credits": "0.1", "cost": True, "cost_unit": "PRIVATE"}, ["cost", "cost_unit"]),
            ({"credits": {"private": "PRIVATE"}, "cost": "0.1", "cost_unit": None}, ["credits", "cost_unit"]),
            ({"credits": None}, ["credits"]),
        ]:
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                raw = json.dumps({"usage": raw_usage}).encode()
                AuditedPost(Mock(return_value=(200, raw)), directory)("/route", {}, b"body", deadline=2)
                receipt, = Path(directory).iterdir()
                self.assertEqual(receipt.stat().st_mode & 0o777, 0o600)
                proof = receipt.read_text()
                self.assertNotIn("PRIVATE", proof)
                usage = json.loads(proof)["usage"]
                self.assertEqual(usage["invalid_fields"], invalid)
                if raw_usage.get("credits") == "0.1":
                    self.assertEqual(usage["credits"], "0.1")

    def test_audit_write_failure_after_post_is_ambiguous_with_no_second_post(self):
        post = Mock(return_value=(200, b"{}"))
        with tempfile.TemporaryDirectory() as parent:
            directory = Path(parent) / "private"
            directory.mkdir(mode=0o700)
            backend = LunaBackend("dummy", transport=AuditedPost(post, directory))
            directory.rmdir()
            request = {"payload": {"history": [], "classification": {"category": "pix"}}}
            with self.assertRaisesRegex(InferenceFailure, "transport_ambiguous") as error:
                backend.infer(request, {}, timeout_s=2.0)
        self.assertIsNone(error.exception.usage)
        post.assert_called_once()

    def test_audit_directory_must_be_private_before_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory).chmod(0o755)
            with self.assertRaisesRegex(ValueError, "CLOUDWALK_E01_AUDIT_DIR"):
                AuditedPost(Mock(), directory)
