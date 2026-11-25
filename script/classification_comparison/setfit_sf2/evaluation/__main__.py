"""CLI operacional. O inventário reservado só existe nos dois últimos estágios."""
import argparse
import sys
from pathlib import Path

from . import workflow


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="stage", required=True)
    for stage, description in (("validate", "Coletar decisões e selecionar a revisão na validação."),
                               ("freeze", "Reauditar o desenvolvimento e selar o comando final."),
                               ("execute", "Executar o final uma vez e selar as respostas."),
                               ("audit", "Recalcular as métricas das respostas seladas.")):
        command = sub.add_parser(stage, help=description)
        command.add_argument("config", type=Path)
        command.add_argument("validation", type=Path)
        if stage != "validate":
            command.add_argument("release", type=Path)
        if stage in ("execute", "audit"):
            command.add_argument("release_sha256")
            command.add_argument("private_inventory", type=Path)
            command.add_argument("destination", type=Path)
        if stage == "audit":
            command.add_argument("execution_sha256")
    args = vars(parser.parse_args(argv))
    name = args.pop("stage")
    try:
        result = getattr(workflow, name)(*args.values())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"{name}: {exc}", file=sys.stderr)
        return 1
    print(result)
    return 0 if result not in ("inconclusive", "failed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
