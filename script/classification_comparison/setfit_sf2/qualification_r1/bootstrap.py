"""Copia somente fontes e recursos públicos do commit aceito antes de importar código SF2."""
import hashlib
import json
import os
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


def public_layout(root):
    directory = root / SF / ".cache/qualificacao-r1-01"
    return dict(config=directory / "config.json", release=directory / "release", run=directory / "final-run")


def public_argument(layout, role, value):
    check(Path(value) == layout[role], "papel fora do caminho público autorizado: " + role)


def arguments(root, commit, args):
    layout = public_layout(root)
    for role in ("config", "release", "run"):
        if hasattr(args, role):
            public_argument(layout, role, getattr(args, role))
    if hasattr(args, "out"):
        public_argument(layout, "release" if args.action == "freeze" else "run", args.out)
    if hasattr(args, "expect"):
        check(re.fullmatch("[0-9a-f]{64}", args.expect), "digest externo inválido")
    if hasattr(args, "execution_sha256"):
        check(re.fullmatch("[0-9a-f]{64}", args.execution_sha256), "digest externo de execução inválido")
    if hasattr(args, "custody"):
        check(args.custody.parent == CUSTODY, "inventário fora da custódia autorizável")
    if args.action == "_worker":
        check(args.commit == commit and args.package == str(PACKAGE) and args.package_sha256 == PACKAGE_SHA and
              args.policy == str(root / CAPTURE_POLICY), "argumentos internos divergentes")
    return layout


CUSTODY = MAIN / ".superpowers/sdd/conclusao-projeto/sf2-final/accepted"
PACKAGE = HISTORY / SF / ".cache/qualificacao-01/training-02/package"
PACKAGE_SHA = "224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872"
CAPTURE_POLICY = "docs/evidencias/c05/sf2/qualificacao-01/execucao-02/avaliacao/capture-policy.json"


def interpreter(invocation=PYTHON, process=Path("/proc/self/exe"), *, allowed=None):
    allowed = allowed or (PYTHON.parent, Path("/home/inteli/.pyenv/versions/3.11.13/bin"))
    def trusted_parent(path):
        check(path.parent in allowed, "cadeia do Python fora das raízes públicas")
        for directory in reversed(path.parents):
            check(not directory.is_symlink(), "diretório do Python redirecionado")
    trusted_parent(invocation)
    path = invocation
    chain = []
    while path.is_symlink():
        target = os.readlink(path)
        check(len(chain) < 16, "cadeia de links do Python inválida")
        chain.append([str(path), target])
        path = Path(os.path.normpath(path.parent / target))
        trusted_parent(path)
    actual = Path(os.readlink(process)) if process.is_symlink() else process
    check(actual == path, "executável do processo diverge da invocação do venv")
    with path.open("rb") as command, process.open("rb") as loaded:
        a, b = os.fstat(command.fileno()), os.fstat(loaded.fileno())
        check((a.st_dev, a.st_ino) == (b.st_dev, b.st_ino), "identidade do Python carregado divergente")
        binary = hashlib.file_digest(loaded, "sha256").hexdigest()
    cfg = invocation.parents[1] / "pyvenv.cfg"
    check(not cfg.is_symlink(), "configuração do venv redirecionada")
    return dict(path=str(invocation), links=chain, target=str(actual), sha256=binary,
                venv_config_sha256=sha(cfg.read_bytes()))


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
    check(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.no_site and sys.version.split()[0] == "3.11.13"
          and Path(sys.executable) == PYTHON, "use o Python pinado com -I -B -S")
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

