from datetime import datetime, timezone
import os
from pathlib import Path
import sys

from script.classification_comparison.setfit_sf2.contracts.core import read, require, sha256
from script.classification_comparison.setfit_sf2.training.package import json_bytes

receipt_path = Path(sys.argv[1])
expected = sys.argv[2]
require(sha256(receipt_path) == expected, "recibo de pré-voo divergente")
receipt = read(receipt_path)
require(receipt["stage"] == "passed" and str(Path.cwd()) == receipt["cwd"], "execução fora do pré-voo")
argv = receipt["training_argv"]
environment = receipt["environment_allowlist"]
require(all(os.environ.get(key) == value for key, value in environment.items()), "ambiente divergente")
require(not Path(argv[-1]).exists(), "saída de treino já existe")
path = receipt_path.parent / "launch-training.json"
with path.open("xb") as handle:
    handle.write(json_bytes({
        "pid": os.getpid(), "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "argv": argv, "cwd": str(Path.cwd()), "preflight_sha256": expected,
        "status_path": str(Path(argv[-1]) / "status.json"),
        "log_path": str(Path(argv[-1]) / "commands.log"),
    }))
os.execve(argv[0], argv, environment)
