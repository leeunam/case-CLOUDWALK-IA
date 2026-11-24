"""Verifica a conclusão e o resultado operacional do desenvolvimento R2."""
from io import BytesIO
from pathlib import Path

from r2.plan import Plan, canonical_digest
from r2 import seal
from adapters.qwen.adapter import numeric_cost
from budget import BudgetError, total_usd, usd
from common import c01, decode
from settings import digest

FILENAME = "development-gate.json"
EVIDENCE = ("plan.json", "invocation.json", "journal.jsonl", "report.json",
            "inputs.jsonl", "observations.jsonl", "decisions.jsonl")


def assess(plan, bundle, costs):
    counts = dict(correct_targets=0, preserved_fields=0, correct_completions=0,
                  integral_reviews=0, raw_urgent=0, errors=0, settled_requests=len(costs))
    elapsed = []
    for item, obs, decision in zip(bundle["inputs"], bundle["observations"], bundle["decisions"], strict=True):
        expected = plan.cases[item["id"]]["expected"]
        _, _, provided = c01.normalize_input(item, plan.catalog)
        applied = {field: decision["fields"][field]["applied"] for field in c01.FIELDS}
        counts["preserved_fields"] += sum(applied[field] == value for field, value in provided.items())
        for field, target in expected.items():
            choice = obs["choices"][field]
            required_status = "abstained" if target == c01.ABSTENTION else "predicted"
            counts["correct_targets"] += choice["status"] == required_status and choice["raw"] == target
            counts["errors"] += choice["status"] in {"invalid", "error"}
            counts["raw_urgent"] += field == "priority" and target == "urgent" and (
                choice["status"] == "predicted" and choice["raw"] == "urgent")
        if c01.ABSTENTION in expected.values():
            counts["integral_reviews"] += decision["outcome"] == "review" and all(applied[f] is None for f in expected)
        else:
            counts["correct_completions"] += decision["outcome"] == "complete" and all(
                applied[f] == target for f, target in expected.items())
        if obs["elapsed_ms"] is not None:
            elapsed.append(obs["elapsed_ms"])
    thresholds = plan.sources["development_gate"]
    passed = all(value == thresholds[name] for name, value in counts.items())
    report_p95 = bundle["report"]["gates"][c01.OBSERVED_GATE]
    # Com seis observações, o nearest-rank p95 é o máximo.
    if plan.mode == "real":
        passed &= len(elapsed) == 6 and max(elapsed) <= thresholds["p95_ms_max"]
    else:
        passed &= not elapsed and report_p95 == dict(state="unmeasured", numerator=None, denominator=6, value=None)
    status = ("pass" if plan.mode == "real" else "fixture_ready") if passed else "failed"
    return dict(counts, latency_samples=len(elapsed), p95_ms=report_p95, status=status)


def settled_costs(snapshot, observations, run_id, reservation):
    rows = [row for row in snapshot["reservations"] if row["run_id"] == run_id]
    corrections = {row["case_id"]: row for row in snapshot["receipt_corrections"] if row["run_id"] == run_id}
    if [row["case_id"] for row in rows] != [obs["id"] for obs in observations]:
        raise BudgetError("reservas de development divergentes das observações")
    costs = {}
    for row, obs in zip(rows, observations, strict=True):
        if (row["state"] != "settled" or row["receipt"] is None or row["observed"] is None
                or row["gateway_pending"] is not None or row["financial_expired"]
                or usd(row["reserved"]) != reservation or obs["requests"] != 1):
            raise BudgetError("development sem custo conhecido e conciliado por chamada")
        observed = usd(row["observed"])
        gateway = observed if row["gateway_observed"] is None else usd(row["gateway_observed"])
        correction = corrections.get(obs["id"])
        final = max(observed, gateway, usd(correction["observed"]) if correction else observed)
        if (final > reservation
                or obs["request_usage"][0]["observed_api_usd"] != numeric_cost(gateway)):
            raise BudgetError("custo comunicado diverge da evidência financeira de development")
        receipt = correction["receipt"] if correction else row["gateway_receipt"] or row["receipt"]
        costs[obs["id"]] = {"observed_usd": str(final), "receipt": receipt}
    return costs


def collect(output, plan, account, cap, *, original_hashes=None):
    if any((output / name).exists() for name in ("interruption.json", "prefix-report.json", "prefix-report.md")):
        raise BudgetError("prefixo interrompido não comprova development concluído")
    paths = {name: output / name for name in EVIDENCE}
    published = {name: path.read_bytes() for name, path in paths.items()}
    published_hashes = {name: digest(content) for name, content in published.items()}
    if original_hashes is not None and published_hashes != original_hashes:
        raise BudgetError("saídas publicadas divergem dos bytes produzidos pelo desenvolvimento")
    committed_hashes = published_hashes if original_hashes is None else original_hashes
    artifacts = {name: {"path": str(path.relative_to(c01.ROOT)), "sha256": committed_hashes[name]}
                 for name, path in paths.items()}
    report = decode(published["report.json"])
    run_id = report["run_id"]
    ids = plan.binding["selected_ids"]
    if (report["split"] != "development" or report["identity"] != plan.identity
            or report["sources"] != plan.report["sources"] or report["git_revision"] != plan.report["git_revision"]
            or report["planned_ids"] != ids or report["completed_ids"] != ids or report["eligibility"] != "inconclusive"
            or any(report["artifacts"].get(kind) != artifacts[f"{kind}.jsonl"] for kind in c01.KINDS)):
        raise BudgetError("relatório de development não corresponde ao plano completo")
    bundle = {kind: list(map(decode, BytesIO(published[f"{kind}.jsonl"]))) for kind in c01.KINDS}
    bundle["report"] = report
    c01.verify_run(bundle, plan.validation, plan.protocol, plan.split, plan.catalog, plan.cases)
    if [obs["id"] for obs in bundle["observations"]] != ids:
        raise BudgetError("observações de development incompletas")
    binding = plan.bound_account(account, cap)
    persisted_plan = decode(published["plan.json"])
    if (persisted_plan["run_id"] != run_id or canonical_digest(persisted_plan["binding"]) != canonical_digest(binding)
            or persisted_plan["input"] != artifacts["inputs.jsonl"]
            or artifacts["inputs.jsonl"]["sha256"] != binding["inputs_sha256"]):
        raise BudgetError("binding ou projeção de development adulterado")

    expected_events = [dict(event="planned", plan=artifacts["plan.json"], **plan.round.versions,
                            contract_version=plan.round.profile.report_version)]
    for case_id in ids:
        expected_events.extend(dict(event=event, id=case_id, attempt=1) for event in ("dispatch_started", "dispatched"))
        expected_events.append(dict(event="completed", id=case_id, attempts=1))
    expected_events.append(dict(event="finished", decisions=len(ids)))
    if canonical_digest(list(map(decode, BytesIO(published["journal.jsonl"])))) != canonical_digest(
            [dict(event, run_id=run_id) for event in expected_events]):
        raise BudgetError("diário de development incompleto ou divergente")

    snapshot = account.status()
    invocation = decode(published["invocation.json"])
    run = next((row for row in snapshot["runs"] if row["id"] == run_id), None)
    if (run is None or run["state"] != "finished" or run["manifest_id"] != plan.manifest_id(account)
            or run["manifest_sha256"] != invocation["manifest_sha256"]
            or invocation["manifest_id"] != run["manifest_id"] or invocation["dry_run"] is not False
            or invocation["stage"] != plan.stage or invocation["synthetic_transport"] is not (plan.mode == "fixture")
            or invocation["config_sha256"] != plan.settings.sha256
            or run["binding_sha256"] != canonical_digest(binding)
            or canonical_digest(run["configuration"]) != canonical_digest(dict(binding, settings=plan.settings.data))):
        raise BudgetError("development não está concluído no ledger da mesma conta e vinculação")
    costs = settled_costs(snapshot, bundle["observations"], run_id, plan.settings.reservation)
    result = assess(plan, bundle, costs)
    observed = total_usd(*(usd(cost["observed_usd"]) for cost in costs.values()))
    return dict(plan.round.versions, **result, run_id=run_id, mode=plan.mode, binding_sha256=run["binding_sha256"],
                manifest_sha256=run["manifest_sha256"], observed_usd=str(observed), costs=costs, artifacts=artifacts)


def verify(reference, final_plan, account, cap):
    path = c01.source_path(reference)
    supplied = c01.read(path)
    required = "pass" if final_plan.mode == "real" else "fixture_ready"
    if not isinstance(supplied, dict) or supplied.get("mode") != final_plan.mode or supplied.get("status") != required:
        raise BudgetError("gate de development falhou ou pertence a outro modo")
    development = Plan("development", final_plan.mode, final_plan.round.prefix + "verificacao",
                       final_plan.config, round_spec=final_plan.round)
    seal.verify(development, account, supplied, reference["sha256"])
    expected = collect(Path(path).parent, development, account, cap)
    if expected["status"] != required or canonical_digest(supplied) != canonical_digest(expected):
        raise BudgetError("gate de development falhou, foi adulterado ou pertence a outro modo")
