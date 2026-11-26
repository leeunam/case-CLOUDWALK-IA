"""Copia somente fontes e recursos públicos do commit aceito antes de importar código SF2."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from contextlib import contextmanager

SF = "script/classification_comparison/setfit_sf2"
PLAN = "docs/planejamento/classificacao-comparativa/sf2"
FINAL_PROTOCOL = PLAN + "/sf2-final-r1-protocolo.json"
FINAL_SCHEMA = PLAN + "/sf2-final-r1.schema.json"
REV = "docs/evidencias/c05/sf2/revisao-01"
PLAN_SHA = "29605e3db4d5f6e9201fd1905dca181412755df2ac9d7b55baccd8d2ff819d1d"
MAIN = Path("/home/inteli/Documents/projetos/case-CLOUDWALK-IA")
HISTORY = MAIN / ".worktrees/sf2-qualificacao"
REPLAY = MAIN / ".worktrees/sf2-replay-r1"
PYTHON = MAIN / ".worktrees/sf2-treinamento" / SF / ".cache/verification/.venv/bin/python"
MIN_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"}
PREFIX = "script.classification_comparison.setfit_sf2"
ENVIRONMENT = {**MIN_ENV, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
               "HF_DATASETS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
               "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1", "TOKENIZERS_PARALLELISM": "false",
               "CUDA_VISIBLE_DEVICES": ""}


def check(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(root, *args):
    return subprocess.check_output(["/usr/bin/git", "--no-replace-objects", "-C", str(root), *args],
                                   env=MIN_ENV)


def committed(root, commit, name):
    check(re.fullmatch("[0-9a-f]{40}", commit) and not Path(name).is_absolute() and ".." not in Path(name).parts,
          "commit ou nome inválido")
    path = root / name
    for component in (*reversed(path.parents), path):
        check(not component.is_symlink(), "origem redirecionada: " + name)
    check(path.is_file(), "origem não regular: " + name)
    raw = path.read_bytes()
    check(git(root, "show", commit + ":" + name) == raw, "bytes fora do commit aceito: " + name)
    return raw


def checkout(root, commit):
    check(root.resolve() == root and git(root, "rev-parse", "HEAD").decode().strip() == commit and
          Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip()) == MAIN / ".git",
          "checkout, raiz principal ou commit divergente")


def resources(root, commit):
    def blob(name):
        return committed(root, commit, name)

    spec = blob(FINAL_PROTOCOL)
    check(sha(spec) == PLAN_SHA, "protocolo SF2-FINAL-R1 divergente")
    anchors = json.loads(spec)["anchors_sha256"]
    preflight = blob(REV + "/preflight.json")
    check(sha(preflight) == anchors["offline_preflight"], "pré-voo R1 divergente")
    prior = json.loads(preflight)["provenance"]
    names = set(prior["current_sources"])
    amendment = blob(PLAN + "/sf2-r1-protocolo.json")
    check(sha(amendment) == anchors["amendment_offline"], "protocolo R1 divergente")
    parent = json.loads(amendment)["parent"]["files"]
    names.update(v["path"] for v in parent.values())
    protocol = blob(parent["protocol"]["path"])
    check(sha(protocol) == anchors["protocol_original"], "protocolo original divergente")
    names.update(v["path"] for v in json.loads(protocol)["sources"].values())
    names.update([FINAL_PROTOCOL, FINAL_SCHEMA, PLAN + "/sf2-r1-protocolo.json", REV + "/selected-policy.json",
                  REV + "/preflight.json", REV + "/execution.json", REV + "/result.json.gz",
                  REV + "/revisoes/revisao-final.md", SF + "/revision_r1/sources.json",
                  PLAN + "/dados/annotations-public.jsonl", PLAN + "/dados/train.jsonl",
                  "docs/evidencias/c05/sf2/dados-publicos-01/review-receipt.json",
                  "docs/evidencias/c05/sf2/dados-publicos-01/token-lengths.json"])
    for package in ("qualification_r1", "runtime_r1"):
        prefix = SF + "/" + package + "/"
        files = git(root, "ls-tree", "-rz", "--name-only", commit, "--", prefix).decode().split("\0")
        modules = {f for f in files if f.endswith(".py") and
                   not any(part.startswith(("test", "fixture")) for part in Path(f[len(prefix):]).parts)}
        check(modules, "implementação aceita ausente: " + package)
        names.update(modules)
    return {name: blob(name) for name in sorted(names)}


def entry_environment():
    check(sys.flags.isolated and sys.dont_write_bytecode and sys.version.split()[0] == "3.11.13"
          and Path(sys.executable) == PYTHON, "use o Python pinado com -I -B")
    check(not any(m == "script" or m.startswith("script.") for m in sys.modules),
          "processo exige imports locais novos")


@contextmanager
def snapshot(root, commit):
    entry_environment()
    checkout(root, commit)
    blobs = resources(root, commit)
    with TemporaryDirectory(prefix="sf2-verified-") as tmp:
        base = Path(tmp)
        for name, raw in blobs.items():
            path = base / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            if name.endswith(".py"):
                # Todos os pais são pacotes regulares do snapshot. Nenhum homônimo em site-packages participa.
                for directory in path.parents:
                    if directory == base:
                        break
                    (directory / "__init__.py").touch(exist_ok=True)
        sys.path.insert(0, str(base))
        try:
            yield base, {name: sha(raw) for name, raw in blobs.items()}
        finally:
            sys.path.remove(str(base))

