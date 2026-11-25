"""Vínculo local entre envelopes IPC originais, posições no plano e tempo do avaliador."""
import json

from adapters.luna.r5.adapter import PROFILE_VERSION, replay_envelope
from common import c01, decode

FILENAME = "luna-evidence.jsonl"


def rows(path):
    with path.open("rb") as stream:
        for line in stream:
            if not line.endswith(b"\n"):
                raise ValueError("registro de evidência incompleto (LF ausente)")
            yield decode(line.decode("utf-8"))


def reference(path, count):
    return dict(path=path.relative_to(c01.ROOT).as_posix(), sha256=c01.digest(path),
                count=count, schema_version=PROFILE_VERSION)


def completed_timings(path, report, candidates):
    measured = {}
    if report["identity"]["mode"] != "real":
        return {}
    for event in rows(path.with_name("journal.jsonl")):
        if event.get("event") == "completed" and "elapsed_ms" in event:
            if event["id"] in measured or event["run_id"] != report["run_id"]:
                raise ValueError("medição externa duplicada ou de outra rodada")
            measured[event["id"]] = event["elapsed_ms"]
    if list(measured) != [obs["id"] for obs in candidates] or any(value is None for value in measured.values()):
        raise ValueError("medições externas divergem do inventário de candidatas")
    return measured


def verify_prefix(path, report, entry, envelopes, inputs):
    interruption = c01.read(path.with_name("interruption.json"))
    original_path = path.with_name(FILENAME)
    originals = list(rows(original_path))
    if (interruption["run_id"] != report["run_id"]
            or interruption["verified_luna_evidence"] != entry
            or interruption["luna_evidence"] != reference(original_path, len(originals))
            or len(originals) not in (len(envelopes), len(envelopes) + 1)
            or json.dumps(originals[:len(envelopes)], sort_keys=True) != json.dumps(envelopes, sort_keys=True)):
        raise ValueError("inventário do prefixo diverge da interrupção")
    if len(originals) > len(envelopes):
        pending = originals[-1]
        pending_id = interruption["interrupted_id"]
        if pending["observation"]["id"] != pending_id or pending_id in inputs:
            raise ValueError("envelope pendente fora da tentativa interrompida")
        planned = c01.read(original_path.with_name("plan.json"))
        full_inputs = {row["id"]: row for row in rows(c01.source_path(planned["input"]))}
        replay_envelope(full_inputs[pending_id], pending, policy_sha256=report["sources"]["policy"]["sha256"])
        if pending["observation"]["identity"] != report["identity"] or pending["observation"]["run_id"] != report["run_id"]:
            raise ValueError("identidade do envelope pendente divergente")


def verify(bundle):
    report = bundle["report"]
    if not report["run_id"].startswith("luna-r5-"):
        raise ValueError("identificador fora do escopo Luna R5")
    entry = report["luna_evidence"]
    path = c01.source_path(entry)
    observations_path = c01.source_path(report["artifacts"]["observations"])
    prefix = observations_path.name == "verified_observations.jsonl"
    name = ("verified_" if prefix else "") + FILENAME
    if path != observations_path.with_name(name):
        raise ValueError("evidência fora da rodada ou do prefixo")
    candidates = [obs for obs in bundle["observations"] if obs["origin"] == "candidate"]
    if entry["count"] != len(candidates):
        raise ValueError("contagem de envelopes divergente")
    inputs = {i["id"]: i for i in bundle["inputs"]}
    measured = completed_timings(path, report, candidates)
    envelopes = list(rows(path))
    if prefix:
        verify_prefix(path, report, entry, envelopes, inputs)
    for envelope, obs in zip(envelopes, candidates, strict=True):
        item = inputs[obs["id"]]
        replay_envelope(item, envelope, policy_sha256=report["sources"]["policy"]["sha256"])
        original = envelope["observation"]
        if original["elapsed_ms"] is not None:
            raise ValueError("tempo externo presente na resposta original da candidata")
        expected = dict(original, elapsed_ms=measured.get(obs["id"]))
        # Comparação por tipo JSON inclusive em contagens, campos booleanos e posições.
        if json.dumps(expected, sort_keys=True) != json.dumps(obs, sort_keys=True):
            raise ValueError("envelope diverge da observação do avaliador")


def verify_public_receipt(path, report):
    """Verifica o recibo publicado. O comando verify-final também verifica o selo da conta informada."""
    output = path.parent
    prefix = path.name == "prefix-report.json"
    expected_name = ("verified_" if prefix else "") + FILENAME
    if c01.source_path(report["luna_evidence"]) != output / expected_name:
        raise ValueError("evidência fora do diretório do relatório")
    if prefix:
        if report["eligibility"] != "inconclusive" or not (output / "interruption.json").is_file():
            raise ValueError("prefixo R5 sem interrupção inconclusiva")
        return
    stage = "development" if report["split"] == "development" else "final"
    filename = "development-gate.json" if stage == "development" else "final-receipt.json"
    receipt = c01.read(output / filename)
    if (path.name != "report.json" or (output / "interruption.json").exists()
            or receipt["run_id"] != report["run_id"] or receipt["mode"] != report["identity"]["mode"]
            or receipt["profile"] != c01.LUNA_R5 or receipt["stage"] != stage
            or receipt["luna_evidence"] != report["luna_evidence"]
            or receipt["report_version"] != report["contract_version"]
            or (stage == "final" and receipt["status"] != report["eligibility"])):
        raise ValueError("recibo incompatível com relatório R5")
    for name in ("plan.json", "journal.jsonl", "invocation.json", "report.json", "inputs.jsonl",
                 "observations.jsonl", "decisions.jsonl", FILENAME):
        if c01.source_path(receipt["artifacts"][name]) != output / name:
            raise ValueError("recibo R5 referencia outro lote")
