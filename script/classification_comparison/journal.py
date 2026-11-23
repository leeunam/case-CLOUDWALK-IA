"""Evidência local de execução, independente do formato congelado das observações."""
import os
from contextlib import ExitStack

from common import c01, encode
from metrics import usage


def append(stream, record):
    stream.write(encode(record) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def inventory(path):
    return {"path": str(path.relative_to(c01.ROOT)), "sha256": c01.digest(path)}


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Journal:
    def __init__(self, output, run_id, inputs):
        self.output = output
        self.run_id = run_id
        self.inputs = inputs
        self.active = None
        self.delivery = None
        self.dispatched = []
        self.observations = []
        self.decisions = []
        self.streams = ExitStack()

    def __enter__(self):
        try:
            for name in ("observations", "decisions", "journal"):
                stream = self.streams.enter_context((self.output / f"{name}.jsonl").open("x", encoding="utf-8"))
                setattr(self, name + "_file", stream)
            self.event("planned", plan=inventory(self.output / "plan.json"))
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
        self.delivery = "unknown"
        self.event("dispatch_started", id=case_id, attempt=1)

    def sent(self):
        self.event("dispatched", id=self.active, attempt=1)
        self.delivery = "stdin_flushed"
        self.dispatched.append(self.active)

    def complete(self, decision, obs):
        if obs is not None:
            append(self.observations_file, obs)
            self.observations.append(obs)
        append(self.decisions_file, decision)
        self.decisions.append(decision)
        self.event("completed", id=decision["id"], attempts=decision["attempts"])
        self.active = self.delivery = None

    def interrupted(self, error):
        completed = [d["id"] for d in self.decisions]
        self.event("interrupted", id=self.active, delivery=self.delivery, error=type(error).__name__,
                   reason=str(error))
        finished = set(completed)
        path = self.output / "verified_inputs.jsonl"
        with path.open("x", encoding="utf-8") as prefix:
            for item in self.inputs:
                if item["id"] in finished:
                    prefix.write(encode(item) + "\n")
            prefix.flush()
            os.fsync(prefix.fileno())
        files = ("plan.json", "journal.jsonl", "verified_inputs.jsonl", "observations.jsonl", "decisions.jsonl")
        manifest = dict(run_id=self.run_id, status="interrupted", eligibility="inconclusive",
                        reason=str(error), error=type(error).__name__, dispatched_ids=self.dispatched,
                        completed_ids=completed, interrupted_id=self.active, delivery=self.delivery,
                        interrupted_usage=({k: None for k in ("requests", "questions", "input_tokens", "output_tokens",
                                                               "observed_api_usd", "estimated_api_usd")}
                                           if self.active is not None else None),
                        not_started_ids=[i["id"] for i in self.inputs if i["id"] not in finished and i["id"] != self.active],
                        verified_prefix_usage=usage(self.observations),
                        artifacts={name: inventory(self.output / name) for name in files})
        temp = self.output / "interruption.tmp"
        with temp.open("x", encoding="utf-8") as stream:
            append(stream, manifest)
        temp.replace(self.output / "interruption.json")
        sync_directory(self.output)

    def __exit__(self, typ, exc, tb):
        try:
            if exc is not None:
                self.interrupted(exc)
            else:
                self.event("finished", decisions=len(self.decisions))
        finally:
            self.streams.close()
