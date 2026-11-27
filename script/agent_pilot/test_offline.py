import unittest
from types import SimpleNamespace
from unittest.mock import patch

from offline import Offline
from offline_check import check
from offline_faults import bridge_confirmed, verify_faults


class OfflineGuardTest(unittest.TestCase):
    def setUp(self):
        self.stack = Offline(SimpleNamespace(project="cloudwalk_e01_offline_segunda", api_port=43309, web_port=45379))

    def test_accepts_selected_projects_loopback_mapping(self):
        with patch.object(self.stack, "run", return_value="127.0.0.1:43309\n") as compose:
            self.stack.require_api_binding()
        compose.assert_called_once_with("port", "--protocol", "tcp", "api", "3000", capture=True, timeout=10)

    def test_wrong_port_interrupts_check_and_faults_before_any_http(self):
        for action, target in ((check, "offline_check.Browser"),
                               (lambda stack: verify_faults(stack, {}), "offline_faults.Browser")):
            with self.subTest(target=target):
                with (patch.object(self.stack, "run", return_value="127.0.0.1:43310\n"),
                      patch.object(self.stack, "sql") as sql, patch(target) as browser):
                    with self.assertRaisesRegex(SystemExit, "porta HTTP indicada não corresponde"):
                        action(self.stack)
                    browser.assert_not_called()
                    sql.assert_not_called()

    def test_bridge_watermark_must_go_past_last_matching_copy(self):
        events = [{"partition": 1, "offset": 5}, {"partition": 1, "offset": 6}]
        snapshot = {"agent.events": events, "event_offsets": {"1": 6}}
        self.assertIsNone(bridge_confirmed(snapshot, events))
        self.assertIsNone(bridge_confirmed({**snapshot, "event_offsets": {}}, events))
        snapshot["event_offsets"]["1"] = 7
        self.assertIs(bridge_confirmed(snapshot, events), snapshot)
        self.assertIsNone(bridge_confirmed(snapshot, events[:1]))
