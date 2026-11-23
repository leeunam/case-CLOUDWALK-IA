import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import transport
from adapter import Adapter, HERE, MODEL, VERSION, c01, decode, request_body, usage_from
from common import decide
from fixture import completion
from pilot import Blocked, Budget, PUBLIC_TARIFF, authorized_cap, identity_digest

IDENTITY = c01.read(HERE / "fixture.json")["identity"]


def hanging_worker(pipe, body, deadline):
    pipe.send(("dispatch", None))
    time.sleep(15)


def setup_limits(**options):
    return {"development_cases": 1, "max_cases": 2, "max_requests": 2, "concurrency": 1, "max_tokens": 128,
            "input_token_ceiling": 8000, "token_limits_confirmed": True, "tariff_verified": True,
            "tariff": PUBLIC_TARIFF, "budget_usd": "1", "usage_cost_unit": "USD", **options}


def budget(settings, has_credential=lambda: True):
    return Budget(settings, Decimal("1"), ["dev", "other-dev"], ["control"], has_credential)


class AdapterTest(unittest.TestCase):
    def setUp(self):
        self.item = {
            "contract_version": VERSION, "id": "dev", "brand": "marca-sintetica", "text": "Um estorno Pix.",
            "catalog": {"version": "1.0.0", "category": {"pix": "Transferência Pix."},
                        "priority": {"basic": "Rotina.", "urgent": "Ação imediata."}},
            "received": {}, "missing": ["category", "priority"],
        }

    def classify(self, response, status=200, **options):
        def gateway(body, deadline, dispatched):
            dispatched()
            return status, response
        fake = Mock(side_effect=gateway)
        observation = Adapter(IDENTITY, "run", "rubrica comum", fake, **options).classify(self.item)
        fake.assert_called_once()
        return observation

    def test_request_uses_only_the_shared_information_and_mask(self):
        self.item.update(received={"category": "pix"}, missing=["priority"],
                         expected={"priority": "urgent"}, rationale="oculto", stratum="oculto")
        request = decode(request_body(self.item, {"category": "pix"}, "rubrica comum", 64))
        schema = request["response_format"]["json_schema"]
        self.assertTrue(schema["strict"])
        self.assertEqual(schema["schema"]["required"], ["priority"])
        self.assertEqual(schema["schema"]["properties"]["priority"]["enum"], ["basic", "urgent", c01.ABSTENTION])
        self.assertEqual(request["model"], MODEL)
        self.assertEqual(request["max_tokens"], 64)
        context = decode(request["messages"][1]["content"])
        self.assertEqual(set(context), {"text", "brand", "catalog", "missing", "received"})
        self.assertEqual(context["catalog"], self.item["catalog"])
        self.assertEqual(context["received"], {"category": "pix"})

    def test_prediction_and_abstention_keep_raw_and_review_in_the_evaluator(self):
        obs = self.classify(completion(MODEL, json.dumps({"category": "pix", "priority": c01.ABSTENTION})))
        self.assertEqual(obs["origin"], "candidate")
        self.assertEqual(obs["questions"], 2)
        self.assertEqual(obs["requests"], 1)
        self.assertIsNone(obs["choices"]["category"]["score"])
        self.assertEqual(obs["choices"]["priority"]["reason"], "explicit")
        decision = decide(self.item, obs, self.item["catalog"], "run")
        self.assertEqual(decision["outcome"], "review")
        self.assertEqual(obs["choices"]["category"]["raw"], "pix")
        self.assertIsNone(decision["fields"]["category"]["applied"])

    def test_channel_value_preserved_in_success_and_review(self):
        self.item.update(received={"category": "pix", "priority": "  "}, missing=["priority"])
        for code in ("basic", c01.ABSTENTION):
            with self.subTest(code=code):
                obs = self.classify(completion(MODEL, json.dumps({"priority": code})))
                self.assertEqual(set(obs["choices"]), {"priority"})
                self.assertEqual(obs["questions"], 1)
                decision = decide(self.item, obs, self.item["catalog"], "run")
                self.assertEqual(decision["fields"]["category"], {"status": "provided", "applied": "pix"})

    def test_catalog_code_missing_malformed_duplicate_and_unsolicited_fields(self):
        for content, reason in (
            ('{"category":"pix","priority":"inventado"}', "invalid_output"),
            ('{"category":"pix"}', "missing_output"),
            ("texto solto", "invalid_output"),
            ('{"category":"pix","priority":"basic","priority":"urgent"}', "invalid_output"),
            ('{"category":"pix","priority":"basic","extra":1}', "invalid_output"),
        ):
            with self.subTest(content=content):
                obs = self.classify(completion(MODEL, content))
                self.assertEqual(obs["choices"]["priority"]["reason"], reason)
                self.assertEqual(decide(self.item, obs, self.item["catalog"], "run")["outcome"], "review")
        obs = self.classify(completion(MODEL, '{"category":"pix","priority":"inventado"}'))
        self.assertEqual(obs["choices"]["priority"]["raw"], "inventado")

    def test_provider_refusal_and_missing_output(self):
        data = {"model": MODEL, "choices": [{"message": {"content": None, "refusal": "recusa simulada"}}]}
        self.assertEqual(self.classify(json.dumps(data).encode())["choices"]["category"]["reason"], "policy")
        data["choices"][0]["message"].pop("refusal")
        self.assertEqual(self.classify(json.dumps(data).encode())["choices"]["category"]["reason"], "missing_output")

    def test_policy_refusal_preserves_raw_fields_and_never_applies_them(self):
        for finish_reason, message, expected in (
            ("stop", {"refusal": "recusa", "content": '{"category":"pix","priority":"urgent"}'}, ("pix", "urgent")),
            ("content_filter", {"content": '{"category":"pix"}'}, ("pix", None)),
            ("content_filter", None, (None, None)),
        ):
            with self.subTest(finish_reason=finish_reason, raw=expected):
                response = {"model": MODEL, "choices": [{"finish_reason": finish_reason, "message": message}]}
                obs = self.classify(json.dumps(response).encode())
                self.assertEqual([obs["choices"][field]["raw"] for field in self.item["missing"]], list(expected))
                for choice in obs["choices"].values():
                    self.assertEqual((choice["status"], choice["reason"]), ("abstained", "policy"))
                decision = decide(self.item, obs, self.item["catalog"], "run")
                self.assertEqual(decision["outcome"], "review")
                self.assertTrue(all(field["applied"] is None for field in decision["fields"].values()))

    def test_ineligible_input_never_dispatches(self):
        transport = Mock()
        candidate = Adapter(IDENTITY, "run", "rubrica", transport)
        self.item.update(received={"category": "inventado"}, missing=["priority"])
        with self.assertRaises(ValueError):
            candidate.classify(self.item)
        transport.assert_not_called()

    def test_returned_model_revision_mismatch_and_unverifiable_model(self):
        obs = self.classify(completion("outro-modelo", '{"category":"pix","priority":"basic"}',
                                       weights_revision="revision-provider"))
        self.assertEqual(obs["returned_model"], "outro-modelo")
        self.assertEqual(obs["weights_revision"], "revision-provider")
        self.assertEqual(obs["choices"]["category"]["reason"], "version_mismatch")
        obs = self.classify(completion(None, '{"category":"pix","priority":"basic"}'))
        self.assertEqual(obs["choices"]["category"]["reason"], "adapter_error")
        self.assertIsNone(obs["returned_model"])

    def test_rate_limit_and_transport_preserve_attempt_and_usage_when_dispatched(self):
        obs = self.classify(b'{"error":{"message":"somente fixture"}}', status=429)
        self.assertEqual(obs["choices"]["priority"]["reason"], "transport")
        self.assertEqual(obs["requests"], 1)
        self.assertIsNone(obs["request_usage"][0]["observed_api_usd"])
        for failure, reason in ((ConnectionError, "transport"), (TimeoutError, "timeout")):
            for sent in (False, True):
                with self.subTest(failure=failure, sent=sent):
                    def fail(body, deadline, dispatched):
                        if sent:
                            dispatched()
                        raise failure
                    gateway = Mock(side_effect=fail)
                    obs = Adapter(IDENTITY, "run", "rubrica", gateway).classify(self.item)
                    gateway.assert_called_once()
                    self.assertEqual(obs["choices"]["category"]["reason"], reason)
                    self.assertEqual(obs["requests"], int(sent))
                    self.assertEqual(len(obs["request_usage"]), int(sent))

    def test_late_success_cannot_use_timeout_delivery_tolerance(self):
        with patch("adapter.time.monotonic", side_effect=(100, 100.001, 105.1)):
            obs = self.classify(completion(MODEL, '{"category":"pix","priority":"basic"}'))
        self.assertEqual(obs["choices"]["category"]["reason"], "timeout")

    def test_post_uses_original_https_connection_and_closes_it_on_success_and_failure(self):
        for fail in (False, True):
            with self.subTest(fail=fail):
                socket_methods = {"connect": Mock(side_effect=OSError if fail else None), "request": Mock(),
                                  "getresponse": Mock(return_value=Mock(status=200, read=Mock(return_value=b"{}"))),
                                  "close": Mock()}
                pipe = Mock()

                def send(event):
                    if event[0] == "response":
                        socket_methods["close"].assert_called_once()

                pipe.send.side_effect = send
                environment = SimpleNamespace(environ={"FEITA_API_KEY": "sintetica"})
                with patch.object(transport, "os", environment), patch.multiple(
                    transport.http.client.HTTPSConnection, **socket_methods
                ):
                    transport.post(pipe, b"{}", time.monotonic() + 1)
                socket_methods["connect"].assert_called_once()
                socket_methods["close"].assert_called_once()
                pipe.close.assert_called_once()
                if fail:
                    socket_methods["request"].assert_not_called()
                    pipe.send.assert_called_once_with(("error", "transport"))
                else:
                    method, path = socket_methods["request"].call_args.args
                    self.assertEqual((method, path), ("POST", transport.PATH))
                    self.assertEqual(socket_methods["request"].call_args.kwargs["body"], b"{}")
                    self.assertEqual([call.args[0] for call in pipe.send.call_args_list],
                                     [("dispatch", None), ("response", (200, b"{}"))])

    def test_worker_is_killed_on_absolute_timeout_without_http(self):
        dispatched = Mock()
        with patch.object(transport, "post", hanging_worker):
            start = time.monotonic()
            with self.assertRaises(TimeoutError):
                transport.FeitaTransport()(b"{}", start + 1, dispatched)
        dispatched.assert_called_once()
        self.assertLess(time.monotonic() - start, 5)

    def test_reported_cost_and_estimate_have_separate_evidence(self):
        sample = {"usage": {"prompt_tokens": 1000, "completion_tokens": 10,
                            "total_tokens": 1010, "cost": 0.003, "credits": 0.3}}
        unknown_unit = usage_from(sample, PUBLIC_TARIFF, None)
        observed = usage_from(sample, PUBLIC_TARIFF, "USD")
        self.assertIsNone(unknown_unit["observed_api_usd"])
        self.assertEqual(observed["observed_api_usd"], 0.003)
        self.assertAlmostEqual(observed["estimated_api_usd"], 0.0004505)
        self.assertEqual(observed["tariff"]["date"], "2026-11-23")
        self.assertIsNone(usage_from({"usage": {"prompt_tokens": 5}}, PUBLIC_TARIFF, None)["estimated_api_usd"])


class PilotTest(unittest.TestCase):
    def test_blockers_are_checked_before_creating_transport(self):
        def inaccessible_credential():
            raise AssertionError("ambiente consultado antes da autorização")

        for changes, expected in (
            ({"budget_usd": None}, "teto"), ({"tariff_verified": False}, "tarifa"),
            ({"tariff": None}, "tarifa"), ({"concurrency": 2}, "concorrência"),
            ({"max_tokens": 0}, "limites"), ({"max_cases": 1}, "reserva"),
            ({"max_requests": 1}, "reserva"), ({"token_limits_confirmed": False}, "tokens"),
            ({"budget_usd": "0.00001"}, "reserva"),
        ):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(Blocked, expected):
                    budget(setup_limits(**changes), has_credential=inaccessible_credential)
        with self.assertRaisesRegex(Blocked, "credencial local"):
            budget(setup_limits(), has_credential=lambda: False)

    def test_authorization_binds_scope_identity_protocol_pilot_and_positive_cap(self):
        scope = "synthetic"
        identity = dict(IDENTITY, mode="real")
        binding = dict(scope=scope, identity=identity, protocol_sha256="protocol", pilot_sha256="pilot")
        manifest = dict(scope=scope, model=MODEL, model_identity_sha256=identity_digest(identity),
                        protocol_sha256="protocol", pilot_sha256="pilot", authorized=True, budget_cap_usd="1")
        self.assertEqual(authorized_cap(manifest, **binding), Decimal(1))
        for field in ("scope", "model", "model_identity_sha256", "protocol_sha256", "pilot_sha256", "budget_cap_usd",
                      "authorized"):
            with self.subTest(field=field), self.assertRaises(Blocked):
                authorized_cap(dict(manifest, **{field: None}), **binding)
        with self.assertRaises(Blocked):
            authorized_cap(manifest, **dict(binding, identity=dict(identity, adapter_version="changed")))

    def test_late_billable_response_keeps_usage_and_stops_next_request(self):
        policy = budget(setup_limits())
        item = AdapterTest()
        item.setUp()

        def respond(body, deadline, dispatched):
            dispatched()
            return 200, completion(MODEL, '{"category":"pix","priority":"urgent"}',
                                   usage={"cost": 2, "prompt_tokens": 1, "completion_tokens": 10})

        gateway = Mock(side_effect=respond)
        candidate = Adapter(dict(IDENTITY, mode="real"), "run", "rubrica", gateway, policy)
        with patch("adapter.time.monotonic", side_effect=[100, 100.001, 104.960]):
            obs = candidate.classify(item.item)
        self.assertEqual(policy.reserved, Decimal("0.0086544"))
        self.assertTrue(policy.stopped)
        self.assertEqual(obs["temperature_state"], "unknown")
        self.assertEqual(obs["returned_model"], MODEL)
        self.assertEqual(obs["choices"]["category"]["reason"], "timeout")
        self.assertEqual(obs["requests"], 1)
        self.assertEqual(obs["request_usage"][0]["observed_api_usd"], 2)
        self.assertEqual(obs["request_usage"][0]["input_tokens"], 1)
        self.assertEqual(obs["request_usage"][0]["output_tokens"], 10)
        blocked = candidate.classify(dict(item.item, id="control"))
        self.assertEqual(blocked["requests"], 0)
        self.assertEqual(blocked["temperature_state"], "unknown")
        gateway.assert_called_once()

    def test_timeout_without_body_keeps_reservation_and_unknown_usage(self):
        policy = budget(setup_limits())
        item = AdapterTest()
        item.setUp()

        def timeout(body, deadline, dispatched):
            dispatched()
            raise TimeoutError

        candidate = Adapter(dict(IDENTITY, mode="real"), "run", "rubrica", timeout, policy)
        obs = candidate.classify(item.item)
        self.assertEqual(obs["request_usage"], [{"input_tokens": None, "output_tokens": None,
                          "observed_api_usd": None, "estimated_api_usd": None, "tariff": None}])
        self.assertEqual(policy.reserved, policy.per_request)
        self.assertEqual(policy.requests, 1)
        self.assertFalse(policy.stopped)

    def test_budget_reserves_before_transport_and_rejects_repeat_or_holdout(self):
        policy = budget(setup_limits())
        with self.assertRaises(Blocked):
            policy.reserve("other-dev", 3000)
        policy.reserve("dev", 3000)
        self.assertEqual(policy.reserved, policy.per_request)
        with self.assertRaises(Blocked):
            policy.reserve("dev", 3000)
        with self.assertRaises(Blocked):
            policy.reserve("control", 8001)
        self.assertEqual(policy.requests, 1)

    def test_transport_only_runs_after_reservation_and_overage_stops_batch(self):
        policy = budget(setup_limits())
        item = AdapterTest()
        item.setUp()
        gateway = Mock()

        def respond(body, deadline, dispatched):
            self.assertEqual(policy.reserved, policy.per_request)
            self.assertEqual(decode(body)["max_tokens"], 128)
            dispatched()
            return 200, completion(MODEL, '{"category":"pix","priority":"basic"}',
                                   usage={"cost": 2, "prompt_tokens": 40, "completion_tokens": 4})
        gateway.side_effect = respond
        candidate = Adapter(dict(IDENTITY, mode="real"), "run", "rubrica", gateway, policy)
        self.assertEqual(candidate.classify(item.item)["requests"], 1)
        self.assertTrue(policy.stopped)
        rejected = candidate.classify(dict(item.item, id="control"))
        self.assertEqual(rejected["requests"], 0)
        gateway.assert_called_once()


class IPCTest(unittest.TestCase):
    def test_c02_runs_development_and_all_eight_natural_controls(self):
        with tempfile.TemporaryDirectory(dir=HERE) as scratch:
            output = Path(scratch) / "result"
            cli = [sys.executable, "-B", "script/classification_comparison/run.py", "--config", str(HERE / "fixture.json"),
                   "--split", "development", "--limit", "1", "--output", str(output)]
            result = subprocess.run(cli, cwd=c01.ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = c01.read(output / "report.json")
            self.assertEqual(len(report["control_ids"]), 13)
            self.assertEqual(len(report["completed_ids"]), 1)
            self.assertEqual(report["identity"]["mode"], "fixture")
            self.assertEqual(report["eligibility"], "inconclusive")
            decisions = {row["id"]: row for row in map(decode, (output / "decisions.jsonl").read_bytes().split(b"\n")[:-1])}
            observations = list(map(decode, (output / "observations.jsonl").read_bytes().split(b"\n")[:-1]))
            candidates = [row for row in observations if row["origin"] == "candidate"]
            self.assertEqual(len(candidates), 9)
            self.assertEqual(len(observations), 10)
            self.assertEqual(sum(row["requests"] for row in candidates), 9)
            self.assertEqual(sum(row["attempts"] == 0 for row in decisions.values()), 4)
            mixed = next(row for row in observations if row["origin"] == "injected_control")
            self.assertIsNone(decisions[mixed["id"]]["fields"]["category"]["applied"])
            self.assertEqual(decisions["ctl-simples"]["fields"]["priority"]["applied"], "basic")

    def test_entrypoint_creates_ready_and_final_and_preserves_lf_delimiters(self):
        item = AdapterTest()
        item.setUp()
        item.item.update(text="Comprovante\u2028do Pix\u2029 no caixa\u0085.")
        with tempfile.TemporaryDirectory() as scratch:
            ready, final = [Path(scratch) / name for name in ("ready.json", "final.json")]
            env = dict(os.environ, CLASSIFICATION_IDENTITY=json.dumps(IDENTITY), CLASSIFICATION_RUN_ID="run",
                       CLASSIFICATION_CONTRACT_VERSION=VERSION, CLASSIFICATION_TIMEOUT_MS="5000",
                       CLASSIFICATION_READY_FILE=str(ready), CLASSIFICATION_FINAL_FILE=str(final),
                       CLASSIFICATION_PROMPT=str(HERE / "prompt.txt"),
                       CLASSIFICATION_RUBRIC=str(c01.PLAN / "rubrica-comum.md"))
            result = subprocess.run([sys.executable, "-B", str(HERE / "adapter.py")],
                                    input=json.dumps(item.item, ensure_ascii=False).encode() + b"\n",
                                    capture_output=True, env=env, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(set(c01.read(ready)), {"runtime", "hardware"})
            self.assertEqual(c01.read(final), {"peak_memory_bytes": None})
            self.assertEqual(decode(result.stdout)["id"], item.item["id"])

    def test_repository_preflight_blocks_disabled_manifest(self):
        command = c01.read(HERE / "real.json")["command"] + ["--preflight"]
        result = subprocess.run(command, cwd=c01.ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("manifesto sem autorização de execução", result.stderr)

    def test_c02_authorized_synthetic_pilot_with_original_source_hashes(self):
        locked = c01.read(HERE.parents[1] / "sources.lock.json")
        self.assertEqual({path: c01.digest(c01.ROOT / path) for path in locked}, locked)
        with tempfile.TemporaryDirectory(dir=HERE) as scratch:
            work = Path(scratch)
            pilot, authorization, config, output = [work / name for name in ("pilot", "auth", "config", "result")]
            pilot.write_text(json.dumps(setup_limits(max_cases=9, max_requests=9)))
            candidate = c01.read(HERE / "real.json")
            approval = {"scope": "synthetic", "model": MODEL, "authorized": True, "budget_cap_usd": "1",
                        "model_identity_sha256": identity_digest(candidate["identity"]),
                        "protocol_sha256": c01.digest(c01.PLAN / "protocolo-comparacao.json"),
                        "pilot_sha256": c01.digest(pilot)}
            authorization.write_text(json.dumps(approval))
            arguments = ["--pilot", str(pilot), "--pilot-sha256", c01.digest(pilot),
                         "--authorization", str(authorization), "--authorization-sha256", c01.digest(authorization)]
            refused = subprocess.run([sys.executable, "-B", str(HERE / "adapter.py"), *arguments, "--preflight"],
                                     cwd=c01.ROOT, capture_output=True, text=True, timeout=10)
            self.assertEqual(refused.returncode, 2)
            self.assertIn("manifesto incompatível com escopo", refused.stderr)
            launcher = (
                f"import sys; sys.path.insert(0, {str(HERE)!r})\n"
                "import adapter\n"
                "from fixture import fake_gateway\n"
                "def reject_live(): raise AssertionError('transporte real instanciado')\n"
                "adapter.FeitaTransport = reject_live\n"
                "adapter.main(synthetic_transport=fake_gateway)\n"
            )
            candidate["command"] = [sys.executable, "-B", "-c", launcher, *arguments]
            config.write_text(json.dumps(candidate))
            cli = [sys.executable, "-B", "script/classification_comparison/run.py", "--mode", "real", "--config",
                   str(config), "--split", "development", "--limit", "1", "--output", str(output)]
            result = subprocess.run(cli, cwd=c01.ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = c01.read(output / "report.json")
            self.assertEqual(report["usage"]["requests"]["value"], 9)
            self.assertEqual(report["eligibility"], "inconclusive")
            self.assertIsNone(report["gates"]["warm_total_latency_p95_ms_max"]["value"])
            observations = list(map(decode, (output / "observations.jsonl").read_bytes().split(b"\n")[:-1]))
            for observation in observations:
                if observation["origin"] == "candidate":
                    self.assertEqual(observation["temperature_state"], "unknown")
                    self.assertGreater(observation["elapsed_ms"], 0)
                    self.assertIsNone(observation["inference_ms"])
        self.assertEqual({path: c01.digest(c01.ROOT / path) for path in locked}, locked)


if __name__ == "__main__":
    unittest.main()
