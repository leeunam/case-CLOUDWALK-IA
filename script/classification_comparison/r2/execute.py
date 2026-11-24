"""Planeja e executa as etapas dedicadas da avaliação R2."""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from r2.plan import R2, STAGES, Plan, gate_reference
from r2 import gate, seal
from adapters.qwen.fixture import completion
from budget import Account, BudgetError, cap_usd
from common import c01, decode, encode
from final_adapter import serve_authorized
from journal import Journal
from run import run_batch, write_json, write_report
from settings import account_from_args, resolve_account


def options_for(args):
    options = ["--stage", args.stage, "--mode", args.mode, "--config", str(args.config.resolve())]
    if args.account is not None:
        options += ["--account", str(args.account.resolve()), "--account-id", args.account_id,
                    "--cap-usd", str(args.cap_usd)]
    if args.development_gate is not None:
        options += ["--development-gate", str(args.development_gate.resolve())]
    return options


def write_plan(output, plan, args, binding, manifest_id, manifest_sha=None):
    output.mkdir(exist_ok=False, parents=True)
    inputs = output / "inputs.jsonl"
    with inputs.open("xb") as stream:
        stream.write(plan.input_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    input_sha = plan.binding["inputs_sha256"]
    plan_sha = write_json(output / "plan.json", dict(plan.round.versions, run_id=plan.report["run_id"], binding=binding,
        input={"path": str(inputs.relative_to(c01.ROOT)), "sha256": input_sha},
        injected_controls=plan.injections, settings=plan.settings.data))
    command = ["rtk", "proxy", "python3", "-B", str(plan.round.entrypoint.relative_to(c01.ROOT)), "run",
               *options_for(args), "--output", "NOVO_DIRETORIO"]
    command += ["--dry-run"] if args.dry_run else ["--manifest", str(args.manifest.resolve()), "--confirm-execution"]
    invocation_sha = write_json(output / "invocation.json", dict(plan.round.versions, stage=plan.stage, git_revision=plan.report["git_revision"],
               command=shlex.join(command), config_sha256=plan.settings.sha256, manifest_id=manifest_id,
               manifest_sha256=manifest_sha, dry_run=args.dry_run, synthetic_transport=plan.mode == "fixture",
               concurrency=1, attempts=1))
    if args.dry_run and manifest_id is not None:
        write_json(output / "manifest-template.json", dict(enabled=False, manifest_id=manifest_id, binding=binding))
    return {"inputs.jsonl": input_sha, "plan.json": plan_sha, "invocation.json": invocation_sha}


def proof_reference(args):
    if args.stage == "development" and args.development_gate is not None:
        raise BudgetError("a etapa development não recebe uma prova anterior")
    return None if args.development_gate is None else gate_reference(args.development_gate)


def authorize(args, plan, account, proof, confirmed):
    authorization = plan.authorize(args.manifest, account, args.cap_usd, confirmed, proof)
    if plan.stage == "final":
        gate.verify(proof, plan, account, args.cap_usd)
    return authorization


def run_evaluation(args, *, fixture_command=None, round_spec=R2):
    if args.mode != "fixture" and fixture_command is not None:
        raise BudgetError("processo de teste só é aceito no modo fixture")
    output = args.output.resolve()
    if output == c01.ROOT or not output.is_relative_to(c01.ROOT):
        raise ValueError("artefatos exigem diretório novo dentro do checkout")
    if output.exists():
        raise FileExistsError("diretório de saída já existe")
    run_id = round_spec.prefix + uuid.uuid4().hex
    plan = Plan(args.stage, args.mode, run_id, args.config, round_spec=round_spec)
    account = resolve_account(args, args.mode)
    proof = proof_reference(args)
    if args.dry_run:
        binding = dict(plan.binding, development_gate=proof)
        manifest_id = None
        if account is not None:
            binding = plan.bound_account(account, args.cap_usd, proof)
            manifest_id = plan.manifest_id(account)
        write_plan(output, plan, args, binding, manifest_id)
        return

    manifest_id, manifest_sha, binding_sha, binding = authorize(args, plan, account, proof, args.confirm_execution)
    account.validate(args.cap_usd)
    original_hashes = {}

    def prepare():
        if args.mode == "real" and not os.environ.get("FEITA_API_KEY", "").strip():
            raise BudgetError("credencial local Feita ausente")
        original_hashes.update(write_plan(output, plan, args, binding, manifest_id, manifest_sha))

    account.claim(run_id, manifest_id, manifest_sha, binding_sha,
                  dict(binding, settings=plan.settings.data), prepare=prepare)
    finished = False
    try:
        adapter = fixture_command or [sys.executable, "-B", str(plan.round.entrypoint), "_adapter"]
        config = {"identity": plan.identity, "contract_version": plan.round.profile.ipc_version,
                  "command": [*adapter, *options_for(args), "--manifest", str(args.manifest.resolve()),
                              "--manifest-sha256", manifest_sha]}

        if plan.round.profile.name == c01.LUNA:
            config["share_case_deadline"] = True

        def publish(inputs, obs, decisions, prefix=False):
            return write_report(output, plan.report.copy(), inputs, obs, decisions, plan.validation, plan.protocol,
                                plan.split, plan.catalog, plan.cases, plan.control_policy, prefix)

        def reserve(item):
            account.reserve(run_id, item["id"], plan.settings.reservation)

        def settle(item, observation):
            timed_out = any(choice["reason"] == "timeout" for choice in observation["choices"].values())
            account.complete_case(run_id, item["id"], timed_out=timed_out)
            if plan.round.stop_on_error and any(
                    choice["status"] in {"error", "invalid"} for choice in observation["choices"].values()):
                raise BudgetError("falha técnica na candidata, lote interrompido após conciliação")

        with Journal(output, run_id, plan.inputs, plan.injections, publish,
                     track_output=plan.stage == "development",
                     profile_metadata=dict(plan.round.versions, contract_version=plan.round.profile.report_version)) as journal:
            observations, decisions = run_batch(
                plan.inputs, config, plan.report, plan.catalog, plan.validation, journal, plan.control_policy,
                before_exchange=reserve, after_candidate=settle)
            original_hashes["report.json"] = publish(plan.inputs, observations, decisions)
            journal.event("finished", decisions=len(decisions))
            original_hashes.update(journal.output_hashes())
            finished = True
    finally:
        account.close_run(run_id, finished=finished)
    if plan.stage == "development":
        result = gate.collect(output, plan, account, args.cap_usd, original_hashes=original_hashes)
        proof_path = output / gate.FILENAME
        proof_sha = write_json(proof_path, result)
        if c01.digest(proof_path) != proof_sha:
            raise BudgetError("prova publicada diverge dos bytes produzidos pelo desenvolvimento")
        seal.create(plan, account, result, proof_sha)
        return result["status"]


def development_fixture(plan):
    # Respostas sintéticas do ensaio de integração. O corpo real nunca inclui ID ou referência.
    abstention = c01.ABSTENTION
    answers = [
        {"category": "payouts"},
        {"category": abstention},
        {"priority": "urgent"},
        {"priority": abstention},
        {"category": "terminal", "priority": "basic"},
        {"category": abstention, "priority": abstention},
    ]
    by_text = {item["text"]: answer for item, answer in zip(plan.candidates.values(), answers, strict=True)}

    def gateway(body, deadline, dispatched):
        request = decode(body)
        item = decode(request["messages"][1]["content"])
        dispatched()
        return 200, completion(request["model"], encode(by_text[item["text"]]),
                               usage={"prompt_tokens": 1000, "completion_tokens": 20,
                                      "cost": "0.000547", "cost_unit": "USD"})

    return gateway


def serve(args, round_spec=R2):
    plan = Plan(args.stage, args.mode, os.environ["CLASSIFICATION_RUN_ID"], args.config, round_spec=round_spec)
    account = resolve_account(args, args.mode)
    _, manifest_sha, _, _ = authorize(args, plan, account, proof_reference(args), confirmed=True)
    transport = development_fixture(plan) if args.mode == "fixture" and plan.stage == "development" else None
    serve_authorized(args, plan, account, manifest_sha, transport, candidate_order=iter(plan.candidates))


def plan_arguments(parser):
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--mode", choices=("real", "fixture"), required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--development-gate", type=Path)
    account_from_args(parser)


def main(round_spec=R2):
    parser = argparse.ArgumentParser(description=__doc__)
    try:
        if sys.argv[1:2] == ["_adapter"]:
            plan_arguments(parser)
            parser.add_argument("--manifest-sha256", required=True)
            serve(parser.parse_args(sys.argv[2:]), round_spec)
            return

        commands = parser.add_subparsers(dest="command", required=True)
        execute = commands.add_parser("run", help="planeja ou executa uma etapa")
        plan_arguments(execute)
        execute.add_argument("--output", type=Path, required=True)
        execute.add_argument("--confirm-execution", action="store_true")
        execute.add_argument("--dry-run", action="store_true")
        for name in ("init-account", "status", "reconcile"):
            command = commands.add_parser(name)
            modes = ("fixture",) if name == "init-account" else ("real", "fixture")
            command.add_argument("--mode", choices=modes, required=True)
            command.add_argument("--account", type=Path, required=True)
            if name == "init-account":
                command.add_argument("--cap-usd", type=cap_usd, required=True)
                command.add_argument("--previous-spend-usd", required=True)
            else:
                command.add_argument("--account-id", required=True)
            if name == "reconcile":
                command.add_argument("--receipt", type=Path, required=True)
        args = parser.parse_args()
        if args.command == "run":
            status = run_evaluation(args, round_spec=round_spec)
            if status == "failed":
                raise BudgetError(f"gate de development reprovado em {args.output / gate.FILENAME}")
            print(args.output)
            return
        if args.command == "init-account":
            account = Account.initialize(args.account, scope="fixture", cap=args.cap_usd,
                                         previous_spend=args.previous_spend_usd)
        else:
            account = Account(args.account, args.account_id, args.mode)
            if round_spec.check_account is not None:
                round_spec.check_account(account)
            if args.command == "reconcile":
                account.reconcile(decode(args.receipt.read_bytes()))
        print(encode(account.status(), indent=2))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"{round_spec.prefix[:-1].upper()} interrompida ({type(exc).__name__}): {exc}\n")


if __name__ == "__main__":
    main()
