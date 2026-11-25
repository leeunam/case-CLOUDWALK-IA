from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

from script.classification_comparison.setfit_sf2.contracts.core import read, require, sha256
from script.classification_comparison.setfit_sf2.training.package import write_json

cache = Path(sys.argv[1])
original = cache / "preflight.json"
previous = read(cache / "training-01/status.json")
require(previous["status"] == "failed", "desfecho inesperado da tentativa 01")
require((cache / "training-01/commands.log").read_text() ==
        "SF2 (PermissionError): [Errno 1] Operation not permitted\n", "log original divergente")
require(not (cache / "training-01/package").exists(), "artefato de treino inesperado na tentativa 01")
receipt = read(original)
require(sha256(original) == "a91cef53ec003b14186a2dc41a23801239cd829ece718f8b71286d2ca2465ae4",
        "pré-voo original divergente")
require(receipt["training_argv"][-1] == str(cache/"training-01"), "saída original divergente")
checks = read(cache / "training-freeze.json")
require(sha256(cache / "training-freeze.json") == receipt["training_freeze_sha256"], "freeze divergente")
bindings = read(cache / "training-files.json")
for role, expected in {**checks["files"], "final_seal": checks["final_seal_sha256"]}.items():
    require(sha256(bindings[role]) == expected, f"papel alterado: {role}")
for path, digest in read(cache / "training-code.json")["files"].items():
    require(sha256(path) == digest, f"código alterado: {path}")
require(sha256(cache / "environment.json") == receipt["environment_sha256"], "ambiente divergente")
receipt["training_argv"][-1] = str(cache/"training-02")
receipt["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
receipt["original_preflight_sha256"] = sha256(original)
receipt["previous_status_sha256"] = sha256(cache/"training-01/status.json")
receipt["previous_log_sha256"] = sha256(cache/"training-01/commands.log")
receipt["launch_reason"] = "Integrador autorizou novo lançamento com permissão para IPC local após interrupção antes do ajuste. Parâmetros, código, pré-treino e dados preservados."
mem = dict((k, int(v.strip().split()[0]) * 1024) for k, v in
           (line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
           if k in {"MemAvailable", "MemTotal", "SwapFree"})
receipt["resources"] = {"disk_free_bytes": shutil.disk_usage(cache).free, "memory_bytes": mem}
target = cache / "attempt-02"
target.mkdir()
write_json(target / "preflight.json", receipt)
print(sha256(target / "preflight.json"))
print(receipt["resources"])
