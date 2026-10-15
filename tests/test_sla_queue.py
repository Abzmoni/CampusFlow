"""Tests for the SLA attention queue."""

import unittest

from copy import deepcopy
from datetime import datetime, timezone

from campusflow.sla_queue import get_sla_attention_queue


class TestSLAAttentionQueue(unittest.TestCase):

    def setUp(self):

        self.now = datetime(
            2026, 10, 14, 12, 0,
            tzinfo=timezone.utc
        )

        self.tickets = [
            {
                "id": "T001",
                "status": "open",
                "priority": "critical",
                "due_at": "2026-10-14T10:00:00+00:00"
            },
            {
                "id": "T002",
                "status": "in_progress",
                "priority": "high",
                "due_at": "2026-10-14T11:00:00+00:00"
            },
            {
                "id": "T003",
                "status": "open",
                "priority": "medium",
                "due_at": "2026-10-14T14:00:00+00:00"
            },
            {
                "id": "T004",
                "status": "resolved",
                "priority": "low",
                "due_at": "2026-10-14T09:00:00+00:00"
            }
        ]

    # Test 1: Overdue tickets should appear first
    def test_overdue_tickets_first(self):

        result = get_sla_attention_queue(
            self.tickets,
            self.now
        )

        ids = [ticket["id"] for ticket in result]

        self.assertEqual(
            ids,
            ["T001", "T002", "T003"]
        )

    # Test 2: Resolved tickets must be excluded
    def test_resolved_tickets_excluded(self):

        result = get_sla_attention_queue(
            self.tickets,
            self.now
        )

        ids = [ticket["id"] for ticket in result]

        self.assertNotIn("T004", ids)

    # Test 3: In-progress tickets should be included
    def test_in_progress_tickets_included(self):

        result = get_sla_attention_queue(
            self.tickets,
            self.now
        )

        ids = [ticket["id"] for ticket in result]

        self.assertIn("T002", ids)

    # Test 4: Earlier deadlines should appear first
    def test_earliest_deadline_first(self):

        tickets = [
            {
                "id": "T001",
                "status": "open",
                "due_at": "2026-10-14T18:00:00+00:00"
            },
            {
                "id": "T002",
                "status": "open",
                "due_at": "2026-10-14T13:00:00+00:00"
            }
        ]

        result = get_sla_attention_queue(
            tickets,
            self.now
        )

        self.assertEqual(
            [ticket["id"] for ticket in result],
            ["T002", "T001"]
        )

    # Test 5: Equal deadlines use numeric ticket IDs
    def test_numeric_id_tie_breaking(self):

        tickets = [
            {
                "id": "T010",
                "status": "open",
                "due_at": "2026-10-14T15:00:00+00:00"
            },
            {
                "id": "T002",
                "status": "open",
                "due_at": "2026-10-14T15:00:00+00:00"
            }
        ]

        result = get_sla_attention_queue(
            tickets,
            self.now
        )

        self.assertEqual(
            [ticket["id"] for ticket in result],
            ["T002", "T010"]
        )

    # Test 6: The original ticket data must not change
    def test_original_tickets_unchanged(self):

        original = deepcopy(self.tickets)

        result = get_sla_attention_queue(
            self.tickets,
            self.now
        )

        self.assertEqual(self.tickets, original)

        # Editing a returned ticket must not affect the original
        result[0]["status"] = "resolved"

        self.assertEqual(self.tickets, original)

    # Test 7: Invalid deadlines must be rejected
    def test_invalid_deadline(self):

        tickets = [
            {
                "id": "T001",
                "status": "open",
                "due_at": "not-a-date"
            }
        ]

        with self.assertRaises(ValueError):

            get_sla_attention_queue(
                tickets,
                self.now
            )


if __name__ == "__main__":
    unittest.main()