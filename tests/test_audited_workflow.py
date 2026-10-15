import unittest

from copy import deepcopy
from datetime import datetime, timezone

from campusflow.audited_workflow import (
    assign_with_history,
    reopen_with_history,
    update_status_with_history
)


class TestAuditedWorkflow(unittest.TestCase):

    def setUp(self):
        # Sample ticket for testing
        self.tickets = [
            {
                "id": "T001",
                "status": "open",
                "assigned_to": None
            }
        ]

        # Empty audit history
        self.events = []

        # Fixed UTC time for predictable tests
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
        self.assertEqual(self.events[0]["event_type"], "ASSIGN")
        self.assertEqual(self.events[0]["actor"], "Admin")
        self.assertEqual(self.events[0]["before_status"], "open")
        self.assertEqual(self.events[0]["after_status"], "open")

    # Test 2: Invalid ticket does not modify data
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

    # Test 3: Invalid actor does not modify data
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

    # Test 4: Invalid event history does not modify data
    def test_invalid_existing_event(self):
        self.events = [
            {"event_id": "invalid"}
        ]

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

    # Test 5: Each assignment gets a unique event ID
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
        self.assertEqual(self.tickets[0]["assigned_to"], "Mary")

    # Test 6: Starting work records a START event
    def test_start_records_history(self):
        assign_with_history(
            self.tickets,
            self.events,
            "T001",
            "John",
            "Admin",
            self.now
        )

        result = update_status_with_history(
            self.tickets,
            self.events,
            "T001",
            "in_progress",
            "John",
            self.now
        )

        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(len(self.events), 2)

        self.assertEqual(
            self.events[1]["event_type"],
            "START"
        )

        self.assertEqual(
            self.events[1]["before_status"],
            "open"
        )

        self.assertEqual(
            self.events[1]["after_status"],
            "in_progress"
        )

    # Test 7: Resolving a ticket records a RESOLVE event
    def test_resolve_records_history(self):
        assign_with_history(
            self.tickets,
            self.events,
            "T001",
            "John",
            "Admin",
            self.now
        )

        update_status_with_history(
            self.tickets,
            self.events,
            "T001",
            "in_progress",
            "John",
            self.now
        )

        result = update_status_with_history(
            self.tickets,
            self.events,
            "T001",
            "resolved",
            "John",
            self.now
        )

        self.assertEqual(result["status"], "resolved")
        self.assertEqual(len(self.events), 3)

        self.assertEqual(
            self.events[2]["event_type"],
            "RESOLVE"
        )

        self.assertEqual(
            self.events[2]["before_status"],
            "in_progress"
        )

        self.assertEqual(
            self.events[2]["after_status"],
            "resolved"
        )

    # Test 8: Invalid transition must not create an event
    def test_invalid_transition_creates_no_event(self):
        original_tickets = deepcopy(self.tickets)
        original_events = deepcopy(self.events)

        with self.assertRaises(ValueError):
            update_status_with_history(
                self.tickets,
                self.events,
                "T001",
                "resolved",
                "Admin",
                self.now
            )

        self.assertEqual(self.tickets, original_tickets)
        self.assertEqual(self.events, original_events)

    # Test 9: Successful reopen records REOPEN event and starts new cycle
    def test_successful_reopen_records_event(self):
        # Progress ticket to resolved first
        assign_with_history(self.tickets, self.events, "T001", "John", "Admin", self.now)
        update_status_with_history(self.tickets, self.events, "T001", "in_progress", "John", self.now)
        update_status_with_history(self.tickets, self.events, "T001", "resolved", "John", self.now)

        reopened = reopen_with_history(
            self.tickets,
            self.events,
            "T001",
            "Supervisor",
            self.now
        )

        self.assertEqual(reopened["status"], "open")
        self.assertEqual(len(self.events), 4)
        reopen_evt = self.events[3]
        self.assertEqual(reopen_evt["event_type"], "REOPEN")
        self.assertEqual(reopen_evt["actor"], "Supervisor")
        self.assertEqual(reopen_evt["before_status"], "resolved")
        self.assertEqual(reopen_evt["after_status"], "open")

    # Test 10: Reopening an unresolved ticket fails without side effects
    def test_reopen_unresolved_ticket_fails_without_side_effects(self):
        original_tickets = deepcopy(self.tickets)
        original_events = deepcopy(self.events)

        with self.assertRaises(ValueError):
            reopen_with_history(
                self.tickets,
                self.events,
                "T001",
                "Supervisor",
                self.now
            )

        self.assertEqual(self.tickets, original_tickets)
        self.assertEqual(self.events, original_events)


if __name__ == "__main__":
    unittest.main()