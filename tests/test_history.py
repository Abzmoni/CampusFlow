import unittest
from datetime import datetime, timezone

from campusflow.history import record_event, get_ticket_history


class TestHistory(unittest.TestCase):

    def setUp(self):
        self.events = []

        self.now = datetime(
            2026, 10, 14, 10, 0,
            tzinfo=timezone.utc
        )

    # Test 1: Record a successful event
    def test_record_event(self):
        event = record_event(
            self.events,
            "T001",
            "CREATE",
            "Admin",
            None,
            "open",
            "Ticket created",
            self.now
        )

        self.assertEqual(event["event_id"], "E001")
        self.assertEqual(len(self.events), 1)

    # Test 2: Generate unique event IDs
    def test_unique_event_ids(self):
        for _ in range(2):
            record_event(
                self.events,
                "T001",
                "ASSIGN",
                "Admin",
                "open",
                "open",
                "Staff assigned",
                self.now
            )

        ids = [event["event_id"] for event in self.events]

        self.assertEqual(ids, ["E001", "E002"])

    # Test 3: Retrieve history for one ticket
    def test_ticket_history(self):
        record_event(
            self.events,
            "T001",
            "CREATE",
            "Admin",
            None,
            "open",
            "Created",
            self.now
        )

        record_event(
            self.events,
            "T002",
            "CREATE",
            "Admin",
            None,
            "open",
            "Created",
            self.now
        )

        history = get_ticket_history(self.events, "T001")

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["ticket_id"], "T001")

    # Test 4: Invalid actor must not create an event
    def test_invalid_actor(self):
        with self.assertRaises(ValueError):
            record_event(
                self.events,
                "T001",
                "CREATE",
                "",
                None,
                "open",
                "Created",
                self.now
            )

        self.assertEqual(self.events, [])

    # Test 5: Timestamp uses UTC
    def test_utc_timestamp(self):
        event = record_event(
            self.events,
            "T001",
            "CREATE",
            "Admin",
            None,
            "open",
            "Created",
            self.now
        )

        self.assertEqual(
            event["timestamp"],
            "2026-10-14T10:00:00+00:00"
        )

    # Test 6: Returned history cannot change saved events
    def test_history_does_not_modify_events(self):
        record_event(
            self.events,
            "T001",
            "CREATE",
            "Admin",
            None,
            "open",
            "Created",
            self.now
        )

        history = get_ticket_history(self.events, "T001")

        history[0]["actor"] = "Changed"

        self.assertEqual(self.events[0]["actor"], "Admin")


if __name__ == "__main__":
    unittest.main()