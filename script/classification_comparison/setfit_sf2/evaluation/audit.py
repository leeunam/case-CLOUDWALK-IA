"""Relê exclusivamente resultados selados; nenhuma operação deste módulo invoca o worker."""
from math import isfinite

from ..contracts.core import CATALOG, PROTOCOL, VERSION, read, read_lines, require, sha256, verify_files
from ..contracts.ipc import project, validate_decision, validate_scores
from .metrics import metrics, percentiles, quality_gates
from .runner import controls
from .selection import scored_rows, select


def originals(directory, records, policy, model, identities, *, catalog=CATALOG):
    seal = read(directory/"seal.json")
    names = ("predictions.jsonl", "controls.jsonl", "timings.jsonl", "stderr.log")
    verify_files(seal["files"], {name: directory/name for name in names})
    timings = read_lines(directory/"timings.jsonl")
    planned = [("case", row) for row in records] + [("control", row) for row in controls()]
    require(len(timings) <= len(planned), "tentativas adicionais")
    valid = {"case": iter(read_lines(directory/"predictions.jsonl")),
             "control": iter(read_lines(directory/"controls.jsonl"))}
    audited, durations, control_calls = [], [], 0
    for i, timing in enumerate(timings):
        kind, row = planned[i]
        require(timing["kind"] == kind and timing["id"] == row["id"], "tentativa fora de ordem")
        ms = timing["elapsed_ms"]
        require(type(ms) in (float, int) and isfinite(ms) and ms >= 0 and type(timing["valid"]) is bool,
                "duração/estado de tentativa inválido")
        if kind == "case":
            durations.append(ms)
        if not timing["valid"]:
            failure = seal["failure"]
            require(i == len(timings)-1 and failure and failure["attempt"]["id"] == row["id"],
                    "interrupção sem vínculo com a tentativa")
            continue
        require(ms <= PROTOCOL["execution"]["timeout_ms_per_case"], "decisão aceita após o prazo")
        decision = next(valid[kind], None)
        require(decision is not None, "previsão original ausente")
        validate_decision(project(row, catalog), decision, policy, model["class_order"], identities)
        if kind == "case":
            audited.append(decision)
        elif row["id"] in ("sf2-control-complete", "sf2-control-invalid"):
            control_calls += sum(decision["calls"].values())
    require(all(next(it, None) is None for it in valid.values()), "decisão sem tentativa observada")
    require(seal["failure"] is not None or len(timings) == len(planned), "controle ou narrativa sem observação")
    return seal, audited, durations, control_calls


def derive(records, dataset_hash, directory, policy, model, identities, costs, *, catalog=CATALOG):
    seal, decisions, durations, control_calls = originals(directory, records, policy, model, identities, catalog=catalog)
    part = records[0]["partition"]
    q = PROTOCOL["data"][part]
    require(len(records) == q["total"] and all(r["partition"] == part for r in records), "partição incompleta")
    observed = len(durations)
    scores = dict(contract_version=VERSION, partition=part, dataset_sha256=dataset_hash,
                  package_sha256=identities["package_sha256"], model_sha256=model["model_sha256"],
                  class_order=model["class_order"], rows=scored_rows(records[:len(decisions)], decisions))
    resources = dict(startup_ms=seal["startup_ms"], peak_ram_bytes=seal["peak_ram_bytes"],
                     peak_cpu_percent=seal["peak_cpu_percent"], **costs)
    require(set(costs) == {"download_ms", "training_ms", "classifier_api_calls"}
            and type(costs["classifier_api_calls"]) is int and costs["classifier_api_calls"] == 0,
            "recibo de consumo incompleto ou incompatível com execução local")
    latency = percentiles(durations)
    # O hash dos scores será o dos bytes JSON materializados pelo chamador.
    report = dict(contract_version=VERSION, partition=part, policy_sha256=identities["policy_sha256"],
                  predictions_sha256=sha256(directory/"predictions.jsonl"), unexecuted_ids=[r["id"] for r in records[observed:]],
                  counts=dict(planned=q["total"], observed=observed), metrics=None, status="inconclusive",
                  resources=resources, latency_ms=latency, reason="Execução interrompida. Consultar seal.json e timings.jsonl.")
    grid = None
    if len(decisions) == len(records):
        validate_scores(scores, records, dataset_sha256=dataset_hash, package_sha256=identities["package_sha256"],
                        model_sha256=model["model_sha256"], class_order=model["class_order"])
    if seal["failure"] is None:
        totals = metrics(records, decisions, control_calls)
        if part == "validation":
            grid = select(records, scores, control_calls, catalog=catalog)
            if grid["selected"]:
                totals = next(p["metrics"] for p in grid["policies"] if p["policy"] == grid["selected"])
        gates = quality_gates(totals, part)
        if part == "final":
            gates["p95"] = latency["p95"] <= PROTOCOL["gates"]["final_observed_total_latency_p95_ms_max"]
        report["metrics"] = totals
        if any(v is None for v in resources.values()):
            report["reason"] = "Medição de recursos ausente."
        else:
            eligible = all(gates.values()) and (part == "final" or grid["selected"] is not None)
            report.update(status="eligible" if eligible else "failed",
                          reason="Gates atendidos." if eligible else "Gates de qualificação reprovados.")
        if part == "validation":
            report["reason"] += " Latência externa da política de coleta. Métricas da política selecionada quando elegível."
    return scores, grid, report
