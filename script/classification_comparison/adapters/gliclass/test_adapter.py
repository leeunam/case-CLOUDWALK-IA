import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch

from adapter import ABSTENTION, FIELDS, ROOT, Context, Worker, choice_from_output, infer, observe
from fake_runtime import load_fake
from model import ContextOverflow, FullTokenizer, HERE, PINS, load_pipeline, verify_snapshot


ENV = {
    "CLASSIFICATION_RUBRIC": str(ROOT / "docs/planejamento/classificacao-comparativa/rubrica-comum.md"),
    "CLASSIFICATION_PROMPT": str(HERE / "prompt.json"),
    "CLASSIFICATION_POLICY": str(HERE / "policy.json"),
}
IDENTITY = {"mode": "fixture"}


def scores(labels, values):
    return [[dict(label=label, score=value) for label, value in zip(labels, values, strict=True)]]


def load_with_failure(policy):
    fallback, info = load_fake(policy)

    def pipeline(text, labels, **options):
        if text == "Teste parcial" and "prioridade" in options["prompt"]:
            raise ValueError("erro injetado")
        if text == "Teste de prazo":
            time.sleep(1)
        return fallback(text, labels, **options)
    return pipeline, info


def fail_load(policy):
    raise FileNotFoundError("checkpoint de teste ausente")


class AdapterTest(unittest.TestCase):
    def setUp(self):
        self.context = Context.load(ENV)
        self.item = dict(contract_version="1.1.0", id="sem-gabarito", text="Texto íntegro\nCom U+2028: \u2028",
                         catalog=self.context.catalog, received={}, missing=list(FIELDS))

    def worker(self, loader=load_fake, context=None):
        worker = Worker(loader, context or self.context)
        self.addCleanup(worker.close)
        return worker

    def test_mapping_retains_exact_text_and_all_urgent_and_abstention_criteria(self):
        item = dict(self.item, received={"category": "pix"}, missing=["priority"])
        text, labels, prompt = self.context.request(item, "priority")

        self.assertEqual(text, item["text"])
        self.assertEqual(set(labels.values()), set(self.context.catalog["priority"]) | {ABSTENTION})
        for label, code in labels.items():
            self.assertIn(self.context.definitions["priority"][code], label)
            self.assertIn(self.context.catalog["priority"].get(code, ""), label)
        self.assertIn("perda em andamento", next(label for label, code in labels.items() if code == "urgent"))
        self.assertIn("fatos sobre impacto/prazo/funcionamento", next(label for label, code in labels.items() if code == ABSTENTION))
        self.assertIn("sem depender de uma palavra-chave isolada", prompt)
        self.assertIn("category: pix", prompt)
        self.assertNotIn(item["id"], prompt)

    def test_category_mapping_retains_catalog_and_full_abstention(self):
        _, labels, prompt = self.context.request(self.item, "category")
        self.assertEqual(set(labels.values()), {"pix", "payouts", "terminal", ABSTENTION})
        self.assertIn("uma operação mencionados isoladamente", next(label for label, code in labels.items() if code == ABSTENTION))
        self.assertNotIn("urgência/impacto", prompt)

    def test_pipeline_gets_original_text_and_zero_examples(self):
        text, labels, prompt = self.context.request(self.item, "category")
        pipeline = Mock(return_value=scores(labels, [0.1, 0.8, 0.1, 0.3]))
        result = infer(pipeline, (text, labels, prompt), self.context.policy)
        pipeline.assert_called_once_with(text, list(labels), prompt=prompt, examples=None, batch_size=1, threshold=0)
        self.assertEqual(result, dict(status="predicted", raw="pix", reason=None, score={"kind": "ranking", "value": 0.8}))

    def test_explicit_abstention_and_tie(self):
        labels = {"pix com descrição": "pix", "abstenção com definição": ABSTENTION}
        explicit = choice_from_output(scores(labels, [0.1, 0.92]), labels, "ranking")
        tied = choice_from_output(scores(labels, [0.92, 0.92]), labels, "ranking")
        self.assertEqual((explicit["reason"], explicit["raw"]), ("explicit", ABSTENTION))
        self.assertEqual((tied["reason"], tied["raw"]), ("policy", {"tied_codes": ["pix", ABSTENTION]}))

    def test_empty_missing_and_invalid_outputs(self):
        labels = {"pix": "pix", "abstenção": ABSTENTION}
        invalid = [
            None, [[{}]], [[{"label": "fora", "score": .5}]], scores(labels, [float("nan"), .1]),
            scores(labels, [False, .1]), [[{"label": "pix", "score": .5}] * 2],
        ]
        for value in invalid:
            with self.subTest(value=value):
                self.assertEqual(choice_from_output(value, labels, "ranking")["reason"], "invalid_output")
        for value in ([[]], [[{"label": "pix", "score": .5}]]):
            self.assertEqual(choice_from_output(value, labels, "ranking")["reason"], "missing_output")

    def test_truncation_is_disabled_before_tokenizing(self):
        input_ids = SimpleNamespace(shape=(1, 513))
        tokenizer = Mock(return_value={"input_ids": input_ids})
        guarded = FullTokenizer(tokenizer, 512)
        with self.assertRaisesRegex(ContextOverflow, "513"):
            guarded(["Texto, critérios e rótulos"], truncation=True, max_length=512, return_tensors="pt")
        tokenizer.assert_called_once_with(["Texto, critérios e rótulos"], truncation=False, return_tensors="pt")
        input_ids.shape = (1, 512)
        self.assertIs(guarded("No limite", truncation=True)["input_ids"], input_ids)

    def test_public_tokenizer_sentinel_keeps_encoder_limit_in_pipeline(self):
        encoder = SimpleNamespace(max_position_embeddings=512)
        config = SimpleNamespace(architecture_type="uni-encoder", encoder_config=encoder)
        model = SimpleNamespace(config=config)
        tokenizer = Mock(model_max_length=1000000000000000019884624838656)
        pipeline = Mock()
        modules = {
            "torch": Mock(),
            "gliclass": SimpleNamespace(GLiClassModel=Mock(**{"from_pretrained.return_value": (model, {})}),
                                        ZeroShotClassificationPipeline=pipeline),
            "transformers": SimpleNamespace(AutoTokenizer=Mock(**{"from_pretrained.return_value": tokenizer})),
        }
        with patch.dict(os.environ), patch.dict(sys.modules, modules), patch("model.verify_snapshot"), \
                patch("model.metadata.version", side_effect=PINS.__getitem__):
            _, info = load_pipeline(dict(self.context.policy, max_tokens=1024))
        guarded_tokenizer = pipeline.call_args.args[1]
        self.assertEqual(info["tokens"], 512)
        self.assertEqual(pipeline.call_args.kwargs["max_length"], 512)
        self.assertEqual(guarded_tokenizer.limit, 512)

    def test_invalid_catalog_complete_and_invalid_values_block_dispatch(self):
        self.assertFalse(self.context.eligible(dict(self.item, catalog={})))
        self.assertFalse(self.context.eligible(dict(self.item, received={"category": "pix", "priority": "urgent"}, missing=[])))
        self.assertFalse(self.context.eligible(dict(self.item, received={"category": 5}, missing=["priority"])))
        self.assertTrue(self.context.eligible(dict(self.item, received={"priority": "  \t"})))
        self.assertTrue(self.context.eligible(dict(self.item, received={"category": "pix"}, missing=["priority"])))

    def test_partial_failure_retains_candidate_observation(self):
        worker = self.worker(load_with_failure)
        self.assertIn("load_ms", worker.receive(time.monotonic() + 2))
        result = observe(dict(self.item, text="Teste parcial"), worker, self.context,
                         IDENTITY, "run", "fake", None)
        self.assertEqual(result["choices"]["category"]["status"], "predicted")
        self.assertEqual(result["choices"]["priority"]["reason"], "adapter_error")
        self.assertEqual(result["questions"], 2)
        self.assertEqual(len(result["request_usage"]), 2)
        self.assertIsNone(result["request_usage"][0]["observed_api_usd"])

    def test_deadline_stops_worker_and_no_second_dispatch_occurs(self):
        policy = dict(self.context.policy, case_timeout_ms=200, response_reserve_ms=30)
        context = replace(self.context, policy=policy)
        worker = self.worker(load_with_failure, context)
        worker.receive(time.monotonic() + 2)
        result = observe(dict(self.item, text="Teste de prazo"), worker, context,
                         IDENTITY, "run", "fake", None)
        self.assertEqual([choice["reason"] for choice in result["choices"].values()], ["timeout", "timeout"])
        self.assertEqual((result["requests"], result["questions"]), (1, 1))
        self.assertIsNone(result["inference_ms"])
        worker.process.join(timeout=1)
        after = observe(self.item, worker, context, IDENTITY, "run", "fake", None)
        self.assertEqual(after["requests"], 0)
        self.assertEqual(after["choices"]["priority"]["reason"], "adapter_error")

    def test_missing_checkpoint_precedes_readiness(self):
        worker = self.worker(fail_load)
        with self.assertRaises(EOFError):
            worker.receive(time.monotonic() + 2)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                verify_snapshot(Path(directory))

    def test_real_candidate_records_zero_api_billing_not_token_counts(self):
        worker = self.worker()
        worker.receive(time.monotonic() + 2)
        result = observe(dict(self.item, received={"category": "pix"}, missing=["priority"]), worker,
                         self.context, {"mode": "real"}, "run", "example", "revision")
        self.assertEqual(set(result["choices"]), {"priority"})
        self.assertEqual((result["requests"], result["questions"]), (1, 1))
        self.assertEqual(result["request_usage"][0]["observed_api_usd"], 0)
        self.assertIsNone(result["request_usage"][0]["input_tokens"])

    def test_c02_dispatches_natural_controls_and_keeps_its_injection(self):
        evidence = HERE / "evidence"
        evidence.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=evidence) as temporary:
            output = Path(temporary) / "test-bundle"
            subprocess.run([sys.executable, "-B", "script/classification_comparison/run.py",
                            "--mode", "fixture", "--split", "development", "--limit", "3",
                            "--config", str(HERE / "fixture.json"), "--output", str(output)],
                           cwd=ROOT, check=True, capture_output=True)
            observations = [json.loads(line) for line in (output / "observations.jsonl").read_text().splitlines()]
            report = json.loads((output / "report.json").read_text())
            self.assertEqual(sum(row["origin"] == "candidate" for row in observations), 11)
            self.assertEqual(sum(row["origin"] == "injected_control" for row in observations), 1)
            self.assertEqual(len((output / "decisions.jsonl").read_text().splitlines()), 16)
            self.assertIsNone(report["environment"]["peak_memory_bytes"])
            self.assertEqual(sum(row["id"].startswith("ctl-") and row["origin"] == "candidate"
                                 for row in observations), 8)


if __name__ == "__main__":
    unittest.main()
