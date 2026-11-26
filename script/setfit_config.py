"""Seleção explícita da integração SetFit nas duas demonstrações."""
from pathlib import Path


def classifier_options(parser, choices):
    parser.add_argument("--classifier", choices=(*choices, "setfit"), default="fixture")
    parser.add_argument("--model-dir", type=Path, help="diretório local do pacote aprovado SetFit R1")


def classifier_overlay(args, root, env):
    if getattr(args, "classifier", "fixture") != "setfit":
        if getattr(args, "model_dir", None) is not None:
            raise SystemExit("--model-dir exige --classifier setfit.")
        return []
    model = args.model_dir
    if model is None or not model.is_dir() or not (model / "manifest.json").is_file():
        raise SystemExit("Informe --model-dir com o pacote SetFit R1 instalado.")
    env["SETFIT_MODEL_PATH"] = str(model.resolve())
    return [root / "compose.setfit.yml"]
