# HeavenzFire Unified Hub — starter runtime

This directory is the first implementation slice of the local-first automation/connector hub.

## Current capability (verified from source, not live-run here)

- Python standard library only.
- Loopback-only HTTP listener by default (127.0.0.1:8765).
- Durable SQLite task and event ledger (WAL + FULL synchronous commits).
- Task enqueue, inspect, list, event history, explicit cancel, and checkpoint-preserving resume request.
- Connector registry currently lists mock plus unconfigured GitHub, PowerShell, Gemini, and browser adapters.
- Optional bearer token via HF_HUB_TOKEN.
- Explicitly does not execute tasks yet. It records tasks for the next implementation phase. The /health response exposes execution_enabled: false.

## Run on Windows PowerShell 5.1

From a checked-out copy of this repository:

    Set-Location .\runtime\unified_hub
    $env:HF_HUB_HOST = '127.0.0.1'
    $env:HF_HUB_PORT = '8765'
    # Optional for local development; if set, clients must send Authorization: Bearer <token>.
    # Do not commit the token or place it in prompts.
    $env:HF_HUB_TOKEN = [guid]::NewGuid().ToString('N')
    python .\server.py

In a second PowerShell window, use the configured token:

    $token = 'PASTE_THE_TOKEN_FROM_THE_SERVER_WINDOW'
    Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8765/health'
    Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8765/v1/connectors' -Headers @{ Authorization = "Bearer $token" }
    $task = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8765/v1/tasks' -Headers @{ Authorization = "Bearer $token" } -ContentType 'application/json' -Body (@{ prompt = 'Demonstration task; do not execute'; connector = 'mock' } | ConvertTo-Json)
    $task
    Invoke-RestMethod -Method Get -Uri ("http://127.0.0.1:8765/v1/tasks/" + $task.id) -Headers @{ Authorization = "Bearer $token" }

## Endpoints

- GET /health — local service health; no secrets returned.
- GET /v1/connectors — connector registry.
- GET /v1/tasks — latest 100 tasks.
- GET /v1/tasks/{id} — task and events.
- GET /v1/events?task_id={id} — event timeline.
- POST /v1/tasks — persist a task as queued.
- POST /v1/tasks/{id}/resume — re-queue eligible interrupted tasks.
- POST /v1/tasks/{id}/cancel — record an explicit cancel event.

## Important limitations

- Do not expose this service to the public internet. The starter refuses non-loopback bind addresses.
- This is not yet a ChatGPT plugin and is not yet a production OpenAPI service. A plugin/API facade can be added only after the runtime is deployed behind an authenticated endpoint reachable by the plugin host.
- Connector entries are metadata only until their adapters are implemented and tested.
- There is no worker/executor in this initial slice. Tasks remain queued; no local shell, GitHub write, browser, or model operation is performed.
- Before enabling execution: add strict request schemas, CSRF/origin strategy if a browser UI is added, credential-store integration, rate limiting, bounded worker lifecycle, idempotency, structured redaction, tests, and a security review.
