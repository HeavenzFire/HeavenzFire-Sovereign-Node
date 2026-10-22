# Unified Intelligence Model (UIM)
## Capability architecture and implementation specification

**Status:** Draft specification  
**Project:** HeavenzFire Unified Field  
**Repository:** `HeavenzFire/HeavenzFire-Sovereign-Node`  
**Principle:** Capability convergence without provider lock-in or uncontrolled autonomy.

## 1. Mission

Build a single, model-agnostic intelligence runtime that can select and combine the strongest available capabilities from LLMs, coding agents, research assistants, multimodal systems, and automation tools. UIM is a software architecture and orchestration layer; it does not magically transfer proprietary model weights, private training, or inaccessible features into one model.

The runtime should choose the smallest reliable set of capabilities that completes the user's task, prefer local resources when adequate, use external services only when authorized and useful, and preserve evidence of what actually happened.

## 2. Design principles

1. **Capability over brand:** route by measured task performance and declared tool support, not model reputation.
2. **Local-first, offline-tolerant:** local Ollama-compatible models and local tools are first-class; remote providers are optional adapters.
3. **No false capability claims:** distinguish implemented, configured, connected, authorized, executed, and verified.
4. **Provider-neutral core:** no business logic depends on one provider's message format, agent loop, or proprietary tool schema.
5. **Composable, not monolithic:** stable interfaces, small modules, versioned contracts, explicit dependencies.
6. **Least privilege:** tools receive task-scoped permissions; read, write, network, secrets, and destructive actions are separate scopes.
7. **Human control for consequential actions:** approval gates for publishing, spending, credential use, external data transfer, destructive changes, and privilege escalation.
8. **Auditable execution:** every task has an ID, plan, tool calls, outputs, approvals, timing, costs where available, and verification results.
9. **Graceful degradation:** unavailable provider, quota exhaustion, network failure, or model mismatch must produce a useful fallback or a clear blocker.
10. **Reproducible quality:** evaluate against a versioned task suite; do not accept self-reported model quality as proof.
11. **Data minimization:** send only the context needed to a provider; redact secrets and support local-only policies.
12. **No uncontrolled self-replication:** agents and workers are bounded by concurrency, budget, tool scopes, deadlines, and cancellation.

## 3. Capability portfolio

UIM should expose capabilities through interfaces. Not every provider or model will implement every interface.

| Capability domain | Required interface | Initial implementation direction |
|---|---|---|
| General reasoning and dialogue | `Model.generate` | Ollama/local model plus optional remote provider adapters |
| Model selection and fallback | `Router.select` | Rules first; benchmark-informed routing later |
| Planning and decomposition | `Planner.plan` | Structured task graph with success criteria |
| Tool/function calling | `Tool.invoke` | JSON-schema validated calls and bounded retries |
| Coding and repository work | `Workspace.read/write/test` | Git, tests, patch review, diff verification |
| Web research and citations | `Research.search/fetch/cite` | Source-backed retrieval with freshness and provenance |
| Browser and desktop control | `Computer.observe/act` | Allow-listed, isolated sessions; screenshot/state checks |
| Sandboxed execution | `Sandbox.run` | Time, memory, filesystem, network, and process limits |
| Retrieval and durable knowledge | `Memory.search/store` | Local index, source links, expiry, user-controlled deletion |
| Vision and document understanding | `Vision.inspect` | Image/PDF/document adapters with provenance |
| Speech and real-time interaction | `Audio.transcribe/speak/stream` | Pluggable ASR/TTS and streaming transports |
| Image/media generation | `Media.generate/edit` | Optional providers; preserve output metadata and rights notes |
| Multi-agent collaboration | `Team.delegate/review` | Specialist roles with bounded parallelism and independent review |
| Structured data and analytics | `Data.query/analyze` | Sandboxed Python/SQL adapters and reproducible outputs |
| External integrations | `Connector` | Versioned connectors with OAuth/token isolation and health checks |
| Long-running jobs | `Task.enqueue/resume/cancel` | Durable queue, checkpoints, idempotency, cancellation |
| Policy and approval | `Policy.evaluate/approve` | Deny-by-default scopes and explicit approval records |
| Observability | `Trace.record` | Structured logs, traces, latency, cost, failures, and audit events |
| Evaluation | `Eval.run/report` | Regression, tool-use, security, latency, and cost tests |

## 4. Reference architecture

```text
User / CLI / IDE / Chat UI
          |
    UIM API + Session
          |
 Policy Engine ---- Approval Broker
          |
 Task Planner / Durable Orchestrator
          |
 Capability Router ---- Memory / Retrieval
          |
 Model Gateway (local and remote adapters)
          |
 Tool Gateway (typed contracts, allow-lists)
          |
 Sandboxes / Git / Browser / Data / Connectors
          |
 Verification + Evidence Ledger + Metrics
```

### Component boundaries

- **API/session:** authenticated entry points, request validation, cancellation, streaming.
- **Planner:** produces a bounded task graph with inputs, expected outputs, risk classification, and acceptance tests.
- **Policy engine:** checks actor, task, resource, data classification, action, and approval requirements before execution.
- **Router:** selects a model/tool by task needs, availability, local-only requirements, quality history, latency, and cost ceiling.
- **Model gateway:** translates UIM's canonical request/response schema to provider-specific APIs and normalizes tool calls, errors, usage, and streaming.
- **Tool gateway:** validates schemas, enforces scopes, applies timeouts/rate limits, and records invocation evidence.
- **Orchestrator:** durable queue, checkpoints, retries only when safe, idempotency keys, cancellation, and recovery.
- **Verification:** independently checks task acceptance criteria; a generated success message alone is not verification.
- **Evidence ledger:** append-only task events with timestamps, input/output hashes where appropriate, tool versions, approvals, and outcome.
- **Capability registry:** reports each feature as `implemented`, `configured`, `connected`, `authorized`, `tested`, or `unavailable`. These states must never be conflated.

## 5. Canonical contracts

Every adapter must implement a small versioned contract rather than exposing provider-specific internals.

### Model adapter

- `id`, `provider`, `model`, `capabilities`, `context_limit` (if known), `locality`, `health`
- `generate(request, policy_context) -> response`
- normalized content blocks: text, image reference, audio reference, structured data, tool call
- normalized errors: authentication, quota, unsupported capability, timeout, unavailable, invalid request
- usage/cost metadata is optional and explicitly marked unknown when unavailable

### Tool adapter

- `id`, `version`, `input_schema`, `output_schema`, `required_scopes`, `risk_class`
- `validate(input)`, `invoke(input, execution_context)`, `health()`
- every invocation receives a deadline, cancellation token, task ID, policy decision, and audit context
- tool output is untrusted data; it cannot override system policy or grant permissions

### Task record

- task ID, owner, created/updated timestamps, goal, plan, state, deadline
- risk/data classification, budget ceilings, selected adapters, approval records
- checkpoints, retry/idempotency metadata, output references, verification results
- terminal state: succeeded, failed, blocked, cancelled, or partially_succeeded

## 6. Model and capability routing

Routing must be evidence-based and explainable. A first version should use explicit rules rather than a second model making opaque routing decisions.

1. Enforce user policy first: local-only, allowed providers, data sensitivity, budget, and tool restrictions.
2. Identify the task class and required modalities/tools.
3. Filter models by actual declared capability and current health.
4. Prefer the local model when it meets the quality threshold and local policy permits it.
5. Use a remote model only if permitted and it offers a material benefit.
6. Set per-task latency, token/cost, tool-call, retry, and wall-clock budgets.
7. Retry only transient errors and idempotent actions; do not blindly replay writes.
8. Fall back to a smaller task, alternative adapter, or explicit blocker.
9. Verify the final artifact independently where feasible.
10. Record why the route was chosen and whether it met the acceptance criteria.

Do not treat benchmark scores as universal intelligence rankings. Maintain task-specific evaluations and update routing only when tests justify the change.

## 7. Agent topology

Use roles as configurations over the same runtime, not separate ungoverned services:

- **Coordinator:** owns task graph and final acceptance criteria.
- **Researcher:** retrieves evidence and preserves source provenance.
- **Builder:** edits code or artifacts in an isolated workspace.
- **Verifier:** independently tests claims, outputs, and acceptance criteria.
- **Security reviewer:** checks permissions, secrets, dependencies, and unsafe side effects.
- **Integrator:** reconciles verified changes and prepares the final result.

Parallel work is permitted only for separable tasks. Each worker receives a narrow brief, scoped tools, resource limits, and a deadline. A verifier must not simply repeat the builder's conclusion; it should inspect independent evidence.

## 8. Security, privacy, and consent

- Default to loopback for local services until authenticated remote access is explicitly configured.
- Never expose a local control API to the public internet without authentication, transport protection, and an explicit threat review.
- Keep credentials in an OS credential store or dedicated secret manager; never write tokens to logs, prompts, repositories, or task artifacts.
- Treat retrieved webpages, repository content, emails, documents, tool outputs, and model outputs as untrusted input.
- Use separate read, write, execute, network, publish, billing, and administrative permissions.
- Require approval for destructive actions, public publishing, purchases, account changes, sensitive data transmission, and privilege escalation.
- Provide cancellation, revocation, retention controls, and a clear audit trail.
- Avoid automatic uploads of user files or conversation context to remote providers.
- Do not claim a provider's quota, billing, authentication, or access restrictions have been bypassed.

## 9. Technical-debt controls

- Maintain architecture decision records (ADRs) for consequential choices.
- Keep a provider-independent domain model and isolate translation code in adapters.
- Version public API and adapter contracts; define compatibility tests.
- Use a small dependency budget; justify each new runtime dependency.
- Pin and audit dependencies; generate an SBOM and scan known vulnerabilities in CI.
- Prefer standard protocols and formats; avoid unnecessary proprietary state.
- Set explicit deprecation windows and migration paths.
- Track complexity, duplicate abstractions, flaky tests, adapter drift, and operational burden.
- No framework adoption without a concrete requirement and measurable benefit.
- No speculative microservices before deployment/scale needs justify them.
- Keep documentation and runnable examples aligned with actual implementation status.

## 10. Evaluation and acceptance gates

A capability is not considered delivered until its tests pass.

### Required test groups

- Contract conformance for every adapter.
- Golden tasks for coding, research, structured extraction, planning, and summarization.
- Tool-call schema validity and malformed-output recovery.
- Prompt-injection and untrusted-output tests.
- Permission denial, approval, revocation, and audit-log tests.
- Offline and provider-outage behavior.
- Quota exhaustion, timeout, cancellation, and retry/idempotency behavior.
- Data-leakage and secret-redaction tests.
- Regression tests against previously passing tasks.
- Latency and cost ceilings measured on reproducible workloads.

### Initial release gate

- Core API starts locally and reports truthful health state.
- Task records survive process restart.
- A mock model and mock tool pass contract tests without external credentials.
- No task can execute an unregistered tool.
- Destructive or external side effects are blocked unless policy and approval permit them.
- Every reported success includes verification evidence.
- Documentation lists tested features separately from planned features.

## 11. Phased implementation plan

### Phase 0 — Baseline and contract
- Audit the existing Sovereign Node and unified hub.
- Define schemas, threat model, task states, and capability-state vocabulary.
- Add architecture decision records and a test harness.
- Deliverable: reviewed spec plus executable contract tests.

### Phase 1 — Local core
- Harden the loopback API, durable task queue, event log, cancellation, and health checks.
- Add mock model/tool adapters and deterministic routing.
- Deliverable: working local orchestration with no provider credentials required.

### Phase 2 — Local model and workspace
- Add Ollama-compatible adapter, repository/workspace adapter, isolated command runner, and test verification.
- Deliverable: a bounded coding task that can be run and verified locally.

### Phase 3 — Research and connectors
- Add source-cited retrieval, GitHub, and opt-in provider adapters.
- Deliverable: capability-aware research and repository workflows with audit records.

### Phase 4 — Multimodal and computer use
- Add image/document/audio interfaces and an isolated browser/desktop driver.
- Deliverable: explicitly authorized multimodal tasks with observation-after-action verification.

### Phase 5 — Specialist agents
- Add bounded delegation, independent review, checkpoint recovery, and concurrency budgets.
- Deliverable: measured improvement over a single-agent baseline without uncontrolled task spawning.

### Phase 6 — Continuous evaluation
- Run regression/security/performance suites and produce release reports.
- Deliverable: evidence-backed capability matrix and versioned release criteria.

## 12. Current implementation status

This document is a specification, not proof that these capabilities are already implemented.

Previously committed in this repository is a Python standard-library unified hub scaffold with a loopback HTTP API, SQLite task/event persistence, connector registry, and execution deliberately disabled. It has not been established by this document as production-ready or fully tested. The first implementation task is to audit and test that scaffold before adding autonomous execution.

Maintain a status matrix with evidence links for every feature:
- **Planned:** described, not implemented.
- **Implemented:** code exists.
- **Tested:** relevant automated tests pass.
- **Configured:** runtime settings are present.
- **Connected:** external endpoint/account is reachable.
- **Authorized:** explicit policy permits the operation.
- **Verified:** end-to-end acceptance test passed.
- **Blocked:** exact reason and required next action are recorded.

## 13. Definition of success

UIM succeeds when it completes real tasks more reliably, transparently, and economically than a collection of disconnected agents; works locally when remote services are unavailable; can change model/provider without rewriting core logic; prevents unauthorized side effects; and provides evidence for its claims.

The goal is not maximum feature count. The goal is maximum verified capability per unit of complexity, cost, risk, and maintenance.
