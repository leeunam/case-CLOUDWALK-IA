import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from publish import PASSWORD_KEY, USERS, PublishError, Stack, generate_env, private_env, read_settings, tunnel_origin


class PublishConfigurationTest(unittest.TestCase):
    def test_generates_once_and_validates_private_mode(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env.publish.local"
            generate_env(path)
            original = path.read_bytes()
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                generate_env(path)
            self.assertEqual(path.read_bytes(), original)
            with private_env(path) as settings:
                passwords = json.loads(settings[PASSWORD_KEY])
                self.assertEqual(set(passwords), set(USERS))
                self.assertEqual(len(set(passwords.values())), len(USERS))
            path.chmod(0o644)
            with self.assertRaises(PublishError), private_env(path):
                self.fail("Permissão aberta foi aceita.")

    def test_refuses_symlink_and_invalid_settings(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env.publish.local"
            generate_env(path)
            link = Path(directory) / "link"
            link.symlink_to(path)
            with self.assertRaises(OSError), private_env(link):
                self.fail("Link simbólico foi aceito.")
            raw = path.read_text()
            for invalid in (raw + "PUBLISH_PUBLIC_HOST=exemplo.invalid\n", raw.splitlines()[0], raw + raw):
                with self.assertRaises(PublishError):
                    read_settings(io.StringIO(invalid))

    def test_tunnel_uses_exact_origin_from_private_banner(self):
        valid = "https://boa-url7.trycloudflare.com"
        self.assertEqual(tunnel_origin(f"INF |   {valid}   |"), valid)
        for value in (
            "http://boa-url7.trycloudflare.com", valid + ":8443", valid + "/",
            valid + ".exemplo.invalid", "https://-boa.trycloudflare.com", valid + "@exemplo.invalid",
            "https://www.boa.trycloudflare.com", valid.upper(), f"{valid} |\n| https://outra.trycloudflare.com",
        ):
            with self.subTest(value=value):
                self.assertIsNone(tunnel_origin(f"INF | {value} |"))

    def test_local_up_keeps_the_tunnel_profile_inactive(self):
        stack = Stack(SimpleNamespace(project="cloudwalk_publish_test", http_port=18080, https_port=18443), {})
        with patch.object(stack, "compose") as compose, patch.object(stack, "check"):
            compose.return_value = ""
            stack.up()
            self.assertEqual(compose.call_args.args[0], "up")
            self.assertNotIn("tunnel", compose.call_args.kwargs)

    def test_rejects_bad_origin_before_calling_docker(self):
        stack = Stack(SimpleNamespace(project="cloudwalk_publish_test", http_port=18080, https_port=18443), {})
        with patch("publish.subprocess.run") as run, self.assertRaises(PublishError):
            stack.compose("up", origin="https://spoof.trycloudflare.com.example.test")
        run.assert_not_called()

    def test_running_setfit_must_answer_ready_at_check_time(self):
        with TemporaryDirectory() as temp:
            model = Path(temp)
            (model / "manifest.json").write_text("{}")
            args = SimpleNamespace(project="cloudwalk_publish_test", http_port=18080, https_port=18443,
                                   classifier="setfit", model_dir=model, action="check")
            stack = Stack(args, {})
            def compose(*command, **_):
                if command[0] == "ps":
                    return "\n".join(stack.services)
                self.assertEqual(command[:4], ("exec", "-T", "setfit", "python"))
                self.assertIn("/ready", command[-1])
                raise PublishError("HTTP 503")
            with patch.object(stack, "compose", side_effect=compose), patch.object(stack, "ca", return_value=None), \
                 patch("publish.ready", return_value=True), self.assertRaisesRegex(PublishError, "SetFit"):
                stack.check()


if __name__ == "__main__":
    unittest.main()
