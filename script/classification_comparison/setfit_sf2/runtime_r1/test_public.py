"""Paridade da única política fixa com 90 frames públicos e os cinco controles."""
import gzip
from hashlib import sha256
from unittest import TestCase

from ..contracts.core import FIELDS, PLAN, decode, read
from ..contracts.ipc import project
from ..evaluation.metrics import metrics, quality_gates
from ..evaluation.runner import controls
from ..evaluation.selection import prepare_replay
from . import derive, load_context, verify
from .context import same_json
from .test_runtime import CAPTURE, R1, context_bytes


class PublicParityTests(TestCase):
    def test_frames_por_id_e_metricas_completas_da_linha_selecionada(self):
        fixed = read(PLAN / "sf2-final-r1-protocolo.json")
        parent = read(PLAN / "sf2-r1-protocolo.json")["parent"]["files"]

        def checked(path, expected):
            data = path.read_bytes()
            self.assertEqual(sha256(data).hexdigest(), expected)
            return data

        def public_bytes(role, path):
            return checked(path, parent[role]["sha256"])

        folder = CAPTURE / "avaliacao/validation"
        records = [decode(line) for line in public_bytes("validation", PLAN / "dados/validation.jsonl").splitlines()]
        scores = decode(public_bytes("scores04", folder / "scores.json"))
        context = load_context(*context_bytes())
        policy = context["selected_policy"]

        raw_cases = public_bytes("predictions", folder / "run/predictions.jsonl").splitlines(keepends=True)
        raw_controls = public_bytes("controls", folder / "run/controls.jsonl").splitlines(keepends=True)
        self.assertEqual((len(records), len(raw_cases), len(raw_controls)), (90, 90, 5))

        def consume(row, frame):
            item = project(row)
            decision = derive(item, frame, context)
            verify(item, frame, decision, context)
            self.assertEqual(decision["id"], row["id"])
            raw = decode(frame)
            for field in FIELDS:
                before, after = raw["fields"][field], decision["fields"][field]
                for name in ("vector", "raw", "margin"):
                    self.assertTrue(same_json(before[name], after[name]))
                if before["decision"] == after["decision"]:
                    self.assertEqual(before["reason"], after["reason"])
                else:
                    self.assertEqual((before["decision"], after["reason"]), ("accept", "below_tau"))
            return decision

        decisions = []
        for row, frame in zip(records, raw_cases, strict=True):
            with self.subTest(id=row["id"]):
                result = consume(row, frame)
                # Em um único ID, a matriz identifica o argmax e as contagens por campo
                # identificam cada abstenção. Cobertura, acerto e aplicação também são auditados.
                replay = prepare_replay([row], scores, 0)
                self.assertEqual(metrics([row], [result], 0), replay(policy))
                decisions.append(result)
        first = decisions[0]
        example = fixed["runtime_api"]["example_public"]
        self.assertEqual({**{key: first[key] for key in example if key != "priority_reason"},
                          "priority_reason": first["fields"]["priority"]["reason"]}, example)
        priority = first["fields"]["priority"]
        self.assertEqual(priority["raw"], "advanced")
        self.assertEqual(max(priority["vector"]["scores"]), .6313874585281872)

        sentinel = [consume(row, frame) for row, frame in zip(controls(), raw_controls, strict=True)]
        self.assertEqual([x["outcome"] for x in sentinel], ["complete", "review", "review", "review", "review"])
        self.assertEqual([[x["calls"][f] for f in FIELDS] for x in sentinel], [[0, 0], [0, 0], [1, 0], [0, 1], [1, 1]])
        self.assertTrue(all(x["applied"] == {} for x in sentinel))
        blocked_calls = sum(sum(x["calls"].values()) for x in sentinel[:2])

        archive = decode(gzip.decompress(checked(R1 / "result.json.gz", fixed["anchors_sha256"]["offline_result_gzip"])))
        self.assertEqual(archive["selected"], policy)
        selected, = [entry for entry in archive["policies"] if entry["policy"] == policy]
        totals = metrics(records, decisions, blocked_calls)
        self.assertEqual(totals, selected["metrics"])
        self.assertEqual(quality_gates(totals, "validation"), selected["gates"])
        self.assertTrue(selected["eligible"])
        self.assertEqual(selected["failed_gates"], [])
