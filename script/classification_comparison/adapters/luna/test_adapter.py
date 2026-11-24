"""Exercita a candidata com envelopes artificiais, isolados dos lotes C05."""
from pathlib import Path
from types import SimpleNamespace
import unittest

from adapters.luna.adapter import LunaAdapter, MODEL, request_body
from adapters.qwen import adapter as qwen
from common import c01, decide, decode, encode

HERE = Path(__file__).resolve().parent
MANIFEST = decode((HERE / "candidate.json").read_bytes())
OPERATION = decode((HERE / "operational.json").read_bytes())
IDENTITY = dict(MANIFEST["identity"], mode="fixture", provider="simulador-c05-luna")
INSTRUCTIONS = "\n\n".join(c01.source_path(MANIFEST[key]).read_text(encoding="utf-8")
                           for key in ("prompt", "rubric"))
CATALOG = {"version": "1.0.0", "category": {"pix": "Pix"}, "priority": {"basic": "Básico", "urgent": "Urgente"}}
RUN = "luna-sintetico"


def envelope(**received):
    missing = [field for field in c01.FIELDS if field not in received]
    return {"contract_version": "1.1.0", "id": "artificial-01", "text": "Como consultar um Pix de exemplo?",
            "brand": "marca-sintetica", "catalog": CATALOG, "received": received, "missing": missing}


def completion(values, *, model=MODEL, message=None, reason="stop", usage=None):
    if message is None:
        message = {"content": encode(values)}
    return {"model": model, "choices": [{"message": message, "finish_reason": reason}], "usage": usage}


class Gateway:
    def __init__(self, response, status=200):
        self.response = response
        self.status = status
        self.bodies = []
        self.closed = 0

    def __call__(self, body, deadline, dispatched):
        dispatched()
        self.bodies.append(body)
        return self.status, encode(self.response).encode()

    def close(self):
        self.closed += 1


class SyntheticBudget:
    max_tokens = 128
    reasoning = None
    tariff = {"source": "fixture", "date": "2026-11-24", "unit": "USD/Mtoken",
              "input": "1", "output": "2", "cache_read": "1", "cache_write": "1"}
    cost_unit = "USD"

    def __init__(self):
        self.reservations = []
        self.usage = []

    def reserve(self, case_id, body_size):
        self.reservations.append((case_id, body_size))

    def observe(self, usage):
        self.usage.append(usage)


class LunaAdapterTests(unittest.TestCase):
    def test_manifesto_preserva_fontes_r2_por_sha(self):
        original = decode((HERE.parent / "qwen" / "r2" / "candidate.json").read_bytes())
        for key in ("prompt", "policy"):
            self.assertEqual(MANIFEST[key], original[key])
        for key in ("prompt", "policy", "rubric"):
            c01.source_path(MANIFEST[key])
        self.assertEqual(MANIFEST["contract_version"], "1.1.0")

    def test_rejeita_identidade_cruzada_ou_orcamento_real_ausente(self):
        gateway = Gateway({})
        for identity in (dict(IDENTITY, provider="feita"), dict(IDENTITY, expected_returned_model=None),
                         dict(IDENTITY, expected_weights_revision="inesperada"), MANIFEST["identity"]):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                LunaAdapter(identity, RUN, INSTRUCTIONS, gateway)
        self.assertEqual(gateway.bodies, [])

    def test_orcamento_falso_ou_sem_interface_bloqueia_gateway(self):
        class FalsyBudget(SyntheticBudget):
            def __bool__(self):
                return False

        valid = SyntheticBudget()
        attributes = {name: getattr(valid, name) for name in
                      ("reserve", "observe", "max_tokens", "reasoning", "cost_unit", "tariff")}
        incomplete = {name: SimpleNamespace(**{key: value for key, value in attributes.items() if key != name})
                      for name in attributes}
        invalid = {
            **incomplete,
            "False": False,
            "objeto falso": FalsyBudget(),
            "reserve inválido": SimpleNamespace(**dict(attributes, reserve=None)),
            "observe inválido": SimpleNamespace(**dict(attributes, observe=None)),
            "limite inválido": SimpleNamespace(**dict(attributes, max_tokens=127)),
            "unidade de custo inválida": SimpleNamespace(**dict(attributes, cost_unit="BRL")),
        }
        answer = completion({"category": "pix"}, usage={"prompt_tokens": 20, "completion_tokens": 3})
        item = envelope(priority="urgent")
        for label, budget in invalid.items():
            for identity in (MANIFEST["identity"], IDENTITY):
                with self.subTest(budget=label, mode=identity["mode"]):
                    gateway = Gateway(answer)
                    with self.assertRaisesRegex(ValueError, "orçamento Luna"):
                        LunaAdapter(identity, RUN, INSTRUCTIONS, gateway, budget).classify(item)
                    self.assertEqual(len(gateway.bodies), 0)

    def test_tarifa_ausente_ou_invalida_bloqueia_gateway(self):
        item = envelope(priority="urgent")
        answer = completion({"category": "pix"}, usage={"prompt_tokens": 20, "completion_tokens": 3})
        tariff = SyntheticBudget.tariff
        invalid = (None, dict(tariff, unit="BRL"), dict(tariff, source=" "), dict(tariff, date="ontem"),
                   dict(tariff, cache_read=None), dict(tariff, input="-1"), dict(tariff, output="NaN"))
        for malformed in invalid:
            for identity in (MANIFEST["identity"], IDENTITY):
                with self.subTest(tariff=malformed, mode=identity["mode"]):
                    budget = SyntheticBudget()
                    budget.tariff = malformed
                    gateway = Gateway(answer)
                    with self.assertRaisesRegex(ValueError, "tarifa"):
                        LunaAdapter(identity, RUN, INSTRUCTIONS, gateway, budget).classify(item)
                    self.assertEqual(len(gateway.bodies), 0)
                    self.assertEqual(budget.reservations, [])
                    self.assertEqual(budget.usage, [])

    def test_orcamento_valido_reserva_antes_do_envio_e_observa_uma_resposta(self):
        item = envelope(priority="urgent")
        budget = SyntheticBudget()
        budget.cost_unit = None
        answer = completion({"category": "pix"}, usage={"prompt_tokens": 20, "completion_tokens": 3})
        gateway = Gateway(answer)

        def capture(body, deadline, dispatched):
            self.assertEqual(budget.reservations, [(item["id"], len(body))])
            self.assertEqual(budget.usage, [])
            return gateway(body, deadline, dispatched)

        adapter = LunaAdapter(MANIFEST["identity"], RUN, INSTRUCTIONS, capture, budget)
        self.addCleanup(adapter.close)
        observation = adapter.classify(item)
        self.assertEqual(observation["requests"], 1)
        self.assertEqual(len(gateway.bodies), 1)
        usage, = budget.usage
        self.assertEqual(usage["tariff"]["source"], "fixture")

    def test_revalida_tarifa_antes_de_usar_sessao_reutilizada(self):
        budget = SyntheticBudget()
        gateway = Gateway(completion({"category": "pix"}))
        adapter = LunaAdapter(IDENTITY, RUN, INSTRUCTIONS, gateway, budget)
        self.addCleanup(adapter.close)
        item = envelope(priority="urgent")
        self.assertEqual(adapter.classify(item)["requests"], 1)
        budget.tariff = None
        with self.assertRaisesRegex(ValueError, "tarifa"):
            adapter.classify(dict(item, id="artificial-02"))
        self.assertEqual((len(gateway.bodies), len(budget.reservations), len(budget.usage), gateway.closed), (1, 1, 1, 1))

    def test_dois_campos_em_uma_chamada_estrita(self):
        item = envelope()
        gateway = Gateway(completion({"category": "pix", "priority": "basic"}))
        adapter = LunaAdapter(IDENTITY, RUN, INSTRUCTIONS, gateway)
        self.addCleanup(adapter.close)

        observation = adapter.classify(item)

        self.assertEqual(len(gateway.bodies), 1)
        self.assertEqual((observation["requests"], observation["questions"]), (1, 2))
        body = decode(gateway.bodies[0])
        self.assertEqual(set(body), {"model", "reasoning_effort", "max_completion_tokens", "stream",
                                     "messages", "response_format"})
        self.assertEqual({key: body[key] for key in OPERATION["request"]["parameters"]},
                         OPERATION["request"]["parameters"])
        self.assertEqual(body["messages"][0], {"role": "system", "content": INSTRUCTIONS})
        self.assertEqual(decode(body["messages"][1]["content"]),
                         {key: item[key] for key in OPERATION["request"]["context"]})
        definition = body["response_format"]["json_schema"]
        self.assertIs(definition["strict"], True)
        self.assertEqual(definition["schema"], {"type": "object", "required": ["category", "priority"],
            "additionalProperties": False, "properties": {"category": {"type": "string", "enum": ["pix", c01.ABSTENTION]},
                "priority": {"type": "string", "enum": ["basic", "urgent", c01.ABSTENTION]}}})
        self.assertTrue(all(choice["score"] is None for choice in observation["choices"].values()))
        self.assertEqual(decide(item, observation, CATALOG, RUN)["outcome"], "complete")

    def test_solicita_apenas_campo_ausente_e_preserva_fornecido(self):
        item = envelope(priority="urgent")
        gateway = Gateway(completion({"category": "pix"}))
        adapter = LunaAdapter(IDENTITY, RUN, INSTRUCTIONS, gateway)
        self.addCleanup(adapter.close)
        decision = decide(item, adapter.classify(item), CATALOG, RUN)
        schema = decode(gateway.bodies[0])["response_format"]["json_schema"]["schema"]
        self.assertEqual(schema["required"], ["category"])
        self.assertEqual(list(schema["properties"]), ["category"])
        self.assertEqual(decision["fields"]["priority"], {"status": "provided", "applied": "urgent"})

    def test_abstencao_nao_aplica_parcial_e_permite_proximo_caso(self):
        item = envelope()
        gateway = Gateway(completion({"category": "pix", "priority": c01.ABSTENTION}))
        adapter = LunaAdapter(IDENTITY, RUN, INSTRUCTIONS, gateway)
        self.addCleanup(adapter.close)
        decision = decide(item, adapter.classify(item), CATALOG, RUN)
        self.assertEqual(decision["outcome"], "review")
        self.assertIsNone(decision["fields"]["category"]["applied"])
        gateway.response = completion(None, message={"refusal": "recusa artificial"})
        observation = adapter.classify(dict(item, id="artificial-02"))
        self.assertTrue(all(choice["reason"] == "policy" for choice in observation["choices"].values()))
        self.assertEqual((len(gateway.bodies), gateway.closed), (2, 0))

    def test_bypass_completo_ou_invalido_antes_do_envio(self):
        for item, reason in ((envelope(category="pix", priority="urgent"), "channel_complete"),
                             (envelope(category="indisponivel"), "invalid_input")):
            with self.subTest(reason=reason):
                gateway = Gateway({})
                adapter = LunaAdapter(IDENTITY, RUN, INSTRUCTIONS, gateway)
                self.assertEqual(decide(item, None, CATALOG, RUN)["reason"], reason)
                with self.assertRaises(ValueError):
                    adapter.classify(item)
                self.assertEqual(gateway.bodies, [])

    def test_invalidos_ou_procedencia_divergente_encerram_a_sessao(self):
        invalid = {"category": "pix", "priority": "basic", "extra": "campo inesperado"}
        valid = {"category": "pix", "priority": "basic"}
        for answer, reason in ((completion(invalid), "invalid_output"),
                               (completion(valid, reason="length"), "invalid_output"),
                               (completion(valid, model="outro"), "version_mismatch"),
                               (completion(valid, model=None), "adapter_error")):
            with self.subTest(reason=reason):
                gateway = Gateway(answer)
                adapter = LunaAdapter(IDENTITY, RUN, INSTRUCTIONS, gateway)
                observation = adapter.classify(envelope())
                self.assertTrue(all(choice["reason"] == reason for choice in observation["choices"].values()))
                self.assertEqual(decide(envelope(), observation, CATALOG, RUN)["outcome"], "review")
                with self.assertRaises(ConnectionError):
                    adapter.classify(envelope())
                adapter.close()
                self.assertEqual((len(gateway.bodies), gateway.closed), (1, 1))

    def test_orcamento_injetado_recebe_uso_de_erro_http(self):
        budget = SyntheticBudget()
        response = completion({}, usage={"prompt_tokens": 20, "completion_tokens": 3, "cost": "0.000026"})
        gateway = Gateway(response, status=429)
        adapter = LunaAdapter(IDENTITY, RUN, INSTRUCTIONS, gateway, budget)
        observation = adapter.classify(envelope())
        self.assertEqual(budget.reservations, [(envelope()["id"], len(gateway.bodies[0]))])
        self.assertEqual(observation["request_usage"], budget.usage)
        self.assertEqual(budget.usage[0]["observed_api_usd"], 0.000026)
        self.assertEqual(gateway.closed, 1)

    def test_sem_orcamento_fixture_nao_publica_tarifa_qwen(self):
        gateway = Gateway(completion({"category": "pix"}, usage={"prompt_tokens": 4, "completion_tokens": 2}))
        adapter = LunaAdapter(IDENTITY, RUN, INSTRUCTIONS, gateway)
        self.addCleanup(adapter.close)
        usage, = adapter.classify(envelope(priority="urgent"))["request_usage"]
        self.assertEqual((usage["input_tokens"], usage["output_tokens"]), (4, 2))
        self.assertIsNone(usage["tariff"])
        self.assertIsNone(usage["estimated_api_usd"])

    def test_projecao_qwen_preserva_formato_e_luna_ignora_parametros_historicos(self):
        item = envelope(priority="urgent")
        received = item["received"]
        expected = {"model": qwen.MODEL, "stream": False, "temperature": 0, "max_tokens": 96,
                    "messages": [{"role": "system", "content": "teste"}, {"role": "user", "content": encode({
                        "text": item["text"], "brand": item["brand"], "catalog": CATALOG,
                        "missing": ["category"], "received": received})}],
                    "response_format": {"type": "json_schema", "json_schema": {
                        "name": "classificacao", "strict": True, "schema": {"type": "object",
                            "required": ["category"], "additionalProperties": False,
                            "properties": {"category": {"type": "string", "enum": ["pix", c01.ABSTENTION]}}}}},
                    "reasoning": {"enabled": False}}
        self.assertEqual(qwen.request_body(item, received, "teste", 96, {"enabled": False}), encode(expected).encode())
        luna = decode(request_body(item, received, "teste", 96, {"enabled": True}))
        self.assertEqual((luna["max_completion_tokens"], luna["reasoning_effort"]), (128, "none"))


if __name__ == "__main__":
    unittest.main()
