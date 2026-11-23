"""Executa a qualificação C05 com a projeção e a evidência da C02."""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
from budget import Account, BudgetError, cap_usd
from settings import HERE, PROFILE, VERSIONS, Plan, account_from_args, resolve_account
from common import c01, decode, encode
from journal import Journal, inventory
from run import run_batch, write_json, write_report


def command_for(args):
    command = ["rtk", "proxy", "python3", "-B", str(Path(__file__).resolve().relative_to(c01.ROOT)),
               "run", "--mode", args.mode, "--config", str(args.config.resolve()),
               "--output", "NOVO_DIRETORIO"]
    if args.account is not None:
        command += ["--account", str(args.account.resolve()), "--account-id", args.account_id,
                    "--cap-usd", str(args.cap_usd)]
    if args.dry_run:
        command.append("--dry-run")
    else:
        command += ["--manifest", str(args.manifest.resolve()), "--confirm-execution"]
    return shlex.join(command)


def write_plan(output, plan, args, account, manifest_sha):
    output.mkdir(exist_ok=False, parents=True)
    inputs_path = output / "inputs.jsonl"
    with inputs_path.open("xb") as stream:
        stream.write(plan.input_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    binding = plan.bound_account(account, args.cap_usd) if account else plan.binding
    write_json(output / "plan.json", dict(binding, run_id=plan.report["run_id"],
               contract_version=PROFILE.report_version, planned_ids=binding["final_ids"],
               selected_ids=binding["final_ids"], input=inventory(inputs_path), injected_controls=plan.injections,
               settings=plan.settings.data))
    write_json(output / "invocation.json", dict(VERSIONS, command=command_for(args),
               config_sha256=plan.settings.sha256, manifest_sha256=manifest_sha, dry_run=args.dry_run,
               git_revision=plan.report["git_revision"], synthetic_transport=args.mode == "fixture",
               concurrency=1, attempts=1))
    if args.dry_run and account:
        write_json(output / "manifest-template.json", dict(enabled=False, manifest_id=uuid.uuid4().hex,
                                                           binding=binding))


def run_evaluation(args, *, fixture_command=None):
    if args.mode not in {"real", "fixture"} or (args.mode == "real" and fixture_command is not None):
        raise BudgetError("transporte de teste só é aceito no modo fixture")
    plan = Plan(args.mode, "c05-" + uuid.uuid4().hex, args.config)
    account = resolve_account(args, args.mode)
    output = args.output.resolve()
    if output == c01.ROOT or not output.is_relative_to(c01.ROOT):
        raise ValueError("artefatos exigem diretório novo dentro do checkout")
    if args.dry_run:
        write_plan(output, plan, args, account, None)
        return

    manifest_id, manifest_sha, binding_sha = plan.authorize(args.manifest, account, args.cap_usd, args.confirm_execution)
    account.validate(args.cap_usd)
    write_plan(output, plan, args, account, manifest_sha)
    run_id = plan.report["run_id"]
    account.claim(run_id, manifest_id, manifest_sha, binding_sha,
                  dict(plan.bound_account(account, args.cap_usd), settings=plan.settings.data))
    adapter = fixture_command or [sys.executable, "-B", str(HERE / "final_adapter.py")]
    config = {"identity": plan.identity, "contract_version": PROFILE.ipc_version,
              "command": [*adapter, "--mode", args.mode, "--config", str(args.config.resolve()),
                          "--manifest", str(args.manifest.resolve()), "--manifest-sha256", manifest_sha,
                          "--account", str(account.path), "--account-id", account.id, "--cap-usd", str(args.cap_usd)]}

    def publish(inputs, obs, decisions, prefix=False):
        write_report(output, plan.report.copy(), inputs, obs, decisions, plan.validation,
                     plan.protocol, plan.split, plan.catalog, plan.cases, plan.control_policy, prefix)

    def reserve(item):
        account.reserve(run_id, item["id"], plan.settings.reservation)

    def settle(item):
        account.complete_case(run_id, item["id"])

    finished = False
    try:
        with Journal(output, run_id, plan.inputs, plan.injections, publish,
                     profile_metadata=dict(VERSIONS, contract_version=PROFILE.report_version)) as journal:
            observations, decisions = run_batch(
                plan.inputs, config, plan.report, plan.catalog, plan.validation, journal, plan.control_policy,
                before_exchange=reserve, after_candidate=settle)
            publish(plan.inputs, observations, decisions)
            journal.event("finished", decisions=len(decisions))
            finished = True
    finally:
        account.close_run(run_id, finished=finished)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run", help="planeja ou executa a qualificação")
    execute.add_argument("--mode", choices=("real", "fixture"), required=True)
    execute.add_argument("--config", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--manifest", type=Path)
    execute.add_argument("--confirm-execution", action="store_true")
    execute.add_argument("--dry-run", action="store_true")
    account_from_args(execute)
    init = commands.add_parser("init-account", help="cria uma conta local com gasto anterior explícito")
    init.add_argument("--mode", choices=("real", "fixture"), required=True)
    init.add_argument("--account", type=Path, required=True)
    init.add_argument("--cap-usd", type=cap_usd, required=True)
    init.add_argument("--previous-spend-usd", required=True)
    for name in ("status", "reconcile"):
        command = commands.add_parser(name)
        command.add_argument("--mode", choices=("real", "fixture"), required=True)
        command.add_argument("--account", type=Path, required=True)
        command.add_argument("--account-id", required=True)
        if name == "reconcile":
            command.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            run_evaluation(args)
            print(args.output)
        elif args.command == "init-account":
            account = Account.initialize(args.account, scope=args.mode, cap=args.cap_usd,
                                         previous_spend=args.previous_spend_usd)
            print(encode(account.status(), indent=2))
        else:
            account = Account(args.account, args.account_id, args.mode)
            if args.command == "reconcile":
                account.reconcile(decode(args.receipt.read_bytes()))
            print(encode(account.status(), indent=2))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"C05 interrompida ({type(exc).__name__}): {exc}\n")


if __name__ == "__main__":
    main()
