"""Controles sintéticos de seleção de alvo, preservação e atomicidade."""

from copy import deepcopy
import io
import json
import unittest

from ..contracts.core import CATALOG, ContractError, FIELDS, LABELS
from ..contracts.ipc import project, validate_decision
from ..training.scores import COLLECTION_POLICY, extract
from .__main__ import serve
from .decide import decide

POLICY_SHA = "1" * 64
TEXT = "fixture de implementação SF2"


class FixturePackage:
    digest = "2" * 64
    model_sha256 = {field: "3" * 64 for field in FIELDS}
    class_order = LABELS

    def __init__(self):
        self.invocations = []
        self.tokenizations = []
        self.length = 5
        self.vectors = dict(zip(FIELDS, ([.8, .1, .05, .05], [.05, .05, .05, .8, .05]), strict=True))

    def token_length(self, text, fields):
        self.tokenizations.append((text, fields))
        return self.length

    def score(self, field, text):
        self.invocations.append((field, text))
        value = self.vectors[field]
        if isinstance(value, Exception):
            raise value
        return {"classes": self.class_order[field], "scores": value}

    @property
    def identities(self):
        return {"package_sha256": self.digest, "model_sha256": self.model_sha256, "policy_sha256": POLICY_SHA}


def record(received):
    return {
        "id": "fixture-sf2-03", "partition": "validation", "family_id": "controle",
        "text": TEXT, "received": received, "gold": {"category": "terminal", "priority": "basic"},
        "author": {"id": "fixture", "kind": "ai"},
    }


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.package = FixturePackage()

    def classify(self, received, *, catalog=CATALOG, interruption=None):
        item = project(record(received), catalog)
        decision = decide(item, self.package, COLLECTION_POLICY, POLICY_SHA)
        validate_decision(item, decision, COLLECTION_POLICY, self.package.class_order,
                          self.package.identities, interruption=interruption)
        return decision

    def test_exercicio_retirar_prioridade_sem_chamar_categoria(self):
        complete = self.classify({"category": "terminal", "priority": "basic"})
        self.assertEqual(complete["applied"], {})
        self.assertEqual(complete["calls"], dict.fromkeys(FIELDS, 0))
        self.assertEqual(self.package.tokenizations, [])
        after = self.classify({"category": "terminal"})
        self.assertEqual(after["received"], {"category": "terminal"})
        self.assertEqual(after["applied"], {"priority": "urgent"})
        self.assertEqual(self.package.invocations, [("priority", TEXT)])

    def test_ausencia_nula_e_em_branco_por_campo(self):
        for value in (None, " \t "):
            after = self.classify({"category": value, "priority": "advanced"})
            self.assertEqual(after["calls"], {"category": 1, "priority": 0})
            self.assertEqual(after["received"], {"category": value, "priority": "advanced"})
            self.assertEqual(after["applied"], {"category": "pix"})

    def test_catalogo_e_valor_invalidos_impedem_qualquer_chamada(self):
        result = self.classify({"category": False})
        self.assertIs(result["received"]["category"], False)
        self.assertEqual(result["fields"]["category"]["reason"], "invalid_input")
        catalog = deepcopy(CATALOG)
        catalog["version"] = "desconhecida"
        result = self.classify({}, catalog=catalog)
        self.assertEqual(result["outcome"], "review")
        self.assertEqual(result["fields"]["priority"]["reason"], "invalid_catalog")
        self.assertEqual(self.package.invocations, [])
        self.assertEqual(self.package.tokenizations, [])

    def test_empresa_pode_restringir_catalogo_sem_renormalizacao(self):
        catalog = deepcopy(CATALOG)
        del catalog["category"]["pix"]
        result = self.classify({}, catalog=catalog)
        self.assertEqual(result["fields"]["category"]["reason"], "inactive_label")
        self.assertEqual(result["fields"]["category"]["raw"], "pix")
        self.assertEqual(result["fields"]["priority"]["raw"], "urgent")
        self.assertEqual(result["applied"], {})

    def test_recusa_parcial_preserva_observacao_de_urgencia(self):
        for scores, reason in (
            ([.05, .05, .1, .8], "raw_review"),
            ([.49, .21, .20, .10], "below_tau"),
            ([.50, .50, .0, .0], "low_margin"),
        ):
            with self.subTest(reason=reason):
                self.package.vectors["category"] = scores
                result = self.classify({})
                self.assertEqual(result["fields"]["category"]["reason"], reason)
                self.assertEqual(result["fields"]["priority"]["raw"], "urgent")
                self.assertEqual(result["calls"], dict.fromkeys(FIELDS, 1))
                self.assertEqual(result["applied"], {})

    def test_score_invalido_timeout_e_erro_bloqueiam_complemento(self):
        for observation, reason in (
            ([float("nan"), 0, 0, 1], "invalid_score"),
            ([1.1, -0.1, 0, 0], "invalid_score"),
            ([.91, 0, 0, 0], "invalid_score"),
            (TimeoutError(), "timeout"),
            (RuntimeError("detalhe de fixture"), "error"),
        ):
            with self.subTest(reason=reason), self.assertLogs(level="WARNING"):
                self.package.vectors["category"] = observation
                result = self.classify({})
                self.assertEqual(result["outcome"], "error")
                self.assertEqual(result["fields"]["category"]["reason"], reason)
                self.assertIsNone(result["fields"]["category"]["vector"])
                self.assertEqual(result["fields"]["priority"]["raw"], "urgent")
                self.assertEqual(result["applied"], {})

    def test_limite_textual_e_rejeicao_de_mascara_ou_gold(self):
        self.package.length = 129
        result = self.classify({}, interruption="too_long")
        self.assertEqual(result["fields"]["category"]["reason"], "too_long")
        self.assertEqual(self.package.invocations, [])
        self.package.length = 128
        self.assertEqual(self.classify({})["outcome"], "complete")
        item = project(record({}))
        self.assertNotIn("gold", item)
        for polluted in ({**item, "gold": {}}, {**item, "missing_fields": ["category"]}):
            with self.assertRaises(ContractError):
                decide(polluted, self.package, COLLECTION_POLICY, POLICY_SHA)

    def test_ready_precede_primeira_entrada_e_cada_resposta_tem_flush(self):
        class Wire(io.StringIO):
            def __init__(self):
                super().__init__()
                self.flushes = []

            def flush(self):
                self.flushes.append(self.getvalue())

        wire = Wire()
        item = project(record({"category": "terminal"}))

        def lines():
            self.assertEqual(wire.flushes, ['{"type":"ready"}\n'])
            self.assertEqual(self.package.invocations, [])
            yield json.dumps(item) + "\n"
            self.assertEqual(len(wire.flushes), 2)
            yield json.dumps({**item, "id": "fixture-seguinte"}) + "\n"

        serve(self.package, COLLECTION_POLICY, POLICY_SHA, lines(), wire)
        self.assertEqual([json.loads(line)["id"] for line in wire.getvalue().splitlines()[1:]],
                         [item["id"], "fixture-seguinte"])

    def test_extracao_usa_vetores_originais_e_recusa_aplicacao_parcial(self):
        row = {**record({}), "missing_fields": list(FIELDS)}
        self.package.vectors["category"] = [.05, .05, .1, .8]
        decision = self.classify({})
        prior_calls = self.package.invocations[:]
        bundle = extract([row], [decision], COLLECTION_POLICY, LABELS, self.package.identities, "4" * 64)
        self.assertEqual(bundle["rows"][0]["heads"], {f: decision["fields"][f]["vector"] for f in FIELDS})
        self.assertEqual(self.package.invocations, prior_calls)
        decision["applied"]["priority"] = "urgent"
        with self.assertRaises(ContractError):
            extract([row], [decision], COLLECTION_POLICY, LABELS, self.package.identities, "4" * 64)


if __name__ == "__main__":
    unittest.main()
