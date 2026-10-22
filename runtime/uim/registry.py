"""Minimal standard-library capability registry for the HeavenzFire UIM.

This module reads declarations; it does not probe or connect to providers.
A manifest entry is not proof that a service is configured, connected, or tested.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path(__file__).resolve().with_name("capability_registry.json")
VALID_STATUSES = {
    "planned", "implemented", "tested", "configured", "connected",
    "authorized", "verified", "blocked", "unavailable",
}


class RegistryError(ValueError):
    """Raised when a registry cannot be trusted as a valid declaration."""


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Cannot load capability registry: {exc}") from exc

    if not isinstance(data, dict) or data.get("schema_version") != "1.0.0":
        raise RegistryError("Unsupported or missing registry schema_version")
    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list):
        raise RegistryError("capabilities must be a list")

    seen: set[str] = set()
    for item in capabilities:
        if not isinstance(item, dict):
            raise RegistryError("Each capability must be an object")
        capability_id = item.get("id")
        status = item.get("status")
        if not isinstance(capability_id, str) or not capability_id.strip():
            raise RegistryError("Every capability requires a non-empty id")
        if capability_id in seen:
            raise RegistryError(f"Duplicate capability id: {capability_id}")
        seen.add(capability_id)
        if status not in VALID_STATUSES:
            raise RegistryError(f"Invalid status for {capability_id}: {status!r}")
        if status in {"connected", "authorized", "verified"} and not item.get("evidence"):
            raise RegistryError(
                f"{capability_id} claims {status!r} without an evidence field"
            )
    return data


def get_capability(capability_id: str, path: Path = REGISTRY_PATH) -> dict[str, Any] | None:
    """Return a copy of a capability record, or None if it is not registered."""
    for item in load_registry(path)["capabilities"]:
        if item["id"] == capability_id:
            return dict(item)
    return None


def list_capabilities(
    *,
    kind: str | None = None,
    statuses: set[str] | None = None,
    path: Path = REGISTRY_PATH,
) -> list[dict[str, Any]]:
    """Filter declarations; does not imply live availability."""
    if statuses is not None and not statuses.issubset(VALID_STATUSES):
        raise RegistryError(f"Unknown statuses: {sorted(statuses - VALID_STATUSES)}")
    items = load_registry(path)["capabilities"]
    return [
        dict(item)
        for item in items
        if (kind is None or item.get("kind") == kind)
        and (statuses is None or item.get("status") in statuses)
    ]


def route_candidates(
    required_capabilities: set[str],
    *,
    path: Path = REGISTRY_PATH,
) -> list[dict[str, Any]]:
    """Return only registered, tested/verified candidates; implementation alone is not routable.

    The initial seed contains declarations rather than executable model adapters,
    so this function intentionally returns no candidate for unimplemented IDs.
    A future router must additionally check health, policy, locality, budget,
    modality support, and task-specific evaluation scores before invocation.
    """
    if not required_capabilities:
        return []
    items = load_registry(path)["capabilities"]
    by_id = {item["id"]: item for item in items}
    if not required_capabilities.issubset(by_id):
        return []
    eligible = {"tested", "verified"}
    candidates = [by_id[item_id] for item_id in sorted(required_capabilities)]
    if any(item.get("status") not in eligible for item in candidates):
        return []
    return [dict(item) for item in candidates]
