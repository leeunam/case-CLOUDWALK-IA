"""Peer IPC sintético, usado exclusivamente pelos testes."""
import base64
import json
from pathlib import Path
import sys
import time


def main():
    mode, path = sys.argv[1:]
    frames = json.loads(Path(path).read_bytes())
    output = sys.stdout.buffer
    time.sleep(.075)
    output.write(b'{"type":"ready"}\n')
    if mode == "early":
        output.write(b'{"premature":true}\n')
    output.flush()
    for line in sys.stdin.buffer:
        item = json.loads(line)
        if set(item) != {"contract_version", "id", "text", "received", "catalog", "missing_fields"}:
            return 3
        if mode == "eof":
            output.write(b'{"truncated":')
            return 0
        if mode == "invalid-utf8":
            output.write(b'\xff\n')
        else:
            output.write(base64.b64decode(frames[item["id"]]))
        output.flush()
    if mode == "extra":
        output.write(b"extraneous\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

