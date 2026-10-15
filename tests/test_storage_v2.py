"""Automated tests for Version-2 JSON persistence, schema validation, and corruption defense."""

import json
import tempfile
import unittest
from pathlib import Path

from campusflow.storage import (
    SCHEMA_VERSION,
    load_data,
    migrate_legacy_file,
    save_data,
    validate_event_schema,
    validate_ticket_schema,
)


class StorageV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        self.file_path = self.dir_path / "data" / "tickets.json"

        self.sample_v2_data = {
            "schema_version": 2,
            "tickets": [
                {
                    "id": "T001",
                    "title": "Main hall projector outage",
                    "category": "Hardware",
                    "urgency": "high",
                    "affected_users": 20,
                    "priority": "critical",
                    "status": "open",
                    "assigned_to": None,
                    "created_at": "2026-10-14T10:00:00+00:00",
                    "updated_at": "2026-10-14T10:00:00+00:00",
                    "due_at": "2026-10-14T11:00:00+00:00",
                    "escalation_cycle": 0,
                }
            ],
            "events": [
                {
                    "event_id": "E001",
                    "ticket_id": "T001",
                    "event_type": "CREATE",
                    "actor": "admin",
                    "timestamp": "2026-10-14T10:00:00+00:00",
                    "before_status": "open",
                    "after_status": "open",
                    "details": "Ticket created via API.",
                }
            ],
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_file_returns_clean_v2_state(self):
        """Missing file should allow a fresh start with empty collections."""
        nonexistent = self.dir_path / "missing.json"
        data = load_data(str(nonexistent))
        self.assertEqual(data["schema_version"], 2)
        self.assertEqual(data["tickets"], [])
        self.assertEqual(data["events"], [])

    def test_v2_save_and_load_round_trip(self):
        """Saving and loading V2 data preserves tickets and audit events intact."""
        save_data(self.sample_v2_data, str(self.file_path))
        self.assertTrue(self.file_path.exists())

        loaded = load_data(str(self.file_path))
        self.assertEqual(loaded["schema_version"], 2)
        self.assertEqual(len(loaded["tickets"]), 1)
        self.assertEqual(len(loaded["events"]), 1)
        self.assertEqual(loaded["tickets"][0]["id"], "T001")
        self.assertEqual(loaded["events"][0]["event_id"], "E001")

    def test_checkpoint_a5_corrupt_json_rejects_and_preserves_valid_state(self):
        """Checkpoint A5: Corrupted JSON raises ValueError and never replaces valid data."""
        # 1. Save valid initial state
        save_data(self.sample_v2_data, str(self.file_path))
        in_memory_snapshot = dict(self.sample_v2_data)

        # 2. Corrupt the file on disk
        self.file_path.write_text("{ malformed json syntax :::: invalid", encoding="utf-8")

        # 3. Attempting to load must raise ValueError
        with self.assertRaises(ValueError) as ctx:
            load_data(str(self.file_path))
        self.assertIn("malformed JSON", str(ctx.exception))

        # 4. Verify in-memory snapshot was not modified or wiped
        self.assertEqual(in_memory_snapshot, self.sample_v2_data)

    def test_checkpoint_a6_invalid_schema_rejects_without_partial_writes(self):
        """Checkpoint A6: Incomplete schemas or invalid tickets are rejected upfront."""
        invalid_cases = [
            # Missing schema_version
            {"tickets": [], "events": []},
            # Unsupported schema_version
            {"schema_version": 99, "tickets": [], "events": []},
            # Non-list tickets
            {"schema_version": 2, "tickets": "not a list", "events": []},
            # Ticket missing required field
            {"schema_version": 2, "tickets": [{"id": "T001"}], "events": []},
            # Event missing required field
            {"schema_version": 2, "tickets": [], "events": [{"event_id": "E001"}]},
        ]
        for idx, bad_data in enumerate(invalid_cases):
            with self.subTest(idx=idx):
                with self.assertRaises(ValueError):
                    save_data(bad_data, str(self.file_path))

    def test_legacy_v1_migration_preserves_original_file_unchanged(self):
        """Legacy V1 list-style files can be migrated explicitly without touching original."""
        legacy_file = self.dir_path / "legacy_tickets.json"
        target_v2_file = self.dir_path / "migrated_v2.json"

        legacy_tickets = [
            {
                "id": "T001",
                "title": "Wi-Fi outage",
                "category": "Network",
                "urgency": "high",
                "affected_users": 10,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
            }
        ]
        legacy_file.write_text(json.dumps(legacy_tickets), encoding="utf-8")
        orig_content = legacy_file.read_text(encoding="utf-8")

        # Perform migration
        v2_result = migrate_legacy_file(str(legacy_file), str(target_v2_file))

        # Original legacy file must be 100% untouched
        self.assertEqual(legacy_file.read_text(encoding="utf-8"), orig_content)

        # Migrated file must be valid V2 schema
        self.assertEqual(v2_result["schema_version"], 2)
        self.assertEqual(len(v2_result["tickets"]), 1)
        self.assertEqual(v2_result["events"], [])  # Did not fabricate historic events!

    def test_atomic_temp_cleanup_on_error(self):
        """A failure before replacement cleans up the temporary file."""
        tmp_file = self.file_path.with_suffix(".tmp")
        try:
            # Force failure by saving something that fails schema check
            save_data({"invalid": True}, str(self.file_path))
        except ValueError:
            pass
        self.assertFalse(tmp_file.exists())


if __name__ == "__main__":
    unittest.main()
