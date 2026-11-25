"""Executar a partir da raiz: python3 -m script.classification_comparison.setfit_sf2.contracts."""
import argparse
import json
import sys
from pathlib import Path

from .core import read, structure, verify_sources
from .artifacts import validate_manifest, validate_report
from .data import validate_record
from .ipc import validate_decision, validate_input


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    schema = sub.add_parser("schema", help="Verificar somente a estrutura JSON")
    schema.add_argument("kind")
    schema.add_argument("path", type=Path)
    record = sub.add_parser("record")
    record.add_argument("path", type=Path)
    ipc = sub.add_parser("ipc", help="Auditar controle/decisão com contexto confiável")
    ipc.add_argument("path", type=Path)
    report = sub.add_parser("report")
    report.add_argument("path", type=Path)
    dataset = sub.add_parser("manifest")
    dataset.add_argument("kind", choices=("publicManifest", "finalSeal", "trainingFreeze", "modelManifest", "freeze"))
    dataset.add_argument("path", type=Path)
    dataset.add_argument("--file", action="append", default=[], metavar="PAPEL=CAMINHO")
    args = parser.parse_args(argv)
    try:
        verify_sources()
        payload = read(args.path)
        result = {}
        if args.action == "record":
            validate_record(payload)
        elif args.action == "schema":
            structure(args.kind, payload)
        elif args.action == "report":
            validate_report(payload)
        elif args.action == "ipc":
            validate_input(payload["input"])
            validate_decision(payload["input"], payload["decision"], payload["policy"], payload["class_order"],
                              payload["identities"], interruption=payload.get("interruption"))
        else:
            paths = {}
            for binding in args.file:
                role, path = binding.split("=", 1)
                if role in paths:
                    raise ValueError("papel de arquivo repetido")
                paths[role] = Path(path)
            result = validate_manifest(args.kind, payload, paths) or {}
        print(json.dumps({"valid": True, **result}, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
