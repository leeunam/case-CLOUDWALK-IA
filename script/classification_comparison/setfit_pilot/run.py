"""Executa as quatro divisões predefinidas, com inferência local em CPU."""

import argparse
import gc
import hashlib
from importlib.metadata import distributions
import json
import os
from pathlib import Path
import platform
import socket
import time

from protocol import FOLD_COUNT, LABELS, REVIEW, SEED, select_data, summarize
from provision import CACHE, HERE, MODEL_DIR, verify_model, write_json
from supervise import TRAIN_LIMIT, timestamp

THREADS = 2
PARAMETERS = {
    "num_epochs": 1,
    "num_iterations": 5,
    "batch_size": 8,
    "body_learning_rate": 2e-5,
    "seed": SEED,
    "eval_strategy": "no",
    "logging_strategy": "no",
    "save_strategy": "no",
    "show_progress_bar": False,
    "report_to": "none",
}


def observe(model, text, classes):
    before = time.perf_counter_ns()
    probabilities = model.predict_proba(text, as_numpy=True, show_progress_bar=False)
    scores = {label: float(score) for label, score in zip(classes, probabilities, strict=True)}
    label = max(scores, key=scores.__getitem__)
    category = None if label == REVIEW else label
    decision = "revisao" if category is None else "categoria"
    elapsed = (time.perf_counter_ns() - before) / 1_000_000
    return {
        "predicted_label": label,
        "decision": decision,
        "category": category,
        "scores_uncalibrated": scores,
        "inference_ms": elapsed,
    }


def run(output, report, control):
    import torch
    from datasets import Dataset
    from sentence_transformers import SentenceTransformer
    from setfit import SetFitModel, Trainer, TrainingArguments
    from sklearn.linear_model import LogisticRegression
    from transformers import set_seed

    torch.set_num_threads(THREADS)
    torch.set_num_interop_threads(THREADS)
    if torch.version.cuda is not None or torch.version.hip is not None:
        raise ValueError("O piloto requer wheel PyTorch para CPU")

    records, data = select_data()
    write_json(output / "data.json", data)
    report["parameters"] = {
        "training": PARAMETERS,
        "head": {"class": "LogisticRegression", **LogisticRegression(random_state=SEED).get_params()},
        "training_total_limit_seconds": TRAIN_LIMIT,
        "training_deadline": "external supervisor, accumulated trainer.train calls",
        "device": "cpu",
        "torch_intraop_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "warmup": "first training text of each fold, excluded from metrics",
    }
    snapshot = verify_model()
    downloaded = json.loads((CACHE / "model-manifest.json").read_text())
    if any(snapshot[field] != downloaded[field] for field in snapshot):
        raise ValueError("Manifesto de download diverge do snapshot verificado")
    write_json(output / "model.json", downloaded)

    train_total = 0.0
    first_encoder_hash = None
    predictions = []
    for fold in data["folds"]:
        number = fold["fold"]
        report["active_fold"] = number
        fold_report = {"fold": number, "status": "loading"}
        report["folds"].append(fold_report)
        write_json(output / "run.json", report)
        set_seed(SEED)
        before_load = time.perf_counter()
        encoder = SentenceTransformer(
            str(MODEL_DIR),
            device="cpu",
            cache_folder=str(CACHE / "sentence-transformers"),
            local_files_only=True,
            trust_remote_code=False,
            model_kwargs={"use_safetensors": True},
        )
        head = LogisticRegression(random_state=SEED)
        model = SetFitModel(model_body=encoder, model_head=head)
        fold_report["load_seconds"] = time.perf_counter() - before_load
        if number == 1:
            limit = encoder.max_seq_length
            lengths = {
                key: len(encoder.tokenizer(row["text"], truncation=False)["input_ids"])
                for key, row in records.items()
            }
            data["tokenization"] = {
                "truncation": False,
                "model_max_sequence_length": limit,
                "input_tokens_including_special_tokens": lengths,
            }
            write_json(output / "data.json", data)
            if any(length > limit for length in lengths.values()):
                raise ValueError("Há relatos que ultrapassam o limite de sequência do modelo")

        train_ids = fold["train_ids"]
        train = Dataset.from_list([records[key] for key in train_ids])
        args = TrainingArguments(output_dir=str(CACHE / "training" / str(number)), **PARAMETERS)
        trainer = Trainer(model=model, args=args, train_dataset=train)
        fold_report["applied_encoder_arguments"] = {
            "epochs": args.embedding_num_epochs,
            "batch_size": args.embedding_batch_size,
            "learning_rate": args.body_embedding_learning_rate,
            "pair_iterations": args.num_iterations,
            "loss": args.loss.__name__,
        }

        weight = encoder[0].auto_model.encoder.layer[-1].output.LayerNorm.weight
        before_hash = hashlib.sha256(weight.detach().numpy().tobytes()).hexdigest()
        if first_encoder_hash is None:
            first_encoder_hash = before_hash
        if before_hash != first_encoder_hash:
            raise ValueError("O encoder não começou com o mesmo peso original em todas as divisões")
        fold_report["encoder_parameter"] = "last_encoder_layer.output.LayerNorm.weight"
        fold_report["encoder_parameter_sha256_before"] = before_hash
        fold_report["status"] = "training"
        write_json(output / "run.json", report)
        print(f"Divisão {number}/{FOLD_COUNT}: treino iniciado", flush=True)

        control.sendall(b"S")
        if control.recv(1) != b"K":
            raise RuntimeError("O supervisor não confirmou o início do treino")
        start_train = time.perf_counter()
        try:
            trainer.train()
        finally:
            fold_report["train_seconds"] = time.perf_counter() - start_train
            control.sendall(b"E")
            train_total += fold_report["train_seconds"]
            report["train_total_seconds"] = train_total

        fold_report["encoder_parameter_sha256_after"] = hashlib.sha256(weight.detach().numpy().tobytes()).hexdigest()
        fold_report["optimizer_steps"] = trainer.st_trainer.state.global_step
        fold_report["pair_rows"] = len(trainer.st_trainer.train_dataset)
        classes = head.classes_.tolist()
        fold_report["fitted_head_classes"] = classes
        if set(classes) != set(LABELS) or fold_report["optimizer_steps"] < 1:
            raise ValueError("O treino não produziu a cabeça esperada e passos do encoder")
        if fold_report["encoder_parameter_sha256_after"] == before_hash:
            raise ValueError("O parâmetro monitorado do encoder não foi ajustado")

        warmup_id = train_ids[0]
        fold_report["warmup_id"] = warmup_id
        fold_report["status"] = "inferring"
        write_json(output / "run.json", report)
        observe(model, records[warmup_id]["text"], classes)
        for key in fold["validation_ids"]:
            result = observe(model, records[key]["text"], classes)
            prediction = {"id": key, "fold": number, "expected_label": records[key]["label"], **result}
            predictions.append(prediction)
            with (output / "predictions.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(prediction, ensure_ascii=False, allow_nan=False) + "\n")
        fold_report["status"] = "complete"
        write_json(output / "run.json", report)
        print(f"Divisão {number}/{FOLD_COUNT}: treino e inferência concluídos", flush=True)
        del trainer, model, encoder, head, weight
        gc.collect()

    del report["active_fold"]
    report["summary"] = summarize(predictions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Novo diretório de evidências")
    parser.add_argument("--control-fd", type=int, required=True)
    arguments = parser.parse_args()
    output = arguments.output
    started = time.perf_counter()
    cpu = next(line.partition(":")[2].strip()
               for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name"))
    report = {
        "task": "C05-SF1",
        "status": "running",
        "started_at_utc": timestamp(),
        "runtime": {
            "python": platform.python_version(),
            "system": platform.system(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "cpu": cpu,
            "logical_cpus_available": len(os.sched_getaffinity(0)),
            "packages": dict(sorted((dist.metadata["Name"], dist.version) for dist in distributions())),
        },
        "runner_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in (
                "install.sh", "model-lock.json", "protocol.py", "provision.py",
                "requirements.txt", "run.py", "run.sh", "supervise.py",
            )
        },
        "folds": [],
    }
    write_json(output / "run.json", report)
    try:
        with socket.socket(fileno=arguments.control_fd) as control:
            control.set_inheritable(False)
            run(output, report, control)
        report["status"] = "complete"
    except (Exception, KeyboardInterrupt) as error:
        report["status"] = "interrupted"
        report["interruption"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        report["finished_at_utc"] = timestamp()
        report["elapsed_seconds"] = time.perf_counter() - started
        write_json(output / "run.json", report)


if __name__ == "__main__":
    main()
