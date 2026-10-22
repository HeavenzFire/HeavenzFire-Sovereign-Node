"""Contract tests for the OpenAI API adapter; all transport is mocked."""
import json
import unittest
from unittest.mock import Mock, patch

from openai_adapter import OpenAIAdapter, OpenAIAdapterError, API_URL


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size=-1):
        return self.body[:size]


class OpenAIAdapterTests(unittest.TestCase):
    def test_requires_api_key_and_model(self):
        with self.assertRaisesRegex(OpenAIAdapterError, "OPENAI_API_KEY"):
            OpenAIAdapter(api_key="", model="example-model")
        with self.assertRaisesRegex(OpenAIAdapterError, "HF_OPENAI_MODEL"):
            OpenAIAdapter(api_key="test-key", model="")

    def test_sends_responses_request_and_returns_text(self):
        response = {
            "id": "resp_test", "model": "example-model",
            "output": [{"type": "message", "content": [
                {"type": "output_text", "text": "READY"}
            ]}],
        }
        with patch("openai_adapter.urllib.request.urlopen", return_value=FakeResponse(response)) as urlopen_mock:
            adapter = OpenAIAdapter(api_key="test-key", model="example-model")
            result = adapter.chat([{"role": "user", "content": "Reply READY"}])
        req = urlopen_mock.call_args.args[0]
        self.assertEqual(req.full_url, API_URL)
        self.assertEqual(req.get_header("Authorization"), "Bearer test-key")
        sent = json.loads(req.data.decode("utf-8"))
        self.assertFalse(sent["store"])
        self.assertEqual(result["content"], "READY")
        self.assertEqual(result["provider"], "openai")

    def test_rejects_oversized_or_invalid_messages(self):
        adapter = OpenAIAdapter(api_key="test-key", model="example-model")
        with self.assertRaises(OpenAIAdapterError):
            adapter.chat([{"role": "tool", "content": "no"}])
        with self.assertRaises(OpenAIAdapterError):
            adapter.chat([{"role": "user", "content": "x" * 32001}])

    def test_sanitizes_http_errors(self):
        from urllib.error import HTTPError
        error = HTTPError(API_URL, 401, "Unauthorized", {}, None)
        with patch("openai_adapter.urllib.request.urlopen", side_effect=error):
            adapter = OpenAIAdapter(api_key="test-key", model="example-model")
            with self.assertRaisesRegex(OpenAIAdapterError, "HTTP 401") as caught:
                adapter.chat([{"role": "user", "content": "hello"}])
        self.assertNotIn("test-key", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
