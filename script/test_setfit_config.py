"""Confere a configuração efetiva das demos sem entrar no daemon nem iniciar serviços."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

from demo import Compose, ROOT
from publish import Stack


@unittest.skipUnless(shutil.which("docker"), "Docker Compose necessário")
class ClassifierConfigTest(unittest.TestCase):
    def test_base_compose_pins_legacy_mode_at_intake_and_processing(self):
        for mode in (None, "fixture", "http"):
            env = {"PATH": os.environ["PATH"]}
            if mode:
                env["CLOUDWALK_JEV_MODE"] = mode
            result = subprocess.run(["docker", "compose", "--env-file", os.devnull, "-f", str(ROOT / "compose.yml"),
                                     "config", "--format", "json"], env=env, capture_output=True, check=True)
            services = json.loads(result.stdout)["services"]
            for key in ("api", "worker"):
                self.assertEqual(services[key]["environment"]["CLOUDWALK_JEV_MODE"], mode or "disabled")
            self.assertNotIn("TYPESAFE_API_KEY", services["api"]["environment"])

    def test_isolation_of_each_demo_and_default(self):
        with tempfile.TemporaryDirectory() as temp:
            model = Path(temp) / "model"
            model.mkdir()
            (model / "manifest.json").write_text("{}")
            for published in (False, True):
                for classifier in (("fixture", "setfit") if published else ("fixture", "disabled", "setfit")):
                    with self.subTest(published=published, classifier=classifier):
                        args = SimpleNamespace(project="c06c_config", http_port=18111, https_port=18444,
                                               api_port=43210, web_port=45210, classifier=classifier,
                                               model_dir=model if classifier == "setfit" else None)
                        if published:
                            stack = Stack(args, {k: "synthetic" for k in (
                                "PUBLISH_DB_PASSWORD", "PUBLISH_RAILS_SECRET", "PUBLISH_CHANNEL_SECRET",
                                "PUBLISH_REQUESTS_SECRET", "PUBLISH_EVENTS_SECRET", "PUBLISH_DEMO_PASSWORDS")})
                            command = stack.command
                        else:
                            stack = Compose(args)
                            command = stack.prefix.copy()
                            command[command.index("--env-file") + 1] = os.devnull
                            stack.env.update({k: "synthetic" for k in (
                                "DEMO_RAILS_SECRET", "DEMO_POSTGRES_PASSWORD", "DEMO_CHANNEL_SECRET",
                                "DEMO_AGENT_EVENTS_SECRET", "DEMO_AGENT_REQUESTS_SECRET", "DEMO_PASSWORDS")})
                        result = subprocess.run([*command, "config", "--format", "json"], check=True,
                                                env=stack.env, capture_output=True)
                        services = json.loads(result.stdout)["services"]
                        if classifier != "setfit":
                            self.assertNotIn("setfit", services)
                            for key in ("api", "worker"):
                                self.assertEqual(services[key]["environment"]["CLOUDWALK_JEV_MODE"], classifier)
                            continue
                        sidecar = services["setfit"]
                        self.assertFalse(sidecar.get("ports"))
                        self.assertEqual(set(sidecar["networks"]), {"inference"})
                        peers = {key for key, svc in services.items() if "inference" in svc.get("networks", {})}
                        self.assertEqual(peers, {"worker", "setfit"})
                        self.assertEqual(services["worker"]["depends_on"]["setfit"]["condition"], "service_healthy")
                        self.assertEqual(services["worker"]["environment"]["SETFIT_URL"], "http://setfit:8080")
                        for key in ("worker", "api"):
                            self.assertEqual(services[key]["environment"]["CLASSIFICATION_PROVIDER"], "setfit")
                            self.assertEqual(services[key]["environment"]["CLOUDWALK_JEV_MODE"], "disabled")
                        mount = next(vol for vol in sidecar["volumes"] if vol["target"] == "/model")
                        self.assertTrue(mount["read_only"])
                        self.assertEqual(mount["source"], str(model))
