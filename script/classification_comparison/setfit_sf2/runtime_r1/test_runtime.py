"""Frames sintéticos. A fixture devolve apenas vetores estáticos ou erros declarados."""
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

from ..adapter.decide import decide
from ..contracts import core, ipc
from ..evaluation.runner import encoded
from . import derive, load_context, verify
from . import context as identities

EVIDENCE = core.ROOT / "docs/evidencias/c05/sf2"
CAPTURE = EVIDENCE / "qualificacao-01/execucao-02"
R1 = EVIDENCE / "revisao-01"


def context_bytes():
    return [(CAPTURE / "avaliacao/capture-policy.json").read_bytes(), (R1 / "selected-policy.json").read_bytes(),
            (CAPTURE / "pacote/manifest.json").read_bytes()]


class SyntheticHeads:
    def __init__(self, context):
        self.digest = context["package_sha256"]
        self.model_sha256 = context["model_sha256"]
        self.class_order = context["class_order"]
        self.values = {"category": [.01, .95, .02, .02], "priority": [.7, .1, .05, .05, .1]}
        self.length = 12

    def token_length(self, text, fields):
        return self.length

    def score(self, field, text):
        value = self.values[field]
        if isinstance(value, Exception):
            raise value
        return {"classes": self.class_order[field], "scores": value}


class RuntimeTests(TestCase):
    def setUp(self):
        self.context = load_context(*context_bytes())
        self.heads = SyntheticHeads(self.context)

    def capture(self, received, catalog=None):
        record = {"id": "fixture-r1", "text": "Texto de teste.", "received": received}
        item = ipc.project(record, core.CATALOG if catalog is None else catalog)
        raw = decide(item, self.heads, self.context["capture_policy"], self.context["capture_policy_sha256"])
        return item, encoded(raw)

    def classify(self, received, catalog=None):
        item, frame = self.capture(received, catalog)
        decision = derive(item, frame, self.context)
        verify(item, frame, decision, self.context)
        return decision

    def test_um_ou_dois_alvos_e_igualdade_nos_dois_limites(self):
        for received in ({}, {"category": None}, {"priority": " \t"}, {"category": "pix"}, {"priority": "basic"}):
            with self.subTest(received=received):
                result = self.classify(received)
                missing = ipc.channel(received, core.CATALOG)[0]
                self.assertEqual(result["received"], received)
                self.assertEqual(result["outcome"], "complete")
                self.assertEqual(result["applied"], {f: {"category": "payouts", "priority": "advanced"}[f]
                                                     for f in missing})
                for field in core.FIELDS:
                    self.assertEqual(result["calls"][field], int(field in missing))
                    self.assertEqual(result["fields"][field]["cut"],
                                     self.context["selected_policy"][field] if field in missing else None)

    def test_controles_bloqueados_sem_corte_ou_chamada(self):
        for received, outcome, reasons in [
            ({"category": "pix", "priority": "basic"}, "complete", ("provided", "provided")),
            ({"priority": False}, "review", ("not_requested", "invalid_input")),
            ({"priority": 2, "category": "pix"}, "review", ("provided", "invalid_input")),
            ({"category": {"code": [1, False]}}, "review", ("invalid_input", "not_requested")),
        ]:
            with self.subTest(received=received):
                result = self.classify(received)
                self.assertEqual(result["outcome"], outcome)
                self.assertEqual(result["applied"], {})
                for field, reason in zip(core.FIELDS, reasons):
                    self.assertEqual(result["fields"][field]["reason"], reason)
                    self.assertIsNone(result["fields"][field]["cut"])
                    self.assertEqual(result["calls"][field], 0)
        bad_catalog = {**core.CATALOG, "version": "outra"}
        decision = self.classify({}, bad_catalog)
        for field in core.FIELDS:
            self.assertEqual(decision["fields"][field]["reason"], "invalid_catalog")
            self.assertEqual(decision["calls"][field], 0)
            self.assertIsNone(decision["fields"][field]["cut"])

    def test_valor_aninhado_preservado_na_revisao_sem_chamadas(self):
        value = {"dados": [True, 7]}
        for _ in range(520):
            value = [value]
        item, frame = self.capture({"category": value})
        decision = derive(item, frame, self.context)
        verify(item, frame, decision, self.context)
        self.assertEqual(decision["outcome"], "review")
        self.assertEqual(decision["fields"]["category"]["reason"], "invalid_input")
        self.assertEqual(decision["fields"]["priority"]["reason"], "not_requested")
        self.assertEqual(decision["calls"], {"category": 0, "priority": 0})
        self.assertEqual(decision["applied"], {})
        self.assertEqual(encoded(decision["received"]), encoded(item["received"]))
        leaf = decision["received"]["category"]
        for _ in range(520):
            leaf = leaf[0]
        for changed in ([1, 7], [7, True], [True, 8]):
            leaf["dados"] = changed
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, "received"):
                verify(item, frame, decision, self.context)

    def test_precedencia_insuficiente_inativo_empate_e_sem_parcial(self):
        catalog = deepcopy(core.CATALOG)
        del catalog["category"]["terminal"]
        for scores, raw, reason in [
            ([.4, .2, .2, .2], "informacao_insuficiente", "raw_review"),
            ([.2, .2, .2, .4], "terminal", "inactive_label"),
            ([0, .5, .5, 0], "payouts", "below_tau"),
        ]:
            with self.subTest(reason=reason):
                self.heads.values["category"] = scores
                result = self.classify({}, catalog)
                field = result["fields"]["category"]
                self.assertEqual((field["reason"], field["raw"]), (reason, raw))
                self.assertEqual(field["vector"]["scores"], scores)
                self.assertEqual(result["fields"]["priority"]["decision"], "accept")
                self.assertEqual((result["outcome"], result["applied"]), ("review", {}))

    def test_erros_de_um_especialista_e_timeout_documentado(self):
        for observation, reason in [(RuntimeError(), "error"), (TimeoutError(), "timeout"), ([0, 0, 0, 0], "invalid_score")]:
            with self.subTest(reason=reason), self.assertLogs(level="WARNING"):
                self.heads.values["priority"] = observation
                result = self.classify({})
                self.assertEqual((result["outcome"], result["applied"]), ("error", {}))
                field = result["fields"]["priority"]
                self.assertEqual((field["reason"], field["cut"]), (reason, self.context["selected_policy"]["priority"]))
                self.assertEqual(result["fields"]["category"]["decision"], "accept")
                self.assertEqual(result["calls"], {"category": 1, "priority": 1})

    def test_interrupcao_sem_evidencia_nao_pode_explicar_zero_chamadas(self):
        self.heads.length = 250
        item, frame = self.capture({})
        with self.assertRaises(ValueError):
            derive(item, frame, self.context)
        self.heads.length = 12
        self.heads.values["category"] = TimeoutError()
        with self.assertLogs(level="WARNING"):
            item, frame = self.capture({})
        raw = core.decode(frame)
        raw["calls"]["category"] = 0
        with self.assertRaises(ValueError):
            derive(item, encoded(raw), self.context)

    def test_bytes_originais_framing_e_chaves_duplicadas(self):
        item, frame = self.capture({})
        decision = derive(item, frame, self.context)
        for wrong in (frame.rstrip(), frame + frame, b"\xff\n", b"{}\r\n", b"\n", frame + b"\n",
                      b"[" * 1500 + b"]" * 1500 + b"\n", None,
                      frame.replace(b'"category":1', b'"category":0,"category":1'), frame.decode()):
            with self.subTest(wrong=repr(wrong)[:50]), self.assertRaises(ValueError):
                derive(item, wrong, self.context)
        with self.assertRaises(ValueError):
            verify(item, b" " + frame, decision, self.context)

    def test_identidade_canal_mascara_e_vetores_de_coleta_integros(self):
        item, frame = self.capture({"priority": "basic"})
        for transform in [
            lambda r: r.update(id="outro"), lambda r: r.update(policy_sha256="0" * 64),
            lambda r: r["model_sha256"].update(category="1" * 64), lambda r: r.update(package_sha256="2" * 64),
            lambda r: r["received"].update(priority=False),
            lambda r: r["fields"]["category"]["vector"]["classes"].reverse(),
            lambda r: r["fields"]["category"]["vector"].update(scores=[1, 1, -1, 0]),
            lambda r: r["fields"]["category"]["vector"].update(scores=[.1, .1, .1, .1]),
        ]:
            raw = core.decode(frame)
            transform(raw)
            with self.assertRaises(ValueError):
                derive(item, encoded(raw), self.context)
        for wrong in ({**item, "gold": {}}, {**item, "missing_fields": []}, {**item, "catalog": None}):
            with self.assertRaises(ValueError):
                derive(wrong, frame, self.context)
        both, frame = self.capture({})
        with self.assertRaises(ValueError):
            derive({**both, "missing_fields": list(reversed(both["missing_fields"]))}, frame, self.context)

    def test_auditor_reconstroi_resultado_e_preserva_tipos_json(self):
        item, frame = self.capture({"priority": None})
        honest = derive(item, frame, self.context)
        for transform in [
            lambda d: d.update(extra=1), lambda d: d.update(id="outro"), lambda d: d.update(raw_sha256="0" * 64),
            lambda d: d.update(selected_policy_sha256="1" * 64), lambda d: d["model_sha256"].update(priority="2" * 64),
            lambda d: d["received"].clear(), lambda d: d["calls"].update(category=True),
            lambda d: d["calls"].update(priority=1.0), lambda d: d["fields"]["category"].update(raw="pix"),
            lambda d: d["fields"]["category"].update(margin=.90), lambda d: d["fields"]["category"].update(reason="below_tau"),
            lambda d: d["fields"]["category"]["vector"]["scores"].reverse(), lambda d: d["applied"].pop("category"),
            lambda d: d.update(outcome="review"), lambda d: d["fields"]["category"].update(extra=False),
        ]:
            altered = deepcopy(honest)
            transform(altered)
            with self.assertRaises(ValueError):
                verify(item, frame, altered, self.context)
        item, frame = self.capture({"priority": True})
        decision = derive(item, frame, self.context)
        decision["received"]["priority"] = 1
        with self.assertRaises(ValueError):
            verify(item, frame, decision, self.context)

    def test_rejeita_contextos_alterados_e_schema_ipc_carregado_adulterado(self):
        for index in range(3):
            buffers = context_bytes()
            buffers[index] += b" "
            with self.assertRaises(ValueError):
                load_context(*buffers)
        item, frame = self.capture({})
        for transform in [
            lambda c: c["class_order"]["category"].reverse(), lambda c: c.update(extra=1),
            lambda c: c["capture_policy"]["priority"].update(delta=0),
            lambda c: c["selected_policy"]["category"].update(tau=.9),
            lambda c: c["capture_policy"].update(contract_version="sf2-r1-offline/1.0"),
            lambda c: c["model_sha256"].update(category="0" * 64),
        ]:
            context = deepcopy(self.context)
            transform(context)
            with self.assertRaises(ValueError):
                derive(item, frame, context)
        with patch.dict(core.validator("input").schema, {"additionalProperties": True}):
            with self.assertRaisesRegex(ValueError, "schema IPC carregado"):
                derive(item, frame, self.context)

    def test_schema_r1_vem_dos_mesmos_bytes_atestados_a_cada_uso(self):
        item, frame = self.capture({})
        honest = derive(item, frame, self.context)
        former_snapshot = identities._snapshot

        def altered(path):
            if path.name == "sf2-final-r1.schema.json":
                return b"{}"
            return former_snapshot(path)

        with patch.object(identities, "_snapshot", side_effect=altered):
            with self.assertRaisesRegex(ValueError, "schema R1"):
                verify(item, frame, honest, self.context)
