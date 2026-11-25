from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
from subprocess import run
import sys
from types import SimpleNamespace

from script.classification_comparison.setfit_sf2.contracts.artifacts import validate_manifest
from script.classification_comparison.setfit_sf2.contracts.core import (
    PLAN, PROTOCOL, ROOT, SCHEMA_PATH, VERSION, read, require, sha256, structure,
)
from script.classification_comparison.setfit_sf2.training.environment import configure_cpu, load_body
from script.classification_comparison.setfit_sf2.training.fit import checked_inputs, preflight_tokenization
from script.classification_comparison.setfit_sf2.training.package import write_json

output = Path(sys.argv[1])
snapshot = Path(sys.argv[2])
base = "99885274faef5b5ee281ca4d87b9d840f85550ac"
git = lambda *args: run(["git", *args], check=True, capture_output=True).stdout
require(Path.cwd() == ROOT, "diretório de fontes divergente")
require(git("rev-parse", "HEAD").decode().strip() == base, "base divergente")
require(git("branch", "--show-current").decode().strip() == "feat/sf2-qualificacao", "branch divergente")
require(not git("status", "--porcelain"), "worktree tem alterações locais")
datos = PLAN / "dados"
review = ROOT / "docs/evidencias/c05/sf2/dados-publicos-01"
files = {role: ROOT / item["path"] for role, item in PROTOCOL["sources"].items()}
files.update(protocol=PLAN / "protocolo.json", contracts=SCHEMA_PATH,
             train=datos / "train.jsonl", validation=datos / "validation.jsonl",
             annotations=datos / "annotations-public.jsonl", public_manifest=datos / "manifest-public.json",
             review_receipt=review / "review-receipt.json", token_lengths=review / "token-lengths.json",
             final_seal=datos / "final-seal.json", arguments=output / "arguments.json",
             training_code=output / "training-code.json")
seal = read(files["final_seal"])
structure("finalSeal", seal)
require(seal["stage"] == "accepted", "selo final não aceito")
summary = (datos / "final-review-summary.md").read_text()
require(sha256(files["public_manifest"]) in summary and all(
    digest in summary for digest in (seal["files"]["final"]["sha256"], seal["files"]["annotations"]["sha256"],
                                     seal["review_receipt_sha256"], seal["token_lengths_sha256"])),
    "selo, manifesto público e resumo de custódia divergem")
require(seal["counts"] == {"total": PROTOCOL["data"]["final"]["total"],
                           "classifiable": PROTOCOL["data"]["final"]["classifiable_cases"],
                           "expected_review": PROTOCOL["data"]["final"]["expected_review_cases"],
                           "urgent_targets": PROTOCOL["data"]["final"]["urgent_target_cases"]}, "quotas do selo divergentes")
write_json(files["arguments"], PROTOCOL["training"])
tracked = {path for role, path in files.items() if role not in {"arguments", "training_code"}}
tracked.update(ROOT / name for name in read(files["training_code"])["files"])
tracked.add(datos / "final-review-summary.md")
for path in sorted(tracked):
    require(path.read_bytes() == git("show", f"{base}:{path.relative_to(ROOT)}"), f"bytes fora da base: {path}")
public = read(files["public_manifest"])
public_result = validate_manifest("publicManifest", public, {
    name: files[name] for name in (*public["files"], "review_receipt", "token_lengths")
})
training_freeze = output / "training-freeze.json"
hashes = {role: sha256(path) for role, path in files.items()}
seal_hash = hashes.pop("final_seal")
write_json(training_freeze, {"contract_version": VERSION, "files": hashes, "final_seal_sha256": seal_hash})
train, validation, lengths, freeze_hash = checked_inputs(SimpleNamespace(training_freeze=training_freeze, **files))
configure_cpu()
body = load_body(snapshot)
preflight_tokenization(body, train + validation, lengths)
environment = read(output / "environment.json")
require(environment["torch_threads"] == [2, 2] and environment["device"] == "cpu", "recursos de execução divergentes")
require(environment["snapshot"]["revision"] == lengths["revision"], "tokenização com revisão divergente")
argv = [sys.executable, "-B", "-m", "script.classification_comparison.setfit_sf2.training", "train",
        "--snapshot", str(snapshot), "--training-freeze", str(training_freeze)]
worker_roles = ("arguments", "training_code", "train", "validation", "annotations", "public_manifest",
                "review_receipt", "token_lengths", "final_seal")
for role in worker_roles:
    argv += ["--" + role.replace("_", "-"), str(files[role])]
argv += ["--output", str(output / "training-01")]
mem = dict((k, int(v.strip().split()[0]) * 1024) for k, v in
           (line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
           if k in {"MemAvailable", "MemTotal", "SwapFree"})
resources = {"disk_free_bytes": shutil.disk_usage(output).free, "memory_bytes": mem}
write_json(output / "training-files.json", {role: str(path) for role, path in files.items()})
write_json(output / "preflight.json", {
    "stage": "passed", "task": "SF2-05A", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "commit_base": base, "tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
    "branch": git("branch", "--show-current").decode().strip(), "cwd": str(ROOT),
    "public_contract_result": public_result, "public_final_counts": seal["counts"],
    "public_tokenization": {"count": len(lengths["lengths"]), "minimum": min(lengths["lengths"].values()),
                            "maximum": max(lengths["lengths"].values()), "equal_to_accepted_receipt": True},
    "resources": resources, "environment_sha256": sha256(output / "environment.json"),
    "training_inventory_sha256": sha256(output / "training-files.json"),
    "training_freeze_sha256": freeze_hash, "final_public_seal_sha256": seal_hash,
    "training_argv": argv, "environment_allowlist": {key: os.environ[key] for key in ["PATH","LANG","HF_HOME","XDG_CACHE_HOME","TMPDIR","HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","HF_DATASETS_OFFLINE","HF_HUB_DISABLE_IMPLICIT_TOKEN","HF_HUB_DISABLE_TELEMETRY","DO_NOT_TRACK","TOKENIZERS_PARALLELISM","CUDA_VISIBLE_DEVICES","OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"]},
})
print(freeze_hash)
