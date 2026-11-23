"""Planeja e executa um único relato de desenvolvimento, sem controles."""
import argparse
import os
import platform
import shlex
import subprocess
import sys
import uuid
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
from adapter import HERE, MODEL, VERSION, pilot_budget, request_body
from common import c01, decode, encode, injected_inventory, preflight, project
from journal import Journal, inventory
from pilot import Blocked, billable_output_ceiling, checked_reasoning, single_case_id
from run import run_batch, write_json, write_report


def run(args, *, synthetic_adapter=None):
    validation, protocol, split, catalog, cases, example = preflight()
    pilot = args.pilot.resolve()
    pilot_bytes = pilot.read_bytes()
    settings = decode(pilot_bytes)
    if not isinstance(settings, dict):
        raise Blocked("configuração de piloto inválida")
    development = [case_id for group in split["development"].values() for case_id in group]
    case_id = single_case_id(settings, development)
    selected = [case_id]
    item = project(cases[case_id], catalog)
    inputs = [item]
    c01.structure(validation, "input", item)
    _, _, received = c01.normalize_input(item, catalog)

    config = c01.read(HERE / "real.json")
    if (config["identity"]["mode"] != "real" or config["identity"]["requested_model"] != MODEL
            or config["contract_version"] != VERSION or protocol["contract_version"] != VERSION):
        raise Blocked("configuração real Qwen incompatível com o contrato")
    report = example["report"].copy()
    sources = dict(report["sources"], prompt=config["prompt"], policy=config["policy"])
    reference = protocol["control_policy"]
    policy = c01.read(c01.source_path(reference))
    injections = injected_inventory([], reference, policy)
    revision = subprocess.check_output(["rtk", "git", "rev-parse", "HEAD"], cwd=c01.ROOT, text=True).strip()
    report.update(identity=config["identity"], sources=sources, split="development",
                  planned_ids=selected, completed_ids=selected, control_ids=[], injected_controls=injections,
                  run_id="c03-" + uuid.uuid4().hex, eligibility="inconclusive", git_revision=revision,
                  environment=dict(report["environment"], runtime=platform.python_version(),
                                   hardware=platform.machine(), peak_memory_bytes=None))
    c01.structure(validation, "report", report)
    c01.verify_sources(report, protocol, split)

    max_tokens = settings.get("max_tokens")
    input_ceiling = settings.get("input_token_ceiling")
    if any(type(value) is not int or value < 1 for value in (max_tokens, input_ceiling)):
        raise Blocked("piloto de um relato exige limites positivos de entrada e saída")
    output_ceiling = billable_output_ceiling(settings)
    reasoning = checked_reasoning(settings)
    instructions = "\n\n".join(c01.source_path(sources[key]).read_text(encoding="utf-8")
                                for key in ("prompt", "rubric"))
    body_bytes = len(request_body(item, received, instructions, max_tokens, reasoning))
    if body_bytes > input_ceiling:
        raise Blocked("requisição excede o limite local de tamanho")

    authorization = args.authorization.resolve() if args.authorization else None
    pins = SimpleNamespace(pilot=pilot, pilot_sha256=sha256(pilot_bytes).hexdigest(), authorization=authorization,
                           authorization_sha256=c01.digest(authorization) if authorization else None)
    reservation = None
    if not args.dry_run:
        scope = "synthetic" if synthetic_adapter is not None else "live"
        # Confere os limites sem carregar a chave. O processo do adaptador confere a credencial.
        budget = pilot_budget(pins, scope, config["identity"], has_credential=lambda: True)
        if budget.allowed != {case_id} or budget.max_requests != 1:
            raise Blocked("autorização do adaptador diverge do plano de um relato")
        reservation = str(budget.per_request)

    candidate = synthetic_adapter if synthetic_adapter is not None else [str(HERE / "adapter.py")]
    config["command"] = [sys.executable, "-B", *candidate, "--pilot", str(pilot),
                         "--pilot-sha256", pins.pilot_sha256]
    output = args.output.resolve()
    if not output.is_relative_to(c01.ROOT) or output == c01.ROOT:
        raise ValueError("artefatos exigem diretório novo dentro do checkout")
    output.mkdir(exist_ok=False, parents=True)
    command = ["rtk", "proxy", "python3", "-B", str(Path(__file__).resolve().relative_to(c01.ROOT)),
               "--pilot", os.path.relpath(pilot, c01.ROOT), "--output", "NOVO_DIRETORIO"]
    if authorization:
        command.extend(["--authorization", os.path.relpath(authorization, c01.ROOT)])
        config["command"].extend(["--authorization", str(authorization),
                                  "--authorization-sha256", pins.authorization_sha256])
    if args.dry_run:
        command.append("--dry-run")
    write_json(output / "invocation.json", dict(command=shlex.join(command), contract_version=VERSION,
               pilot_sha256=pins.pilot_sha256, authorization_sha256=pins.authorization_sha256,
               launcher_sha256=c01.digest(Path(__file__)), control_policy=reference, attempts=1, concurrency=1,
               dry_run=args.dry_run, synthetic_transport=synthetic_adapter is not None))
    inputs_path = output / "inputs.jsonl"
    with inputs_path.open("x", encoding="utf-8") as stream:
        stream.write(encode(item) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    write_json(output / "plan.json", dict(run_id=report["run_id"], identity=report["identity"], sources=sources,
               planned_ids=selected, selected_ids=selected, control_ids=[], injected_controls=injections,
               contract_version=VERSION, input=inventory(inputs_path), concurrency=1, attempts=1,
               max_requests=1, max_tokens=max_tokens, input_token_ceiling=input_ceiling,
               billable_output_token_ceiling=output_ceiling, reasoning=reasoning, request_body_bytes=body_bytes,
               reservation_usd=reservation))
    if args.dry_run:
        return

    def publish(inputs, observations, decisions, prefix=False):
        write_report(output, report.copy(), inputs, observations, decisions, validation, protocol, split,
                     catalog, cases, policy, prefix)

    with Journal(output, report["run_id"], inputs, injections, publish) as journal:
        observations, decisions = run_batch(inputs, config, report, catalog, validation, journal, policy)
        publish(inputs, observations, decisions)
        journal.event("finished", decisions=len(decisions))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, default=HERE / "piloto-unitario-exemplo.json")
    parser.add_argument("--authorization", type=Path, help="manifesto local para execução real")
    parser.add_argument("--output", type=Path, required=True, help="diretório novo dentro do checkout")
    parser.add_argument("--dry-run", action="store_true", help="grava o plano sem iniciar o adaptador")
    args = parser.parse_args()
    if not args.dry_run and args.authorization is None:
        parser.error("execução real exige --authorization")
    try:
        run(args)
    except (OSError, ValueError, KeyError, TypeError, TimeoutError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"Piloto interrompido ({type(exc).__name__}): {exc}\n")
    print(args.output)


if __name__ == "__main__":
    main()
