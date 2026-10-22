# Windows Control Relay — Architecture Decision Record

Status: design accepted; local connectivity not yet established
Date: 2026-10-22
Scope: ChatGPT-assisted, PowerShell 5.1-compatible operations on an authorized Windows workstation.

## Decision

Do not use an unauthenticated `HttpListener` that accepts arbitrary command strings and passes them to `Invoke-Expression`. Do not expose raw RDP, VNC, or a PowerShell listener to the public internet. A hosted ChatGPT Action cannot call the workstation's `localhost`; localhost is relative to the caller.

GitHub may be used as a control/development plane, but **this public repository must not be used as a live command queue or result channel**. Task payloads, host diagnostics, tokens, paths, and command output may contain private information. A live relay requires a separate private control plane or a dedicated authenticated tunnel.

## Target topology

1. ChatGPT prepares a structured task request; it does not receive a general shell.
2. The request is stored in a private control plane, or sent through an authenticated private API.
3. A Windows-side agent initiates outbound HTTPS polling; no inbound workstation port is opened.
4. The agent validates a strict task schema, a unique task ID, expiration, allowed operation, and replay protection.
5. Read-only operations can run from a fixed local allowlist.
6. Mutating, administrative, network, credential, and destructive actions require a distinct local approval step.
7. The agent records timestamp, task ID, operation name, approval decision, exit status, and redacted summary.
8. The result is returned only to the private control plane. Secrets and raw environment dumps are never returned.
9. The service runs as a standard user and is stopped/disabled with one explicit command.
10. Every task and result is correlated by ID; retries are idempotent.

## GitHub-specific guardrails

- The repository `HeavenzFire/HeavenzFire-Sovereign-Node` is public. Never put a live task queue, machine output, API key, PAT, private path inventory, or sensitive diagnostic in it.
- A GitHub self-hosted runner is not a safe general-purpose bridge by itself: workflow code can execute on the host. Never allow untrusted pull-request workflows to run on a workstation runner. Use a dedicated, least-privilege runner only for reviewed, fixed workflows if that design is selected.
- Prefer a dedicated **private** control repository or authenticated tunnel for private task envelopes and results. Use a fine-grained credential with the narrowest possible permissions; store it locally, not in the repository.
- Require explicit approval before running any operation that changes state. Repository ownership or a model response is not a substitute for local approval.

## Initial operation allowlist

The first implementation should expose only read-only diagnostics such as:
- hub health and connector status;
- disk free-space summary (drive, total bytes, free bytes only);
- selected service status;
- selected process names and IDs;
- Git status for a configured workspace.

Do not add arbitrary PowerShell, `Invoke-Expression`, `Start-Process` with caller-controlled arguments, unrestricted file reads, credential export, registry writes, firewall changes, or deletion to the initial allowlist.

## Acceptance gates

The relay is **not connected** until all gates pass:

- [ ] Local agent installed and its exact path recorded.
- [ ] Agent binds no inbound network listener.
- [ ] Private transport authentication and expiration/replay tests pass.
- [ ] Unknown operation, malformed payload, expired task, duplicate task, and missing approval are rejected.
- [ ] Command arguments cannot be injected through task fields.
- [ ] Logs redact tokens and sensitive output.
- [ ] Stop/disable procedure is tested.
- [ ] End-to-end smoke test reports a generated task ID, the local agent's result, and an auditable event.
- [ ] No claim of connectivity is made based solely on GitHub commits or CI.

## Current verified state

The Unified Hub starter currently persists tasks and events but reports `execution_enabled: false`. Its default listener is loopback-only. The optional OpenAI API adapter is a separate hosted API integration and is not the current ChatGPT session. Neither component, by itself, provides remote Windows execution.

## Next implementation slice

Create and secure a private control plane first. Then implement a PowerShell 5.1 local polling agent with typed operations and a deny-by-default dispatcher. Do not enable a command-string endpoint.
