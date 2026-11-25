"""Vínculo local entre envelopes IPC originais, posições no plano e tempo do avaliador."""
import json
from types import SimpleNamespace

from adapters.luna.r5.adapter import PROFILE_VERSION, replay_envelope
from common import c01, decide, decode
from journal import interrupted_usage, observation_digest
from metrics import usage

FILENAME = "luna-evidence.jsonl"


def same_json(left, right):
    # A igualdade Python confunde booleanos com números ao comparar registros.
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


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


def verify_interruption(path, bundle, interruption):
    from r2.gate import completed_events

    report = bundle["report"]
    inventory = interruption["artifacts"]
    streams = ("inputs", "observations", "decisions")
    verified = {f"verified_{kind}.jsonl": report["artifacts"][kind] for kind in streams}
    required = {"plan.json", "journal.jsonl", "observations.jsonl", "decisions.jsonl", FILENAME,
                "verified_" + FILENAME, *verified}
    if set(inventory) != required or any(inventory[name] != ref for name, ref in verified.items()):
        raise ValueError("inventário de originais e prefixos incompleto")
    for name in required:
        if c01.source_path(inventory[name]) != path.with_name(name):
            raise ValueError("artefato de interrupção fora da rodada")

    plan = c01.read(path.with_name("plan.json"))
    binding = plan["binding"]
    input_path = c01.source_path(plan["input"])
    full_inputs = list(rows(input_path))
    planned = [item["id"] for item in full_inputs]
    committed = [item["id"] for item in bundle["inputs"]]
    pending_id = interruption["interrupted_id"]
    rest = planned[len(committed):]
    if (plan["run_id"] != report["run_id"] or binding["identity"] != report["identity"]
            or binding["profile"] != c01.LUNA_R5 or binding["inputs_sha256"] != plan["input"]["sha256"]
            or input_path != path.with_name("inputs.jsonl") or planned != binding["selected_ids"] + binding["control_ids"]
            or not same_json(full_inputs[:len(committed)], bundle["inputs"]) or interruption["completed_ids"] != committed
            or (pending_id is not None and rest[:1] != [pending_id])
            or interruption["not_started_ids"] != (rest if pending_id is None else rest[1:])
            or interruption["status"] != "interrupted" or interruption["eligibility"] != "inconclusive"):
        raise ValueError("ordem da interrupção divergente do plano e do prefixo")

    journal = list(rows(path.with_name("journal.jsonl")))
    versions = {k: plan[k] for k in ("profile", "protocol_version", "report_version", "ipc_contract_version")}
    initial = dict(event="planned", plan=inventory["plan.json"], **versions, contract_version=report["contract_version"])
    candidates = [o for o in bundle["observations"] if o["origin"] == "candidate"]
    expected = [initial, *completed_events(bundle["decisions"], candidates,
                                           include_timings=report["identity"]["mode"] == "real")]
    if not journal or any(event.get("run_id") != report["run_id"] for event in journal):
        raise ValueError("diário ausente ou de outra execução")
    events = [{k: v for k, v in e.items() if k != "run_id"} for e in journal]
    pending = interruption["interrupted_observation"]
    last = dict(event="interrupted", id=pending_id, delivery=interruption["delivery"],
                error=interruption["error"], reason=interruption["reason"],
                validated_observation_sha256=observation_digest(pending))
    if (not same_json(events[-1], last) or not same_json(events[:len(expected)], expected)
            or [r["id"] for r in events if r["event"] == "dispatched"] != interruption["dispatched_ids"]):
        raise ValueError("eventos do diário divergem da fase ou da observação da interrupção")

    tail = events[len(expected):-1]
    start = dict(event="dispatch_started", id=pending_id, attempt=1)
    if pending_id is None:
        valid_tails = [[]]
        if not rest:
            valid_tails.append([dict(event="finished", decisions=len(committed))])
        valid = tail in valid_tails and interruption["delivery"] is None
    else:
        by_delivery = {"not_sent": [[], [start, dict(event="not_sent", id=pending_id)]],
                       "unknown": [[start]], "stdin_flushed": [[start, dict(event="dispatched", id=pending_id, attempt=1)]]}
        valid = tail in by_delivery.get(interruption["delivery"], []) and (not tail or pending_id in binding["candidate_ids"])
    if not valid:
        raise ValueError("despacho pendente diverge da ordem ou da entrega registrada")
    for kind in ("observations", "decisions"):
        originals = list(rows(path.with_name(f"{kind}.jsonl")))
        recorded = bundle[kind]
        extra = originals[len(recorded):]
        if (not same_json(originals[:len(recorded)], recorded) or len(extra) > 1
                or extra and (extra[0]["id"] != pending_id or extra[0]["run_id"] != report["run_id"]
                              or kind == "observations" and not same_json(extra[0], pending))):
            raise ValueError("stream original diverge do prefixo ou da tentativa pendente")
        if kind == "decisions" and extra:
            item = full_inputs[len(recorded)]
            catalog = c01.read(c01.source_path(report["sources"]["catalog"]))
            if not same_json(extra[0], decide(item, pending, catalog, report["run_id"])):
                raise ValueError("decisão pendente diverge da observação e do insumo")
    samples, consumed = interrupted_usage(pending_id, interruption["delivery"], pending)
    if (interruption["interrupted_usage_samples"] != samples or interruption["interrupted_usage"] != consumed
            or interruption["verified_prefix_usage"] != usage(bundle["observations"])):
        raise ValueError("uso interrompido diverge das observações")
    return {row["id"]: row for row in full_inputs}, binding["candidate_ids"]


def verify_prefix(path, bundle, entry, envelopes):
    report = bundle["report"]
    interruption = c01.read(path.with_name("interruption.json"))
    full_inputs, candidate_ids = verify_interruption(path, bundle, interruption)
    original_path = path.with_name(FILENAME)
    originals = list(rows(original_path))
    if (interruption["run_id"] != report["run_id"]
            or interruption["verified_luna_evidence"] != entry
            or interruption["luna_evidence"] != reference(original_path, len(originals))
            or len(originals) not in (len(envelopes), len(envelopes) + 1)
            or not same_json(originals[:len(envelopes)], envelopes)):
        raise ValueError("inventário do prefixo diverge da interrupção")
    pending_id = interruption["interrupted_id"]
    observed = interruption["interrupted_observation"]
    if observed is not None and (observed["id"] != pending_id or observed["run_id"] != report["run_id"]):
        raise ValueError("observação pendente de outra tentativa")
    if len(originals) > len(envelopes):
        pending = originals[-1]
        if (pending_id not in candidate_ids or pending["observation"]["id"] != pending_id
                or interruption["delivery"] != "stdin_flushed"):
            raise ValueError("envelope pendente fora da tentativa interrompida")
        replay_envelope(full_inputs[pending_id], pending, policy_sha256=report["sources"]["policy"]["sha256"])
        if pending["observation"]["identity"] != report["identity"] or pending["observation"]["run_id"] != report["run_id"]:
            raise ValueError("identidade do envelope pendente divergente")
        if observed is not None:
            expected = pending["observation"]
            if report["identity"]["mode"] == "real":
                expected = dict(expected, elapsed_ms=observed["elapsed_ms"])
            if not same_json(expected, observed):
                raise ValueError("observação pendente diverge do envelope")
    elif observed is not None and observed["origin"] == "candidate":
        raise ValueError("observação pendente sem envelope original")


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
        verify_prefix(path, bundle, entry, envelopes)
    for envelope, obs in zip(envelopes, candidates, strict=True):
        item = inputs[obs["id"]]
        replay_envelope(item, envelope, policy_sha256=report["sources"]["policy"]["sha256"])
        original = envelope["observation"]
        if original["elapsed_ms"] is not None:
            raise ValueError("tempo externo presente na resposta original da candidata")
        expected = dict(original, elapsed_ms=measured.get(obs["id"]))
        if not same_json(expected, obs):
            raise ValueError("envelope diverge da observação do avaliador")


def verify_public_receipt(path, bundle, *, protocol, catalog, cases):
    """Verifica o recibo publicado. O comando verify-final também verifica o selo da conta informada."""
    report = bundle["report"]
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
            or (stage == "final" and receipt.get("status") != report["eligibility"])):
        raise ValueError("recibo incompatível com relatório R5")
    for name in ("plan.json", "journal.jsonl", "invocation.json", "report.json", "inputs.jsonl",
                 "observations.jsonl", "decisions.jsonl", FILENAME):
        if c01.source_path(receipt["artifacts"][name]) != output / name:
            raise ValueError("recibo R5 referencia outro lote")
    if stage == "development":
        from r2.gate import assess
        costs = receipt.get("costs")
        if not isinstance(costs, dict) or set(costs) != {obs["id"] for obs in bundle["observations"]}:
            raise ValueError("custos públicos não correspondem ao desenvolvimento")
        assessment = assess(SimpleNamespace(cases=cases, catalog=catalog, mode=report["identity"]["mode"],
                                            sources=c01.round_sources(protocol)), bundle, costs)
        if any(not same_json(receipt.get(k), v) for k, v in assessment.items()):
            raise ValueError("resultado público do gate diverge das observações de desenvolvimento")
