"""Evidência local de execução, independente do formato congelado das observações."""
import os
import signal
from contextlib import ExitStack

from common import c01, decode, encode
from metrics import usage


def append(stream, record):
    # A CLI POSIX entrega Ctrl+C entre registros duráveis, inclusive durante fsync.
    mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    try:
        stream.write(encode(record) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)


def records(path):
    with path.open(encoding="utf-8", newline="\n") as lines:
        return list(map(decode, lines))


def inventory(path):
    return {"path": str(path.relative_to(c01.ROOT)), "sha256": c01.digest(path)}


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Journal:
    def __init__(self, output, run_id, inputs, planned_injections, publish, *, profile_metadata=None):
        self.planned_injections = planned_injections
        self.publish = publish
        self.output = output
        self.run_id = run_id
        self.inputs = inputs
        self.profile_metadata = profile_metadata or {}
        self.active = None
        self.pending_observation = None
        self.observations = []
        self.decisions = []
        self.streams = ExitStack()

    def __enter__(self):
        try:
            for name in ("observations", "decisions", "journal"):
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
        append(self.journal_file, {"event": event, "run_id": self.run_id, **details})

    def begin_dispatch(self, case_id):
        # Write-ahead: after this boundary a broken write can have reached the reader.
        self.active = case_id
        self.event("dispatch_started", id=case_id, attempt=1)

    def sent(self):
        self.event("dispatched", id=self.active, attempt=1)

    def complete(self, decision, obs):
        self.active = decision["id"]
        self.pending_observation = obs
        if obs is not None:
            append(self.observations_file, obs)
            self.observations.append(obs)
        append(self.decisions_file, decision)
        self.decisions.append(decision)
        self.event("completed", id=decision["id"], attempts=decision["attempts"])
        self.active = self.pending_observation = None

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
        self.event("interrupted", id=active, delivery=delivery, error=type(error).__name__, reason=str(error))

        observations = records(self.output / "observations.jsonl")
        prefix_obs = [o for o in observations if o["id"] in finished]
        prefix_decisions = [d for d in records(self.output / "decisions.jsonl") if d["id"] in finished]
        prefix_inputs = [i for i in self.inputs if i["id"] in finished]
        files = ["plan.json", "journal.jsonl", "observations.jsonl", "decisions.jsonl"]
        for name, rows in (("inputs", prefix_inputs), ("decisions", prefix_decisions), ("observations", prefix_obs)):
            filename = f"verified_{name}.jsonl"
            with (self.output / filename).open("x", encoding="utf-8") as stream:
                stream.writelines(encode(row) + "\n" for row in rows)
                stream.flush()
                os.fsync(stream.fileno())
            files.append(filename)

        pending = next((o for o in observations if o["id"] == active), None)
        if pending is None and self.pending_observation and self.pending_observation["id"] == active:
            pending = self.pending_observation
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
