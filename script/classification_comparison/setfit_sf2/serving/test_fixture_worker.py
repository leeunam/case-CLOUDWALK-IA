"""Processo de teste. Somente fixtures públicas e falhas de transporte induzidas."""
import json
import os
from pathlib import Path
import sys
import time


def main():
    root, fixtures = map(Path, sys.argv[1:])
    mode = lambda: (root / "mode").read_text()
    with (root / "starts").open("a") as stream:
        print(os.getpid(), file=stream)
    if mode() == "boot-timeout":
        time.sleep(30)
    print("unexpected" if mode() == "early" else '{"type":"ready"}', flush=True)
    for line in sys.stdin.buffer:
        item = json.loads(line)
        with (root / "received").open("a") as stream:
            print(json.dumps(item["missing_fields"]), file=stream)
        behavior = mode()
        if behavior == "timeout":
            time.sleep(30)
        if behavior == "eof":
            return
        if behavior == "delay":
            time.sleep(0.25)
        scenario = behavior if behavior in ("review", "error", "complete-both") else "complete"
        frame = (fixtures / (scenario + ".jsonl")).read_bytes()
        parsed = json.loads(frame)
        if behavior == "too-long":
            parsed.update(outcome="review", applied={}, calls={"category": 0, "priority": 0})
            parsed["fields"]["priority"].update(decision="review", reason="too_long", raw=None, vector=None, margin=None)
            frame = json.dumps(parsed).encode() + b"\n"
        elif behavior in ("id", "package_sha256", "policy_sha256"):
            parsed[behavior] = "0" * 64
            frame = json.dumps(parsed).encode() + b"\n"
        elif behavior == "oversize":
            frame = b" " * 65536 + frame
        elif behavior == "exact-limit":
            frame = b" " * (65536 - len(frame)) + frame
        elif behavior == "duplicate":
            frame = frame.replace(b'"calls":', b'"calls":null,"calls":')
        elif behavior == "nan":
            frame = frame.replace(b'"elapsed_ms":1', b'"elapsed_ms":NaN')
        elif behavior == "utf8":
            frame = b"\xff\n"
        elif behavior == "extra":
            frame += b"extra\n"
        sys.stdout.buffer.write(frame)
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
