"""Provisionamento, treino supervisionado e extração de scores SF2."""

import argparse
import importlib
from pathlib import Path
import shutil
import sys

from . import supervise

PATH_ROLES = ("snapshot", "training_freeze", "arguments", "training_code", "train", "validation",
              "annotations", "public_manifest", "review_receipt", "token_lengths", "final_seal")


def check(args):
    from .environment import check_pins, configure_cpu, snapshot_receipt
    from .package import write_json

    versions = check_pins()
    configure_cpu()
    for dependency in ("datasets", "joblib", "jsonschema", "numpy", "safetensors", "sentence_transformers",
                       "sentencepiece", "setfit", "sklearn", "torch", "transformers"):
        importlib.import_module(dependency)
    snapshot = snapshot_receipt(args.snapshot)
    if args.copy_to:
        shutil.copytree(args.snapshot, args.copy_to)
        if snapshot_receipt(args.copy_to) != snapshot:
            raise ValueError("cópia do snapshot diverge dos hashes conferidos")
    torch = importlib.import_module("torch")
    write_json(args.output, {"versions": versions, "snapshot": snapshot, "device": "cpu",
                             "torch_threads": [torch.get_num_threads(), torch.get_num_interop_threads()]})
    print(f"{len(versions) - 1} pins conferidos; {len(snapshot['files'])} arquivos do snapshot conferidos")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    installer = commands.add_parser("install", help="Provisiona um ambiente com prazo de 30 min")
    installer.add_argument("--snapshot", type=Path, required=True)
    installer.add_argument("--output", type=Path, required=True)
    checker = commands.add_parser("check", help="Confere pins, imports e snapshot")
    checker.add_argument("--snapshot", type=Path, required=True)
    checker.add_argument("--output", type=Path, required=True)
    checker.add_argument("--copy-to", type=Path)
    code = commands.add_parser("code-manifest", help="Gera o inventário para congelar o código de treino")
    code.add_argument("--output", type=Path, required=True)
    for name in ("train", "run-worker"):
        trainer = commands.add_parser(name)
        for key in PATH_ROLES:
            trainer.add_argument("--" + key.replace("_", "-"), type=Path, required=True)
        trainer.add_argument("--output", type=Path, required=True)
        if name == "run-worker":
            trainer.add_argument("--control-fd", type=int, required=True)
            trainer.add_argument("--staging", type=Path, required=True)
    scores = commands.add_parser("scores", help="Extrai scores de decisões originais seladas")
    for key in ("package", "validation", "policy", "predictions", "output"):
        scores.add_argument("--" + key, type=Path, required=True)
    scores.add_argument("--package-sha256", required=True)
    scores.add_argument("--predictions-sha256", required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "install":
            return supervise.install(args.snapshot, args.output)
        if args.command == "check":
            check(args)
        elif args.command == "train":
            return supervise.train(args.output, argv[1:])
        elif args.command == "run-worker":
            from .fit import run

            run(args)
        elif args.command == "code-manifest":
            from .fit import code_manifest
            from .package import write_json

            write_json(args.output, code_manifest())
        elif args.command == "scores":
            from .scores import run

            run(args)
    except Exception as error:
        print(f"SF2 ({type(error).__name__}): {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
