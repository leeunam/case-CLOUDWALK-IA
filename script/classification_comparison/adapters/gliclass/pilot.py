"""Executa somente desenvolvimento pelo runner comum e guarda o diagnóstico."""
import argparse
import hashlib
import shutil
import subprocess
import sys
import time

from adapter import ROOT, atomic_json, read_json
from model import HERE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, choices=range(3, 25), default=3, metavar="3..24")
    parser.add_argument("--context-limit", type=int, choices=(512, 2048),
                        help="512 conservador, 2048 experimental apenas em desenvolvimento")
    parser.add_argument("--profile", choices=("A", "B", "C", "D"),
                        help="perfil versionado da matriz de desenvolvimento, sempre com 2048 tokens")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.profile and args.context_limit == 512:
        parser.error("perfis A/B/C/D exigem o limite de desenvolvimento de 2048")
    limit = args.context_limit or (2048 if args.profile else 512)
    profile = args.profile or ("A" if limit == 2048 else None)
    row = None
    config = HERE / "real.json"
    if profile:
        matrix = read_json(HERE / "development-matrix.json")
        row = matrix["profiles"][profile]
        config = HERE / row["config"]
        if hashlib.sha256(config.read_bytes()).hexdigest() != row["config_sha256"]:
            parser.error("configuração não confere com o hash da matriz de desenvolvimento")
    run_name = ("dry" if args.dry_run else "dev") + f"-{args.limit}-{limit}-{profile or 'base'}-{time.time_ns()}"
    output = HERE / "evidence" / run_name
    output.parent.mkdir(parents=True, exist_ok=True)
    runner = ROOT / "script/classification_comparison/run.py"
    command = [sys.executable, "-B", str(runner), "--mode", "real", "--split", "development",
               "--config", str(config), "--output", str(output),
               "--limit", str(args.limit), "--concurrency", "1", "--attempts", "1"]
    if args.dry_run:
        command.append("--dry-run")
    result = subprocess.run(command, cwd=ROOT, stderr=subprocess.PIPE, check=False)
    sys.stderr.buffer.write(result.stderr)
    if output.is_dir():
        (output / "candidate-stderr.log").write_bytes(result.stderr)
        if row is not None:
            atomic_json(output / "development-profile.json", dict(row, profile=profile,
                        matrix_version=matrix["version"], context_limit=limit))
        if not args.dry_run:
            for name in ("snapshot.json", "runtime-freeze.txt"):
                source = HERE / ".cache" / name
                if source.is_file():
                    shutil.copyfile(source, output / name)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
