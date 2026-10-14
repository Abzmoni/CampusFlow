import unittest

from copy import deepcopy
from datetime import datetime, timezone

from campusflow.audited_workflow import assign_with_history


class TestAuditedWorkflow(unittest.TestCase):

    def setUp(self):

        self.tickets = [
            {
                "id": "T001",
                "status": "open",
                "assigned_to": None
            }
        ]

        self.events = []

        self.now = datetime(
            2026, 10, 14, 10, 0,
            tzinfo=timezone.utc
        )

    # Test 1: Successful assignment records an event
    def test_successful_assignment(self):

        result = assign_with_history(
            self.tickets,
            self.events,
            "T001",
            "John",
            "Admin",
            self.now
        )

        self.assertEqual(result["assigned_to"], "John")

        self.assertEqual(len(self.events), 1)

        self.assertEqual(
            self.events[0]["event_type"],
            "ASSIGN"
        )

        self.assertEqual(
            self.events[0]["actor"],
            "Admin"
        )

        self.assertEqual(
            self.events[0]["before_status"],
            "open"
        )

        self.assertEqual(
            self.events[0]["after_status"],
            "open"
        )

    # Test 2: Invalid ticket changes nothing
    def test_invalid_ticket(self):

        original_tickets = deepcopy(self.tickets)
        original_events = deepcopy(self.events)

        with self.assertRaises(ValueError):

            assign_with_history(
                self.tickets,
                self.events,
                "T999",
                "John",
                "Admin",
                self.now
            )

        self.assertEqual(self.tickets, original_tickets)
        self.assertEqual(self.events, original_events)

    # Test 3: Invalid actor changes nothing
    def test_invalid_actor(self):

        original_tickets = deepcopy(self.tickets)
        original_events = deepcopy(self.events)

        with self.assertRaises(ValueError):

            assign_with_history(
                self.tickets,
                self.events,
                "T001",
                "John",
                "",
                self.now
            )

        self.assertEqual(self.tickets, original_tickets)
        self.assertEqual(self.events, original_events)

    # Test 4: Invalid event history changes nothing
    def test_invalid_existing_event(self):

        self.events = [{"event_id": "invalid"}]

        original_tickets = deepcopy(self.tickets)
        original_events = deepcopy(self.events)

        with self.assertRaises(ValueError):

            assign_with_history(
                self.tickets,
                self.events,
                "T001",
                "John",
                "Admin",
                self.now
            )

        self.assertEqual(self.tickets, original_tickets)
        self.assertEqual(self.events, original_events)

    # Test 5: Repeated successful assignments get unique IDs
    def test_unique_event_ids(self):

        assign_with_history(
            self.tickets,
            self.events,
            "T001",
            "John",
            "Admin",
            self.now
        )

        assign_with_history(
            self.tickets,
            self.events,
            "T001",
            "Mary",
            "Admin",
            self.now
        )

        event_ids = [
            event["event_id"]
            for event in self.events
        ]

        self.assertEqual(event_ids, ["E001", "E002"])

        self.assertEqual(
            self.tickets[0]["assigned_to"],
            "Mary"
        )


if __name__ == "__main__":
    unittest.main()