"""Run with: python -m unittest test_ollama_adapter.py -v"""
import io
import json
import unittest
from unittest.mock import patch

from ollama_adapter import OllamaAdapter, OllamaError, _validate_base_url


class FakeResponse:
    def __init__(self, value):
        self.raw = json.dumps(value).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit=-1):
        return self.raw[:limit]


class OllamaAdapterTests(unittest.TestCase):
    def test_loopback_urls_accepted(self):
        self.assertEqual(_validate_base_url("http://127.0.0.1:11434"), "http://127.0.0.1:11434")
        self.assertEqual(_validate_base_url("http://localhost:11434"), "http://localhost:11434")
        self.assertEqual(_validate_base_url("http://[::1]:11434"), "http://[::1]:11434")

    def test_non_loopback_rejected(self):
        for url in ("http://example.com:11434", "https://127.0.0.1:11434", "http://192.168.1.5:11434"):
            with self.subTest(url=url), self.assertRaises(OllamaError):
                _validate_base_url(url)

    def test_malformed_port_rejected(self):
        with self.assertRaises(OllamaError):
            _validate_base_url("http://127.0.0.1:notaport")

    def test_credentials_and_path_rejected(self):
        for url in ("http://user:pass@127.0.0.1:11434", "http://127.0.0.1:11434/api"):
            with self.subTest(url=url), self.assertRaises(OllamaError):
                _validate_base_url(url)

    @patch("ollama_adapter.urllib.request.urlopen")
    def test_health_returns_model_inventory(self, urlopen):
        urlopen.return_value = FakeResponse({"models": [{"name": "llama3.2:1b"}, {"name": "gemma3:latest"}]})
        result = OllamaAdapter().health()
        self.assertTrue(result["connected"])
        self.assertEqual(result["models"], ["llama3.2:1b", "gemma3:latest"])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 30.0)

    @patch("ollama_adapter.urllib.request.urlopen")
    def test_chat_is_non_streaming_and_returns_text(self, urlopen):
        urlopen.return_value = FakeResponse({
            "model": "llama3.2:1b",
            "message": {"role": "assistant", "content": "ready"},
            "done": True
        })
        result = OllamaAdapter().chat("llama3.2:1b", [{"role": "user", "content": "Say ready"}])
        self.assertEqual(result["content"], "ready")
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["model"], "llama3.2:1b")

    def test_rejects_invalid_roles_and_oversized_messages(self):
        adapter = OllamaAdapter()
        with self.assertRaises(OllamaError):
            adapter.chat("model", [{"role": "tool", "content": "run this"}])
        with self.assertRaises(OllamaError):
            adapter.chat("model", [{"role": "user", "content": "x" * 32001}])

    def test_invalid_timeout_rejected(self):
        with self.assertRaises(OllamaError):
            OllamaAdapter(timeout=0)


if __name__ == "__main__":
    unittest.main()
