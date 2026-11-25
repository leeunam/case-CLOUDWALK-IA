"""Subprocessos sintéticos exercitam o supervisor sem ajustar modelos."""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import sys
from tempfile import TemporaryDirectory
from threading import Timer
import unittest
from unittest.mock import patch

from .supervise import Interrupted, Supervisor, supervise_run, train, watch_training


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

    @contextmanager
    def staged_train(self, output, *, missing_digest=False):
        @contextmanager
        def fixture_child(_supervisor, _command, **_options):
            package = output / "staging/package"
            package.mkdir()
            encoded = b'{"fixture":true}'
            (package / "manifest.json").write_bytes(encoded)
            evidence = {} if missing_digest else {"package_sha256": hashlib.sha256(encoded).hexdigest()}
            (package.parent / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
            yield object()

        with patch.object(Supervisor, "child", fixture_child), patch(
            train.__module__ + ".watch_training", return_value=.25
        ):
            yield

    def test_cancelamento_antes_da_conclusao_remove_artefatos(self):
        original_replace = Path.replace
        original_write = Path.write_text
        for boundary in ("evidence.json", "package", "recibo terminal"):
            with self.subTest(boundary=boundary), TemporaryDirectory() as temp:
                output = Path(temp) / "fixture"

                def replace(source, target):
                    if target == output / boundary:
                        signal.raise_signal(signal.SIGTERM)
                    return original_replace(source, target)

                def write(source, data, *args, **kwargs):
                    if boundary == "recibo terminal" and source == output / "status.tmp":
                        if json.loads(data)["status"] == "complete":
                            signal.raise_signal(signal.SIGTERM)
                    return original_write(source, data, *args, **kwargs)

                with self.staged_train(output), patch.object(Path, "replace", replace), patch.object(
                    Path, "write_text", write
                ):
                    self.assertEqual(train(output, []), 143)
                status = json.loads((output / "status.json").read_text(encoding="utf-8"))
                self.assertEqual((status["status"], status["exit_code"]), ("cancelled", 143))
                self.assertNotIn("package_sha256", status)
                for name in ("evidence.json", "package", "staging"):
                    self.assertFalse((output / name).exists())

    def test_sinal_pendente_antes_do_compromisso_veta_o_pacote(self):
        original_replace = Path.replace
        signals = {signal.SIGTERM}
        with TemporaryDirectory() as temp:
            output = Path(temp) / "fixture"

            def replace(source, target):
                if target == output / "package":
                    signal.raise_signal(signal.SIGTERM)
                return original_replace(source, target)

            old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, signals)
            try:
                with self.staged_train(output), patch.object(Path, "replace", replace):
                    self.assertEqual(train(output, []), 143)
            finally:
                if signal.sigpending() & signals:
                    signal.sigwait(signals)
                signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)

            receipt = json.loads((output / "status.json").read_text())
            self.assertEqual((receipt["status"], receipt["exit_code"]), ("cancelled", 143))
            self.assertFalse((output / "package").exists())
            self.assertFalse((output / "evidence.json").exists())

    def test_sinal_apos_compromisso_preserva_pacote_e_recibo(self):
        original_replace = Path.replace
        with TemporaryDirectory() as temp:
            output = Path(temp) / "fixture"

            def replace(source, target):
                result = original_replace(source, target)
                if target == output / "status.json" and json.loads(target.read_text())["status"] == "complete":
                    signal.raise_signal(signal.SIGTERM)
                return result

            with self.staged_train(output), patch.object(Path, "replace", replace):
                self.assertEqual(train(output, []), 0)
            receipt = json.loads((output / "status.json").read_text())
            self.assertEqual((receipt["status"], receipt["exit_code"]), ("complete", 0))
            evidence = json.loads((output / "evidence.json").read_text())
            self.assertEqual(receipt["package_sha256"], evidence["package_sha256"])
            self.assertTrue((output / "package/manifest.json").is_file())

    def test_excecao_inesperada_registra_falha_e_propaga(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "fixture"
            with self.staged_train(output, missing_digest=True), self.assertRaisesRegex(KeyError, "package_sha256"):
                train(output, [])
            receipt = json.loads((output / "status.json").read_text())
            self.assertEqual((receipt["status"], receipt["exit_code"]), ("failed", 1))
            self.assertIn("package_sha256", receipt["message"])
            self.assertIn("finished_at_utc", receipt)
            for name in ("evidence.json", "package", "staging"):
                self.assertFalse((output / name).exists())

    def test_saida_zero_sem_fim_dos_dois_ajustes_falha(self):
        with self.assertRaisesRegex(Interrupted, "sem confirmação"):
            self.run_child(Supervisor(), "pass", .2)


if __name__ == "__main__":
    unittest.main()
