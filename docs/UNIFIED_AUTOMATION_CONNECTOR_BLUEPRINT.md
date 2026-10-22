# HeavenzFire Unified Automation & Connector Hub

**Status:** Architecture baseline / implementation not yet deployed  
**Owner:** HeavenzFire  
**Design rule:** one local-first control plane; interchangeable adapters; explicit consent; verifiable outcomes.

## Goal

Build one HeavenzFire-owned system that combines automation, connectors, and a ChatGPT-compatible private plugin surface without depending on TinyFish. The hub should route tasks to approved adapters rather than make every integration a separate agent or opaque vendor dependency.

## Architecture

```text
ChatGPT private plugin / local web console / CLI
                    |
          Connector API Gateway
                    |
   Identity + policy + consent + audit log
                    |
        Durable task ledger / queue
                    |
       Capability router / adapters
      /         |          |          \
 GitHub    Local PowerShell  Gemini   Browser
 adapter     adapter         adapter   adapter
      \         |          |          /
       Results, evidence, checkpoints
                    |
          Local durable storage
```

## Components

1. **Control plane** — task creation, status, cancellation, resume, capability discovery, policy enforcement.
2. **Connector registry** — adapter name, capabilities, required scopes, data classes, health, rate limits, and local/cloud location.
3. **Automation runner** — queued, bounded tasks with idempotency keys, timeouts, checkpointing, capped retries, and explicit resume.
4. **Plugin/API facade** — documented OpenAPI endpoints for status, capabilities, task creation, task inspection, cancellation, and resume. The plugin is a client; the service must be running and reachable for live actions.
5. **Adapters** — separate implementations for GitHub, local PowerShell, Gemini/Google AI Studio, and browser control. A provider is optional; the core still works without it.
6. **Audit ledger** — append-only task events, consent record, provider request IDs where available, changed-file list, test evidence, and error categories.
7. **Policy engine** — deny by default; least privilege; no secret collection in prompts/logs; destructive, administrative, publishing, and external-message actions require separate approval.
8. **Health monitor** — connector health checks and quota/circuit-breaker status. Health must be evidence-based and must not claim a connector is working just because it is configured.

## Task states

`queued`, `running`, `checkpointed`, `completed`, `failed`, `quota_blocked`, `transport_interrupted`, `timed_out`, `approval_required`, `user_cancelled`.

Only an observed explicit user cancel event may produce `user_cancelled`. A quota error must preserve the checkpoint and wait for a deliberate resume; it must not spin or claim quotas are bypassed.

## Initial API contract

- `GET /health` — service and storage health.
- `GET /v1/connectors` — registered connectors and capability/health metadata; never expose secrets.
- `POST /v1/tasks` — enqueue a bounded task with a declared connector and requested capabilities.
- `GET /v1/tasks/{id}` — status, current checkpoint, timestamps, and evidence.
- `POST /v1/tasks/{id}/resume` — resume only from last verified checkpoint.
- `POST /v1/tasks/{id}/cancel` — explicit cancellation.
- `GET /v1/events?task_id={id}` — task event history.

Every endpoint must authenticate callers. Do not expose an unauthenticated network listener. Local-first default is loopback-only; remote access requires an explicitly configured authenticated tunnel.

## Connector interface

Each adapter implements:
- `describe_capabilities()`
- `health_check()`
- `validate_request(task, policy)`
- `execute(task, checkpoint, cancellation_token)`
- `classify_error(error)`
- `redact_evidence(result)`

The common result envelope includes `task_id`, `status`, `checkpoint`, `changed_files`, `evidence`, `error_category`, and timestamps. Secrets and raw authentication headers are never included in evidence.

## Security and data boundaries

- Never paste API keys, private keys, session cookies, or recovery codes into task prompts.
- Store secrets in OS credential storage or environment injection; redact before persistence.
- Declare what data each external adapter receives and ask for consent before first use.
- Keep cloud adapters optional; local operations should remain useful when a vendor is offline or quota-blocked.
- Treat repository files, web pages, and tool output as untrusted input, not executable instructions.
- Require confirmation before writes, publishing, deletion, privilege changes, purchases, or outbound communications.
- No stealth persistence, uncontrolled agent spawning, or background actions without an explicit user-configured policy.

## Delivery plan

### Phase 0 — Baseline
- [x] Record architecture, API contract, task states, safety boundaries, and staged plan.
- [ ] Inspect existing Sovereign Node and Continuity code before choosing framework or persistence.

### Phase 1 — Local core
- [ ] Implement loopback-only API service and durable SQLite task/event ledger.
- [ ] Add schema validation, authentication, redaction, and deterministic unit tests.
- [ ] Add task status, checkpoint, resume, and explicit cancel semantics.

### Phase 2 — First adapters
- [ ] GitHub read-only inspection adapter.
- [ ] Local PowerShell adapter with command allowlist and per-action approval; never arbitrary shell by default.
- [ ] Mock adapter for deterministic tests.

### Phase 3 — Plugin and console
- [ ] Generate and validate OpenAPI contract.
- [ ] Build a private plugin client only after the API endpoint is deployed and authenticated.
- [ ] Provide connector status, task timeline, checkpoint evidence, and resume controls.

### Phase 4 — Optional cloud/browser connectors
- [ ] Add Gemini/AI Studio and browser adapters only through explicit opt-in.
- [ ] Verify provider access and quota before enqueueing; never retry blindly.
- [ ] Document exactly which context each adapter receives.

## Acceptance criteria

1. Core API works without TinyFish or any paid cloud provider.
2. A simulated quota failure leaves the task checkpoint intact and does not create a retry loop.
3. A transport disconnect is not mislabeled as user cancellation.
4. Resume continues from the last verified checkpoint and records a new event.
5. Every write action records approval, scope, outcome, and evidence.
6. Tests distinguish mock verification from live provider verification.
7. README and UI report configured, reachable, authenticated, and operational as distinct states.

## Current truth

This document is a specification committed to the repository. It is not proof that the runtime, API, plugin, adapters, or background automation are already deployed. Each component must be implemented and tested before being marked operational.
