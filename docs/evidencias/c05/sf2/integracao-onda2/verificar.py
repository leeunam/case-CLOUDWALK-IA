"""Aceite SF2-03/04 com artefatos numéricos gerados localmente. Execute com -B."""
import argparse
from contextlib import ExitStack, contextmanager
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from script.classification_comparison.setfit_sf2.adapter import _fixture_worker
from script.classification_comparison.setfit_sf2.adapter.test_decide import FixturePackage
from script.classification_comparison.setfit_sf2.contracts.core import FIELDS, LABELS, read, read_lines, sha256
from script.classification_comparison.setfit_sf2.contracts.test_artifacts import ArtifactTest
from script.classification_comparison.setfit_sf2.evaluation import runner, workflow
from script.classification_comparison.setfit_sf2.training import fit, package
from script.classification_comparison.setfit_sf2.training.scores import COLLECTION_POLICY
from script.classification_comparison.setfit_sf2.training.test_package import PackageTests

MOD = "script.classification_comparison.setfit_sf2"
SF2 = Path("script/classification_comparison/setfit_sf2")
SCRIPT = Path(__file__).resolve()
PYTHON = [sys.executable, "-B"]
COMMANDS = []


def cli(module, args, expected=0):
    argv = [*PYTHON, "-m", MOD + "." + module, *map(str, args)]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=180)
    assert result.returncode == expected, (argv, result.stdout, result.stderr)
    COMMANDS.append(dict(argv=argv, exit=result.returncode, stdout=result.stdout.strip(), stderr=result.stderr.strip()))
    return result


def observe_harness(trace_path, policy_path):
    # Espiões de leitura e de escrita delegam às mesmas streams. score() também executa normalmente.
    with trace_path.open("x") as trace:
        def event(kind, value):
            print(json.dumps([kind, value]), file=trace, flush=True)

        def inputs():
            for line in sys.stdin:
                event("input", json.loads(line))
                yield line

        class Wire:
            def write(self, line):
                event("stdout", json.loads(line))
                return sys.stdout.write(line)

            def flush(self):
                return sys.stdout.flush()

        score = FixturePackage.score
        serve = _fixture_worker.serve

        def observed_score(self, field, text):
            event("forward", field)
            return score(self, field, text)

        def observed_serve(pkg, policy, digest, stdin, stdout):
            return serve(pkg, policy, digest, inputs(), Wire())

        with patch.object(FixturePackage, "score", observed_score), patch.object(_fixture_worker, "serve", observed_serve):
            sys.argv = [sys.argv[0], "--policy", str(policy_path)]
            _fixture_worker.main()


def observe_real_startup(trace_path, worker_args):
    from torch.nn import Module
    from setfit import SetFitModel
    from sentence_transformers import SentenceTransformer
    from script.classification_comparison.setfit_sf2.adapter import __main__ as adapter

    def observed(original, name):
        def delegated(*args, **kwargs):
            calls.append(name)
            return original(*args, **kwargs)
        return delegated

    calls = []
    with ExitStack() as guards:
        for cls, method in ((Module, "_call_impl"), (SetFitModel, "predict_proba"), (SentenceTransformer, "encode")):
            guards.enter_context(patch.object(cls, method, observed(getattr(cls, method), cls.__name__+"."+method)))
        sys.argv = [sys.argv[0], *worker_args]
        code = adapter.main()
    runner.save(trace_path, calls)
    return code


def empty_real_worker(root, cfg):
    log = root/"startup-forwards.json"
    # Mesmo main e pacote, stdin vazio. Do início do carregamento até EOF, o contador deve ficar zerado.
    args = read(cfg["capture_command"])[4:]
    argv = [*PYTHON, str(SCRIPT), "observe-startup", str(log), *args]
    result = subprocess.run(argv, input="", text=True, capture_output=True, timeout=90)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ['{"type":"ready"}'] and read(log) == []
    return dict(argv=argv, stdout=result.stdout.strip(), observed_calls=read(log))


def transport(root):
    path = root / "policy-control.json"
    policy = {**COLLECTION_POLICY, "category": {"tau": 0.9, "delta": 0.0}}
    runner.save(path, policy)
    trace = root / "trace.jsonl"
    argv = [*PYTHON, str(SCRIPT), "observer", str(trace), str(path)]
    row = dict(id="controle-duplo", text="controle", received={}, gold={"category": "pix", "priority": "urgent"})
    identities = dict(package_sha256=FixturePackage.digest, model_sha256=FixturePackage.model_sha256,
                      policy_sha256=sha256(path))
    seal = runner.supervise([row], argv, policy, {"class_order": LABELS}, identities, root/"transport", 30)
    assert seal["failure"] is None, seal
    events = read_lines(trace)
    assert events.pop(0) == ["stdout", {"type": "ready"}]
    masks = [["category", "priority"], [], [], ["category"], ["priority"], ["category", "priority"]]
    cases = []
    for source, fields in zip([row, *runner.controls()], masks, strict=True):
        kind, item = events.pop(0)
        assert kind == "input" and item["id"] == source["id"]
        assert set(item) == {"id", "text", "received", "missing_fields", "catalog", "contract_version"}
        for field in fields:
            assert events.pop(0) == ["forward", field]
        kind, frame = events.pop(0)
        assert kind == "stdout" and frame["id"] == source["id"]
        assert frame["calls"] == {f: int(f in fields) for f in FIELDS}
        assert frame["received"] == source["received"]
        if len(fields) == 2:
            assert frame["outcome"] == "review" and frame["applied"] == {}
            assert frame["fields"]["category"]["reason"] == "below_tau"
            assert frame["fields"]["priority"]["raw"] == "urgent"
        cases.append(dict(id=item["id"], forwarded=fields, applied=frame["applied"], outcome=frame["outcome"]))
    assert not events
    return dict(argv=argv, startup_ms=seal["startup_ms"], trace_sha256=sha256(trace), cases=cases)


def configuration(root, validation):
    training, paths, _ = ArtifactTest()._training_case(root)
    inventory = fit.code_manifest()
    package.write_json(paths["training_code"], inventory)
    training["files"]["training_code"] = sha256(paths["training_code"])
    freeze = root/"training-freeze.json"
    runner.save(freeze, training)
    # A factory de 03 cria dois pesos de fixture; conserve os manifestos dos especialistas.
    # Substitua o freeze provisório pelos bytes válidos desta população numérica e sele de novo.
    with fixture_package() as factory:
        pkg = root/"package"
        pkg.mkdir()
        original = read(factory.root/"manifest.json")
        exports = {}
        for f in FIELDS:
            shutil.copytree(factory.root/f, pkg/f)
            members = {k: v for k, v in original["files"].items() if k.startswith(f + ".")}
            exports[f] = original["models"][f], members, original["class_order"][f]
        digest = package.seal_package(pkg, freeze, paths["arguments"], exports, factory.versions)
    model, model_files = package.read_verified_package(pkg, digest)
    adapter = root/"adapter-code.json"
    entrypoint = SF2/"adapter/__main__.py"
    package.write_json(adapter, {"files": {**inventory["files"], str(entrypoint): sha256(ROOT/entrypoint)}})
    runner.save(root/"versions.json", model["versions"])
    runner.save(root/"costs.json", dict(training_ms=0, download_ms=0, classifier_api_calls=0))
    policy = root/"capture-policy.json"
    runner.save(policy, COLLECTION_POLICY)
    for phase, p in (("capture", policy), ("final", validation/"policy.json")):
        runner.save(root/(phase+"-cmd.json"), [*PYTHON, "-m", MOD+".adapter", "--package", str(pkg),
                                               "--package-sha256", digest, "--policy", str(p)])
    config = root/"config.json"
    runner.save(config, dict(training_files={k: str(v) for k, v in paths.items()},
                             model_files={k: str(v) for k, v in model_files.items()},
                             model_manifest=str(pkg/"manifest.json"), adapter=str(adapter),
                             versions=str(root/"versions.json"), costs=str(root/"costs.json"),
                             capture_policy=str(policy), capture_command=str(root/"capture-cmd.json"),
                             final_command=str(root/"final-cmd.json"), startup_seconds=90))
    return config


@contextmanager
def fixture_package():
    try:
        PackageTests.setUpClass()
        yield PackageTests
    finally:
        PackageTests.doClassCleanups()


def probe_sources(root, config):
    # O subprocesso resolve imports no espelho. Copiam-se só fontes, contratos e metadados.
    cfg = read(config)
    shadow = root/"mirror"
    index = read(cfg["adapter"])["files"]
    paths = {ROOT / key for key in index}
    paths.update(workflow.sources().values())
    paths.add(SF2.absolute()/"evaluation/__init__.py")
    paths.update(ROOT/entry["path"] for entry in workflow.PROTOCOL["sources"].values())
    for source in sorted(paths):
        dest = shadow/source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    probe = """
import json, sys
from pathlib import Path
from script.classification_comparison.setfit_sf2.evaluation import workflow
assert workflow.ROOT == Path.cwd()
cfg, _ = workflow.public_setup(sys.argv[1])
print(json.dumps(workflow.capture_receipt(cfg, cfg["capture_policy"])))
"""
    def preflight():
        result = subprocess.run([*PYTHON, "-c", probe, str(config)], cwd=shadow, capture_output=True,
                                text=True, check=True, timeout=30)
        return json.loads(result.stdout)

    baseline = preflight()
    assert baseline == read(root/"validation/capture.json")
    checks = []
    for rel in ["adapter/decide.py", "adapter/__main__.py", "contracts/__init__.py", "contracts/ipc.py"]:
        key = str(SF2/rel)
        path = shadow/key
        previous = path.read_bytes()
        path.write_bytes(previous + b"\n# fixture de custodia\n")
        try:
            changed = sha256(path)
            assert changed != index[key]
            after = preflight()
            checks.append(dict(member=rel, original_sha256=index[key], changed_sha256=changed,
                               capture_changed=[k for k in baseline if baseline[k] != after[k]]))
        finally:
            path.write_bytes(previous)
    return checks


def negative_checks(root, cfg_path, validation):
    # Apenas bytes temporários da execução de QA. Cada controle restaura seu arquivo.
    cfg = read(cfg_path)
    checks = []
    paths = [(Path(cfg["capture_command"]), b" ", "coleta diverge"),
             (Path(cfg["capture_policy"]), b" ", "coleta diverge"),
             (validation/"run/timings.jsonl", b" ", "SHA-256 divergente"),
             (validation/"run/predictions.jsonl", b" ", "SHA-256 divergente")]
    for path, suffix, reason in paths:
        before = path.read_bytes()
        try:
            path.write_bytes(before + suffix)
            dest = root/"rejeicao"
            trial = cli("evaluation", ["freeze", cfg_path, validation, dest], 1)
            assert reason in trial.stderr and not dest.exists()
            checks.append({"file": path.name, "error": trial.stderr.strip()})
        finally:
            path.write_bytes(before)
    changed = {**COLLECTION_POLICY, "category": {"tau": 0.6, "delta": 0.0}}
    capture_policy = Path(cfg["capture_policy"])
    saved = capture_policy.read_bytes()
    try:
        package.write_json(capture_policy, changed)
        dest = root/"coleta-com-corte-trocado"
        trial = cli("evaluation", ["validate", cfg_path, dest], 1)
        assert "política de coleta não predeterminada" in trial.stderr and not (dest/"run").exists()
        checks.append({"file": "capture-policy.json", "error": trial.stderr.strip()})
    finally:
        capture_policy.write_bytes(saved)
    return checks


def main(root):
    root.mkdir(exist_ok=False)
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      HF_HUB_DISABLE_IMPLICIT_TOKEN="1", HF_HUB_DISABLE_TELEMETRY="1",
                      HF_HOME=str(root/"hf-cache"), XDG_CACHE_HOME=str(root/"cache"),
                      TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1")
    sentinel = root/"sentinela-inventario-final"
    sentinel.write_text("fixture reservada")
    # O primeiro open do arquivo será observável até em montagens relatime.
    os.utime(sentinel, ns=(1_000_000_000, 2_000_000_000))
    result = dict(transport=transport(root))
    validation = root/"validation"
    cfg_path = configuration(root, validation)
    cfg = read(cfg_path)
    run = validation/"run"
    assert cli("evaluation", ["validate", cfg_path, validation], 1).stdout.strip() == "failed"
    model = read(cfg["model_manifest"])
    capture = read(validation/"capture.json")
    seal = read(run/"seal.json")
    assert seal["failure"] is None
    records = read_lines(cfg["training_files"]["validation"])
    assert [r["text"] for r in records] == [f"validation-{i}" for i in range(90)]
    frames, journal = read_lines(run/"predictions.jsonl"), read_lines(run/"timings.jsonl")
    assert [r["id"] for r in frames] == [r["id"] for r in records]
    assert [r["id"] for r in journal] == [r["id"] for r in [*records, *runner.controls()]]
    assert all(r["valid"] for r in journal)
    assert capture["argv"] == sha256(cfg["capture_command"]) and capture["adapter"] == sha256(cfg["adapter"])
    assert capture["policy"] == sha256(cfg["capture_policy"]) and read(cfg["capture_policy"]) == COLLECTION_POLICY
    assert all(sha256(run/k) == v for k, v in seal["files"].items())
    extractor = ["scores", "--package", root/"package", "--package-sha256", sha256(cfg["model_manifest"]),
                 "--validation", cfg["training_files"]["validation"], "--policy", cfg["capture_policy"],
                 "--predictions", run/"predictions.jsonl", "--predictions-sha256", seal["files"]["predictions.jsonl"],
                 "--output", root/"scores03.json"]
    cli("training", extractor)
    scores = read(root/"scores03.json")
    assert scores == read(validation/"scores.json")
    for record, frame, row in zip(records, frames, scores["rows"], strict=True):
        assert row["heads"] == {f: frame["fields"][f]["vector"] for f in record["missing_fields"]}
    selection = read(validation/"selection.json")
    assert selection["policy_count"] == 225 and selection["eligible_count"] == 0
    assert read(validation/"grid.json")["selected"] is None
    assert selection["predictions_sha256"] == seal["files"]["predictions.jsonl"]
    assert selection["grid_sha256"] == sha256(validation/"grid.json")
    assert selection["timings_sha256"] == seal["files"]["timings.jsonl"]
    assert selection["scores_sha256"] == sha256(validation/"scores.json")
    assert selection["capture_policy_sha256"] == capture["policy"]
    assert not (validation/"policy.json").exists()
    release = root/"release"
    freeze = cli("evaluation", ["freeze", cfg_path, validation, release], 1)
    assert "validação inelegível" in freeze.stderr and not release.exists()

    attempted = []
    def audit_hook(event, args):
        if event == "open" and args[0] == str(sentinel):
            attempted.append(args[0])
    sys.addaudithook(audit_hook)
    # Um digest de controle fora de release não abre o final. O primeiro acesso exigido é release.json.
    try:
        workflow.execute(cfg_path, validation, release, "0"*64, sentinel, root/"final-out")
    except FileNotFoundError as err:
        assert Path(err.filename) == release/"release.json"
    else:
        raise AssertionError("execute prosseguiu sem liberação")
    assert not attempted and sentinel.stat().st_atime_ns == 1_000_000_000
    assert not (validation/"final-exposure.json").exists() and not (root/"final-out").exists()
    result.update(real_startup=empty_real_worker(root, cfg), selection=selection, capture=capture, run_seal=seal,
                  stats=read(validation/"report.json")["latency_ms"], rows=len(scores["rows"]),
                  vectors=sum(len(r["heads"]) for r in scores["rows"]), journal_entries=len(journal),
                  versions=model["versions"], model_sha256=model["model_sha256"],
                  scores03_sha256=sha256(root/"scores03.json"), equal_score_objects=True,
                  adapter_members=len(read(cfg["adapter"])["files"]), source_checks=probe_sources(root, cfg_path),
                  sentinel_open_attempts=len(attempted), negative_checks=negative_checks(root, cfg_path, validation),
                  commands=COMMANDS,
                  worker_argv=read(cfg["capture_command"]))
    package.write_json(root/"recibo.json", result)
    print(root/"recibo.json")
    missing = [item["member"] for item in result["source_checks"] if not item["capture_changed"]]
    if missing:
        print("Aceite bloqueado por fontes divergentes sem detecção: " + ", ".join(missing), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["observer"]:
        observe_harness(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1:2] == ["observe-startup"]:
        sys.exit(observe_real_startup(Path(sys.argv[2]), sys.argv[3:]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("output", type=Path, help="diretório novo de evidência temporária")
        sys.exit(main(parser.parse_args().output.resolve()))
