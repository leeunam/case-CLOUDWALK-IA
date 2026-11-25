"""Evidência local de execução, independente do formato congelado das observações."""
import json
import os
import signal
from contextlib import ExitStack
from hashlib import sha256

from common import c01, decode, encode
from metrics import usage


def append(stream, record):
    # A CLI POSIX entrega Ctrl+C entre registros duráveis, inclusive durante fsync.
    mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    try:
        line = encode(record) + "\n"
        stream.write(line)
        stream.flush()
        os.fsync(stream.fileno())
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)
    return line


def records(path):
    with path.open(encoding="utf-8", newline="\n") as lines:
        return list(map(decode, lines))


def inventory(path):
    return {"path": str(path.relative_to(c01.ROOT)), "sha256": c01.digest(path)}


def observation_digest(obs):
    return sha256(json.dumps(obs, sort_keys=True, separators=(",", ":")).encode()).hexdigest() if obs is not None else None


def interrupted_usage(active, delivery, pending):
    pending_samples = usage([pending]) if pending is not None else None
    pending_usage = None
    if active is not None:
        pending_usage = {k: None for k in ("requests", "questions", "input_tokens", "output_tokens",
                                            "observed_api_usd", "estimated_api_usd")}
        if pending_samples:
            for key, value in pending_samples.items():
                if key in pending_usage and value["state"] == "measured":
                    pending_usage[key] = value["value"]
        elif delivery == "not_sent":
            pending_usage.update(requests=0, questions=0)
    return pending_samples, pending_usage


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Journal:
    def __init__(self, output, run_id, inputs, planned_injections, publish, *, profile_metadata=None,
                 track_output=False):
        self.planned_injections = planned_injections
        self.publish = publish
        self.output = output
        self.run_id = run_id
        self.inputs = inputs
        self.profile_metadata = profile_metadata or {}
        self.audited = self.profile_metadata.get("profile") == c01.LUNA_R5
        self.pending_envelope = None
        self.active = None
        self.pending_observation = None
        self.observations = []
        self.decisions = []
        self.streams = ExitStack()
        self.stream_names = ("observations", "decisions", "journal")
        if self.audited:
            self.stream_names += ("luna-evidence",)
        self.hashes = {name: sha256() for name in self.stream_names} if track_output or self.audited else {}

    def output_hashes(self):
        return {f"{name}.jsonl": value.hexdigest() for name, value in self.hashes.items()}

    def __enter__(self):
        try:
            for name in self.stream_names:
                stream = self.streams.enter_context((self.output / f"{name}.jsonl").open("x", encoding="utf-8"))
                setattr(self, name + "_file", stream)
            self.event("planned", plan=inventory(self.output / "plan.json"), **self.profile_metadata)
            sync_directory(self.output)
            sync_directory(self.output.parent)
            return self
        except BaseException:
            self.streams.close()
            raise

    def event(self, event, **details):
        self.record("journal", {"event": event, "run_id": self.run_id, **details})

    def record(self, name, record):
        line = append(getattr(self, name + "_file"), record)
        if self.hashes:
            self.hashes[name].update(line.encode("utf-8"))

    def begin_dispatch(self, case_id):
        # Write-ahead: after this boundary a broken write can have reached the reader.
        self.active = case_id
        self.event("dispatch_started", id=case_id, attempt=1)

    def sent(self):
        self.event("dispatched", id=self.active, attempt=1)

    def complete(self, decision, obs):
        self.active = decision["id"]
        self.pending_observation = obs
        timing = {}
        if self.audited and obs is not None and obs["origin"] == "candidate":
            if self.pending_envelope is None or self.pending_envelope["observation"]["id"] != obs["id"]:
                raise ValueError("envelope ausente para a observação")
            self.record("luna-evidence", self.pending_envelope)
            if obs["identity"]["mode"] == "real":
                timing["elapsed_ms"] = obs["elapsed_ms"]
        if obs is not None:
            self.record("observations", obs)
            self.observations.append(obs)
        self.record("decisions", decision)
        self.decisions.append(decision)
        self.event("completed", id=decision["id"], attempts=decision["attempts"], **timing)
        self.active = self.pending_observation = self.pending_envelope = None

    def interrupted(self, error):
        # A publicação final pode ter falhado depois de escrever parte do relatório.
        for name in ("report.json", "report.md", "report.tmp"):
            (self.output / name).unlink(missing_ok=True)
        # A linha completed sincronizada confirma observação e decisão anteriores.
        events = records(self.output / "journal.jsonl")
        completed = [e["id"] for e in events if e["event"] == "completed"]
        finished = set(completed)
        dispatched = [e["id"] for e in events if e["event"] == "dispatched"]
        started = [e["id"] for e in events if e["event"] == "dispatch_started"]
        active = next((i for i in reversed(started) if i not in finished), None)
        if active is None and self.active not in finished:
            active = self.active
        delivery = None
        if active is not None:
            if active in dispatched:
                delivery = "stdin_flushed"
            elif any(e["event"] == "not_sent" and e["id"] == active for e in events) or active not in started:
                delivery = "not_sent"
            else:
                delivery = "unknown"
        stopped = dict(id=active, delivery=delivery, error=type(error).__name__, reason=str(error))
        if not self.audited:
            self.event("interrupted", **stopped)
        observations = records(self.output / "observations.jsonl")
        pending = next((o for o in observations if o["id"] == active), None)
        if pending is None and self.pending_observation and self.pending_observation["id"] == active:
            pending = self.pending_observation
        if self.audited:
            self.event("interrupted", **stopped, validated_observation_sha256=observation_digest(pending))

        prefix_obs = [o for o in observations if o["id"] in finished]
        prefix_decisions = [d for d in records(self.output / "decisions.jsonl") if d["id"] in finished]
        prefix_inputs = [i for i in self.inputs if i["id"] in finished]
        files = ["plan.json", "journal.jsonl", "observations.jsonl", "decisions.jsonl"]
        streams = [("inputs", prefix_inputs), ("decisions", prefix_decisions), ("observations", prefix_obs)]
        if self.audited:
            from luna_r5.audit import FILENAME, rows as evidence_rows
            originals = list(evidence_rows(self.output / FILENAME))
            if self.pending_envelope is not None and self.pending_envelope not in originals:
                self.record("luna-evidence", self.pending_envelope)
                originals.append(self.pending_envelope)
            evidence = [e for e in originals if e["observation"]["id"] in finished]
            streams.append(("luna-evidence", evidence))
            files.append(FILENAME)
        for name, rows in streams:
            filename = f"verified_{name}.jsonl"
            with (self.output / filename).open("x", encoding="utf-8") as stream:
                stream.writelines(encode(row) + "\n" for row in rows)
                stream.flush()
                os.fsync(stream.fileno())
            files.append(filename)

        pending_samples, pending_usage = interrupted_usage(active, delivery, pending)
        injected = [o["id"] for o in prefix_obs if o["origin"] == "injected_control"]
        inventory_fields = dict(self.planned_injections) if injected else {}
        inventory_fields.update(ids=injected, count=len(injected))
        versions = {"contract_version": c01.get_profile().report_version, **self.profile_metadata}
        manifest = dict(versions, injected_controls=inventory_fields, run_id=self.run_id, status="interrupted", eligibility="inconclusive",
                        reason=str(error), error=type(error).__name__, dispatched_ids=dispatched,
                        completed_ids=completed, interrupted_id=active, delivery=delivery,
                        interrupted_observation=pending, interrupted_usage=pending_usage,
                        interrupted_usage_samples=pending_samples,
                        not_started_ids=[i["id"] for i in self.inputs if i["id"] not in finished and i["id"] != active],
                        verified_prefix_usage=usage(prefix_obs),
                        artifacts={name: inventory(self.output / name) for name in files})
        if self.audited:
            from luna_r5.audit import reference
            manifest["luna_evidence"] = reference(self.output / FILENAME, len(originals))
            manifest["verified_luna_evidence"] = reference(self.output / ("verified_" + FILENAME), len(evidence))
        temp = self.output / "interruption.tmp"
        with temp.open("x", encoding="utf-8") as stream:
            append(stream, manifest)
        temp.replace(self.output / "interruption.json")
        sync_directory(self.output)
        self.publish(prefix_inputs, prefix_obs, prefix_decisions, prefix=True)

    def __exit__(self, typ, exc, tb):
        try:
            if exc is not None:
                self.interrupted(exc)
        finally:
            self.streams.close()
