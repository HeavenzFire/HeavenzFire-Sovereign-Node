"""Integration tests for Unified Hub Ollama routes; uses mocked provider calls."""
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import server


class OllamaHubRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(server, "DB_PATH", Path(self.temp.name) / "hub.sqlite3")
        self.db_patch.start()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%s" % self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        self.db_patch.stop()
        self.temp.cleanup()

    def request(self, path, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = Request(self.base + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=2) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_health_route_reports_live_probe_evidence(self):
        fake = unittest.mock.Mock()
        fake.health.return_value = {"provider": "ollama", "connected": True, "models": ["llama3.2:1b"]}
        with patch.object(server, "OllamaAdapter", return_value=fake):
            status, body = self.request("/v1/uim/ollama/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "connected")
        self.assertEqual(body["models"], ["llama3.2:1b"])
        self.assertEqual(body["evidence"], "live /api/tags probe")

    def test_unavailable_provider_is_not_reported_connected(self):
        fake = unittest.mock.Mock()
        fake.health.side_effect = server.OllamaError("Ollama request failed (ConnectionRefusedError)")
        with patch.object(server, "OllamaAdapter", return_value=fake):
            status, body = self.request("/v1/uim/ollama/health")
        self.assertEqual(status, 503)
        self.assertEqual(body["status"], "unavailable")
        self.assertEqual(body["models"], [])

    def test_chat_returns_text_without_enabling_execution(self):
        fake = unittest.mock.Mock()
        fake.chat.return_value = {
            "provider": "ollama", "model": "llama3.2:1b",
            "content": "Text only; do not run shell commands.", "done": True,
        }
        with patch.object(server, "OllamaAdapter", return_value=fake):
            status, body = self.request("/v1/uim/ollama/chat", {
                "model": "llama3.2:1b",
                "messages": [{"role": "user", "content": "Return a safe response"}],
            })
        self.assertEqual(status, 200)
        self.assertFalse(body["execution_enabled"])
        self.assertEqual(body["content"], "Text only; do not run shell commands.")
        fake.chat.assert_called_once_with(
            "llama3.2:1b", [{"role": "user", "content": "Return a safe response"}]
        )


if __name__ == "__main__":
    unittest.main()
