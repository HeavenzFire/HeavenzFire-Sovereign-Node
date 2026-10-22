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

## Unified Hub Ollama endpoints

The local Unified Hub now exposes the bounded Ollama adapter through these loopback-only API routes. Requests must pass the hub's authorization check; when `HF_HUB_TOKEN` is set, send `Authorization: Bearer <token>`.

- `GET /v1/uim/ollama/health`: performs a live `/api/tags` probe and returns `connected` with a model inventory only when the probe succeeds. A failed probe returns HTTP 503 and `unavailable`.
- `POST /v1/uim/ollama/chat`: accepts JSON with `model` and `messages`, applies adapter validation and timeout limits, and returns response text. It never executes model output or tool calls.
- `GET /v1/connectors`: lists Ollama as `probe_required`; this static connector listing is not evidence of a live connection.

Example PowerShell 5.1 probe after starting the hub:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8765/v1/uim/ollama/health"
```

Example chat request:

```powershell
$body = @{
    model = "llama3.2:1b"
    messages = @(@{ role = "user"; content = "Reply with READY" })
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8765/v1/uim/ollama/chat" -ContentType "application/json" -Body $body
```

Use a model name returned by the health probe. These routes do not enable task execution; `/health` continues to report `execution_enabled: false`. Route tests mock the Ollama provider, so a successful CI run verifies the API contract, not connectivity to your local machine.

## Hosted GPT / OpenAI API worker

The optional hosted GPT worker uses the OpenAI Responses API from the local Unified Hub. It is a separate API worker and **does not connect to or clone the current ChatGPT conversation**.

Configure these environment variables in the process that launches the hub; never commit keys to GitHub:

- `OPENAI_API_KEY`: an API key authorized for the account/project.
- `HF_OPENAI_MODEL`: a model identifier available to that API key.

PowerShell 5.1 example for the current terminal only:

```powershell
$env:OPENAI_API_KEY = Read-Host "Enter OpenAI API key"
$env:HF_OPENAI_MODEL = Read-Host "Enter an API model identifier"
python .\runtime\unified_hub\server.py
```

The key is held in the process environment, not the repository. Avoid putting it directly in command history or sharing terminal output.

- `GET /v1/uim/openai/status` reports `configured_not_probed` when both variables exist. This is a local configuration check, not proof of network or account access.
- `POST /v1/uim/openai/chat` makes a real API request and returns text only.
- `GET /v1/connectors` lists the worker as `not_configured` or `configured_not_probed`; it never claims live connectivity based only on configuration.

Example request:

```powershell
$body = @{
    messages = @(@{ role = "user"; content = "Reply with GPT_WORKER_READY" })
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8765/v1/uim/openai/chat" -ContentType "application/json" -Body $body
```

Hosted requests may incur API charges and transmit submitted message content to OpenAI. Do not send private data unless the applicable data-handling policy permits it. API calls are separate from ChatGPT subscription access. Model output is returned as text and is never executed as a command by these routes. Task execution remains disabled.

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
