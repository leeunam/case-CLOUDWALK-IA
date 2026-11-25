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
from script.classification_comparison.setfit_sf2.contracts.core import FIELDS, LABELS, read, read_lines, sha256
from script.classification_comparison.setfit_sf2.evaluation import runner, workflow
from script.classification_comparison.setfit_sf2.training import fit, package
from script.classification_comparison.setfit_sf2.training.scores import COLLECTION_POLICY

MOD = "script.classification_comparison.setfit_sf2"
SF2 = Path("script/classification_comparison/setfit_sf2")
SCRIPT = Path(__file__).resolve()
PYTHON = [sys.executable, "-B"]
COMMANDS = []
WORKFLOW_CHANGE = ("5f289573b5f90263f533554acca28595d571319160c90f7dd0852473abe2b351",
                   "951feaf647ba124c3559f3b46da9da559bfc4d2cfa8fc139fa60d0d3e35e3f09")
# Inicializador público da base de QA, fora dos papéis da captura.
EVALUATION_INIT_SHA256 = "09d616613e32bb83a907fb19f7d0fffa1942706f5e265b98ee6a26bedbce84f5"
HISTORIC_RECEIPT = "ce8d97b3a51109e11830ba9aeb0c7edbc9c643ea710628535bd155f000fb1297"


def cli(module, args, expected=0):
    argv = [*PYTHON, "-m", MOD + "." + module, *map(str, args)]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=180)
    assert result.returncode == expected, (argv, result.stdout, result.stderr)
    COMMANDS.append(dict(argv=argv, exit=result.returncode, stdout=result.stdout.strip(), stderr=result.stderr.strip()))
    return result


def observe_harness(trace_path, policy_path):
    from script.classification_comparison.setfit_sf2.adapter.test_decide import FixturePackage

    from script.classification_comparison.setfit_sf2.adapter import _fixture_worker

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
    from script.classification_comparison.setfit_sf2.adapter.test_decide import FixturePackage

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
    from script.classification_comparison.setfit_sf2.contracts.test_artifacts import ArtifactTest

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
    runner.save(config, fixture_config(root, paths, model_files))
    return config


def fixture_config(root, training_files, model_files):
    return dict(training_files={k: str(v) for k, v in training_files.items()},
                model_files={k: str(v) for k, v in model_files.items()},
                model_manifest=str(root/"package/manifest.json"), adapter=str(root/"adapter-code.json"),
                versions=str(root/"versions.json"), costs=str(root/"costs.json"),
                capture_policy=str(root/"capture-policy.json"), capture_command=str(root/"capture-cmd.json"),
                final_command=str(root/"final-cmd.json"), startup_seconds=90)


@contextmanager
def fixture_package():
    from script.classification_comparison.setfit_sf2.training.test_package import PackageTests

    try:
        PackageTests.setUpClass()
        yield PackageTests
    finally:
        PackageTests.doClassCleanups()


def contained(base, name, *, existing=False):
    member = Path(name)
    if (not member.parts or member.is_absolute() or ".." in member.parts or
            member.as_posix() != name or "\\" in name):
        raise ValueError(f"caminho relativo não canônico: {name}")
    path = base/member
    if base.resolve() != base or path.resolve() != path:
        raise ValueError(f"caminho redirecionado fora do local autorizado: {path}")
    if existing and not path.is_file():
        raise ValueError(f"arquivo regular ausente: {path}")
    return path


def prepare_mirror(root, config, historical):
    # Os nomes do pacote e dos arquivos da fixture vêm da factory. Config não autoriza novos caminhos.
    fixture = config.parent
    model = package.read_hashed(contained(fixture, "package/manifest.json", existing=True), historical["package"])
    model_files = package.package_paths(fixture/"package", model)
    files = package.read_hashed(contained(fixture, "adapter-code.json", existing=True), historical["adapter"])["files"]
    sources = workflow.sources()
    protocol_path = contained(ROOT, sources["protocol"].relative_to(ROOT).as_posix(), existing=True)
    protocol = package.read_hashed(protocol_path, historical["protocol"])
    metadata = {k: contained(ROOT, entry["path"], existing=True) for k, entry in protocol["sources"].items()}
    metadata.update(protocol=protocol_path, contracts=sources["schema"])
    generated = dict(train="train.jsonl", validation="validation.jsonl", annotations="annotations-public.jsonl",
                     review_receipt="review_receipt.json", token_lengths="token_lengths.json", training_code="code.json",
                     arguments="arguments.json", public_manifest="public.json", final_seal="seal.json")
    training = {**metadata, **{k: fixture/v for k, v in generated.items()}}
    cfg = read(contained(fixture, "config.json", existing=True))
    if cfg != fixture_config(fixture, training, model_files):
        raise ValueError("configuração fora dos papéis e caminhos autorizados da fixture")
    fixture_paths = list(model_files.values()) + [fixture/name for name in generated.values()]
    fixture_paths.extend(Path(value) for value in cfg.values() if isinstance(value, str))
    for path in fixture_paths:
        contained(fixture, path.relative_to(fixture).as_posix(), existing=True)

    # Prepare a lista inteira antes da primeira cópia, inclusive os destinos ainda inexistentes.
    names = set(files)
    names.update(path.relative_to(ROOT).as_posix() for path in [*sources.values(), *metadata.values()])
    initializer = (SF2/"evaluation/__init__.py").as_posix()
    names.add(initializer)
    shadow = root/"mirror"
    copies = [(contained(ROOT, name, existing=True), contained(shadow, name)) for name in sorted(names)]
    for _, destination in copies:
        if destination.exists():
            raise ValueError(f"destino do espelho já existe: {destination}")
    for role, entry in protocol["sources"].items():
        if sha256(metadata[role]) != entry["sha256"]:
            raise ValueError(f"metadado público divergente: {role}")
    if sha256(ROOT/initializer) != EVALUATION_INIT_SHA256:
        raise ValueError("inicializador público do avaliador divergente")
    reference = workflow.capture_receipt(cfg, cfg["capture_policy"])
    changed_roles = sorted(k for k in reference.keys() | historical.keys() if reference.get(k) != historical.get(k))
    workflow_change = (historical.get("evaluation/workflow.py"), reference.get("evaluation/workflow.py"))
    if changed_roles and (changed_roles != ["evaluation/workflow.py"] or workflow_change != WORKFLOW_CHANGE):
        raise ValueError(f"entradas da coleta divergentes do histórico: {changed_roles}")
    for source, destination in copies:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return cfg, files, reference, changed_roles


def probe_sources(root, config, validation, receipt, historical):
    shadow = root/"mirror"
    cfg, files, reference, changed_roles = prepare_mirror(root, config, historical)

    def invoke(*args):
        return subprocess.run([*PYTHON, str(SCRIPT), "probe", *map(str, args)], cwd=shadow,
                              capture_output=True, text=True, timeout=60)

    def clean_preflight():
        proc = invoke("preflight", config)
        if proc.returncode:
            raise ValueError(f"pré-voo da cópia íntegra recusado: {proc.stderr.strip()}")
        return json.loads(proc.stdout)

    if clean_preflight() != reference:
        raise ValueError("pré-voo do espelho diverge do checkout")
    receipt.update(index_sha256=sha256(cfg["adapter"]), argv_sha256=sha256(cfg["capture_command"]),
                   historical_capture_sha256=sha256(validation/"capture.json"), changed_roles=changed_roles,
                   workflow_sha256=reference["evaluation/workflow.py"], adapter_members=len(files),
                   clean_preflight=True, source_checks=[])
    positive = "contracts/ipc.py"
    for n, rel in enumerate(("adapter/decide.py", "adapter/__main__.py", "contracts/__init__.py", positive)):
        key = str(SF2/rel)
        path = shadow/key
        previous = path.read_bytes()
        path.write_bytes(previous + b"\n# fixture de custodia\n")
        try:
            check = dict(member=rel, original_sha256=files[key], changed_sha256=sha256(path), stages={})
            receipt["source_checks"].append(check)
            if check["changed_sha256"] == files[key]:
                raise ValueError(f"sonda não alterou {key}")
            reason = "SHA-256 divergente no membro do adaptador: " + key
            for stage, args in (("validate", [config, root/f"capture-{n}"]),
                                ("freeze", [config, validation, root/f"release-{n}"])):
                proc = invoke(stage, *args)
                message = proc.stderr.strip()
                check["stages"][stage] = dict(exit=proc.returncode, reason=message)
                if proc.returncode != 1 or message != f"{stage}: {reason}" or proc.stdout:
                    raise ValueError(f"{stage} deixou de recusar {rel} pelo SHA-256 esperado "
                                     f"(saída {proc.returncode}, stderr={message!r}, stdout={proc.stdout.strip()!r})")
            if (root/f"capture-{n}"/"run").exists() or (root/f"release-{n}").exists():
                raise ValueError(f"execução ou liberação criada após divergência em {key}")
            if sha256(cfg["adapter"]) != receipt["index_sha256"] or sha256(cfg["capture_command"]) != receipt["argv_sha256"]:
                raise ValueError("índice ou argv mudou durante a sonda")
        finally:
            path.write_bytes(previous)
    if clean_preflight() != reference:
        raise ValueError("pré-voo não foi restabelecido após restaurar as fontes")
    observed = {check["member"] for check in receipt["source_checks"] if len(check["stages"]) == 2}
    if positive not in observed or len(observed) != 4:
        raise ValueError("controle positivo de contracts/ipc.py ou sonda esperada ausente")
    receipt.update(positive_control=positive, restored_preflight=True)


def run_probe(args):
    # Um eventual avanço indevido até o worker deve reprovar a prova sem repetir a inferência.
    from script.classification_comparison.setfit_sf2.evaluation.__main__ import main as evaluate
    if workflow.ROOT != Path.cwd():
        raise ValueError("módulos carregados fora do espelho")
    if args[0] == "preflight":
        cfg, _ = workflow.public_setup(args[1])
        print(json.dumps(workflow.capture_receipt(cfg, cfg["capture_policy"])))
        return 0
    with patch.object(workflow, "supervise", side_effect=AssertionError("tentativa de iniciar worker na sonda")):
        return evaluate(args)


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


def offline(root):
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                      HF_HUB_DISABLE_IMPLICIT_TOKEN="1", HF_HUB_DISABLE_TELEMETRY="1",
                      HF_HOME=str(root/"hf-cache"), XDG_CACHE_HOME=str(root/"cache"),
                      TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1")


def main(root):
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
                  adapter_members=len(read(cfg["adapter"])["files"]),
                  sentinel_open_attempts=len(attempted), negative_checks=negative_checks(root, cfg_path, validation),
                  commands=COMMANDS,
                  worker_argv=read(cfg["capture_command"]))
    return result, cfg_path, validation


def verify(output, prior):
    output.mkdir(mode=0o700, exist_ok=False)
    receipt = {"mode": "custody" if prior else "full_fixture"}
    try:
        if sys.flags.optimize:
            raise ValueError("a prova exige as asserções habilitadas")
        offline(output)
        if prior:
            config, validation = prior/"config.json", prior/"validation"
            original = contained(prior, "recibo.json", existing=True)
            old = package.read_hashed(original, HISTORIC_RECEIPT)
            receipt.update(source_fixture=str(prior), historical_receipt_sha256=HISTORIC_RECEIPT)
            historical = old["capture"]
            if read(contained(prior, "validation/capture.json", existing=True)) != historical:
                raise ValueError("captura diferente da registrada na rodada histórica")
            for role in ("predictions.jsonl", "timings.jsonl", "controls.jsonl"):
                if sha256(contained(prior, "validation/run/"+role, existing=True)) != old["run_seal"]["files"][role]:
                    raise ValueError(f"evidência original divergente: {role}")
        else:
            measurements, config, validation = main(output)
            receipt["fixture"] = measurements
            historical = measurements["capture"]
        probe_sources(output, config, validation, receipt, historical)
        receipt.update(status="passed", exit_code=0, reason="Pré-voo íntegro e restaurado. Quatro sondas recusadas nas duas etapas.")
    except Exception as exc:
        receipt.update(status="failed", exit_code=1, reason=f"{type(exc).__name__}: {exc}")
    package.write_json(output/"recibo.json", receipt)
    print(f"{receipt['status']}: {receipt['reason']}", file=sys.stderr if receipt["exit_code"] else sys.stdout)
    return receipt["exit_code"]


if __name__ == "__main__":
    if sys.argv[1:2] == ["probe"]:
        sys.exit(run_probe(sys.argv[2:]))
    if sys.argv[1:2] == ["observer"]:
        observe_harness(Path(sys.argv[2]), Path(sys.argv[3]))
    elif sys.argv[1:2] == ["observe-startup"]:
        sys.exit(observe_real_startup(Path(sys.argv[2]), sys.argv[3:]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("output", type=Path, help="diretório novo de evidência temporária")
        parser.add_argument("--fixture-anterior", type=Path, help="saída confiável do ensaio numérico de QA")
        args = parser.parse_args()
        sys.exit(verify(args.output.resolve(), args.fixture_anterior.resolve() if args.fixture_anterior else None))
