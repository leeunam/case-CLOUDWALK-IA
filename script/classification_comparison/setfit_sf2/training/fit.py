"""Treina os dois especialistas fixados, exporta e verifica o reload."""

import gc
import hashlib
import resource
import socket
from time import perf_counter, process_time
import warnings

from ..adapter.decide import assess
from ..contracts.artifacts import validate_manifest
from ..contracts.core import CATALOG, FIELDS, LABELS, PLAN, PROTOCOL, ROOT, SCHEMA_PATH, decode, read, require, sha256
from ..contracts.ipc import validate_vector
from .environment import HERE, RECIPE, check_pins, configure_cpu, length, load_body, resolved_requirements, snapshot_receipt
from .package import export_specialist, head_classes, load_package, read_hashed, score_vector, seal_package, write_json


def code_manifest():
    contract_dir = HERE.parent / "contracts"
    _, requirements = resolved_requirements(HERE / "requirements.txt")
    paths = {*HERE.glob("*.py"), *requirements, HERE.parent / "adapter/decide.py",
             ROOT / "script/classification_comparison/setfit_pilot/provision.py"}
    paths.update(path for path in contract_dir.glob("*.py") if path.name != "__main__.py")
    paths = {path for path in paths if not path.name.startswith(("test_", "_fixture"))}
    return {"files": {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(paths)}}


def checked_inputs(args):
    paths = {key: ROOT / entry["path"] for key, entry in PROTOCOL["sources"].items()}
    paths.update(protocol=PLAN / "protocolo.json", contracts=SCHEMA_PATH)
    for role in ("train", "validation", "annotations", "public_manifest", "review_receipt", "token_lengths",
                 "final_seal", "arguments", "training_code"):
        paths[role] = getattr(args, role)
    require(read(args.training_code) == code_manifest(), "inventário do código de treino diverge do checkout")
    encoded = args.training_freeze.read_bytes()
    freeze = decode(encoded.decode("utf-8"))
    validate_manifest("trainingFreeze", freeze, paths)
    train = read_hashed(args.train, freeze["files"]["train"], jsonl=True)
    validation = read_hashed(args.validation, freeze["files"]["validation"], jsonl=True)
    token_lengths = read_hashed(args.token_lengths, freeze["files"]["token_lengths"])
    return train, validation, token_lengths, hashlib.sha256(encoded).hexdigest()


def training_inputs(records, field):
    return [{"text": record["text"], "label": record["gold"][field]} for record in records]


def preflight_tokenization(body, records, receipt):
    observed = {row["id"]: length(body.tokenizer, row["text"]) for row in records}
    require(all(value <= RECIPE["max_sequence_length"] for value in observed.values()), "relato excede 128 tokens")
    require(observed == receipt["lengths"], "tokenização reexecutada diverge do recibo aprovado")


def monitored_digest(body):
    parameter = body[0].auto_model.encoder.layer[-1].output.LayerNorm.weight
    return hashlib.sha256(parameter.detach().cpu().numpy().tobytes()).hexdigest()


def build_trainer(field, body, records, work):
    from datasets import Dataset
    from setfit import SetFitModel, Trainer, TrainingArguments
    from sklearn.linear_model import LogisticRegression

    prepared = training_inputs(records, field)
    expected = LABELS[field]
    require({row["label"] for row in prepared} == set(expected), f"classes de treino incompletas para {field}")
    head = LogisticRegression(**{key: value for key, value in RECIPE["head"].items() if key != "class"})
    model = SetFitModel(model_body=body, model_head=head)
    args = TrainingArguments(
        output_dir=str(work / f"trainer-{field}"),
        **{k: RECIPE[k] for k in ("num_epochs", "num_iterations", "batch_size", "body_learning_rate", "seed")},
        eval_strategy="no", logging_strategy="no", save_strategy="no",
        show_progress_bar=False, report_to="none",
    )
    trainer = Trainer(model=model, args=args, train_dataset=Dataset.from_list(prepared))
    st_args = trainer.st_trainer.args
    applied = {
        "num_epochs": st_args.num_train_epochs,
        "num_iterations": trainer.args.num_iterations,
        "batch_size": st_args.per_device_train_batch_size,
        "body_learning_rate": st_args.learning_rate,
        "seed": st_args.seed,
    }
    require(applied == {key: RECIPE[key] for key in applied}, f"receita efetiva diverge para {field}")
    return model, trainer, applied


def resolved_setfit_arguments(args):
    return {key: value.__name__ if callable(value) else value for key, value in args.to_dict().items()}


def fit_specialist(field, body, records, work, control, *, expected_initial=None):
    from sklearn.exceptions import ConvergenceWarning

    model, trainer, applied = build_trainer(field, body, records, work)
    args, head = trainer.args, model.model_head
    original = monitored_digest(body)
    require(expected_initial is None or original == expected_initial,
            "especialistas não partiram do mesmo peso original")
    control.sendall(b"S")
    require(control.recv(1) == b"K", "supervisor não autorizou início do ajuste")
    started = perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        trainer.train()
    seconds = perf_counter() - started
    control.sendall(b"E")
    adjusted = monitored_digest(body)
    pairs = len(trainer.st_trainer.train_dataset)
    steps = trainer.st_trainer.state.global_step
    require(pairs == 2 * RECIPE["num_iterations"] * len(records) and steps > 0 and adjusted != original,
            f"encoder não completou o ajuste prescrito para {field}")
    require(set(head_classes(head)) == set(LABELS[field]), f"cabeça de {field} sem classes esperadas")
    evidence = {
        "field": field, "status": "trained",
        "setfit_arguments": resolved_setfit_arguments(args), "applied_encoder_arguments": applied,
        "loss": args.loss.__name__, "head_parameters": head.get_params(),
        "classes": head_classes(head), "head_iterations": head.n_iter_.tolist(),
        "pair_rows": pairs, "optimizer_steps": steps, "training_seconds": seconds,
        "monitored_parameter": "last_encoder_layer.output.LayerNorm.weight",
        "encoder_parameter_sha256_before": original, "encoder_parameter_sha256_after": adjusted,
    }
    return model, evidence


def verify_reload(package, examples, baseline):
    results = []
    grid = PROTOCOL["review_policy"]
    for field in FIELDS:
        classes = package.class_order[field]
        for example, before in zip(examples, baseline[field], strict=True):
            after = package.score(field, example["text"])
            raw_before = validate_vector(before, classes)[0]
            raw_after = validate_vector(after, classes)[0]
            error = max(abs(x - y) for x, y in zip(before["scores"], after["scores"], strict=True))
            require(error <= RECIPE["reload_score_absolute_tolerance"] and raw_before == raw_after,
                    f"reload não reproduz scores do especialista {field}")
            for tau in grid["tau_grid"]:
                for delta in grid["delta_grid"]:
                    cut = {"tau": tau, "delta": delta}
                    first = assess(before, classes, cut, CATALOG[field])
                    second = assess(after, classes, cut, CATALOG[field])
                    require(first["reason"] == second["reason"], f"reload altera decisão de {field}")
            results.append({"id": example["id"], "field": field, "max_abs_score_diff": error, "raw": raw_after})
    return results


def run(args):
    start, cpu_start = perf_counter(), process_time()
    versions = check_pins()
    configure_cpu()
    from transformers import set_seed

    training, validation, token_lengths, freeze_digest = checked_inputs(args)
    snapshot = snapshot_receipt(args.snapshot)
    package_root = args.staging / "package"
    package_root.mkdir()
    examples = training[:3]
    exports, baseline, evidence = {}, {}, {}
    expected_initial = None
    with socket.socket(fileno=args.control_fd) as control:
        for field in FIELDS:
            set_seed(RECIPE["seed"])
            body = load_body(args.snapshot)
            if field == FIELDS[0]:
                preflight_tokenization(body, training + validation, token_lengths)
            print(f"SF2 treino {field}: ajuste de encoder e cabeça", flush=True)
            model, detail = fit_specialist(field, body, training, args.staging, control,
                                           expected_initial=expected_initial)
            expected_initial = detail["encoder_parameter_sha256_before"]
            evidence[field] = detail
            baseline[field] = [score_vector(model, example["text"]) for example in examples]
            exports[field] = export_specialist(package_root, field, model, snapshot, detail)
            del model, body
            gc.collect()

        package_digest = seal_package(package_root, args.training_freeze, args.arguments, exports, versions)
        require(sha256(package_root / "training-freeze.json") == freeze_digest,
                "congelamento do pré-treino mudou durante o ajuste")
        package = load_package(package_root, package_digest, versions)
        reload_checks = verify_reload(package, examples, baseline)
        write_json(args.staging / "evidence.json", {
            "task": "SF2-03", "package_sha256": package_digest, "versions": versions,
            "training_freeze_sha256": package.manifest["training_freeze_sha256"],
            "specialists": evidence, "reload_checks": reload_checks,
            "resources": {"elapsed_seconds": perf_counter() - start, "cpu_seconds": process_time() - cpu_start,
                          "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        })
