"""Run with: python -m unittest test_registry.py"""
import json
import tempfile
import unittest
from pathlib import Path

from registry import RegistryError, get_capability, list_capabilities, load_registry, route_candidates


class RegistryTests(unittest.TestCase):
    def test_seed_registry_loads_and_has_unique_ids(self):
        data = load_registry()
        ids = [item["id"] for item in data["capabilities"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(data["principles"]["local_first"])

    def test_session_is_not_claimed_as_local_api(self):
        item = get_capability("uim.chatgpt.current_session")
        self.assertIsNotNone(item)
        self.assertEqual(item["scope"], "current_chat_session_only")
        self.assertIn("does not expose", item["description"])

    def test_unimplemented_provider_is_not_routable(self):
        self.assertEqual(route_candidates({"uim.ollama"}), [])

    def test_unknown_capability_is_not_routable(self):
        self.assertEqual(route_candidates({"not.registered"}), [])

    def test_filter_by_kind_and_status(self):
        items = list_capabilities(kind="model_adapter", statuses={"implemented"})
        self.assertTrue(items)
        self.assertTrue(all(item["status"] == "implemented" for item in items))

    def test_duplicate_ids_rejected(self):
        data = {
            "schema_version": "1.0.0",
            "capabilities": [
                {"id": "same", "status": "planned"},
                {"id": "same", "status": "planned"}
            ]
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "registry.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(RegistryError):
                load_registry(path)

    def test_connection_claim_requires_evidence(self):
        data = {
            "schema_version": "1.0.0",
            "capabilities": [{"id": "fake", "status": "connected"}]
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "registry.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(RegistryError):
                load_registry(path)


if __name__ == "__main__":
    unittest.main()
