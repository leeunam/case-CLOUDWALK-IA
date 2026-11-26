"""Vetores públicos do contrato HTTP. Reproduz decisões com frames sintéticos e sem inferência."""

import hashlib
import json
import unittest
from pathlib import Path

from script.classification_comparison.setfit_sf2.contracts import ipc
from script.classification_comparison.setfit_sf2.runtime_r1 import derive, load_context, verify

DIRECTORY = Path(__file__).resolve().parent
FIXTURES = DIRECTORY / "fixtures"
ROOT = DIRECTORY.parents[2]
EVIDENCE = ROOT / "docs/evidencias/c05/sf2"
QUALIFIED = EVIDENCE / "qualificacao-01/execucao-02"


def read(path):
    return json.loads(path.read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def catalog_bytes(catalog):
    return json.dumps(catalog, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class HttpVectorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pins = read(DIRECTORY / "pins.json")
        cls.request = read(FIXTURES / "request.json")
        cls.context = load_context(
            (QUALIFIED / "avaliacao/capture-policy.json").read_bytes(),
            (EVIDENCE / "revisao-01/selected-policy.json").read_bytes(),
            (QUALIFIED / "pacote/manifest.json").read_bytes(),
        )
        cls.item = ipc.project(cls.request, {"version": cls.pins["ipc_catalog_version"], **cls.request["catalog"]})

    def test_catalog_vector(self):
        catalog = self.request["catalog"]
        for mapping in (catalog, *catalog.values()):
            self.assertEqual(list(mapping), sorted(mapping, reverse=True))
        data = catalog_bytes(catalog)
        self.assertEqual(data, (FIXTURES / "catalog-canonical.json").read_bytes())
        self.assertEqual(len(data), 449)
        self.assertEqual(digest(data), "0cadca6fc5e2291b3e471df649d098123bf01cb8b422803c45b6cb9f22d63807")
        changed = {**catalog, "category": {**catalog["category"], "pix": catalog["category"]["pix"] + "!"}}
        self.assertNotEqual(digest(catalog_bytes(changed)), digest(data))
        next_version = {**self.request, "catalog_version": self.request["catalog_version"] + 1}
        self.assertNotEqual(next_version["catalog_version"], self.request["catalog_version"])
        self.assertEqual(digest(catalog_bytes(next_version["catalog"])), digest(data))

    def test_public_pins_match_qualified_sources(self):
        pins, context = self.pins, self.context
        for key in ("capture_policy", "capture_policy_sha256", "model_sha256", "package_sha256", "class_order"):
            self.assertEqual(pins[key], context[key])
        self.assertEqual(pins["decision_policy"], context["selected_policy"])
        self.assertEqual(pins["decision_policy_sha256"], context["selected_policy_sha256"])
        inventory = QUALIFIED / "avaliacao/adapter.json"
        self.assertEqual(pins["worker_inventory_sha256"], digest(inventory.read_bytes()))
        self.assertEqual(pins["worker_files"], read(inventory)["files"])
        release = EVIDENCE / "final-r1-preparacao-02/final-fix-publico/release.json"
        freeze = release.with_name("freeze.json")
        self.assertEqual(pins["release_sha256"], digest(release.read_bytes()))
        self.assertEqual(pins["freeze_sha256"], read(release)["freeze_sha256"])
        self.assertEqual(pins["freeze_sha256"], digest(freeze.read_bytes()))
        frozen = read(freeze)["current_sources"]
        for filename, value in pins["runtime_files"].items():
            self.assertEqual(value, frozen[filename])

    def test_token_boundary_vectors_pair_with_refusal(self):
        at_limit, above_limit = read(FIXTURES / "token-boundaries.json")
        for vector, length in ((at_limit, 128), (above_limit, 129)):
            self.assertEqual(vector["text"], " ".join(["a"] * (length - 2)))
            self.assertEqual(vector["qualified_tokens"], dict(category=length, priority=length))
            self.assertIs(vector["admitted"], length == 128)
        self.assertEqual(read(FIXTURES / "422-text-out-of-scope.json"),
                         dict(contract_version=self.pins["contract_version"], error="text_out_of_scope"))

    def test_verified_http_projection(self):
        for outcome in ("complete", "review", "error"):
            with self.subTest(outcome=outcome):
                frame = (FIXTURES / f"{outcome}.jsonl").read_bytes()
                decision = derive(self.item, frame, self.context)
                verify(self.item, frame, decision, self.context)
                response = read(FIXTURES / f"response-{outcome}.json")
                self.assertEqual(decision["outcome"], outcome)
                self.assertEqual(decision["contract_version"], self.pins["decision_namespace"])
                self.assertEqual(decision["received"], self.request["received"])
                projection = {
                    key: decision[key] for key in ("id", "outcome", "applied", "calls", "fields",
                                                   "package_sha256", "model_sha256", "capture_policy_sha256")
                }
                projection.update(
                    contract_version=self.request["contract_version"], catalog_version=self.request["catalog_version"],
                    catalog_sha256=digest(catalog_bytes(self.request["catalog"])),
                    decision_policy_sha256=decision["selected_policy_sha256"], raw_frame_sha256=decision["raw_sha256"],
                )
                self.assertGreaterEqual(response.pop("elapsed_ms"), 0)
                self.assertEqual(response, projection)
                self.assertNotEqual(response["raw_frame_sha256"], digest(frame.rstrip(b"\n")))

    def test_too_long_frame_without_pre_admission_proof_is_rejected_by_r1(self):
        frame = read(FIXTURES / "complete.jsonl")
        frame.update(outcome="review", applied={}, calls={"category": 0, "priority": 0})
        frame["fields"]["priority"].update(decision="review", reason="too_long", raw=None, vector=None, margin=None)
        line = json.dumps(frame).encode() + b"\n"
        self.assertEqual(read(FIXTURES / "502-invalid-worker-frame.json")["error"], "invalid_worker_frame")
        with self.assertRaises(ValueError):
            derive(self.item, line, self.context)


if __name__ == "__main__":
    unittest.main()
