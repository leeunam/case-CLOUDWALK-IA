"""Runner C02. O stdout do adaptador contém uma observação por entrada apta."""
import argparse
import select
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import tempfile
import time
import uuid

sys.dont_write_bytecode = True
from common import HERE, c01, decide, decode, encode, preflight, project
from metrics import eligibility, summarize


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def inventory(path):
    return dict(path=str(path.relative_to(c01.ROOT)), sha256=c01.digest(path))


def exchange(proc, item):
    proc.stdin.write((encode(item) + "\n").encode("utf-8"))
    proc.stdin.flush()
    # LF is the only record separator. Bound the entire read, even for partial writes.
    deadline = time.monotonic() + 5.25
    line = bytearray()
    while not line.endswith(b"\n"):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([proc.stdout], [], [], remaining)[0]:
            raise TimeoutError(f"sem observação para {item['id']}")
        chunk = os.read(proc.stdout.fileno(), 65536)
        if not chunk:
            raise ValueError(f"observação incompleta para {item['id']}")
        line.extend(chunk)
    obs = decode(line.decode("utf-8"))
    if not isinstance(obs, dict) or obs.get("id") != item["id"]:
        raise ValueError(f"ID de resposta divergente para {item['id']}")
    if time.monotonic() > deadline - .25 and not any(
            isinstance(choice, dict) and choice.get("reason") == "timeout" for choice in obs.get("choices", {}).values()):
        raise TimeoutError(f"resposta fora do prazo para {item['id']}")
    return obs


def run_batch(inputs, config, report, catalog, validation, output):
    obs_rows, decisions = [], []
    with tempfile.TemporaryDirectory() as scratch:
        ready = Path(scratch) / "ready.json"
        env = dict(os.environ, CLASSIFICATION_IDENTITY=encode(config["identity"]),
                   CLASSIFICATION_TIMEOUT_MS="5000", CLASSIFICATION_RUN_ID=report["run_id"], CLASSIFICATION_READY_FILE=str(ready),
                   CLASSIFICATION_RUBRIC=str(c01.source_path(report["sources"]["rubric"])),
                   CLASSIFICATION_PROMPT=str(c01.source_path(report["sources"]["prompt"])),
                   CLASSIFICATION_POLICY=str(c01.source_path(report["sources"]["policy"])))
        started = time.monotonic()
        proc = subprocess.Popen(config["command"], cwd=c01.ROOT, env=env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            while not ready.is_file():
                if proc.poll() is not None or time.monotonic() - started > 120:
                    raise ValueError("adaptador indisponível na inicialização")
                time.sleep(.01)
            info = c01.read(ready)
            report["environment"].update({k: info[k] for k in ("peak_memory_bytes", "infrastructure_usd", "seed") if k in info})
            report["environment"].update(runtime=info["runtime"], hardware=info["hardware"],
                                         cold_start_ms=(time.monotonic() - started) * 1000)
            c01.structure(validation, "report", report)
            with (output / "observations.jsonl").open("x", encoding="utf-8") as observations, (
                    output / "decisions.jsonl").open("x", encoding="utf-8") as verdicts:
                for item in inputs:
                    start = time.monotonic()
                    c01.structure(validation, "input", item)
                    missing, invalid, _ = c01.normalize_input(item, catalog)
                    obs = None
                    if missing and not invalid and item["catalog"] == catalog:
                        obs = exchange(proc, item)
                        c01.structure(validation, "observation", obs)
                        c01.verify_observation(obs, missing, report, catalog)
                    d = decide(item, obs, catalog, report["run_id"])
                    c01.structure(validation, "decision", d)
                    c01.verify_case(item, obs, d, report, catalog)
                    if obs is not None:
                        if config["identity"]["mode"] == "real":
                            obs["elapsed_ms"] = (time.monotonic() - start) * 1000
                        observations.write(encode(obs) + "\n")
                        obs_rows.append(obs)
                    verdicts.write(encode(d) + "\n")
                    decisions.append(d)
            proc.stdin.close()
            if not select.select([proc.stdout], [], [], 5)[0] or proc.stdout.read(1):
                raise ValueError("saída adicional depois da última observação")
            if proc.wait(timeout=5):
                raise ValueError("adaptador encerrou com erro")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            proc.stdin.close()
            proc.stdout.close()
    return obs_rows, decisions


def describe(report):
    def format_metric(m):
        if m["value"] is None:
            return f"sem medição (n={m['denominator']})"
        if m["numerator"] is None:
            return f"{m['value']:.3f} ms (n={m['denominator']})"
        return f"{m['numerator']}/{m['denominator']}" + (" (parcial)" if m["state"] == "partial" else "")

    lines = [f"# Avaliação {report['run_id']}", "",
             f"Modo {report['identity']['mode']}. Elegibilidade {report['eligibility']}.",
             f"{len(report['completed_ids'])} relatos e {len(report['control_ids'])} controles.",
             "", "| Campo | Acerto bruto | Acerto aplicado | Cobertura automática |",
             "| --- | --- | --- | --- |"]
    for field, summary in report["by_field"].items():
        values = [format_metric(summary[k]) for k in ("raw_accuracy", "applied_accuracy", "automatic_coverage")]
        lines.append("| " + " | ".join([field, *values]) + " |")
    for dimension in ("by_mask", "by_stratum", "by_field"):
        lines += ["", f"## {dimension}", "", "| Fatia | Métrica | Contagem |", "| --- | --- | --- |"]
        for group, metrics in report[dimension].items():
            lines.extend(f"| {group} | {name} | {format_metric(m)} |" for name, m in metrics.items())
    lines += ["", "## Urgentes com prioridade omitida", ""]
    lines.extend(f"- {k} · {format_metric(v)}" for k, v in report["urgent_outcomes"].items())
    lines += ["", "## Indicadores", "", f"- p50 · {format_metric(report['latency_p50_ms'])}"]
    lines.extend(f"- {k} · {format_metric(v)}" for k, v in report["gates"].items())
    lines += ["", "## Uso por tentativa e requisição", ""]
    for k, v in report["usage"].items():
        value = "sem medição" if v["value"] is None else str(v["value"])
        lines.append(f"- {k} · {value} ({v['samples']}/{v['expected_samples']} amostras)")
    return "\n".join(lines) + "\n"


def run(args):
    validation, protocol, split, catalog, cases, example = preflight()
    config = c01.read(args.config)
    report = example["report"].copy()
    sources = dict(report["sources"], policy=config["policy"], prompt=config["prompt"])
    ids = [i for group in split[args.split].values() for i in group] if args.split != "control" else []
    if args.limit is not None and not 1 <= args.limit <= len(ids):
        raise ValueError("limite fora da população da partição")
    completed = ids[:args.limit]
    controls = example["inputs"]
    inputs = [project(cases[i], catalog) for i in completed] + controls
    for item in inputs:
        c01.structure(validation, "input", item)
        c01.normalize_input(item, catalog)
    if config["identity"]["mode"] != args.mode:
        raise ValueError("modo explícito diverge da identidade congelada")
    if not isinstance(config["command"], list) or not config["command"] or not all(
            isinstance(arg, str) and arg for arg in config["command"]):
        raise ValueError("command requer lista de argumentos")
    report.update(identity=config["identity"], sources=sources, split=args.split, completed_ids=completed,
                  planned_ids=ids, run_id="c02-" + uuid.uuid4().hex, eligibility="inconclusive",
                  git_revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=c01.ROOT, text=True).strip(),
                  environment=dict(report["environment"], runtime=platform.python_version(), hardware=platform.machine()))
    c01.structure(validation, "report", report)
    c01.verify_sources(report, protocol, split)
    output = args.output.resolve()
    if not output.is_relative_to(c01.ROOT):
        raise ValueError("artefatos exigem caminho relativo ao checkout")
    output.mkdir(exist_ok=False, parents=True)
    command = ["rtk", "proxy", "python3", "-B", str((HERE / "run.py").relative_to(c01.ROOT)),
               "--mode", args.mode, "--split", args.split, "--config",
               os.path.relpath(args.config.resolve(), c01.ROOT), "--output", "NOVO_DIRETORIO"]
    if args.limit:
        command += ["--limit", str(args.limit)]
    if args.dry_run:
        command.append("--dry-run")
    write_json(output / "invocation.json", dict(command=shlex.join(command),
               config_sha256=c01.digest(args.config), attempts=args.attempts, concurrency=args.concurrency))
    inputs_path = output / "inputs.jsonl"
    inputs_path.write_text("".join(encode(item) + "\n" for item in inputs), encoding="utf-8")
    if args.dry_run:
        write_json(output / "plan.json", dict(run_id=report["run_id"], identity=report["identity"],
                   sources=sources, planned_ids=ids, selected_ids=completed, control_ids=report["control_ids"],
                   input=inventory(inputs_path), concurrency=args.concurrency, attempts=args.attempts))
        return
    obs, decisions = run_batch(inputs, config, report, catalog, validation, output)
    report.update(summarize(cases, inputs, obs, decisions, catalog, completed, fixture=args.mode == "fixture"))
    if args.split == "final_test" and len(completed) < len(ids):
        # For a partial final test the contract retains known full-test populations.
        counts = protocol["exact_test_denominators"]
        populations = {"automatic_completion_on_expected_review_cases": counts["expected_review_cases"],
                       "automatic_non_urgent_applied_when_expected_urgent": counts["urgent_priority_omitted_cases"],
                       "automatic_coverage_on_fully_classifiable_cases_min": counts["fully_classifiable_cases"],
                       "raw_urgent_recognition_min": counts["urgent_priority_omitted_cases"],
                       "warm_total_latency_p95_ms_max": len(ids)}
        for name, population in populations.items():
            partial(report["gates"][name], population)
        for value in report["urgent_outcomes"].values():
            partial(value, counts["urgent_priority_omitted_cases"])
        partial(report["latency_p50_ms"], len(ids))
    report["eligibility"] = eligibility(report, protocol, obs, decisions)
    report["artifacts"] = {kind: inventory(output / (kind + ".jsonl")) for kind in c01.KINDS}
    bundle = dict(inputs=inputs, observations=obs, decisions=decisions, report=report)
    c01.verify_run(bundle, validation, protocol, split, catalog, cases)
    (output / "report.md").write_text(describe(report), encoding="utf-8")
    write_json(output / "report.json", report)


def partial(m, population):
    if m["value"] is None:
        m["denominator"] = population
    elif m["denominator"] < population:
        m["state"] = "partial"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="diretório novo dentro do checkout")
    parser.add_argument("--config", type=Path, default=HERE / "fixture.json")
    parser.add_argument("--mode", choices=("fixture", "real"), default="fixture")
    parser.add_argument("--split", choices=("development", "control", "final_test"), default="development")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--concurrency", type=int, choices=[1], default=1)
    parser.add_argument("--attempts", type=int, choices=[1], default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, ValueError, KeyError, TypeError, TimeoutError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"Lote interrompido ({type(exc).__name__}): {exc}\n")
    print(args.output)


if __name__ == "__main__":
    main()
