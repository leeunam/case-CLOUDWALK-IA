"""Worker local SF2 IPC por stdin/stdout JSONL."""

import argparse
from contextlib import redirect_stdout
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter_ns

from ..contracts.core import decode, structure
from ..training.environment import check_pins, configure_cpu
from ..training.package import load_package
from .decide import decide


def serve(package, policy, policy_sha256, inputs, wire):
    wire.write('{"type":"ready"}\n')
    wire.flush()
    for line in inputs:
        started = perf_counter_ns()
        decision = decide(decode(line), package, policy, policy_sha256, started=started)
        wire.write(json.dumps(decision, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n")
        wire.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--package-sha256", required=True)
    parser.add_argument("--policy", required=True, type=Path)
    args = parser.parse_args()

    wire = sys.stdout
    try:
        with redirect_stdout(sys.stderr):
            encoded = args.policy.read_bytes()
            policy = decode(encoded.decode("utf-8"))
            structure("policy", policy)
            versions = check_pins()
            configure_cpu()
            package = load_package(args.package, args.package_sha256, versions)
            serve(package, policy, hashlib.sha256(encoded).hexdigest(), sys.stdin, wire)
    except Exception as error:
        print(f"Worker SF2 encerrado ({type(error).__name__}): {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
