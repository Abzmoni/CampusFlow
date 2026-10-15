"""Tests for CampusFlow Pro CLI actions."""

import unittest

from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import patch

from campusflow.cli_actions import (
    create_with_history,
    confirm_duplicate_warning,
)


class TestCLIActions(unittest.TestCase):

    def setUp(self):
        self.tickets = []
        self.events = []

        self.now = datetime(
            2026, 10, 14, 12, 0,
            tzinfo=timezone.utc,
        )

    def create_sample_ticket(self):
        return create_with_history(
            self.tickets,
            self.events,
            "Campus Wi-Fi is down",
            "Network",
            "high",
            15,
            "Admin",
            now=self.now,
        )

    # Test 1: A new ticket is created successfully
    def test_create_ticket_success(self):
        ticket = self.create_sample_ticket()

        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["status"], "open")
        self.assertEqual(len(self.tickets), 1)

    # Test 2: Creation records a CREATE event
    def test_create_event_recorded(self):
        self.create_sample_ticket()

        self.assertEqual(len(self.events), 1)
        self.assertEqual(
            self.events[0]["event_type"],
            "CREATE",
        )
        self.assertEqual(
            self.events[0]["ticket_id"],
            "T001",
        )
        self.assertEqual(
            self.events[0]["actor"],
            "Admin",
        )

    # Test 3: Cancelling a duplicate changes nothing
    def test_duplicate_cancelled(self):
        self.create_sample_ticket()

        original_tickets = deepcopy(self.tickets)
        original_events = deepcopy(self.events)

        result = create_with_history(
            self.tickets,
            self.events,
            "  CAMPUS   WI-FI IS DOWN  ",
            "network",
            "high",
            15,
            "Admin",
            confirm_duplicates=lambda ids: False,
            now=self.now,
        )

        self.assertIsNone(result)
        self.assertEqual(self.tickets, original_tickets)
        self.assertEqual(self.events, original_events)

    # Test 4: A confirmed duplicate can be created
    def test_duplicate_confirmed(self):
        self.create_sample_ticket()

        received_ids = []

        def confirm(ids):
            received_ids.extend(ids)
            return True

        result = create_with_history(
            self.tickets,
            self.events,
            "campus wi-fi is down",
            "Network",
            "high",
            15,
            "Admin",
            confirm_duplicates=confirm,
            now=self.now,
        )

        self.assertEqual(received_ids, ["T001"])
        self.assertEqual(result["id"], "T002")
        self.assertEqual(len(self.tickets), 2)
        self.assertEqual(len(self.events), 2)

    # Test 5: A duplicate is cancelled if no confirmation is supplied
    def test_duplicate_without_confirmation(self):
        self.create_sample_ticket()

        result = create_with_history(
            self.tickets,
            self.events,
            "Campus Wi-Fi is down",
            "Network",
            "high",
            15,
            "Admin",
            now=self.now,
        )

        self.assertIsNone(result)
        self.assertEqual(len(self.tickets), 1)
        self.assertEqual(len(self.events), 1)

    # Test 6: Invalid actor changes nothing
    def test_invalid_actor(self):
        with self.assertRaises(ValueError):
            create_with_history(
                self.tickets,
                self.events,
                "Printer not working",
                "Hardware",
                "medium",
                3,
                "",
                now=self.now,
            )

        self.assertEqual(self.tickets, [])
        self.assertEqual(self.events, [])

    # Test 7: The confirmation prompt accepts yes
    @patch("builtins.input", return_value="yes")
    def test_confirmation_prompt(self, mock_input):
        result = confirm_duplicate_warning(["T001", "T003"])

        self.assertTrue(result)
        mock_input.assert_called_once()


if __name__ == "__main__":
    unittest.main()