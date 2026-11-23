import hashlib
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
from model import FILES, ContextOverflow, FullTokenizer, HERE, LABEL_SEPARATOR, PINS, load_pipeline, snapshot_manifest, verify_snapshot


ENV = {
    "CLASSIFICATION_RUBRIC": str(ROOT / "docs/planejamento/classificacao-comparativa/rubrica-comum.md"),
    "CLASSIFICATION_PROMPT": str(HERE / "prompt.json"),
    "CLASSIFICATION_POLICY": str(HERE / "policy.json"),
}
IDENTITY = {"mode": "fixture"}
MATRIX = json.loads((HERE / "development-matrix.json").read_text())["profiles"]


def profile_context(profile):
    row = MATRIX[profile]
    return Context.load(dict(ENV, CLASSIFICATION_PROMPT=str(ROOT / row["prompt"]["path"]),
                             CLASSIFICATION_POLICY=str(ROOT / row["policy"]["path"])))


def scores(labels, values):
    return [[dict(label=label, score=value) for label, value in zip(labels, values, strict=True)]]


def load_with_failure(policy, on_forward):
    fallback, info = load_fake(policy, on_forward)

    def pipeline(text, labels, **options):
        if text == "Teste de preparação":
            raise ContextOverflow("tokenizer recusou antes do forward")
        priority = options["prompt"].startswith("Determine a prioridade")
        if text == "Teste parcial" and priority:
            on_forward()
            raise ValueError("erro injetado no forward")
        if text == "Teste de morte do worker":
            on_forward()
            os._exit(9)
        if text == "Teste de prazo" or (text == "Teste de prazo parcial" and priority):
            on_forward()
            time.sleep(1)
            raise AssertionError("caso sintético deve ser interrompido no prazo")
        return fallback(text, labels, **options)
    return pipeline, info


def fail_load(policy, on_forward):
    raise FileNotFoundError("checkpoint de teste ausente")


class AdapterTest(unittest.TestCase):
    def setUp(self):
        self.context = Context.load(ENV)
        self.item = dict(contract_version="1.1.0", id="sem-gabarito", brand="marca-sintetica", text="Texto íntegro\nCom U+2028: \u2028",
                         catalog=self.context.catalog, received={}, missing=list(FIELDS))

    def worker(self, loader=load_fake, context=None):
        worker = Worker(loader, context or self.context)
        self.addCleanup(worker.close)
        return worker

    def test_each_single_question_retains_full_context_and_integral_text(self):
        for target, provided, code in (("category", "priority", "basic"), ("priority", "category", "pix")):
            item = dict(self.item, received={provided: code}, missing=[target], expected="gabarito-secreto")
            with self.subTest(target=target):
                query = self.context.request(item, (target,))
                text, labels, prompt = query.text, query.labels_by_field[target], query.prompt
                context_str = prompt.split("Contexto do atendimento (JSON):\n", 1)[1].split("\n", 1)[0]
                context = json.loads(context_str)
                self.assertEqual(text, item["text"])
                self.assertEqual(context["marca"], item["brand"])
                self.assertEqual(context["mascara_de_omissao"], [target])
                self.assertEqual(context["campos_recebidos"], {
                    provided: {"valor": code, "significado": self.context.catalog[provided][code]}})
                self.assertEqual(context["catalogo"], self.context.catalog)
                self.assertEqual(prompt.count(self.context.rubric), 1)
                self.assertEqual(labels, {key: key for key in (*self.context.catalog[target], ABSTENTION)})
                self.assertNotIn(item["id"], prompt)
                self.assertNotIn(item["expected"], prompt)

    def test_each_double_question_retains_both_omissions_and_the_same_rubric(self):
        item = dict(self.item, received={"category": None, "priority": " "})
        for field in FIELDS:
            query = self.context.request(item, (field,))
            labels, prompt = query.labels_by_field[field], query.prompt
            context_str = prompt.split("Contexto do atendimento (JSON):\n", 1)[1].split("\n", 1)[0]
            context = json.loads(context_str)
            self.assertEqual(context["mascara_de_omissao"], list(FIELDS))
            self.assertEqual(context["campos_recebidos"], {
                "category": {"valor": None, "significado": "campo ausente"},
                "priority": {"valor": " ", "significado": "campo ausente"},
            })
            self.assertIn(self.context.rubric, prompt)
            self.assertEqual(set(labels), {*self.context.catalog[field], ABSTENTION})

    def test_pipeline_gets_original_text_and_zero_examples(self):
        query = self.context.request(self.item, ("category",))
        labels = query.labels_by_field["category"]
        pipeline = Mock(return_value=scores(labels, [0.1, 0.8, 0.1, 0.3]))
        result = infer(pipeline, query, self.context.policy)
        pipeline.assert_called_once_with(query.text, list(labels), prompt=query.prompt,
                                         examples=None, batch_size=1, threshold=0)
        self.assertEqual(result["category"], dict(status="predicted", raw="pix", reason=None,
                                                 score={"kind": "ranking", "value": 0.8}))

    def test_explicit_abstention_and_tie(self):
        labels = {"pix com descrição": "pix", "abstenção com definição": ABSTENTION}
        explicit = choice_from_output(scores(labels, [0.1, 0.92]), labels, "ranking")
        tied = choice_from_output(scores(labels, [0.92, 0.92]), labels, "ranking")
        self.assertEqual((explicit["reason"], explicit["raw"]), ("explicit", ABSTENTION))
        self.assertEqual((tied["reason"], tied["raw"]), ("policy", {"tied_codes": ["pix", ABSTENTION]}))

    def test_absent_output_has_null_raw(self):
        labels = {"pix": "pix", ABSTENTION: ABSTENTION}
        for value in (None, [], [[]]):
            self.assertEqual(choice_from_output(value, labels, "ranking"),
                             dict(status="invalid", raw=None, reason="missing_output", score=None))

    def test_invalid_output_preserves_raw_unknown_labels_and_partial_scores(self):
        labels = {"pix": "pix", ABSTENTION: ABSTENTION}
        for value, raw in [
            ([[{}]], [[{}]]),
            ([[{"label": "fora", "score": .99}]], [[{"label": "fora", "score": .99}]]),
            (scores(labels, [False, .1]), scores(labels, [False, .1])),
            ([[{"label": "pix", "score": .5}]], [[{"label": "pix", "score": .5}]]),
            ("pix", {"valor": "pix"}),
            (ABSTENTION, {"valor": ABSTENTION}),
        ]:
            with self.subTest(value=value):
                self.assertEqual(choice_from_output(value, labels, "ranking"),
                                 dict(status="invalid", raw=raw, reason="invalid_output", score=None))

    def test_invalid_output_is_serializable_without_nonfinite_json(self):
        labels = {"pix": "pix", ABSTENTION: ABSTENTION}
        for nonfinite in (float("nan"), float("inf"), float("-inf")):
            invalid = scores(labels, [nonfinite, .1])
            result = choice_from_output(invalid, labels, "ranking")
            self.assertEqual(result["reason"], "invalid_output")
            self.assertEqual(result["raw"], scores(labels, [None, .1]))
            json.dumps(result, allow_nan=False)
        self.assertEqual(choice_from_output(float("nan"), labels, "ranking")["raw"], {"valor": None})

    def test_truncation_is_disabled_before_tokenizing(self):
        input_ids = SimpleNamespace(shape=(1, 513))
        tokenizer = Mock(return_value={"input_ids": input_ids})
        guarded = FullTokenizer(tokenizer, 512)
        with self.assertRaisesRegex(ContextOverflow, "513"):
            guarded(["Texto, critérios e rótulos"], truncation=True, max_length=512, return_tensors="pt")
        tokenizer.assert_called_once_with(["Texto, critérios e rótulos"], truncation=False, return_tensors="pt")
        input_ids.shape = (1, 512)
        self.assertIs(guarded("No limite", truncation=True)["input_ids"], input_ids)

    def test_public_sentinel_is_metadata_and_policy_selects_context_limit(self):
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
        experimental = json.loads((HERE / "policy-dev-2048.json").read_text())
        for policy, expected in ((self.context.policy, 512), (experimental, 2048)):
            with self.subTest(limit=expected), patch.dict(os.environ), patch.dict(sys.modules, modules), \
                    patch("model.verify_snapshot"), patch("model.metadata.version", side_effect=PINS.__getitem__):
                _, info = load_pipeline(policy)
                guarded_tokenizer = pipeline.call_args.args[1]
                self.assertEqual(info["configured_context_tokens"], expected)
                self.assertEqual(info["encoder_max_position_embeddings"], 512)
                self.assertEqual(info["tokenizer_declared_model_max_length"], tokenizer.model_max_length)
                self.assertEqual(pipeline.call_args.kwargs["max_length"], expected)
                self.assertEqual(guarded_tokenizer.limit, expected)

    def test_native_hook_and_cpu_threads_match_profile(self):
        for profile, threads in (("C", 4), ("D", 2)):
            with self.subTest(profile=profile):
                model = Mock()
                model.config.architecture_type = "uni-encoder"
                torch = Mock()
                pipeline = Mock()
                tokenizer = Mock(model_max_length=2048)
                modules = {
                    "torch": torch,
                    "gliclass": SimpleNamespace(GLiClassModel=Mock(**{"from_pretrained.return_value": (model, {})}),
                                                ZeroShotClassificationPipeline=pipeline),
                    "transformers": SimpleNamespace(AutoTokenizer=Mock(**{"from_pretrained.return_value": tokenizer})),
                }
                callback = Mock()
                with patch.dict(os.environ), patch.dict(sys.modules, modules), patch("model.verify_snapshot"), \
                        patch("model.metadata.version", side_effect=PINS.__getitem__):
                    load_pipeline(profile_context(profile).policy, callback)
                    self.assertEqual(os.environ["OMP_NUM_THREADS"], str(threads))
                torch.set_num_threads.assert_called_once_with(threads)
                torch.set_num_interop_threads.assert_called_once_with(1)
                self.assertEqual(pipeline.call_args.kwargs["label_separator"], LABEL_SEPARATOR)
                model.register_forward_pre_hook.assert_called_once()
                callback.assert_not_called()
                model.register_forward_pre_hook.call_args.args[0](model, ())
                callback.assert_called_once_with()

    def test_snapshot_rejects_substitution_with_unchanged_size(self):
        public = snapshot_manifest()
        self.assertEqual(len(public), 7)
        self.assertEqual(sum(item["size"] for item in public.values()), 588168305)
        self.assertIn("lfs_sha256", public["tokenizer.json"])
        self.assertNotIn("lfs_sha256", public["config.json"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            files = {}
            for name in FILES:
                original = name.encode("ascii")
                (path / name).write_bytes(original)
                size = len(original)
                files[name] = {"size": size, "git_blob_sha1": hashlib.sha1(
                    f"blob {size}\0".encode("ascii") + original).hexdigest()}
                if "lfs_sha256" in public[name]:
                    files[name]["lfs_sha256"] = hashlib.sha256(original).hexdigest()
                    # Para LFS, o blob Git descreve o ponteiro e difere do conteúdo local.
                    files[name]["git_blob_sha1"] = "0" * 40

            with patch("model.snapshot_manifest", return_value=files):
                self.assertEqual(verify_snapshot(path), files["model.safetensors"]["lfs_sha256"])
                for name in ("tokenizer.json", "config.json"):
                    with self.subTest(name=name):
                        file = path / name
                        original = file.read_bytes()
                        file.write_bytes(b"x" * len(original))
                        with self.assertRaisesRegex(ValueError, name):
                            verify_snapshot(path)
                        file.write_bytes(original)

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
                         {"mode": "real"}, "run", "fake", None)
        self.assertEqual(result["temperature_state"], "warm")
        self.assertGreater(result["elapsed_ms"], 0)
        self.assertEqual([choice["reason"] for choice in result["choices"].values()], ["timeout", "timeout"])
        self.assertEqual((result["requests"], result["questions"]), (1, 1))
        self.assertIsNone(result["inference_ms"])
        worker.process.join(timeout=1)
        after = observe(self.item, worker, context, {"mode": "real"}, "run", "fake", None)
        self.assertEqual(after["temperature_state"], "unknown")
        self.assertGreaterEqual(after["elapsed_ms"], 0)
        self.assertIsNone(after["inference_ms"])
        self.assertEqual(after["attempt"], 1)
        self.assertEqual(after["requests"], 0)
        self.assertEqual(after["choices"]["priority"]["reason"], "adapter_error")

    def test_profile_configs_pin_prompt_policy_and_experiment_dimensions(self):
        self.assertEqual(set(MATRIX), {"A", "B", "C", "D"})
        policies = {}
        for profile, (threads, representation, layout) in {
            "A": (4, "codes", "separate"), "B": (4, "descriptive", "separate"),
            "C": (4, "descriptive", "grouped"), "D": (2, "descriptive", "grouped"),
        }.items():
            with self.subTest(profile=profile):
                row = MATRIX[profile]
                path = HERE / row["config"]
                config = json.loads(path.read_text())
                self.assertEqual(row["config_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                for key in ("prompt", "policy"):
                    self.assertEqual(config[key], row[key])
                    self.assertEqual(row[key]["sha256"], hashlib.sha256(
                        (ROOT / row[key]["path"]).read_bytes()).hexdigest())
                policy = policies[profile] = profile_context(profile).policy
                self.assertEqual((row["threads"], row["label_representation"], row["forward_layout"]),
                                 (threads, representation, layout))
                self.assertEqual((policy["threads"], policy.get("label_representation", "codes"),
                                  policy.get("forward_layout", "separate")), (threads, representation, layout))
                self.assertEqual(config["identity"]["policy_version"], policy["version"])
                self.assertEqual((policy["max_tokens"], policy["case_timeout_ms"], policy["response_reserve_ms"],
                                  policy["max_worker_rss_bytes"], policy["examples"]),
                                 (2048, 5000, 150, 6 * 1024**3, []))
        self.assertEqual({key for key in policies["B"] if policies["B"][key] != policies["C"][key]},
                         {"version", "forward_layout"})
        self.assertEqual({key for key in policies["C"] if policies["C"][key] != policies["D"][key]},
                         {"version", "threads"})
        self.assertEqual(MATRIX["B"]["prompt"], MATRIX["C"]["prompt"])
        self.assertEqual(MATRIX["C"]["prompt"], MATRIX["D"]["prompt"])

    def test_descriptive_projection_preserves_context_and_distinct_rubric_labels(self):
        item = dict(self.item, received={"category": None, "priority": " "}, expected="segredo")
        baseline, separate, grouped = (profile_context(profile) for profile in ("A", "B", "C"))
        query = grouped.request(item, FIELDS)
        for field in FIELDS:
            original = baseline.request(item, (field,))
            described = separate.request(item, (field,))
            self.assertEqual((described.text, described.prompt), (original.text, original.prompt))
            self.assertEqual(described.labels_by_field[field], query.labels_by_field[field])
            for code, description in grouped.catalog[field].items():
                self.assertEqual(query.labels_by_field[field][f"{code}: {description}"], code)
        common_suffix = original.prompt.split("Contexto do atendimento (JSON):", 1)[1]
        self.assertEqual(query.prompt.split("Contexto do atendimento (JSON):", 1)[1], common_suffix)
        self.assertEqual(query.text, item["text"])
        self.assertEqual(query.prompt.count(grouped.rubric), 1)
        self.assertNotIn(item["expected"], query.prompt)
        self.assertNotIn(item["id"], query.prompt)
        category = next(label for label, code in query.labels_by_field["category"].items() if code == ABSTENTION)
        priority = next(label for label, code in query.labels_by_field["priority"].items() if code == ABSTENTION)
        self.assertIn("operação mencionados isoladamente não provam uma categoria.", category)
        self.assertIn("Reconhecer a falta de informação não cria uma quinta prioridade.", priority)
        self.assertNotEqual(category, priority)

    def grouped_response(self, winners):
        context = profile_context("C")
        query = context.request(self.item, FIELDS)
        output = [[dict(label=f"{field}.{label}", score=0.9 if code == winners[field] else 0.1)
                   for field, labels in query.labels_by_field.items() for label, code in labels.items()]]
        return context, query, output

    def test_grouped_inverts_exact_flattened_labels_and_ranks_per_field(self):
        for expected in ({"category": "pix", "priority": "urgent"},
                         {"category": ABSTENTION, "priority": "urgent"},
                         {"category": "pix", "priority": ABSTENTION}):
            with self.subTest(expected=expected):
                context, query, output = self.grouped_response(expected)
                output[0].reverse()
                pipeline = Mock(return_value=output)
                result = infer(pipeline, query, context.policy)
                hierarchy = {field: list(labels) for field, labels in query.labels_by_field.items()}
                pipeline.assert_called_once_with(query.text, hierarchy, classification_type="multi-label",
                                                 return_hierarchical=False, prompt=query.prompt, examples=None,
                                                 batch_size=1, threshold=0)
                self.assertEqual(sum(map(len, hierarchy.values())), 9)
                for field, code in expected.items():
                    self.assertEqual(result[field]["raw"], code)
                    self.assertEqual(result[field]["score"], {"kind": "ranking", "value": 0.9})
                    self.assertEqual(result[field]["status"], "abstained" if code == ABSTENTION else "predicted")

    def assert_review_without_application(self, item, result):
        with patch.object(sys, "path", [str(HERE.parents[1]), *sys.path]):
            from common import decide
        decision = decide(item, {"choices": result}, self.context.catalog, "run")
        self.assertEqual(decision["outcome"], "review")
        self.assertTrue(all(field["applied"] is None for field in decision["fields"].values()))

    def test_grouped_rejects_missing_duplicate_unexpected_and_invalid_scores(self):
        context, query, output = self.grouped_response({"category": "pix", "priority": "urgent"})
        row, *rest = output[0]
        invalid = [
            ("missing_label", rest, True),
            ("duplicate_label", [*output[0], row], True),
            ("absent_score", [{"label": row["label"]}, *rest], True),
            ("unexpected_label", [dict(row, label=row["label"] + " "), *rest], False),
            ("absent_label_key", [{"score": .1}, *rest], False),
            ("nan", [dict(row, score=float("nan")), *rest], True),
            ("infinity", [dict(row, score=float("inf")), *rest], True),
            ("boolean", [dict(row, score=True), *rest], True),
        ]
        for name, rows, known_field in invalid:
            with self.subTest(name=name):
                result = infer(Mock(return_value=[rows]), query, context.policy)
                self.assertEqual(result["category"]["status"], "invalid")
                self.assertIsNone(result["category"]["score"])
                self.assertEqual(result["priority"]["status"], "predicted" if known_field else "invalid")
                json.dumps(result, allow_nan=False)
                self.assert_review_without_application(self.item, result)

        # A ausência integral de uma lista de campo não recebe scores inventados.
        only_priority = [[row for row in output[0] if row["label"].startswith("priority.")]]
        result = infer(Mock(return_value=only_priority), query, context.policy)
        self.assertEqual(result["category"], dict(status="invalid", raw=None, reason="missing_output", score=None))
        self.assert_review_without_application(self.item, result)

    def test_profiles_count_forwards_questions_and_usage_on_natural_controls(self):
        fixture = json.loads((HERE / "fixture.json").read_text())
        evidence = HERE / "evidence"
        evidence.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=evidence) as directory:
            for profile, forwards in (("A", 2), ("B", 2), ("C", 1), ("D", 1)):
                with self.subTest(profile=profile):
                    row = MATRIX[profile]
                    config = dict(fixture, prompt=row["prompt"], policy=row["policy"],
                                  identity=dict(fixture["identity"], policy_version=row["policy"]["version"]))
                    path, output = (Path(directory) / f"{profile}{suffix}" for suffix in (".json", "-bundle"))
                    path.write_text(json.dumps(config))
                    run = subprocess.run([sys.executable, "-B", "script/classification_comparison/run.py",
                                          "--mode", "fixture", "--split", "development", "--limit", "3",
                                          "--config", str(path), "--output", str(output)], cwd=ROOT,
                                         capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    observations = {obs["id"]: obs for obs in
                                    map(json.loads, (output / "observations.jsonl").read_text().splitlines())}
                    for control, counts in (("ctl-duplo", (forwards, 2)), ("ctl-simples", (1, 1))):
                        observation = observations[control]
                        self.assertEqual((observation["requests"], observation["questions"]), counts)
                        self.assertEqual(len(observation["request_usage"]), counts[0])
                        self.assertEqual(observation["origin"], "candidate")
                    self.assertEqual({choice["status"] for choice in observations["ctl-duplo"]["choices"].values()},
                                     {"predicted"})

    def test_grouped_timeout_and_preprocessing_do_not_invent_forwards(self):
        context = profile_context("C")
        context = replace(context, policy=dict(context.policy, case_timeout_ms=250, response_reserve_ms=30))
        worker = self.worker(load_with_failure, context)
        worker.receive(time.monotonic() + 2)
        identity = {"mode": "real"}  # Exercita a telemetria real com o pipeline sintético.
        before_forward = observe(dict(self.item, text="Teste de preparação"), worker, context,
                                 identity, "run", "fake", None)
        self.assertEqual((before_forward["requests"], before_forward["questions"]), (0, 0))
        self.assertEqual(before_forward["temperature_state"], "unknown")
        self.assertEqual(before_forward["request_usage"], [])
        timed_out = observe(dict(self.item, text="Teste de prazo"), worker, context, identity, "run", "fake", None)
        self.assertEqual((timed_out["requests"], timed_out["questions"]), (1, 2))
        self.assertEqual(len(timed_out["request_usage"]), 1)
        self.assertEqual(timed_out["temperature_state"], "warm")
        self.assertIsNone(timed_out["inference_ms"])
        self.assertEqual({choice["reason"] for choice in timed_out["choices"].values()}, {"timeout"})
        worker.process.join(timeout=1)
        self.assertFalse(worker.process.is_alive())
        self.assert_review_without_application(self.item, timed_out["choices"])
        after = observe(self.item, worker, context, identity, "run", "fake", None)
        self.assertEqual((after["requests"], after["questions"]), (0, 0))
        self.assertEqual(after["temperature_state"], "unknown")

    def test_grouped_worker_exit_retains_attempt_and_forward_audit(self):
        context = profile_context("C")
        worker = self.worker(load_with_failure, context)
        worker.receive(time.monotonic() + 2)
        item = dict(self.item, text="Teste de morte do worker")
        result = observe(item, worker, context, {"mode": "real"}, "run", "fake", None)
        self.assertEqual((result["attempt"], result["requests"], result["questions"]), (1, 1, 2))
        self.assertEqual(result["temperature_state"], "warm")
        self.assertEqual(len(result["request_usage"]), 1)
        self.assertEqual({choice["reason"] for choice in result["choices"].values()}, {"adapter_error"})
        self.assert_review_without_application(item, result["choices"])
        after = observe(self.item, worker, context, {"mode": "real"}, "run", "fake", None)
        self.assertEqual((after["requests"], after["questions"]), (0, 0))
        self.assertEqual(after["temperature_state"], "unknown")

    def test_separate_deadline_retains_first_choice_for_audit_only(self):
        context = profile_context("B")
        context = replace(context, policy=dict(context.policy, case_timeout_ms=250, response_reserve_ms=30))
        worker = self.worker(load_with_failure, context)
        worker.receive(time.monotonic() + 2)
        result = observe(dict(self.item, text="Teste de prazo parcial"), worker, context,
                         {"mode": "real"}, "run", "fake", None)
        self.assertEqual((result["requests"], result["questions"], len(result["request_usage"])), (2, 2, 2))
        self.assertEqual(result["temperature_state"], "warm")
        self.assertIsNone(result["inference_ms"])
        self.assertEqual(result["choices"]["category"]["status"], "predicted")
        self.assertEqual(result["choices"]["priority"]["reason"], "timeout")
        self.assert_review_without_application(self.item, result["choices"])

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
