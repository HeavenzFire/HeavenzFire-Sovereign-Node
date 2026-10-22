#!/usr/bin/env python3
"""Minimal local-first task ledger/API for the HeavenzFire Unified Hub.

Python standard library only. Binds to loopback by default. This is a durable
control-plane starter, not an arbitrary command executor or a production plugin
endpoint. External access must be added only with reviewed authentication/TLS.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
UIM_ROOT = ROOT.parent / "uim"
if str(UIM_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(UIM_ROOT))
from ollama_adapter import OllamaAdapter, OllamaError
from openai_adapter import OpenAIAdapter, OpenAIAdapterError

DB_PATH = Path(os.environ.get("HF_HUB_DB", str(ROOT / "hub.sqlite3")))
HOST = os.environ.get("HF_HUB_HOST", "127.0.0.1")
PORT = int(os.environ.get("HF_HUB_PORT", "8765"))
TOKEN = os.environ.get("HF_HUB_TOKEN", "")
TASK_STATES = {
    "queued", "running", "checkpointed", "completed", "failed",
    "quota_blocked", "transport_interrupted", "timed_out",
    "approval_required", "user_cancelled",
}
CONNECTORS = [
    {"id": "mock", "state": "available", "capabilities": ["test", "simulate_failure"]},
    {"id": "github", "state": "not_configured", "capabilities": ["repository_read", "issue_read"]},
    {"id": "powershell", "state": "not_configured", "capabilities": ["allowlisted_local_command"]},
    {"id": "gemini", "state": "not_configured", "capabilities": ["model_request"]},
    {"id": "browser", "state": "not_configured", "capabilities": ["approved_browser_task"]},
]


def now() -> int:
    return int(time.time())


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.executescript("""
    CREATE TABLE IF NOT EXISTS tasks (
      id TEXT PRIMARY KEY, prompt TEXT NOT NULL, connector TEXT NOT NULL,
      status TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
      checkpoint TEXT NOT NULL DEFAULT '', error_category TEXT NOT NULL DEFAULT '',
      changed_files TEXT NOT NULL DEFAULT '[]', approval_required INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
      at INTEGER NOT NULL, event TEXT NOT NULL, details TEXT NOT NULL DEFAULT '{}',
      FOREIGN KEY(task_id) REFERENCES tasks(id)
    );
    """)
    con.commit()
    return con


def event(con: sqlite3.Connection, task_id: str, name: str, details=None) -> None:
    con.execute("INSERT INTO events(task_id, at, event, details) VALUES(?,?,?,?)",
                (task_id, now(), name, json.dumps(details or {}, ensure_ascii=False)))
    con.commit()


def task_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["changed_files"] = json.loads(d["changed_files"])
    d["approval_required"] = bool(d["approval_required"])
    return d


class Handler(BaseHTTPRequestHandler):
    server_version = "HeavenzFireUnifiedHub/0.1"

    def log_message(self, fmt, *args):
        # Avoid logging request bodies, tokens, or prompt content.
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_json(self, status, value):
        raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 65536:
                raise ValueError("body must be 1..65536 bytes")
            obj = json.loads(self.rfile.read(length))
            if not isinstance(obj, dict):
                raise ValueError("JSON object required")
            return obj
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError("invalid JSON request") from exc

    def authorized(self):
        # Loopback-only development mode can run without a token. If a token is
        # configured, require constant-time comparison for all non-health routes.
        if not TOKEN:
            return self.client_address[0] in ("127.0.0.1", "::1")
        supplied = self.headers.get("Authorization", "")
        return secrets.compare_digest(supplied, "Bearer " + TOKEN)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            return self.send_json(200, {
                "service": "heavenzfire-unified-hub", "version": "0.1",
                "storage": "sqlite", "host": HOST, "authenticated_mode": bool(TOKEN),
                "execution_enabled": False,
            })
        if not self.authorized():
            return self.send_json(401, {"error": "unauthorized"})
        if parsed.path == "/v1/uim/openai/status":
            configured = bool(os.environ.get("OPENAI_API_KEY", "").strip()
                              and os.environ.get("HF_OPENAI_MODEL", "").strip())
            return self.send_json(200, {
                "capability": "uim.openai", "status": "configured_not_probed" if configured else "unconfigured",
                "provider": "openai", "model": os.environ.get("HF_OPENAI_MODEL", "") if configured else None,
                "credential_source": "OPENAI_API_KEY environment variable",
                "evidence": "local environment configuration only; no API request made",
            })
        if parsed.path == "/v1/uim/ollama/health":
            try:
                result = OllamaAdapter().health()
                return self.send_json(200, {
                    "capability": "uim.ollama", "status": "connected",
                    "checked_at": now(), "provider": "ollama", "models": result["models"],
                    "evidence": "live /api/tags probe",
                })
            except OllamaError as exc:
                return self.send_json(503, {
                    "capability": "uim.ollama", "status": "unavailable",
                    "checked_at": now(), "provider": "ollama", "models": [],
                    "error": str(exc),
                })
        if parsed.path == "/v1/connectors":
            connectors = [dict(item) for item in CONNECTORS]
            connectors.append({
                "id": "openai",
                "state": "configured_not_probed" if (
                    os.environ.get("OPENAI_API_KEY", "").strip()
                    and os.environ.get("HF_OPENAI_MODEL", "").strip()
                ) else "not_configured",
                "capabilities": ["model_chat"],
                "status_endpoint": "/v1/uim/openai/status",
                "chat_endpoint": "/v1/uim/openai/chat",
            })
            connectors.append({
                "id": "ollama", "state": "probe_required",
                "capabilities": ["model_inventory", "model_chat"],
                "health_endpoint": "/v1/uim/ollama/health",
            })
            return self.send_json(200, {"connectors": connectors})
        if parsed.path == "/v1/tasks":
            with db() as con:
                rows = con.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 100").fetchall()
            return self.send_json(200, {"tasks": [task_dict(r) for r in rows]})
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 3 and parts[:2] == ["v1", "tasks"]:
            with db() as con:
                row = con.execute("SELECT * FROM tasks WHERE id=?", (parts[2],)).fetchone()
                if not row:
                    return self.send_json(404, {"error": "task_not_found"})
                events = con.execute("SELECT at,event,details FROM events WHERE task_id=? ORDER BY id",
                                     (parts[2],)).fetchall()
            result = task_dict(row)
            result["events"] = [{**dict(e), "details": json.loads(e["details"])} for e in events]
            return self.send_json(200, result)
        if parsed.path == "/v1/events":
            task_id = parse_qs(parsed.query).get("task_id", [""])[0]
            with db() as con:
                rows = con.execute("SELECT at,event,details FROM events WHERE task_id=? ORDER BY id",
                                   (task_id,)).fetchall()
            return self.send_json(200, {"events": [{**dict(r), "details": json.loads(r["details"])} for r in rows]})
        return self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        if not self.authorized():
            return self.send_json(401, {"error": "unauthorized"})
        try:
            body = self.read_json()
        except ValueError as exc:
            return self.send_json(400, {"error": str(exc)})
        path = urlparse(self.path).path
        if path == "/v1/uim/openai/chat":
            messages = body.get("messages")
            try:
                result = OpenAIAdapter().chat(messages)
            except OpenAIAdapterError as exc:
                return self.send_json(502, {
                    "capability": "uim.openai", "status": "request_failed",
                    "error": str(exc), "execution_enabled": False,
                })
            return self.send_json(200, {
                "capability": "uim.openai", "status": "response_received",
                "provider": result["provider"], "model": result["model"],
                "content": result["content"], "response_id": result["response_id"],
                "execution_enabled": False,
            })
        if path == "/v1/uim/ollama/chat":
            model, messages = body.get("model"), body.get("messages")
            try:
                result = OllamaAdapter().chat(model, messages)
            except OllamaError as exc:
                # Keep model output inert: this endpoint returns text only and never executes tools.
                return self.send_json(502, {
                    "capability": "uim.ollama", "status": "request_failed",
                    "error": str(exc), "execution_enabled": False,
                })
            return self.send_json(200, {
                "capability": "uim.ollama", "status": "response_received",
                "provider": result["provider"], "model": result["model"],
                "content": result["content"], "done": result["done"],
                "execution_enabled": False,
            })
        if path == "/v1/tasks":
            prompt = body.get("prompt")
            connector = body.get("connector", "mock")
            if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
                return self.send_json(400, {"error": "prompt must be 1..12000 characters"})
            allowed = {c["id"] for c in CONNECTORS}
            if connector not in allowed:
                return self.send_json(400, {"error": "unknown_connector", "available": sorted(allowed)})
            if connector != "mock" and next(c for c in CONNECTORS if c["id"] == connector)["state"] != "configured":
                return self.send_json(409, {"error": "connector_not_configured", "connector": connector})
            task_id, ts = str(uuid.uuid4()), now()
            approval = 1
            with db() as con:
                con.execute("""INSERT INTO tasks(id,prompt,connector,status,created_at,updated_at,
                    checkpoint,error_category,changed_files,approval_required)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (task_id, prompt.strip(), connector, "queued", ts, ts, "Task accepted; no execution has occurred.", "",
                     "[]", approval))
                event(con, task_id, "task_queued", {"connector": connector, "approval_required": True})
            return self.send_json(201, {"id": task_id, "status": "queued",
                                        "message": "Persisted only; execution is not enabled in this starter."})
        parts = path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["v1", "tasks"] and parts[3] in ("resume", "cancel"):
            task_id, action = parts[2], parts[3]
            with db() as con:
                row = con.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
                if not row:
                    return self.send_json(404, {"error": "task_not_found"})
                if action == "cancel":
                    if row["status"] in ("completed", "failed", "user_cancelled"):
                        return self.send_json(409, {"error": "task_terminal", "status": row["status"]})
                    con.execute("UPDATE tasks SET status='user_cancelled',updated_at=? WHERE id=?", (now(), task_id))
                    event(con, task_id, "explicit_user_cancel", {"source": "api"})
                else:
                    if row["status"] not in ("quota_blocked", "transport_interrupted", "timed_out", "failed", "checkpointed"):
                        return self.send_json(409, {"error": "task_not_resumable", "status": row["status"]})
                    con.execute("UPDATE tasks SET status='queued',updated_at=?,error_category='' WHERE id=?", (now(), task_id))
                    event(con, task_id, "resume_requested", {"checkpoint": row["checkpoint"]})
                con.commit()
                updated = con.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            return self.send_json(200, task_dict(updated))
        return self.send_json(404, {"error": "not_found"})

    def do_OPTIONS(self):
        self.send_json(204, {})


def main():
    if HOST not in ("127.0.0.1", "::1", "localhost"):
        raise SystemExit("Refusing non-loopback bind in starter. Review authentication/TLS before remote access.")
    if not TOKEN:
        print("WARNING: HF_HUB_TOKEN is unset; loopback-only development mode.")
    with db():
        pass
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"HeavenzFire Unified Hub listening on http://{HOST}:{PORT}")
    print(f"SQLite ledger: {DB_PATH}")
    print("Execution is intentionally disabled; queued tasks are persisted but not run.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
