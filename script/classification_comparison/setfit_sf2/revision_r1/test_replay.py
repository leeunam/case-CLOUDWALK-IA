"""Fixtures sintéticas. O arquivo de testes nunca abre frames, scores ou grade reais."""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
import gzip
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ..contracts.core import FIELDS, REVIEW, VERSION, read, structure
from ..evaluation.metrics import metrics
from ..evaluation.runner import encoded
from ..evaluation.selection import prepare_replay, scored_rows, select
from ..evaluation.test_evaluation import POLICY, fixture, records, templates
from . import cli, engine


# Gerados no commit histórico com a mesma fixture, antes de usar o replay R1.
GOLDEN_GRID = "8e2187ca9227250d3ca0beb24ed25e366eecd31103b83771085c78aa3c94f4e7"
GOLDEN_BASELINE = "7e9449ea428276dd37c82d29a8f6722b5b2d0537616e42ec830ebc8a51dc402c"


def sample(*, certain_error=False):
    rows = records("validation")
    decisions = list(templates(rows, weak=True).values())
    field = decisions[24]["fields"]["category"]
    vector = field["vector"]
    top, runner_up, margin = (.99, .01, .98) if certain_error else (.92, .08, .84)
    vector["scores"] = [top if c == "pix" else runner_up if c == "payouts" else 0 for c in vector["classes"]]
    field["margin"] = margin
    for decision in decisions:
        for key, item in decision["fields"].items():
            if item["cut"] is not None:
                item["cut"] = POLICY[key]
    bundle = dict(partition="validation", rows=scored_rows(rows, decisions[:90]), class_order=fixture("both")["class_order"])
    return rows, decisions, bundle


def write(root, name, content):
    path = root/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else encoded(content))


def fingerprint(path):
    return cli.sha(path.read_bytes())


def setup_capture(root, history, *, certain_error=False):
    """Monta uma captura sintética relocável. Reutiliza só fontes e índices públicos."""
    repo = cli.ROOT
    paths = {k: root/name for k, name in cli.PARENT_FILES.items()}
    for name in cli.SOURCES | {cli.INVENTORY}:
        write(root, name, (repo/name).read_bytes())
    def put(role, value):
        write(root, cli.PARENT_FILES[role], value)
    def put_lines(role, rows):
        put(role, b"".join(map(encoded, rows)))
    for role in ("training_arguments", "final_seal", "capture_versions"):
        put(role, (repo/cli.PARENT_FILES[role]).read_bytes())
    for name in cli.EXTRA_TRAINING.values():
        if name not in cli.SOURCES:
            write(root, name, {"fixture": name})
    put("parent_config", {"fixture": "Os caminhos históricos jamais são seguidos", "capture_policy": "/proibido"})
    put("capture_argv", ["fixture-sem-executavel"])
    put("capture_costs", dict(classifier_api_calls=0, training_ms=0, download_ms=0))
    put("capture_policy", POLICY)
    inventory = read(root/cli.INVENTORY)
    put("training_code", {"files": {key: inventory[key] for key in cli.TRAINING_SOURCES}})
    put("adapter_index", {"files": {key: inventory[key] for key in cli.ADAPTER_MEMBERS}})

    rows, decisions, bundle = sample(certain_error=certain_error)
    put_lines("validation", rows)
    public = read(repo/cli.PARENT_FILES["public_manifest"])
    for role in public["files"]:
        file = paths["validation"] if role == "validation" else root/cli.EXTRA_TRAINING[role]
        public["files"][role]["sha256"] = fingerprint(file)
    put("public_manifest", public)
    freeze = read(repo/cli.PARENT_FILES["training_freeze"])
    for role in freeze["files"]:
        if role in cli.EXTRA_TRAINING:
            path = root/cli.EXTRA_TRAINING[role]
        else:
            path = paths[{"contracts": "schema", "arguments": "training_arguments"}.get(role, role)]
        freeze["files"][role] = fingerprint(path)
    put("training_freeze", freeze)
    model = read(repo/cli.PARENT_FILES["package_manifest"])
    model["files"]["training_freeze"] = model["training_freeze_sha256"] = fingerprint(paths["training_freeze"])
    put("package_manifest", model)
    for field in FIELDS:
        for part in (*cli.COMPONENTS, "manifest"):
            path = f"{cli.PACK}/{field}/{part}.json"
            write(root, path, (repo/path).read_bytes())

    ids = dict(package_sha256=fingerprint(paths["package_manifest"]), model_sha256=model["model_sha256"],
               policy_sha256=fingerprint(paths["capture_policy"]))
    for decision in decisions:
        decision.update(ids)
    put_lines("predictions", decisions[:90])
    put_lines("controls", decisions[90:])
    put_lines("journal", (dict(kind="case" if i < 90 else "control", id=d["id"], elapsed_ms=1, valid=True)
                          for i, d in enumerate(decisions)))
    run = paths["seal"].parent
    write(run, "stderr.log", b"fixture")
    put("seal", dict(contract_version=VERSION, failure=None, startup_ms=1, peak_ram_bytes=4096, peak_cpu_percent=1,
                     files={name: fingerprint(run/name) for name in ("timings.jsonl","controls.jsonl","predictions.jsonl","stderr.log")}))
    bundle.update(contract_version=VERSION, dataset_sha256=fingerprint(paths["validation"]),
                  model_sha256=model["model_sha256"], package_sha256=ids["package_sha256"])
    put("scores04", bundle)
    put("scores03", json.dumps(bundle, indent=2).encode())
    original = select(rows, bundle, 0)
    grid_bytes = encoded(original)
    put("parent_grid_gzip", gzip.compress(grid_bytes))
    put("parent_grid_original", dict(size_bytes=len(grid_bytes), sha256=cli.sha(grid_bytes)))
    put("parent_selection", dict(policy_count=225, eligible_count=0, selected_policy_sha256=None,
                                 capture_policy_sha256=ids["policy_sha256"], scores_sha256=fingerprint(paths["scores04"]),
                                 predictions_sha256=fingerprint(paths["predictions"]), grid_sha256=cli.sha(grid_bytes),
                                 timings_sha256=fingerprint(paths["journal"]), latency_source="observed_capture_policy_external_total"))
    put("parent_report", dict(contract_version=VERSION, partition="validation", status="failed", reason="Fixture",
                              policy_sha256=ids["policy_sha256"], score_package_sha256=fingerprint(paths["scores04"]),
                              predictions_sha256=fingerprint(paths["predictions"]), unexecuted_ids=[],
                              counts=dict(planned=90,observed=90), metrics=metrics(rows, decisions[:90], 0),
                              latency_ms=dict(n=90,p50=1,p95=1,maximum=1), resources=dict(startup_ms=1,
                              peak_ram_bytes=4096,peak_cpu_percent=1,download_ms=0,training_ms=0,classifier_api_calls=0)))
    for name in set(cli.CAPTURE_PATHS.values()) | cli.ADAPTER_MEMBERS:
        write(history, name, (root/name).read_bytes())
    old_selection = cli.CAPTURE_PATHS["evaluation/selection.py"]
    write(history, old_selection, b"# selecao historica sintetica, nunca importada")
    capture = {role: fingerprint(history/name) for role,name in cli.CAPTURE_PATHS.items()}
    put("capture", capture)
    put("pre_validation", dict(preflight_status="passed", capture_expected=capture, adapter_member_count=17,
                               package_member_count=len(model["files"]), package_sha256=fingerprint(paths["package_manifest"]),
                               evaluation_config_sha256=fingerprint(paths["parent_config"])))
    amendment = read(repo/cli.AMENDMENT)
    amendment["parent"]["original_grid_sha256"] = cli.sha(grid_bytes)
    for role, info in amendment["parent"]["files"].items():
        info["sha256"] = fingerprint(paths[role])
    write(root, cli.AMENDMENT, amendment)
    return paths


def guarded_fixture_cli():
    """O harness abre este processo isolado. Dentro da CLI, subprocessos são proibidos."""
    import runpy
    import sys
    from pathlib import Path
    seen = set()
    def guard(event, args):
        if event.startswith(("socket.", "subprocess.", "os.system", "os.posix_spawn", "os.fork")):
            raise RuntimeError("operação externa em replay: " + event)
        if event == "import":
            name = args[0]
            if name.split(".")[0] in {"torch", "joblib", "setfit"} or ".adapter" in name or ".training" in name:
                raise RuntimeError("importação de modelo/worker: " + name)
        if event == "open" and isinstance(args[0], str):
            path = Path(args[0])
            if ("sf2-final" in path.parts or path.suffix in {".joblib", ".safetensors"}
                    or path.name in {"final.jsonl", ".env"}):
                raise RuntimeError("leitura fora do escopo: " + str(path))
            seen.add(path.name)
    sys.argv = sys.argv[1:]
    sys.addaudithook(guard)
    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    except SystemExit as exc:
        if exc.code in (0, 1):
            assert {"scores-sf2-03.json", "seal.json", "cli.py"} <= seen
        raise


def fixture_cli(root, history):
    harness = inspect.getsource(guarded_fixture_cli) + "\nguarded_fixture_cli()"
    command = [sys.executable, "-I", "-B", "-c", harness, str(root/cli.SF/"revision_r1/cli.py"),
               "--historical-root", str(history), "--amendment-sha256", fingerprint(root/cli.AMENDMENT),
               "--inventory-sha256", fingerprint(root/cli.INVENTORY)]
    return subprocess.run(command, capture_output=True, text=True)


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        base = Path(cls.temp.name)
        cls.root, cls.history = base/"repo", base/"history"
        cls.paths = setup_capture(cls.root, cls.history)
        cls.pin = fingerprint(cls.root/cli.AMENDMENT)
        cls.index_pin = fingerprint(cls.root/cli.INVENTORY)
        cls.amendment = read(cls.root/cli.AMENDMENT)
        cls.schema = (cls.root/cli.SCHEMA).read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @contextmanager
    def replaced(self, path, data):
        original = path.read_bytes()
        try:
            path.write_bytes(data)
            yield
        finally:
            path.write_bytes(original)

    def test_end_to_end_one_round_without_network_worker_or_final(self):
        first_run = fixture_cli(self.root, self.history)
        self.assertEqual(first_run.returncode, 0, first_run.stderr)
        output = self.root/cli.DESTINATION/"result.json"
        first = output.read_bytes()
        second_run = fixture_cli(self.root, self.history)
        self.assertEqual(second_run.returncode, 2)
        self.assertIn("destino R1 já existe", second_run.stderr)
        self.assertEqual(first, output.read_bytes())
        result = json.loads(first)
        self.assertEqual(result["original_grid_sha256"], GOLDEN_GRID)
        self.assertEqual(engine.digest(result["baseline_argmax"]), GOLDEN_BASELINE)
        self.assertEqual(len(result["policies"]), 270)
        self.assertEqual(result["counts"], dict(original=225,original_eligible=0,additional=45,union=270,eligible=45))
        self.assertEqual(result["selected"], dict(contract_version="sf2-r1-offline/1.0", category=dict(tau=.95,delta=0),
                                                  priority=dict(tau=.5,delta=0)))
        self.assertEqual(result["scope_limits"]["final_release"], False)
        self.assertTrue(all(n == 0 for n in result["new_consumption"].values()))
        self.assertFalse(result["provenance"]["weights_verified_in_replay"])

    def test_negative_cli_signals_code_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, history = Path(tmp)/"negative", Path(tmp)/"history"
            setup_capture(root, history, certain_error=True)
            process = fixture_cli(root, history)
            self.assertEqual(process.returncode, 1, process.stderr)
            result = read(root/cli.DESTINATION/"result.json")
            self.assertIsNone(result["selected"])
            self.assertEqual(result["status"], "negative")
            self.assertEqual(result["counts"]["eligible"], 0)
            self.assertTrue(all("wrong_expected_review" in row["failed_gates"] for row in result["policies"]))

    def test_tampering_rejected_by_initializer_before_engine_import(self):
        tests = [self.paths[role] for role in ("seal","predictions","controls","journal","scores03","scores04",
                                                "parent_config","capture_policy","parent_grid_gzip","package_manifest")]
        tests += [self.history/cli.CAPTURE_PATHS["evaluation/selection.py"], self.root/cli.SF/"evaluation/selection.py",
                  self.root/cli.INVENTORY, self.root/cli.AMENDMENT, self.paths["seal"].with_name("stderr.log")]
        for path in tests:
            with self.subTest(name=path), self.replaced(path,b"alterado"), self.assertRaisesRegex(ValueError,"SHA-256"):
                cli.attest(self.root,self.history,self.pin,self.index_pin)
        for role, new_path in (("validation","../outside"),("capture","/tmp/outside"),("seal","diferente.json")):
            tampered = deepcopy(self.amendment)
            tampered["parent"]["files"][role]["path"] = new_path
            blob = encoded(tampered)
            with self.replaced(self.root/cli.AMENDMENT, blob), self.assertRaisesRegex(ValueError,"caminhos públicos"):
                cli.attest(self.root,self.history,cli.sha(blob),self.index_pin)
        manifest = read(self.root/cli.INVENTORY)
        del manifest[cli.SF+"/revision_r1/cli.py"]
        blob = encoded(manifest)
        with self.replaced(self.root/cli.INVENTORY,blob), self.assertRaisesRegex(ValueError,"conjunto de fontes"):
            cli.attest(self.root,self.history,self.pin,cli.sha(blob))
        (self.root/"redirecionado").symlink_to(self.history)
        with self.assertRaisesRegex(ValueError,"redirecionado"):
            cli.safe_path(self.root,"redirecionado/arquivo")

    def test_snapshot_survives_source_replacement_after_attestation(self):
        attested = cli.attest(self.root, self.history, self.pin, self.index_pin)
        destination = self.root/"fixture-snapshot-result"
        inputs = {**self.paths, "stderr": self.paths["seal"].with_name("stderr.log")}
        old_scores = inputs["scores03"].read_bytes()
        changed = {"scores03": b"\n" + old_scores}
        changed.update({role: b"{}" for role in ("protocol", "schema", "catalog", "validation", "seal", "predictions", "stderr")})
        self.assertEqual(json.loads(changed["scores03"]), json.loads(old_scores))
        self.assertNotEqual(cli.sha(changed["scores03"]), cli.sha(old_scores))

        used_scores = []
        original_open = Path.open
        def deny_original_read(path, mode="r", *args, **kwargs):
            if "r" in mode and path.is_relative_to(self.root):
                self.fail("reabriu arquivo da origem após a atestação: " + str(path))
            if "r" in mode and path.name == inputs["scores03"].name:
                with original_open(path, "rb") as stream:
                    used_scores.append(cli.sha(stream.read()))
            return original_open(path, mode, *args, **kwargs)

        with ExitStack() as stack:
            for role, content in changed.items():
                stack.enter_context(self.replaced(inputs[role], content))
            # Isola os módulos do motor carregados exclusivamente nesta fixture.
            stack.enter_context(patch.dict(sys.modules))
            stack.enter_context(patch.object(sys, "meta_path", sys.meta_path.copy()))
            stack.enter_context(patch.object(Path, "open", deny_original_read))
            report = cli.replay_attested(*attested, destination)
        self.assertEqual(used_scores, [cli.sha(old_scores)])
        self.assertEqual(report["provenance"]["parent_files"]["scores03"]["sha256"], used_scores[0])
        self.assertEqual(report["original_grid_sha256"], GOLDEN_GRID)
        self.assertEqual(report, read(destination/"result.json"))

    def test_semantic_audit_precedes_replay(self):
        data = engine.audit_capture(self.amendment, self.paths)
        archive = gzip.decompress(self.paths["parent_grid_gzip"].read_bytes())
        for item in ("baseline_argmax", "policies"):
            different = json.loads(archive)
            del different[item]
            with self.assertRaisesRegex(ValueError, "225 políticas ou baseline"):
                engine.confirm_original(data, encoded(different), self.amendment["parent"])
        frames = [json.loads(line) for line in self.paths["predictions"].read_bytes().splitlines()]
        frames[0]["applied"] = {}
        corrupted = b"".join(map(encoded, frames))
        seal = read(self.paths["seal"])
        seal["files"]["predictions.jsonl"] = cli.sha(corrupted)
        with (self.replaced(self.paths["predictions"], corrupted), self.replaced(self.paths["seal"], encoded(seal)),
              self.assertRaisesRegex(ValueError, "aplicação parcial")):
            engine.audit_capture(self.amendment,self.paths)
        scores = read(self.paths["scores03"])
        scores["rows"][0]["heads"]["category"]["scores"].reverse()
        with self.replaced(self.paths["scores03"],encoded(scores)), self.assertRaisesRegex(ValueError,"vetores"):
            engine.audit_capture(self.amendment,self.paths)
        altered = deepcopy(self.amendment)
        altered["extension"]["priority_tau"].append(.95)
        with self.assertRaisesRegex(ValueError, "cortes"):
            engine.extension_policies(altered,self.schema)
        altered = deepcopy(self.amendment)
        altered["validation_quotas"]["classifiable_cases"] = 71
        with self.assertRaisesRegex(ValueError,"quotas"):
            engine.audit_capture(altered,self.paths)

    def test_boundaries_atomicity_raw_review_and_provided_fields(self):
        rows, _, bundle = sample()
        index = next(i for i,r in enumerate(rows) if r["missing_fields"] == list(FIELDS) and REVIEW not in r["gold"].values())
        row, scores = rows[index], deepcopy(bundle["rows"][index])
        category = scores["heads"]["category"]
        def cut(tau, delta):
            return dict(category=dict(tau=tau,delta=delta), priority=dict(tau=.5,delta=0))
        def replay(policy):
            return prepare_replay([row], {**bundle, "rows":[scores]}, 0)(policy)
        category["scores"] = [.0,.08,.92,.0]
        self.assertEqual(replay(cut(.90,0))["applied_accuracy"]["priority"]["denominator"], 1)
        self.assertEqual(replay(cut(.95,0))["applied_accuracy"]["priority"]["denominator"], 0)
        category["scores"] = [0,.05,.95,0]
        self.assertEqual(replay(cut(.95,0))["automatic_coverage"]["numerator"], 1)
        category["scores"] = [0,.4,.6,0]
        self.assertEqual(replay(cut(.6,.2))["automatic_coverage"]["numerator"], 0)
        category["scores"] = [1,0,0,0]
        self.assertEqual(replay(cut(.5,0))["review_by_case"]["numerator"], 1)
        category["scores"] = [.5,.5,.5,.5]
        with self.assertRaisesRegex(ValueError, "soma"):
            replay(cut(.95,0))
        _, _, scores_bundle = sample()
        total = prepare_replay(rows,scores_bundle,0)(cut(.95,0))
        self.assertEqual(total["preservation"]["numerator"], total["preservation"]["denominator"])
        self.assertEqual(total["partial_applications"],0)
        self.assertEqual(total["raw_urgent"]["numerator"],13)

    def test_distinct_contracts_uniqueness_and_no_eligible_policy(self):
        data = engine.audit_capture(self.amendment, self.paths)
        original = select(*data)
        policies = engine.extension_policies(self.amendment,self.schema)
        with self.assertRaises(ValueError):
            structure("policy",policies[0])
        for row in original["policies"]:
            structure("policy",row["policy"])
        with self.assertRaisesRegex(ValueError,"duplicada"):
            engine.check_union(original, policies[:-1]+[policies[0]])
        rows, scores, _ = data
        negative = engine.compare((rows,scores,1),select(rows,scores,1),policies)
        self.assertEqual(negative["status"],"negative")
        self.assertIsNone(negative["selected"])
        self.assertTrue(all("control_calls" in p["failed_gates"] for p in negative["policies"]))
