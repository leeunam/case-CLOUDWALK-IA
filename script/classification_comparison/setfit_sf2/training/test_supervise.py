"""Subprocessos sintéticos exercitam o supervisor sem ajustar modelos."""

import os
from pathlib import Path
import signal
import socket
import sys
from tempfile import TemporaryDirectory
from threading import Timer
import unittest

from .supervise import Interrupted, Supervisor, supervise_run, watch_training


def control_child(body):
    return [
        sys.executable, "-c",
        "import socket, sys, time\n"
        "with socket.socket(fileno=int(sys.argv[1])) as control:\n"
        + "\n".join("    " + line for line in body.splitlines()),
    ]


class SupervisorTests(unittest.TestCase):
    def run_child(self, supervisor, body, limit):
        parent, child = socket.socketpair()
        with parent, child:
            command = [*control_child(body), str(child.fileno())]
            with supervisor.child(command, pass_fds=(child.fileno(),)) as process:
                self.process = process
                child.close()
                return watch_training(supervisor, process, parent, limit, expected_stages=2)

    def test_soma_os_dois_ajustes_e_ignora_exportacao_entre_eles(self):
        body = """
for _ in range(2):
    control.sendall(b"S")
    assert control.recv(1) == b"K"
    time.sleep(.03)
    control.sendall(b"E")
    time.sleep(.30)
"""
        measured = self.run_child(Supervisor(), body, .3)
        self.assertGreaterEqual(measured, .05)
        self.assertLess(measured, .3)
        self.assertEqual(self.process.returncode, 0)

    def test_estouro_acumulado_encerra_grupo(self):
        body = """
for _ in range(2):
    control.sendall(b"S")
    assert control.recv(1) == b"K"
    time.sleep(.12)
    control.sendall(b"E")
"""
        with self.assertRaises(Interrupted) as caught:
            self.run_child(Supervisor(), body, .2)
        self.assertEqual(caught.exception.code, 124)
        self.assertEqual(self.process.returncode, -signal.SIGKILL)

    def test_cancelamento_externo_registra_saida_e_mata_filho(self):
        def operation(supervisor, log):
            timer = Timer(.2, os.kill, (os.getpid(), signal.SIGTERM))
            timer.start()
            try:
                self.run_child(supervisor, "time.sleep(5)", 1)
            finally:
                timer.cancel()

        with TemporaryDirectory() as temp:
            output = Path(temp) / "fixture-cancelada"
            self.assertEqual(supervise_run(output, operation), 143)
            status = (output / "status.json").read_text()
        self.assertIn('"status": "cancelled"', status)
        self.assertEqual(self.process.returncode, -signal.SIGKILL)

    def test_saida_zero_sem_fim_dos_dois_ajustes_falha(self):
        with self.assertRaisesRegex(Interrupted, "sem confirmação"):
            self.run_child(Supervisor(), "pass", .2)


if __name__ == "__main__":
    unittest.main()
