# HeavenzFire Unified Intelligence Model (UIM)

UIM is the capability registry and routing foundation for the Unified Field. This first slice adds a validated capability registry and tests. It does not yet connect models or execute tasks.

## The assistant integration boundary

The assistant in the current ChatGPT session can use tools exposed to this session. That is not the same as exposing this exact live conversation or its internal model as an API callable by a local Python process. The registry records this distinction explicitly.

To let the local UIM call a model, configure a supported API adapter with credentials that the user intentionally supplies or authorizes. This creates a provider-backed model endpoint; it does **not** make the current ChatGPT session itself callable. Never attempt to extract session cookies, hidden credentials, internal endpoints, or browser tokens.

Likewise, GitHub, browser, and desktop integrations available in a ChatGPT session do not automatically pass their credentials or permissions into the local UIM runtime. Each local connector requires its own explicit configuration, least-privilege credentials, and tests.

## Capability status vocabulary

- `planned`: design only.
- `implemented`: source code exists.
- `tested`: a named test suite passed.
- `configured`: required local settings are present.
- `connected`: a live health check succeeded.
- `authorized`: policy and consent permit the operation.
- `verified`: an end-to-end acceptance test passed.
- `blocked`: a specific blocker is recorded.
- `unavailable`: the capability cannot currently be used.

Do not promote a status from a declaration alone. Keep test output, health-check timestamps, and evidence links alongside runtime status.

## Files

- `capability_registry.json`: seed capability inventory; it is not live discovery.
- `registry.py`: standard-library registry validator and filter.
- `test_registry.py`: registry contract tests.

## Test on Windows PowerShell 5.1

From the repository root:

```powershell
Set-Location .\runtime\uim
python -m unittest .\test_registry.py -v
if ($LASTEXITCODE -ne 0) { throw "UIM registry tests failed" }
```

The tests require a compatible Python 3.10+ runtime for built-in generic annotations. Python 3.12 is suitable.

## Next integration order

1. Run and record registry tests on the user's Windows machine.
2. Add runtime health probes with explicit timeouts and redacted results.
3. Implement an Ollama adapter and verify the local endpoint/model inventory.
4. Implement the model gateway and task-specific routing policies.
5. Add a scoped GitHub adapter using separate credentials; begin read-only.
6. Add the allow-listed PowerShell runner and isolated browser adapter.
7. Connect approval records, task ledger, cancellation, idempotency, and independent verification.
8. Only then enable bounded task execution.

## Security requirements

- Bind local services to loopback by default.
- Never commit tokens or copy ChatGPT/browser credentials into this runtime.
- Do not accept arbitrary shell commands or arbitrary URLs from model output.
- Require explicit approval for destructive operations, publishing, spending, credential use, sensitive data transfer, and privilege escalation.
- Treat model output, repository files, webpages, and connector results as untrusted input.
- Never claim a queued task ran; execution requires an executor and verifiable output.
