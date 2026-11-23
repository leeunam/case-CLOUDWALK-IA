"""Executa somente desenvolvimento pelo runner comum e guarda o diagnóstico."""
import argparse
import shutil
import subprocess
import sys
import time

from adapter import ROOT
from model import HERE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, choices=range(3, 25), default=3, metavar="3..24")
    parser.add_argument("--context-limit", type=int, choices=(512, 2048), default=512,
                        help="512 conservador, 2048 experimental apenas em desenvolvimento")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_name = ("dry" if args.dry_run else "dev") + f"-{args.limit}-{args.context_limit}-{time.time_ns()}"
    config = "real.json" if args.context_limit == 512 else "real-dev-2048.json"
    output = HERE / "evidence" / run_name
    output.parent.mkdir(parents=True, exist_ok=True)
    runner = ROOT / "script/classification_comparison/run.py"
    command = [sys.executable, "-B", str(runner), "--mode", "real", "--split", "development",
               "--config", str(HERE / config), "--output", str(output),
               "--limit", str(args.limit), "--concurrency", "1", "--attempts", "1"]
    if args.dry_run:
        command.append("--dry-run")
    result = subprocess.run(command, cwd=ROOT, stderr=subprocess.PIPE, check=False)
    sys.stderr.buffer.write(result.stderr)
    if output.is_dir():
        (output / "candidate-stderr.log").write_bytes(result.stderr)
        if not args.dry_run:
            for name in ("snapshot.json", "runtime-freeze.txt"):
                source = HERE / ".cache" / name
                if source.is_file():
                    shutil.copyfile(source, output / name)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
