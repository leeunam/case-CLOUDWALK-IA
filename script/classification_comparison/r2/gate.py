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
FINAL_RECEIPT = "final-receipt.json"
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
        raise BudgetError("reservas divergentes das observações")
    costs = {}
    for row, obs in zip(rows, observations, strict=True):
        if (row["state"] != "settled" or row["receipt"] is None or row["observed"] is None
                or row["gateway_pending"] is not None or row["financial_expired"]
                or usd(row["reserved"]) != reservation or obs["requests"] != 1):
            raise BudgetError("etapa sem custo conhecido e conciliado por chamada")
        observed = usd(row["observed"])
        gateway = observed if row["gateway_observed"] is None else usd(row["gateway_observed"])
        correction = corrections.get(obs["id"])
        final = max(observed, gateway, usd(correction["observed"]) if correction else observed)
        if (final > reservation
                or obs["request_usage"][0]["observed_api_usd"] != numeric_cost(gateway)):
            raise BudgetError("custo comunicado diverge da evidência financeira da etapa")
        receipt = correction["receipt"] if correction else row["gateway_receipt"] or row["receipt"]
        costs[obs["id"]] = {"observed_usd": str(final), "receipt": receipt}
    return costs


def collect(output, plan, account, cap, *, original_hashes=None, development_gate=None):
    if any((output / name).exists() for name in ("interruption.json", "prefix-report.json", "prefix-report.md")):
        raise BudgetError("prefixo interrompido não comprova development concluído")
    audited = plan.round.profile.name == c01.LUNA_R5
    final = plan.stage == "final"
    if final and (not audited or development_gate is None):
        raise BudgetError("recibo final exige R5 e prova de desenvolvimento")
    names = (*EVIDENCE, "luna-evidence.jsonl") if audited else EVIDENCE
    paths = {name: output / name for name in names}
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
    expected_split = "final_test" if final else "development"
    if (report["split"] != expected_split or report["identity"] != plan.identity
            or report["sources"] != plan.report["sources"] or report["git_revision"] != plan.report["git_revision"]
            or report["planned_ids"] != ids or report["completed_ids"] != ids or (not final and report["eligibility"] != "inconclusive")
            or report["control_ids"] != plan.binding["control_ids"]
            or any(report["artifacts"].get(kind) != artifacts[f"{kind}.jsonl"] for kind in c01.KINDS)):
        raise BudgetError("relatório não corresponde ao plano completo")
    bundle = {kind: list(map(decode, BytesIO(published[f"{kind}.jsonl"]))) for kind in c01.KINDS}
    bundle["report"] = report
    c01.verify_run(bundle, plan.validation, plan.protocol, plan.split, plan.catalog, plan.cases)
    if audited:
        evidence = report["luna_evidence"]
        if any(evidence[k] != v for k, v in artifacts["luna-evidence.jsonl"].items()):
            raise BudgetError("inventário do relatório diverge dos envelopes originais")
    candidates = [obs for obs in bundle["observations"] if obs["origin"] == "candidate"]
    if [obs["id"] for obs in candidates] != list(plan.candidates):
        raise BudgetError("observações da candidata incompletas")
    binding = plan.bound_account(account, cap, development_gate)
    persisted_plan = decode(published["plan.json"])
    if (persisted_plan["run_id"] != run_id or canonical_digest(persisted_plan["binding"]) != canonical_digest(binding)
            or persisted_plan["input"] != artifacts["inputs.jsonl"]
            or artifacts["inputs.jsonl"]["sha256"] != binding["inputs_sha256"]):
        raise BudgetError("binding ou projeção da etapa adulterado")

    expected_events = [dict(event="planned", plan=artifacts["plan.json"], **plan.round.versions,
                            contract_version=plan.round.profile.report_version)]
    indexed = {obs["id"]: obs for obs in candidates}
    for decision in bundle["decisions"]:
        case_id = decision["id"]
        timing = {}
        if case_id in indexed:
            expected_events.extend(dict(event=event, id=case_id, attempt=1) for event in ("dispatch_started", "dispatched"))
            if audited and plan.mode == "real":
                timing["elapsed_ms"] = indexed[case_id]["elapsed_ms"]
        expected_events.append(dict(event="completed", id=case_id, attempts=decision["attempts"], **timing))
    expected_events.append(dict(event="finished", decisions=len(bundle["decisions"])))
    if canonical_digest(list(map(decode, BytesIO(published["journal.jsonl"])))) != canonical_digest(
            [dict(event, run_id=run_id) for event in expected_events]):
        raise BudgetError("diário de execução incompleto ou divergente")

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
        raise BudgetError("etapa não está concluída no ledger da mesma conta e vinculação")
    costs = settled_costs(snapshot, candidates, run_id, plan.settings.reservation)
    result = dict(status=report["eligibility"]) if final else assess(plan, bundle, costs)
    if audited:
        result.update(luna_evidence=report["luna_evidence"], stage=plan.stage)
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


def verify_final(output, plan, account, cap, development_gate):
    """Reproduz o recibo fechado com a conta e o selo independentes fornecidos pelo operador."""
    if plan.stage != "final" or plan.round.profile.name != c01.LUNA_R5:
        raise BudgetError("verificação de recibo final exige perfil R5 e etapa final")
    output = output.resolve()
    if not output.is_relative_to(c01.ROOT):
        raise BudgetError("recibo final exige saída dentro do checkout")
    verify(development_gate, plan, account, cap)
    path = output / FINAL_RECEIPT
    published = c01.read(path)
    seal.verify(plan, account, published, c01.digest(path))
    expected = collect(output, plan, account, cap, development_gate=development_gate)
    if canonical_digest(expected) != canonical_digest(published):
        raise BudgetError("recibo final divergente da execução")
