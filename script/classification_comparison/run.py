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
from common import HERE, c01, decide, decode, encode, injected_inventory, injected_observation, preflight, project
from metrics import eligibility, summarize
from journal import Journal, inventory, sync_directory


def write_json(path, value):
    temp = path.with_suffix(".tmp")
    with temp.open("x", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
    temp.replace(path)
    sync_directory(path.parent)


class ResponseStream:
    def __init__(self, stdout):
        self.stdout = stdout
        self.pending = bytearray()

    def record(self, deadline):
        while True:
            end = self.pending.find(b"\n")
            if end >= 0:
                line = self.pending[:end].removesuffix(b"\r")
                del self.pending[:end + 1]
                return decode(line.decode("utf-8"))
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.stdout], [], [], remaining)[0]:
                raise TimeoutError("adaptador silencioso ou registro incompleto")
            chunk = os.read(self.stdout.fileno(), 65536)
            if not chunk:
                raise ValueError("EOF antes de uma observação terminada por LF")
            self.pending.extend(chunk)

    def finish(self):
        if self.pending or not select.select([self.stdout], [], [], 5)[0] or os.read(self.stdout.fileno(), 1):
            raise ValueError("stdout adicional ou sem EOF após a última observação")


CASE_SECONDS = 5
TIMEOUT_DELIVERY_SECONDS = .25


def check_deadline(obs, deadline, now):
    if now <= deadline:
        return
    choices = obs.get("choices")
    if now <= deadline + TIMEOUT_DELIVERY_SECONDS and isinstance(choices, dict) and any(
            isinstance(c, dict) and c.get("status") == "error" and c.get("reason") == "timeout"
            for c in choices.values()):
        return
    raise TimeoutError(f"resposta fora do prazo para {obs['id']}")


def exchange(proc, item, responses, journal, deadline):
    if responses.pending or select.select([proc.stdout], [], [], 0)[0]:
        raise ValueError("stdout inesperado ou fechado antes do próximo despacho")
    payload = (encode(item) + "\n").encode("utf-8")
    journal.begin_dispatch(item["id"])
    if time.monotonic() >= deadline:
        journal.event("not_sent", id=item["id"])
        raise TimeoutError(f"prazo esgotado antes do envio de {item['id']}")
    proc.stdin.write(payload)
    proc.stdin.flush()
    journal.sent()
    obs = responses.record(deadline + TIMEOUT_DELIVERY_SECONDS)
    if not isinstance(obs, dict) or obs.get("id") != item["id"]:
        raise ValueError(f"ID de resposta divergente para {item['id']}")
    check_deadline(obs, deadline, time.monotonic())
    return obs


def run_batch(inputs, config, report, catalog, validation, journal, policy):
    with tempfile.TemporaryDirectory() as scratch:
        ready = Path(scratch) / "ready.json"
        final = Path(scratch) / "final.json"
        env = dict(os.environ, CLASSIFICATION_CONTRACT_VERSION=report["contract_version"],
                   CLASSIFICATION_IDENTITY=encode(config["identity"]),
                   CLASSIFICATION_FINAL_FILE=str(final), CLASSIFICATION_TIMEOUT_MS="5000",
                   CLASSIFICATION_RUN_ID=report["run_id"], CLASSIFICATION_READY_FILE=str(ready),
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
            environment = dict(report["environment"])
            environment.update({k: info[k] for k in ("infrastructure_usd", "seed") if k in info})
            environment.update(runtime=info["runtime"], hardware=info["hardware"],
                                         cold_start_ms=(time.monotonic() - started) * 1000)
            c01.structure(validation, "report", dict(report, environment=environment))
            report["environment"] = environment
            responses = ResponseStream(proc.stdout)
            for item in inputs:
                start = time.monotonic()
                deadline = start + CASE_SECONDS
                c01.structure(validation, "input", item)
                missing, invalid, _ = c01.normalize_input(item, catalog)
                obs = None
                if item["id"] in policy["controls"]:
                    obs = injected_observation(item, report["run_id"], policy)
                elif missing and not invalid and item["catalog"] == catalog:
                    obs = exchange(proc, item, responses, journal, deadline)
                if obs is not None:
                    c01.structure(validation, "observation", obs)
                    c01.verify_observation(obs, missing, report, catalog)
                    if obs["origin"] == "injected_control":
                        local = dict(report, control_ids=[item["id"]], injected_controls=injected_inventory(
                            [item["id"]], report["injected_controls"]["policy"], policy))
                        c01.verify_injected_controls(local, {"inputs": {item["id"]: item},
                                                            "observations": {item["id"]: obs}},
                                                     {"control_policy": report["injected_controls"]["policy"]})
                    journal.pending_observation = obs
                d = decide(item, obs, catalog, report["run_id"])
                c01.structure(validation, "decision", d)
                c01.verify_case(item, obs, d, report, catalog)
                if obs is not None and obs["origin"] == "candidate":
                    end = time.monotonic()
                    check_deadline(obs, deadline, end)
                    if config["identity"]["mode"] == "real":
                        # O diário conserva a resposta original se a medição final for incompatível.
                        obs = dict(obs, elapsed_ms=(end - start) * 1000)
                        c01.structure(validation, "observation", obs)
                        c01.verify_observation(obs, missing, report, catalog)
                journal.complete(d, obs)
            proc.stdin.close()
            responses.finish()
            if proc.wait(timeout=5):
                raise ValueError("adaptador encerrou com erro")
            if final.exists():
                resources = c01.read(final)
                if not isinstance(resources, dict) or set(resources) != {"peak_memory_bytes"}:
                    raise ValueError("metadados finais inválidos")
                peak = resources["peak_memory_bytes"]
                if peak is not None and (type(peak) is not int or peak < 0):
                    raise ValueError("peak_memory_bytes final inválido")
                report["environment"]["peak_memory_bytes"] = peak
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            proc.stdin.close()
            proc.stdout.close()
    return journal.observations, journal.decisions


def describe(report, prefix=False):
    def format_metric(m):
        if m["value"] is None:
            return f"sem medição (n={m['denominator']})"
        if m["numerator"] is None:
            return f"{m['value']:.3f} ms (n={m['denominator']})"
        return f"{m['numerator']}/{m['denominator']}" + (" (parcial)" if m["state"] == "partial" else "")

    status = "Lote interrompido. Elegibilidade inconclusiva." if prefix else f"Elegibilidade {report['eligibility']}."
    lines = [f"# Avaliação {report['run_id']}", "",
             f"Modo {report['identity']['mode']}. {status}",
             f"{len(report['completed_ids'])} relatos e {len(report['control_ids'])} controles.",
             f"Controles injetados pelo avaliador: {report['injected_controls']['count']}.",
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
    if config.get("contract_version") != protocol["contract_version"]:
        raise ValueError("configuração incompatível com o contrato")
    reference = protocol["control_policy"]
    policy = c01.read(c01.source_path(reference))
    controls = example["inputs"]
    reserved = [item["id"] for item in controls if item["id"] in policy["controls"]]
    if set(reserved) != set(policy["controls"]):
        raise ValueError("plano omite controle reservado da política")
    report["injected_controls"] = injected_inventory(reserved, reference, policy)
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
                  environment=dict(report["environment"], runtime=platform.python_version(),
                                   hardware=platform.machine(), peak_memory_bytes=None))
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
               config_sha256=c01.digest(args.config), contract_version=report["contract_version"],
               control_policy=reference, attempts=args.attempts, concurrency=args.concurrency))
    inputs_path = output / "inputs.jsonl"
    with inputs_path.open("x", encoding="utf-8") as stream:
        stream.writelines(encode(item) + "\n" for item in inputs)
        stream.flush()
        os.fsync(stream.fileno())
    write_json(output / "plan.json", dict(run_id=report["run_id"], identity=report["identity"],
                   sources=sources, planned_ids=ids, selected_ids=completed, control_ids=report["control_ids"],
                   injected_controls=report["injected_controls"], contract_version=report["contract_version"],
                   input=inventory(inputs_path), concurrency=args.concurrency, attempts=args.attempts))
    if args.dry_run:
        return
    def publish(inputs, obs, decisions, prefix=False):
        write_report(output, report.copy(), inputs, obs, decisions, validation, protocol, split, catalog,
                     cases, policy, prefix)

    with Journal(output, report["run_id"], inputs, report["injected_controls"], publish) as journal:
        obs, decisions = run_batch(inputs, config, report, catalog, validation, journal, policy)
        publish(inputs, obs, decisions)
        journal.event("finished", decisions=len(decisions))


def write_report(output, report, inputs, obs, decisions, validation, protocol, split, catalog, cases, policy, prefix):
    completed = [d["id"] for d in decisions if d["id"] in cases]
    controls = [d["id"] for d in decisions if d["id"] not in cases]
    injected = [o["id"] for o in obs if o["origin"] == "injected_control"]
    if not prefix and (completed != report["completed_ids"] or controls != report["control_ids"] or
                       injected != report["injected_controls"]["ids"]):
        raise ValueError("lote completo diverge do plano de relatos e controles")
    report.update(completed_ids=completed, control_ids=controls,
                  injected_controls=injected_inventory(injected, protocol["control_policy"], policy))
    report.update(summarize(cases, inputs, obs, decisions, catalog, completed,
                            fixture=report["identity"]["mode"] == "fixture"))
    if report["split"] == "final_test" and len(completed) < len(report["planned_ids"]):
        # For a partial final test the contract retains known full-test populations.
        counts = protocol["exact_test_denominators"]
        populations = {"automatic_completion_on_expected_review_cases": counts["expected_review_cases"],
                       "automatic_non_urgent_applied_when_expected_urgent": counts["urgent_priority_omitted_cases"],
                       "automatic_coverage_on_fully_classifiable_cases_min": counts["fully_classifiable_cases"],
                       "raw_urgent_recognition_min": counts["urgent_priority_omitted_cases"],
                       "warm_total_latency_p95_ms_max": len(report["planned_ids"])}
        for name, population in populations.items():
            partial(report["gates"][name], population)
        for value in report["urgent_outcomes"].values():
            partial(value, counts["urgent_priority_omitted_cases"])
        partial(report["latency_p50_ms"], len(report["planned_ids"]))
    report["eligibility"] = eligibility(report, protocol, obs, decisions)
    stream_prefix = "verified_" if prefix else ""
    report["artifacts"] = {k: inventory(output / f"{stream_prefix}{k}.jsonl") for k in c01.KINDS}
    bundle = dict(inputs=inputs, observations=obs, decisions=decisions, report=report)
    c01.verify_run(bundle, validation, protocol, split, catalog, cases)
    name = "prefix-report" if prefix else "report"
    (output / f"{name}.md").write_text(describe(report, prefix), encoding="utf-8")
    # No contrato 1.1, a evidência completa pode exigir um veredito mesmo após interrupção.
    if not prefix or report["eligibility"] == "inconclusive":
        write_json(output / f"{name}.json", report)


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
