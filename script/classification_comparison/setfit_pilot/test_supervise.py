"""Exercita os controles com subprocessos locais, sem dependências de ML."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from provision import CACHE, HERE, safe_environment, write_json

DRIVER = """
import os
import sys
import supervise

supervise.INSTALL_LIMIT = 0.7
supervise.TRAIN_LIMIT = 0.6
commands = supervise.installation_commands


def stubs(progress):
    mode = os.environ["PILOT_TEST_MODE"]
    code = 27 if mode == "dependency_error" else 0
    yield "install_dependencies", [
        sys.executable, "-c", f"import sys; print('pip simulado', file=sys.stderr); sys.exit({code})"
    ]
    yield commands(progress)[-1]


supervise.installation_commands = stubs
supervise.main()
"""

CURL = """#!/usr/bin/env python3
import os
from pathlib import Path
import sys
import time

mode = os.environ["PILOT_TEST_MODE"]
if mode == "download_error":
    sys.exit(22)
if mode == "download_hang":
    Path("worker-ready").touch()
    time.sleep(8)
output = Path(sys.argv[sys.argv.index("--output") + 1])
output.write_bytes(b"invalid" if mode == "verification_error" else b"weights")
"""

TRAINER = r"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import socket
import sys
import time
from provision import write_json

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path)
parser.add_argument("--control-fd", type=int)
args = parser.parse_args()
mode = os.environ["PILOT_TEST_MODE"]
path = args.output / "run.json"
report = json.loads(path.read_text())

if mode == "worker_error":
    report["interruption"] = {"message": "erro específico do worker"}
    write_json(path, report)
    sys.exit(37)

if mode == "success":
    time.sleep(0.75)
with socket.socket(fileno=args.control_fd) as channel:
    for fold in range(1, 3):
        report["active_fold"] = fold
        state = {"fold": fold, "status": "training"}
        report["folds"].append(state)
        write_json(path, report)
        channel.sendall(b"S")
        assert channel.recv(1) == b"K"
        Path("worker-ready").touch()
        if mode == "native_hang":
            ctypes.CDLL(None).sleep(8)
        time.sleep(0.38 if mode == "cumulative_timeout" else 0.03)
        channel.sendall(b"E")
        state["status"] = "complete"
        write_json(path, report)
        with (args.output / "predictions.jsonl").open("a") as results:
            results.write(json.dumps({"fold": fold}) + "\n")
report["status"] = "complete"
write_json(path, report)
"""


class ControlTests(unittest.TestCase):
    def setUp(self):
        CACHE.mkdir(exist_ok=True)
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory(dir=CACHE)))
        for name in ("supervise.py", "provision.py"):
            shutil.copyfile(HERE / name, self.folder / name)
        for name, program in (("drive.py", DRIVER), ("run.py", TRAINER), ("curl", CURL)):
            (self.folder / name).write_text(program)
        (self.folder / "curl").chmod(0o700)
        python = self.folder / ".venv/bin/python"
        python.parent.mkdir(parents=True)
        python.symlink_to(sys.executable)
        write_json(self.folder / "model-lock.json", {
            "model": "stub-model",
            "revision": "stub-revision",
            "files": {"model.safetensors": {"size": 7, "sha256": hashlib.sha256(b"weights").hexdigest()}},
        })

    def launch(self, name, mode, signal_to_send=None):
        command = [sys.executable, "-B", "drive.py", name]
        if name == "train":
            command += ["--output", "evidence"]
        env = {
            **safe_environment(),
            "PILOT_TEST_MODE": mode,
            "PATH": f"{self.folder}:{os.environ['PATH']}",
        }
        start = time.monotonic()
        with subprocess.Popen(command, cwd=self.folder, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True) as process:
            if signal_to_send is not None:
                while process.poll() is None and not (self.folder / "worker-ready").exists():
                    if time.monotonic() - start > 2:
                        process.kill()
                        self.fail("O subprocesso de teste não atingiu a etapa de espera")
                    time.sleep(0.01)
                process.send_signal(signal_to_send)
            stdout, stderr = process.communicate(timeout=10)
        return process.returncode, stdout, stderr, time.monotonic() - start

    def installation(self, mode, expected_code, status, phase, signal_to_send=None):
        code, stdout, stderr, elapsed = self.launch("install", mode, signal_to_send)
        self.assertEqual(code, expected_code, stderr)
        attempt = Path(stdout.strip().removeprefix("Registro de instalação em "))
        state = json.loads((attempt / "status.json").read_text())
        self.assertEqual((state["status"], state["phase"], state["exit_code"]), (status, phase, expected_code))
        self.assertIn("finished_at_utc", state)
        self.assertIn("pip simulado", (attempt / "commands.log").read_text())
        self.assertLess(elapsed, 3)
        return attempt

    def training(self, mode, expected_code, signal_to_send=None):
        code, _, stderr, elapsed = self.launch("train", mode, signal_to_send)
        self.assertEqual(code, expected_code, stderr)
        self.assertLess(elapsed, 3)
        return json.loads((self.folder / "evidence/run.json").read_text())

    def test_successful_provision_survives_later_dependency_error(self):
        attempt = self.installation("success", 0, "complete", "verify_model")
        receipt = self.folder / ".cache/model-manifest.json"
        original = (receipt.read_bytes(), (attempt / "status.json").read_bytes())
        self.installation("dependency_error", 27, "failed", "install_dependencies")
        self.assertEqual((receipt.read_bytes(), (attempt / "status.json").read_bytes()), original)

    def test_download_error_keeps_curl_exit_code(self):
        self.installation("download_error", 22, "failed", "download_model")

    def test_verification_error_has_its_own_phase(self):
        self.installation("verification_error", 1, "failed", "verify_model")
        self.assertFalse((self.folder / ".cache/model-manifest.json").exists())

    def test_installation_timeout(self):
        self.installation("download_hang", 124, "timed_out", "download_model")

    def test_installation_cancellation(self):
        self.installation("download_hang", 130, "cancelled", "download_model", signal.SIGINT)

    def test_training_does_not_charge_time_outside_fit(self):
        self.assertEqual(self.training("success", 0)["status"], "complete")

    def test_training_timeout_interrupts_native_call(self):
        state = self.training("native_hang", 124)
        self.assertEqual(state["interruption"]["kind"], "timed_out")
        self.assertEqual(state["folds"], [{"fold": 1, "status": "interrupted", "interrupted_during": "training"}])
        self.assertFalse((self.folder / "evidence/predictions.jsonl").exists())

    def test_training_budget_is_cumulative_and_preserves_completed_fold(self):
        state = self.training("cumulative_timeout", 124)
        self.assertEqual([row["status"] for row in state["folds"]], ["complete", "interrupted"])
        self.assertEqual((self.folder / "evidence/predictions.jsonl").read_text().splitlines(), ['{"fold": 1}'])

    def test_training_cancellation(self):
        state = self.training("native_hang", 143, signal.SIGTERM)
        self.assertEqual(state["interruption"]["kind"], "cancelled")
        self.assertEqual(state["folds"][0]["status"], "interrupted")

    def test_training_error_preserves_worker_diagnosis(self):
        state = self.training("worker_error", 37)
        self.assertEqual(state["interruption"], {"kind": "failed", "exit_code": 37, "message": "erro específico do worker"})


if __name__ == "__main__":
    unittest.main()
