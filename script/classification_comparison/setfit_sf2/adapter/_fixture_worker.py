"""Worker de controle SF2-03 para integração local, com especialistas fictícios."""

import argparse
import hashlib
from pathlib import Path
import sys

from ..contracts.core import decode, structure
from .__main__ import serve
from .test_decide import FixturePackage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, type=Path)
    args = parser.parse_args()
    encoded = args.policy.read_bytes()
    policy = decode(encoded.decode("utf-8"))
    structure("policy", policy)
    serve(FixturePackage(), policy, hashlib.sha256(encoded).hexdigest(), sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
