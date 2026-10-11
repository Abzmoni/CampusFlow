"""Unit tests for JSON persistence module."""
import json
import tempfile
import unittest
from pathlib import Path

from campusflow.storage import load_tickets, save_tickets


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        self.file_path = self.dir_path / "data" / "tickets.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_nonexistent_file_returns_empty_list(self):
        nonexistent = self.dir_path / "nonexistent.json"
        tickets = load_tickets(str(nonexistent))
        self.assertEqual(tickets, [])

    def test_save_and_load_round_trip(self):
        sample_tickets = [
            {
                "id": "T001",
                "title": "Wi-Fi outage",
                "category": "Network",
                "urgency": "high",
                "affected_users": 15,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
            },
            {
                "id": "T002",
                "title": "Broken screen",
                "category": "Hardware",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
            },
        ]
        save_tickets(sample_tickets, str(self.file_path))
        self.assertTrue(self.file_path.exists())

        loaded = load_tickets(str(self.file_path))
        self.assertEqual(loaded, sample_tickets)

    def test_load_malformed_json_raises_value_error(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text("{ malformed json content ...", encoding="utf-8")

        with self.assertRaises(ValueError) as ctx:
            load_tickets(str(self.file_path))
        self.assertIn("malformed JSON", str(ctx.exception))

    def test_load_non_list_json_raises_value_error(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(json.dumps({"not_a": "list"}), encoding="utf-8")

        with self.assertRaises(ValueError) as ctx:
            load_tickets(str(self.file_path))
        self.assertIn("expected a list of tickets", str(ctx.exception))

    def test_save_rejects_non_list(self):
        for invalid in [None, {}, "string", 123]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError) as ctx:
                    save_tickets(invalid, str(self.file_path))
                self.assertIn("must be a list", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
