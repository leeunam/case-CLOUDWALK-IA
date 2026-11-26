"""Pré-voo público e comandos condicionais SF2-FINAL-R1. Usar Python pinado -I -B."""
import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).absolute().parents[4]
HERE = "script/classification_comparison/setfit_sf2/qualification_r1/"
MODULE = "script.classification_comparison.setfit_sf2"


def bootstrap():
    env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    command = ["/usr/bin/git", "--no-replace-objects", "-C", str(ROOT)]
    commit = subprocess.check_output([*command, "rev-parse", "HEAD"], env=env).decode().strip()
    blobs = {}
    for name in ("cli.py", "bootstrap.py"):
        path = ROOT / (HERE + name)
        raw = subprocess.check_output([*command, "show", commit + ":" + HERE + name], env=env)
        if path.resolve() != path or path.read_bytes() != raw:
            raise ValueError("inicializador fora do commit aceito")
        blobs[name] = raw
    module = types.ModuleType("_sf2_bootstrap")
    exec(compile(blobs["bootstrap.py"], str(ROOT / HERE / "bootstrap.py"), "exec"), module.__dict__)
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


def active_worker(args, pre, release, guard, b, commit, source_hashes, snapshot):
    import os
    from importlib import import_module
    storage = import_module(MODULE + ".qualification_r1.storage")
    seal = json.loads(storage.read(snapshot / b.FINAL_PROTOCOL))["anchors_sha256"]["public_final_seal"]
    # Derivar o digest da reserva, nunca dos próprios arquivos que se quer liberar.
    reserved = json.loads(storage.read(guard.shared / (seal + ".json")))
    expected = reserved["release_sha256"]
    guard.authorization(expected, seal)
    guard.verify(args.release, expected, seal, args.run)
    config, frozen, command = release.chain(args.release, expected)
    require = storage.require
    require(args.commit == commit and config == pre.configuration(ROOT, commit, args.release, args.run)
            and frozen["current_sources"] == source_hashes and command["argv"] == [sys.executable, "-I", "-B", *sys.argv]
            and command["cwd"] == os.getcwd() and command["environment"] == dict(os.environ), "worker fora da liberação")
    dependencies = import_module(MODULE + ".qualification_r1.dependencies")
    require(dependencies.inventory(frozen["versions"]) == frozen["dependencies"], "dependências do worker divergentes")
    # O próprio adaptador original só inicia após vincular este processo à reserva única.
    storage.exclusive(args.run / "worker-started.json", storage.encoded(dict(release_sha256=expected, pid=os.getpid())))
    raw = storage.read(snapshot / pre.PUBLIC["package_manifest"], args.package_sha256)
    pack = import_module(MODULE + ".qualification_r1.package")
    with pack.verified_package(pre.PACKAGE, raw, args.package_sha256) as (local, _):
        adapter = import_module(MODULE + ".adapter.__main__")
        sys.argv = ["sf2-worker", "--package", str(local), "--package-sha256", args.package_sha256,
                    "--policy", str(snapshot / pre.PUBLIC["policy"])]
        return adapter.main()


def dispatch(args):
    b, commit = bootstrap()
    with b.snapshot(ROOT, commit) as (snapshot, sources):
        pre = importlib.import_module(MODULE + ".qualification_r1.preflight")
        release = importlib.import_module(MODULE + ".qualification_r1.release")
        flow = importlib.import_module(MODULE + ".qualification_r1.execution")
        exposure = importlib.import_module(MODULE + ".qualification_r1.exposure")
        guard = exposure.Guard.production()
        def inspect(config):
            return pre.inspect_public(ROOT, commit, snapshot, sources, config)

        if args.action == "template":
            return pre.configuration(ROOT, commit, args.release, args.run)
        if args.action == "freeze":
            return release.freeze(args.config, args.out, inspect)
        if args.action == "_worker":
            return active_worker(args, pre, release, guard, b, commit, sources, snapshot)
        checked = release.check(args.release, args.expect, inspect)
        if args.action == "check":
            return args.expect
        config, _, _ = release.chain(args.release, args.expect)
        dest = args.out if args.action == "execute" else args.run
        b.check(str(dest) == config["run"], "destino diferente do planejado")
        runtime = importlib.import_module(MODULE + ".runtime_r1")
        if args.action == "execute":
            return flow.execute(checked, args.release, args.expect, args.custody, dest, guard,
                                load_records=flow.records_from_custody, supervise=flow._supervise,
                                derive=runtime.derive, verify=runtime.verify)
        return flow.audit(checked, args.release, args.expect, args.custody, dest, args.execution_sha256, guard,
                          load_records=flow.records_from_custody, verify=runtime.verify)


if __name__ == "__main__":
    try:
        result = dispatch(parse(sys.argv[1:]))
        if type(result) is int:
            sys.exit(result)
        print(json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else result)
    except (OSError, ValueError, KeyError, ImportError, subprocess.CalledProcessError) as exc:
        sys.exit(f"SF2-FINAL-R1 interrompida: {type(exc).__name__}: {exc}")

