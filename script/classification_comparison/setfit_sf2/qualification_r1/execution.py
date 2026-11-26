"""Exposição única e auditoria dos artefatos confirmados por dois digests externos."""
import base64
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from ..contracts.artifacts import validate_manifest
from ..contracts.core import CATALOG, PROTOCOL, decode
from ..contracts.ipc import project
from ..evaluation.metrics import metrics, percentiles, quality_gates
from .runner import FILES, _supervise, schedule
from .storage import canonical, digest, encoded, publish, read, require


def records_from_custody(inventory, seal):
    paths = decode(read(inventory))
    require(set(paths) == {"final", "annotations", "review_receipt", "token_lengths"}, "inventário privado divergente")
    with TemporaryDirectory(prefix="sf2-custody-") as tmp:
        files, blobs = {}, {}
        for role, location in paths.items():
            spec = seal["files"].get(role)
            expected = spec["sha256"] if spec else seal[role + "_sha256"]
            src = canonical(Path(location))
            name = spec["path"] if spec else role + ".json"
            require(not spec or src.name == name, "arquivo de outra partição")
            files[role] = Path(tmp) / name
            blobs[role] = read(src, expected)
            files[role].write_bytes(blobs[role])
        validate_manifest("finalSeal", seal, files)
    return [decode(line) for line in blobs["final"].splitlines()]


def execute(checked, release, expected, custody, dest, guard, *, load_records, supervise, derive, verify):
    frozen, context, final_seal, cmd = checked
    receipt = guard.reserve(release, expected, frozen["final_seal_sha256"], dest, custody)
    dest.mkdir()
    seal_sha = failure = None
    try:
        records = load_records(custody, final_seal)
        supervise(records, cmd["argv"], context, dest / "run", 60, derive=derive, verify=verify,
                  catalog=CATALOG, timeout_ms=5000, cwd=cmd["cwd"], environment=cmd["environment"])
        seal_sha = digest(read(dest / "run/seal.json"))
    except (Exception, KeyboardInterrupt) as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)}
    raw = encoded(dict(exposure=receipt, release_sha256=expected, seal_sha256=seal_sha, interruption=failure))
    publish(dest / "execution.json", raw)
    return digest(raw)


def audit_run(root, seal_digest, records, context, verify):
    seal = decode(read(root / "seal.json", seal_digest))
    planned = schedule(records)
    base = {name for pair in FILES.values() for name in pair} | {"stderr.log", "timings.jsonl"}
    files = seal["files"]
    timing_bytes = read(root / "timings.jsonl", files["timings.jsonl"])
    timings = [decode(t) for t in timing_bytes.splitlines()]
    expected_units = [f"observations/{i:04d}.json" for i in range(len(timings))]
    require(len(timings) <= len(planned) and set(files) == base | set(expected_units), "inventário de observações divergente")
    read(root / "stderr.log", files["stderr.log"])
    groups = {k: [iter(read(root / name, files[name]).splitlines(keepends=True)) for name in names]
              for k, names in FILES.items()}
    audited, durations, interrupted, calls = [], [], [], 0
    for i, t in enumerate(timings):
        kind, row = planned[i]
        ms = t["elapsed_ms"]
        require(set(t) == {"kind", "id", "elapsed_ms", "valid"} and (t["kind"], t["id"]) == (kind, row["id"])
                and type(t["valid"]) is bool and type(ms) in (float, int) and isfinite(ms) and ms >= 0,
                "tempo, ordem ou vínculo do journal inválido")
        unit = decode(read(root / expected_units[i], files[expected_units[i]]))
        require(encoded(unit["timing"]) == encoded(t), "journal diverge da unidade atômica")
        if kind == "case":
            durations.append(ms)
        if not t["valid"]:
            require(i == len(timings)-1 and seal["failure"] and seal["failure"]["attempt"] == t
                    and set(unit) == {"timing", "rejected_base64"}, "tentativa interrompida inválida")
            base64.b64decode(unit["rejected_base64"], validate=True)
            interrupted.append(row["id"])
            continue
        require(ms <= 5000, "aceite após o prazo")
        raw, decision_line = (next(iterator, None) for iterator in groups[kind])
        require(raw and decision_line and raw == base64.b64decode(unit["frame_base64"], validate=True)
                and decision_line == encoded(unit["decision"]), "bruto ou decisão sem vínculo com a unidade")
        decision = decode(decision_line)
        require(decision["id"] == row["id"] and decision["raw_sha256"] == digest(raw), "ID/hash divergente")
        verify(project(row, CATALOG), raw, decision, context)
        if kind == "case":
            audited.append(decision)
        elif row["id"] in ("sf2-control-complete", "sf2-control-invalid"):
            calls += sum(decision["calls"].values())
    require(all(next(it, None) is None for group in groups.values() for it in group), "decisão sem tentativa")
    unstarted = [row["id"] for _, row in planned[len(timings):]]
    require(unstarted == seal["unstarted_ids"] and interrupted == seal["interrupted_ids"] and
            (not (unstarted or interrupted) or seal["failure"]), "IDs sem observação incompatíveis")
    latency = percentiles(durations)
    require(latency == seal["case_latency_ms"], "latência divergente")
    result = dict(status="inconclusive", unstarted_ids=unstarted, interrupted_ids=interrupted, verified_cases=len(audited),
                  verified_controls=sum(t["kind"] == "control" and t["valid"] for t in timings),
                  latency_ms=latency, resources=seal["resources"], startup_ms=seal["startup_ms"], failure=seal["failure"],
                  historical_capture_costs=seal["historical_capture_costs"])
    if seal["failure"] or len(records) != PROTOCOL["data"]["final"]["total"]:
        return result
    observed = []
    for role in ("worker", "supervisor"):
        info = seal["resources"][role]
        if (info.get("scope") != "process" or type(info.get("pid")) is not int or info["pid"] <= 0 or
            type(info.get("peak_ram_bytes")) is not int or info["peak_ram_bytes"] <= 0 or
            type(info.get("peak_cpu_percent")) not in (float, int) or not isfinite(info["peak_cpu_percent"]) or
            info["peak_cpu_percent"] < 0):
            return result
        observed.append(info["pid"])
    if len(set(observed)) != 2 or type(seal["startup_ms"]) not in (float, int) or not 0 <= seal["startup_ms"] <= 60000:
        return result
    m = metrics(records, audited, calls)
    gates = quality_gates(m, "final")
    gates["p95"] = latency["p95"] <= PROTOCOL["gates"]["final_observed_total_latency_p95_ms_max"]
    return dict(result, metrics=m, gates=gates, status="eligible" if all(gates.values()) else "failed")


def audit(checked, release, expected, custody, dest, execution_sha, guard, *, load_records, verify):
    frozen, context, final_seal, _ = checked
    receipt = guard.verify(release, expected, frozen["final_seal_sha256"], dest, custody)
    execution = decode(read(dest / "execution.json", execution_sha))
    require(execution["release_sha256"] == expected and execution["exposure"] == receipt, "execução de outra reserva")
    if execution["seal_sha256"] is None:
        require(execution["interruption"], "recibo sem selo ou interrupção")
        return {"status": "inconclusive", "failure": execution["interruption"]}
    require(execution["interruption"] is None, "recibo de execução contraditório")
    read(dest / "run/seal.json", execution["seal_sha256"])
    return audit_run(dest / "run", execution["seal_sha256"], load_records(custody, final_seal), context, verify)

