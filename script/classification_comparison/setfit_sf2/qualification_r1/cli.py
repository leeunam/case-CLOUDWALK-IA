"""Pré-voo público e comandos condicionais SF2-FINAL-R1. Usar Python pinado -I -B -S."""
import argparse
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from contextlib import ExitStack

ROOT = Path(__file__).absolute().parents[4]
HERE = "script/classification_comparison/setfit_sf2/qualification_r1/"
MODULE = "script.classification_comparison.setfit_sf2"


def bootstrap():
    env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    # Antes de carregar o bootstrap, fixe a worktree por descritor, inclusive seus pais.
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as stack:
        fd = os.open("/", flags)
        stack.callback(os.close, fd)
        for part in ROOT.parts[1:]:
            fd = os.open(part, flags, dir_fd=fd)
            stack.callback(os.close, fd)
        cmd = ["/usr/bin/git", "--no-replace-objects", "-C", f"/proc/self/fd/{fd}"]
        commit = subprocess.check_output([*cmd, "rev-parse", "HEAD"], pass_fds=(fd,), env=env).decode().strip()
        name = HERE + "bootstrap.py"
        raw = subprocess.check_output([*cmd, "show", commit + ":" + name], pass_fds=(fd,), env=env)
    module = types.ModuleType("_sf2_bootstrap")
    exec(compile(raw, str(ROOT / name), "exec"), module.__dict__)
    for name in ("cli.py", "bootstrap.py"):
        module.committed(ROOT, commit, HERE + name)
    return module, commit


def parse(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    verbs = parser.add_subparsers(dest="action", required=True)
    for action in ("template", "freeze", "check", "execute", "audit", "_worker"):
        p = verbs.add_parser(action)
        if action == "freeze":
            p.add_argument("--config", required=True, type=Path)
        else:
            p.add_argument("--release", required=True, type=Path)
        if action in ("template", "audit", "_worker"):
            p.add_argument("--run", required=True, type=Path)
        if action in ("freeze", "execute"):
            p.add_argument("--out", required=True, type=Path)
        if action in ("check", "execute", "audit"):
            p.add_argument("--expect", required=True)
        if action in ("execute", "audit"):
            p.add_argument("--custody", required=True, type=Path)
        if action == "audit":
            p.add_argument("--execution-sha256", required=True)
        if action == "_worker":
            for name in ("commit", "package", "package-sha256", "policy"):
                p.add_argument("--" + name, required=True)
    return parser.parse_args(argv)


def active_worker(args, pre, guard, b, commit, source_hashes, snapshot, authenticated):
    import os
    from importlib import import_module
    storage = import_module(MODULE + ".qualification_r1.storage")
    expected, config = authenticated.sha256, authenticated.config
    frozen, command = authenticated.frozen, authenticated.command
    guard.verify(args.release, expected, frozen["final_seal_sha256"], args.run)
    require = storage.require
    require(args.commit == commit and config == pre.configuration(ROOT, commit, args.release, args.run)
            and frozen["current_sources"] == source_hashes and command["argv"] == [sys.executable, "-I", "-B", "-S", *sys.argv]
            and command["cwd"] == os.getcwd() and command["environment"] == dict(os.environ), "worker fora da liberação")
    verify_interpreter(frozen, b.interpreter())
    # O próprio adaptador original só inicia após vincular este processo à reserva única.
    storage.exclusive(args.run / "worker-started.json", storage.encoded(dict(release_sha256=expected, pid=os.getpid())))
    raw = storage.read(snapshot / pre.PUBLIC["package_manifest"], args.package_sha256)
    pack = import_module(MODULE + ".qualification_r1.package")
    with pack.verified_package(pre.PACKAGE, raw, args.package_sha256) as (local, _):
        adapter = import_module(MODULE + ".adapter.__main__")
        sys.argv = ["sf2-worker", "--package", str(local), "--package-sha256", args.package_sha256,
                    "--policy", str(snapshot / pre.PUBLIC["policy"])]
        return adapter.main()


def verify_interpreter(frozen, actual):
    if frozen["python_executable"] != actual:
        raise ValueError("Python efetivamente carregado diverge da liberação")


def authenticate(args, b, commit, snapshot, sources, layout, release, guard, storage):
    """Somente o primeiro freeze e a emissão de seu template precedem uma liberação."""
    if args.action in ("freeze", "template"):
        return None
    protocol = storage.decode(storage.read(snapshot / b.FINAL_PROTOCOL, b.PLAN_SHA))
    seal = protocol["anchors_sha256"]["public_final_seal"]
    if args.action == "_worker":
        reserved = storage.decode(storage.read(guard.shared / (seal + ".json")))
        expected = reserved["release_sha256"]
        guard.verify(args.release, expected, seal, args.run)
    else:
        expected = args.expect
    authenticated = release.chain(args.release, expected, layout=layout)
    config, frozen = authenticated.config, authenticated.frozen
    b.check(frozen["final_seal_sha256"] == seal, "selo público da liberação divergente")
    b.check(config["accepted_commit"] == frozen["accepted_commit"] == commit
            and frozen["current_sources"] == sources, "fontes efetivas divergem da liberação")
    b.check(type(frozen["dependencies"]) is dict and set(frozen["dependencies"]) == {"pth", "distributions"},
            "inventário de dependências liberado inválido")
    verify_interpreter(frozen, b.interpreter())
    return authenticated


def pin_public_temporaries():
    # A primeira consulta implícita de tempfile (inclusive em terceiros) já usa a raiz pública.
    tempfile.tempdir = "/tmp"
    for key in ("TMPDIR", "TEMP", "TMP"):
        if key in os.environ:
            os.environ[key] = "/tmp"


def dispatch(args):
    b, commit = bootstrap()
    layout = b.arguments(ROOT, commit, args)
    with b.snapshot(ROOT, commit) as (snapshot, sources):
        # Estes módulos do snapshot usam somente a biblioteca padrão.
        release = importlib.import_module(MODULE + ".qualification_r1.release")
        guard = importlib.import_module(MODULE + ".qualification_r1.exposure").Guard.production()
        storage = importlib.import_module(MODULE + ".qualification_r1.storage")
        authenticated = authenticate(args, b, commit, snapshot, sources, layout, release, guard, storage)
        dep = importlib.import_module(MODULE + ".qualification_r1.dependencies")
        origin = snapshot / "docs/evidencias/c05/sf2/qualificacao-01/execucao-02/pacote/manifest.json"
        raw = origin.read_bytes()
        b.check(b.sha(raw) == b.PACKAGE_SHA, "manifesto do ambiente divergente")
        expected = authenticated.frozen["dependencies"] if authenticated is not None else None
        with dep.environment(json.loads(raw)["versions"], expected=expected) as dependencies:
            return dispatch_verified(args, b, commit, snapshot, sources, layout, dependencies,
                                     release, guard, authenticated)


def dispatch_verified(args, b, commit, snapshot, sources, layout, dependencies, release, guard, authenticated):
    pre = importlib.import_module(MODULE + ".qualification_r1.preflight")
    flow = importlib.import_module(MODULE + ".qualification_r1.execution")
    def inspect(config):
        return pre.inspect_public(ROOT, commit, snapshot, sources, config, dependencies)

    if args.action == "template":
        return pre.configuration(ROOT, commit, args.release, args.run)
    if args.action == "freeze":
        return release.freeze(args.config, args.out, inspect, layout=layout)
    if args.action == "_worker":
        return active_worker(args, pre, guard, b, commit, sources, snapshot, authenticated)
    checked = release.check_authenticated(authenticated, inspect)
    if args.action == "check":
        return args.expect
    config = authenticated.config
    dest = args.out if args.action == "execute" else args.run
    b.check(str(dest) == config["run"], "destino diferente do planejado")
    runtime = importlib.import_module(MODULE + ".runtime_r1")
    if args.action == "execute":
        return flow.execute(checked, args.release, args.expect, args.custody, dest, guard,
                            load_records=flow.records_from_custody, supervise=flow._supervise,
                            derive=runtime.derive, verify=runtime.verify)
    return flow.audit(checked, args.release, args.expect, args.custody, dest, args.execution_sha256, guard,
                      load_records=flow.records_from_custody, verify=runtime.verify)


def main(argv):
    pin_public_temporaries()
    return dispatch(parse(argv))


if __name__ == "__main__":
    try:
        result = main(sys.argv[1:])
        if type(result) is int:
            sys.exit(result)
        print(json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else result)
    except (OSError, ValueError, KeyError, ImportError, subprocess.CalledProcessError) as exc:
        sys.exit(f"SF2-FINAL-R1 interrompida: {type(exc).__name__}: {exc}")

