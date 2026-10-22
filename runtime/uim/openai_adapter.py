"""Bounded OpenAI API adapter for HeavenzFire UIM.

Uses OPENAI_API_KEY from the process environment. The key is never accepted in
request JSON, returned in responses, or written to logs. This is a hosted API
worker, not a bridge to the current ChatGPT conversation.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

API_URL = "https://api.openai.com/v1/responses"
MAX_INPUT_CHARS = 32000
MAX_MESSAGES = 64
DEFAULT_TIMEOUT = 45.0


class OpenAIAdapterError(RuntimeError):
    """Sanitized API transport, configuration, or response error."""


class OpenAIAdapter:
    def __init__(self, api_key: str | None = None, model: str | None = None,
                 timeout: float = DEFAULT_TIMEOUT):
        self.api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self.model = model if model is not None else os.environ.get("HF_OPENAI_MODEL", "")
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            raise OpenAIAdapterError("OPENAI_API_KEY is not configured")
        if not isinstance(self.model, str) or not self.model.strip() or len(self.model) > 200:
            raise OpenAIAdapterError("HF_OPENAI_MODEL must name an API-accessible model")
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 300:
            raise OpenAIAdapterError("Timeout must be greater than 0 and at most 300 seconds")
        self.timeout = float(timeout)

    def chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        if not isinstance(messages, list) or not (1 <= len(messages) <= MAX_MESSAGES):
            raise OpenAIAdapterError(f"messages must contain 1..{MAX_MESSAGES} entries")
        normalized: list[dict[str, str]] = []
        total_chars = 0
        for message in messages:
            if not isinstance(message, dict):
                raise OpenAIAdapterError("Each message must be an object")
            role, content = message.get("role"), message.get("content")
            if role not in {"system", "user", "assistant", "developer"} or not isinstance(content, str):
                raise OpenAIAdapterError("Each message requires a supported role and string content")
            total_chars += len(content)
            normalized.append({"role": role, "content": content})
        if total_chars > MAX_INPUT_CHARS:
            raise OpenAIAdapterError(f"Total message content exceeds {MAX_INPUT_CHARS} characters")

        payload = json.dumps({"model": self.model, "input": normalized, "store": False}).encode("utf-8")
        request = urllib.request.Request(
            API_URL, data=payload, method="POST",
            headers={
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(2_000_001)
        except urllib.error.HTTPError as exc:
            # Never return the provider body: it can contain request details.
            raise OpenAIAdapterError(f"OpenAI API returned HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", None)
            category = type(reason).__name__ if reason is not None else type(exc).__name__
            raise OpenAIAdapterError(f"OpenAI API request failed ({category})") from None
        if len(raw) > 2_000_000:
            raise OpenAIAdapterError("OpenAI API response exceeded 2 MB limit")
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise OpenAIAdapterError("OpenAI API returned invalid JSON") from None
        if not isinstance(result, dict):
            raise OpenAIAdapterError("OpenAI API response must be a JSON object")

        text_parts: list[str] = []
        for item in result.get("output", []):
            if not isinstance(item, dict):
                continue
            for part in item.get("content", []):
                if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    text_parts.append(part["text"])
        if not text_parts:
            raise OpenAIAdapterError("OpenAI API response did not contain output text")
        return {
            "provider": "openai",
            "model": result.get("model", self.model),
            "content": "".join(text_parts),
            "response_id": result.get("id"),
        }
