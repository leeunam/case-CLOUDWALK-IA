"""Ensaio serial. Apenas o integrador inicia a pilha R01."""
import json
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "script/resilience"))
from run import environment  # noqa: E402


def main():
    project = "cloudwalk_r01_" + uuid.uuid4().hex[:12]
    args = ["docker", "compose", "-p", project, "--env-file", "script/resilience/stack.env",
            "-f", "compose.yml", "-f", "script/resilience/compose.yml", "-f", "script/kafka_recovery/compose.yml"]
    env = environment()

    def compose(*command, timeout=600, output=sys.stderr):
        subprocess.run([*args, *command], cwd=ROOT, env=env, stdout=output, check=True, timeout=timeout)

    print(json.dumps({"project": project, "revision": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}), flush=True)
    try:
        compose("up", "-d", "--build", "kafka_setup", "api", "worker", "requests", "outbox")
        compose("build", "probe")
        compose("run", "--rm", "--no-deps", "-T", "probe", "python", "-B", "/r01/trial.py", output=None)
    finally:
        compose("down", "--volumes", "--remove-orphans", timeout=120)


if __name__ == "__main__":
    main()
