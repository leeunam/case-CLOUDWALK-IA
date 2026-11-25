"""Round-trip Safetensors/joblib e worker real com microencoder de fixture."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
import warnings

from ..adapter.test_decide import record
from ..contracts.core import FIELDS, LABELS, VERSION, read, sha256
from ..contracts.ipc import project, validate_decision
from .environment import check_pins, configure_cpu, load_body
from .fit import build_trainer, fit_specialist, preflight_tokenization, resolved_setfit_arguments, verify_reload
from .package import export_specialist, load_package, read_hashed, read_verified_package, score_vector, seal_package, write_json
from .scores import COLLECTION_POLICY, publish_new

FIXTURE = "fixture-sf2-03: parâmetros sintéticos, sem otimização de encoder ou cabeça"
MODULE = "script.classification_comparison.setfit_sf2.adapter"


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.versions = check_pins()
        configure_cpu()
        import numpy as np
        from setfit import SetFitModel
        from sklearn.linear_model import LogisticRegression
        from transformers import BertConfig, BertModel, BertTokenizer, set_seed

        set_seed(42)
        temp = TemporaryDirectory()
        cls.addClassCleanup(temp.cleanup)
        cls.fixture = Path(temp.name)
        base = cls.fixture / "bert-fixture"
        vocab = {word: index for index, word in enumerate(
            ("[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "fixture", "teste", "sf", "##2"))}
        tokenizer = BertTokenizer(vocab=vocab, model_max_length=128)
        config = BertConfig(vocab_size=len(vocab), hidden_size=8, num_hidden_layers=1,
                            num_attention_heads=2, intermediate_size=16, max_position_embeddings=128)
        BertModel(config).save_pretrained(base, safe_serialization=True)
        tokenizer.save_pretrained(base)

        cls.body = load_body(base)
        cls.root = cls.fixture / "pacote-fixture"
        cls.root.mkdir()
        freeze = cls.fixture / "training-freeze.json"
        arguments = cls.fixture / "arguments.json"
        write_json(arguments, {"fixture": FIXTURE})
        write_json(freeze, {
            "contract_version": VERSION,
            "files": {role: "0" * 64 for role in (
                "rubric", "catalog", "model_lock", "requirements", "protocol", "contracts", "train",
                "validation", "annotations", "training_code", "public_manifest", "review_receipt", "token_lengths",
            )} | {"arguments": sha256(arguments)},
            "final_seal_sha256": "0" * 64,
        })
        cls.policy_path = cls.fixture / "policy.json"
        write_json(cls.policy_path, COLLECTION_POLICY)
        cls.examples = [{"id": "controle", "text": "fixture teste sf2"}]
        exports, cls.baseline = {}, {}
        for field, winner in zip(FIELDS, ("pix", "urgent"), strict=True):
            classes = sorted(LABELS[field])
            head = LogisticRegression()
            head.classes_ = np.array(classes)
            head.coef_ = np.zeros((len(classes), 8))
            head.intercept_ = np.array([5.0 if label == winner else 0.0 for label in classes])
            head.n_features_in_ = 8
            head.n_iter_ = np.array([0])
            model = SetFitModel(model_body=cls.body, model_head=head)
            cls.baseline[field] = [score_vector(model, example["text"]) for example in cls.examples]
            exports[field] = export_specialist(cls.root, field, model, {"fixture": FIXTURE}, {"fixture": FIXTURE})
        cls.digest = seal_package(cls.root, freeze, arguments, exports, cls.versions)

    def worker(self, lines, package_digest=None):
        return subprocess.run(
            [sys.executable, "-B", "-m", MODULE, "--package", self.root,
             "--package-sha256", package_digest or self.digest, "--policy", self.policy_path],
            input="".join(json.dumps(line) + "\n" for line in lines), text=True, capture_output=True, timeout=45,
        )

    def test_receita_resolvida_pelo_trainer_real_sem_chamar_train(self):
        train = [{"text": "fixture " + label, "gold": {"category": label}, "id": "omitido",
                  "partition": "train"} for label in LABELS["category"]]
        model, trainer, applied = build_trainer("category", self.body, train, self.fixture)
        self.assertEqual(trainer.train_dataset.column_names, ["text", "label"])
        self.assertEqual(applied, {"num_epochs": 1, "num_iterations": 5, "batch_size": 8,
                                   "body_learning_rate": 2e-5, "seed": 42})
        self.assertEqual(model.model_head.get_params()["class_weight"], "balanced")
        self.assertEqual(model.model_head.get_params()["max_iter"], 1000)
        self.assertEqual(model.model_head.get_params()["random_state"], 42)
        self.assertIsNone(trainer.eval_dataset)
        evidence = json.loads(json.dumps(resolved_setfit_arguments(trainer.args), allow_nan=False))
        self.assertEqual(evidence["loss"], "CosineSimilarityLoss")

    def test_aviso_de_convergencia_interrompe_sem_confirmacao(self):
        from setfit import Trainer
        from sklearn.exceptions import ConvergenceWarning

        train = [{"text": "fixture " + label, "gold": {"category": label}} for label in LABELS["category"]]
        control = Mock()
        control.recv.return_value = b"K"

        def warn():
            warnings.warn("controle de convergência", ConvergenceWarning)

        with patch.object(Trainer, "train", side_effect=warn), self.assertRaises(ConvergenceWarning):
            fit_specialist("category", self.body, train, self.fixture, control)
        control.sendall.assert_called_once_with(b"S")

    def test_prevoo_confere_recibo_e_recusa_texto_longo(self):
        with self.assertRaisesRegex(ValueError, "diverge do recibo"):
            preflight_tokenization(self.body, self.examples, {"lengths": {"controle": 1}})
        past_limit = [{**self.examples[0], "text": "fixture " * 129}]
        with self.assertRaisesRegex(ValueError, "excede 128"):
            preflight_tokenization(self.body, past_limit, {"lengths": {"controle": 128}})

    def test_reload_reproduz_scores_decisoes_e_identidades(self):
        package = load_package(self.root, self.digest, self.versions)
        checks = verify_reload(package, self.examples, self.baseline)
        self.assertEqual(len(checks), 2)
        self.assertLessEqual(max(item["max_abs_score_diff"] for item in checks), 1e-6)

    def test_integridade_recusa_hash_inventario_e_cabeca_alterados(self):
        import joblib

        with patch.object(joblib, "load", side_effect=AssertionError("não deve desserializar")) as loader:
            with self.assertRaisesRegex(ValueError, "SHA-256 confiável"):
                load_package(self.root, "f" * 64, self.versions)
            extra = self.root / "category/body/extra.json"
            extra.touch()
            try:
                with self.assertRaisesRegex(ValueError, "fora do inventário"):
                    load_package(self.root, self.digest, self.versions)
            finally:
                extra.unlink()
            head = self.root / "category/head/logistic.joblib"
            original = head.read_bytes()
            try:
                head.write_bytes(b"fixture adulterada")
                with self.assertRaisesRegex(ValueError, "SHA-256 divergente"):
                    load_package(self.root, self.digest, self.versions)
            finally:
                head.write_bytes(original)
            loader.assert_not_called()

    def test_worker_real_ready_jsonl_preservacao_e_texto_longo(self):
        given = project(record({"category": "terminal"}))
        long = {**given, "id": "fixture-longa", "text": "fixture " * 129}
        result = self.worker((given, long))
        self.assertEqual(result.returncode, 0, result.stderr)
        ready, output, too_long = result.stdout.splitlines()
        self.assertEqual(ready, '{"type":"ready"}')
        manifest, _ = read_verified_package(self.root, self.digest)
        identities = {"package_sha256": self.digest, "model_sha256": manifest["model_sha256"],
                      "policy_sha256": sha256(self.policy_path)}
        validate_decision(given, json.loads(output), COLLECTION_POLICY, manifest["class_order"], identities)
        validate_decision(long, json.loads(too_long), COLLECTION_POLICY, manifest["class_order"], identities,
                          interruption="too_long")
        self.assertEqual(json.loads(output)["received"], {"category": "terminal"})
        self.assertEqual(json.loads(output)["calls"], {"category": 0, "priority": 1})
        self.assertEqual(json.loads(output)["applied"], {"priority": "urgent"})

    def test_worker_envelope_invalido_interrompe_e_log_fica_em_stderr(self):
        invalid = {**project(record({})), "gold": {}}
        result = self.worker((invalid,))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '{"type":"ready"}\n')
        self.assertIn("Worker SF2 encerrado", result.stderr)

    def test_publicacao_unica_e_hash_do_journal(self):
        output = self.fixture / "score-package-fixture.json"
        bundle = {"fixture": FIXTURE}
        publish_new(output, bundle)
        self.assertEqual(read_hashed(output, sha256(output)), bundle)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            read_hashed(output, "1" * 64)
        with self.assertRaises(FileExistsError):
            publish_new(output, {"fixture": "substituição"})
        self.assertEqual(read(output), bundle)
        jsonl = self.fixture / "fixture-with-line-separator.jsonl"
        row = {"text": "texto\u2028de controle"}
        jsonl.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        self.assertEqual(read_hashed(jsonl, sha256(jsonl), jsonl=True), [row])


if __name__ == "__main__":
    unittest.main()
