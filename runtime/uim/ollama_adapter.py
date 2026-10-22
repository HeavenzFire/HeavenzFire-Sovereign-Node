"""Small, dependency-free Ollama adapter for the HeavenzFire UIM.

Security defaults:
- Only loopback HTTP endpoints are accepted.
- Network calls have explicit timeouts.
- Streaming is disabled to simplify bounded response handling.
- This adapter does not execute tools or interpret model output as commands.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any
from ipaddress import ip_address
from urllib.parse import urlsplit


DEFAULT_BASE_URL = "http://127.0.0.1:11434"
MAX_PROMPT_CHARS = 32000
MAX_MESSAGES = 64
DEFAULT_TIMEOUT = 30.0


class OllamaError(RuntimeError):
    """Sanitized error from local Ollama transport or response validation."""


def _validate_base_url(base_url: str) -> str:
    if not isinstance(base_url, str) or not base_url.strip():
        raise OllamaError("Ollama base URL must be a non-empty string")
    parsed = urlsplit(base_url.strip())
    if parsed.scheme != "http" or not parsed.hostname:
        raise OllamaError("Ollama adapter accepts loopback HTTP URLs only")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OllamaError("Credentials, query strings, and fragments are not allowed in base URL")
    hostname = parsed.hostname.lower()
    is_loopback = hostname == "localhost"
    if not is_loopback:
        try:
            is_loopback = ip_address(hostname).is_loopback
        except ValueError:
            is_loopback = False
    if not is_loopback:
        raise OllamaError("Refusing non-loopback Ollama endpoint")
    path = parsed.path.rstrip("/")
    if path:
        raise OllamaError("Ollama base URL must not contain a path")
    try:
        port = parsed.port
    except ValueError:
        raise OllamaError("Invalid port") from None
    if port is not None and not (1 <= port <= 65535):
        raise OllamaError("Invalid port")
    authority_host = f"[{hostname}]" if ":" in hostname else hostname
    return f"http://{authority_host}" + (f":{port}" if port else "")


class OllamaAdapter:
    def __init__(self, base_url: str | None = None, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = _validate_base_url(
            base_url or os.environ.get("HF_OLLAMA_BASE_URL", DEFAULT_BASE_URL)
        )
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 300:
            raise OllamaError("Timeout must be greater than 0 and at most 300 seconds")
        self.timeout = float(timeout)

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self.base_url + path
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(2_000_001)
        except urllib.error.HTTPError as exc:
            raise OllamaError(f"Ollama returned HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # Do not leak request headers, credentials, or full transport objects.
            reason = getattr(exc, "reason", None)
            category = type(reason).__name__ if reason is not None else type(exc).__name__
            raise OllamaError(f"Ollama request failed ({category})") from None
        if len(raw) > 2_000_000:
            raise OllamaError("Ollama response exceeded 2 MB limit")
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise OllamaError("Ollama returned invalid JSON") from None
        if not isinstance(result, dict):
            raise OllamaError("Ollama response must be a JSON object")
        return result

    def health(self) -> dict[str, Any]:
        """Probe Ollama's model inventory. Success proves reachability, not model quality."""
        result = self._request("/api/tags")
        models = result.get("models", [])
        if not isinstance(models, list):
            raise OllamaError("Ollama model inventory has an unexpected shape")
        names = [
            item.get("name")
            for item in models
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        ]
        return {"provider": "ollama", "connected": True, "models": names}

    def chat(self, model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Perform one non-streaming chat request; never executes returned tool calls."""
        if not isinstance(model, str) or not model.strip() or len(model) > 200:
            raise OllamaError("A model name of 1..200 characters is required")
        if not isinstance(messages, list) or not (1 <= len(messages) <= MAX_MESSAGES):
            raise OllamaError(f"messages must contain 1..{MAX_MESSAGES} entries")
        normalized: list[dict[str, str]] = []
        total_chars = 0
        allowed_roles = {"system", "user", "assistant"}
        for message in messages:
            if not isinstance(message, dict):
                raise OllamaError("Each message must be an object")
            role, content = message.get("role"), message.get("content")
            if role not in allowed_roles or not isinstance(content, str):
                raise OllamaError("Each message requires a supported role and string content")
            total_chars += len(content)
            normalized.append({"role": role, "content": content})
        if total_chars > MAX_PROMPT_CHARS:
            raise OllamaError(f"Total message content exceeds {MAX_PROMPT_CHARS} characters")
        result = self._request("/api/chat", {
            "model": model.strip(),
            "messages": normalized,
            "stream": False,
        })
        message = result.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise OllamaError("Ollama response did not contain message.content")
        return {
            "provider": "ollama",
            "model": result.get("model", model.strip()),
            "content": message["content"],
            "done": bool(result.get("done", False)),
        }
