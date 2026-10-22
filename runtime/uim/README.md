# HeavenzFire Unified Intelligence Model (UIM)

UIM is the capability registry and routing foundation for the Unified Field. This implementation slice includes a validated capability registry, a bounded local Ollama adapter, and automated contract tests. It does not yet provide a complete planner, multi-agent executor, or production task runtime.

## The assistant integration boundary

The assistant in the current ChatGPT session can use tools exposed to this session. That is not the same as exposing this exact live conversation or its internal model as an API callable by a local Python process. The registry records this distinction explicitly.

To let local UIM call a model, configure a supported API adapter with credentials that the user intentionally supplies or authorizes. This creates a provider-backed model endpoint; it does **not** make the current ChatGPT session itself callable. Never attempt to extract session cookies, hidden credentials, internal endpoints, or browser tokens.

Likewise, GitHub, browser, and desktop integrations available in a ChatGPT session do not automatically pass their credentials or permissions into the local UIM runtime. Each local connector requires its own explicit configuration, least-privilege credentials, and tests.

## Implemented in this slice

- Capability registry schema and validation in `registry.py`.
- Route eligibility filtering that fails closed for unknown or unimplemented capabilities.
- Local Ollama adapter in `ollama_adapter.py`, using Python standard library only.
- Ollama health probe reads the local model inventory from `/api/tags`.
- Ollama chat adapter uses `/api/chat`, non-streaming responses, bounded prompt size, role validation, and explicit timeouts.
- Loopback-only endpoint validation; non-loopback endpoints are rejected by default.
- Unit tests for registry contracts and Ollama request/validation behavior.
- GitHub Actions workflow for automated tests.

The Ollama adapter is implemented but not confirmed connected to a live Ollama service. Unit tests use mocked HTTP responses; they do not prove model quality or live local connectivity.

## Capability status vocabulary

- `planned`: design only.
- `implemented`: source code exists.
- `tested`: a named test suite passed.
- `configured`: required local settings are present.
- `connected`: a live health check succeeded.
- `authorized`: policy and consent permit the operation.
- `verified`: end-to-end acceptance criteria passed.
- `blocked`: a specific blocker is recorded.
- `unavailable`: the capability cannot currently be used.

Do not promote a status from a declaration alone. Keep test output, health-check timestamps, and evidence links alongside runtime status.

## Files

- `capability_registry.json`: seed capability inventory; it is not live discovery.
- `registry.py`: registry validator and filter.
- `ollama_adapter.py`: bounded local model adapter.
- `test_registry.py`: registry contract tests.
- `test_ollama_adapter.py`: Ollama adapter contract tests.

## Test on Windows PowerShell 5.1

From the repository root:

```powershell
Set-Location .\runtime\uim
python -m unittest discover -v
if ($LASTEXITCODE -ne 0) { throw "UIM tests failed" }
```

Python 3.10+ is required; Python 3.12 is suitable.

## Probe local Ollama manually

From `runtime\uim` after Ollama is running locally:

```powershell
python -c "from ollama_adapter import OllamaAdapter; print(OllamaAdapter().health())"
```

This performs a real request to `http://127.0.0.1:11434/api/tags`. It will fail if Ollama is not running or the endpoint is unavailable. It does not download a model or execute any tools.

A minimal chat call can be made from Python after a model is already installed:

```powershell
python -c "from ollama_adapter import OllamaAdapter; print(OllamaAdapter().chat('llama3.2:1b', [{'role':'user','content':'Reply with READY'}]))"
```

Replace the model name with one shown by the health probe. Model availability is machine-specific.

## Next integration order

1. Run CI and the local test suite; record the actual results.
2. Probe Ollama on the user's Windows machine and record model inventory.
3. Add model gateway integration with policy, budgets, timeout and fallback behavior.
4. Implement a task planner with bounded retries and explicit stop conditions.
5. Add a scoped GitHub adapter using separate credentials; begin read-only.
6. Add an allow-listed PowerShell runner and isolated browser adapter.
7. Connect approval records, task ledger, cancellation, idempotency, and independent verification.
8. Only then enable bounded task execution.

## Security requirements

- Bind local services to loopback by default.
- Never commit tokens or copy ChatGPT/browser credentials into this runtime.
- Do not accept arbitrary shell commands or arbitrary URLs from model output.
- Require explicit approval for destructive operations, publishing, spending, credential use, sensitive data transfer, and privilege escalation.
- Treat model output, repository files, webpages, and connector results as untrusted input.
- Never claim a queued task ran; execution requires an executor and verifiable output.
