import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from script.classification_acceptance.aceite_integrado import verify_direct_classification, verify_requests


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "audit/classification-acceptance"


class AcceptanceControlsTest(unittest.TestCase):
    def test_direct_preserves_each_channel_field(self):
        for mode in ("fixture", "setfit"):
            record = json.loads((ARCHIVE / f"{mode}.json").read_text())["cases"]["direto"]["initial"]
            verify_direct_classification(record)
            for field, changed in (("category", "pix"), ("priority", "basic"),
                                   ("category_source", "setfit"), ("priority_source", "supervisor")):
                with self.subTest(mode=mode, field=field), self.assertRaises(AssertionError):
                    verify_direct_classification({**record, field: changed})

    def test_request_version_matches_outbox_even_on_a_duplicate(self):
        for mode in ("fixture", "setfit"):
            archive = json.loads((ARCHIVE / f"{mode}.json").read_text())
            for label, capture in archive["kafka"].items():
                row = archive["cases"][label]
                (turn,) = row.get("after_correction", row["initial"])["turns"]
                event = {"event_id": capture["request_id"], "schema_version": capture["request_version"]}
                with self.subTest(mode=mode, case=label):
                    verify_requests(turn, [event, event.copy()])
                    changed = "1.1" if event["schema_version"] == "1.0" else "1.0"
                    with self.assertRaises(AssertionError):
                        verify_requests(turn, [event, {**event, "schema_version": changed}])

    def test_optimized_cli_fails_before_accessing_the_stack_or_writing_results(self):
        # O audit hook detecta rede e processos filhos (inclusive o cliente Docker).
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "sitecustomize.py").write_text(
                "import sys\n"
                "def guard(event, args):\n"
                "    if event in ('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen'):\n"
                "        raise RuntimeError('Contato externo durante o aceite')\n"
                "sys.addaudithook(guard)\n"
            )
            result = directory / "resultado.json"
            for flags, optimization in ((["-O"], ""), ([], "1")):
                with self.subTest(flags=flags, env=optimization):
                    env = {**os.environ, "PYTHONPATH": temp, "PYTHONOPTIMIZE": optimization}
                    completed = subprocess.run(
                        [sys.executable, "-B", *flags, "-m", "script.classification_acceptance.aceite_integrado",
                         "--classifier", "setfit", "--project", "cloudwalk_demo_teste",
                         "--origin", "http://127.0.0.1:1", "--credentials", str(directory / "ausente"),
                         "--output", str(result)],
                        cwd=ROOT, env=env, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assertIn("Use Python sem otimização", completed.stderr)
                    self.assertFalse(result.exists())
