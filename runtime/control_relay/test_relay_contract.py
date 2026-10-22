import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
AGENT = ROOT / "runtime" / "control_relay" / "Invoke-HeavenzFireControlRelay.ps1"
INSTALLER = ROOT / "runtime" / "control_relay" / "Install-HeavenzFireControlRelay.ps1"


class ControlRelayContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AGENT.read_text(encoding="utf-8")
        cls.installer = INSTALLER.read_text(encoding="utf-8")

    def test_agent_is_powershell_51_and_deny_by_allowlist(self):
        self.assertIn("#requires -Version 5.1", self.agent)
        self.assertIn("[ValidateSet('status','disk','processes','git-status')]", self.agent)

    def test_agent_does_not_expose_listener_or_dynamic_command_execution(self):
        lowered = self.agent.lower()
        self.assertNotIn("invoke-expression", lowered)
        self.assertNotIn("http.listener", lowered)
        self.assertNotIn("start-job", lowered)
        self.assertIn("inbound_listener = $false", lowered)
        self.assertIn("execution_enabled = $false", lowered)

    def test_git_status_requires_explicit_git_workspace(self):
        self.assertIn("git-status requires -Workspace", self.agent)
        self.assertIn("status --short --branch", self.agent)

    def test_installer_is_non_persistent_and_uses_tls12(self):
        self.assertIn("SecurityProtocolType]::Tls12", self.installer)
        self.assertIn("No service, scheduled task, firewall rule, or inbound listener was created.", self.installer)
        self.assertIn("remote transport is intentionally not configured", self.installer.lower())


if __name__ == "__main__":
    unittest.main()
