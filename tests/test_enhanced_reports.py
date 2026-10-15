"""Automated tests for enhanced reporting."""

import unittest

from copy import deepcopy
from datetime import datetime, timezone, timedelta

from campusflow.reports import generate_enhanced_report


class TestEnhancedReports(unittest.TestCase):

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
                "due_at": "2026-10-14T10:00:00+00:00",
                "escalation_cycle": 1
            },
            {
                "id": "T002",
                "status": "in_progress",
                "priority": "high",
                "due_at": "2026-10-14T11:00:00+00:00",
                "escalation_cycle": 0
            },
            {
                "id": "T003",
                "status": "open",
                "priority": "medium",
                "due_at": "2026-10-14T14:00:00+00:00",
                "escalation_cycle": 0
            },
            {
                "id": "T004",
                "status": "resolved",
                "priority": "low",
                "due_at": "2026-10-14T09:00:00+00:00",
                "escalation_cycle": 0
            }
        ]

    # Test 1: Count every ticket
    def test_total_tickets(self):

        report = generate_enhanced_report(
            self.tickets,
            self.now
        )

        self.assertEqual(report["total"], 4)

    # Test 2: Count tickets by status
    def test_status_counts(self):

        report = generate_enhanced_report(
            self.tickets,
            self.now
        )

        self.assertEqual(
            report["by_status"],
            {
                "open": 2,
                "in_progress": 1,
                "resolved": 1
            }
        )

    # Test 3: Count tickets by priority
    def test_priority_counts(self):

        report = generate_enhanced_report(
            self.tickets,
            self.now
        )

        self.assertEqual(
            report["by_priority"],
            {
                "critical": 1,
                "high": 1,
                "medium": 1,
                "low": 1
            }
        )

    # Test 4: Count overdue unresolved tickets
    def test_overdue_count(self):

        report = generate_enhanced_report(
            self.tickets,
            self.now
        )

        self.assertEqual(report["overdue"], 2)

    # Test 5: Count tickets escalated this cycle
    def test_escalated_count(self):

        report = generate_enhanced_report(
            self.tickets,
            self.now
        )

        self.assertEqual(
            report["escalated_this_cycle"],
            1
        )

    # Test 6: Reports must not modify original tickets
    def test_report_does_not_modify_tickets(self):

        original = deepcopy(self.tickets)

        generate_enhanced_report(
            self.tickets,
            self.now
        )

        self.assertEqual(self.tickets, original)

    # Test 7: Empty tickets produce zero counts
    def test_empty_report(self):

        report = generate_enhanced_report(
            [],
            self.now
        )

        self.assertEqual(report["total"], 0)
        self.assertEqual(report["overdue"], 0)
        self.assertEqual(report["escalated_this_cycle"], 0)

    # Test 8: A ticket is not overdue at its exact deadline
    def test_exact_deadline_not_overdue(self):

        tickets = [
            {
                "id": "T005",
                "status": "open",
                "priority": "critical",
                "due_at": self.now.isoformat(),
                "escalation_cycle": 0
            }
        ]

        report = generate_enhanced_report(
            tickets,
            self.now
        )

        self.assertEqual(report["overdue"], 0)

    # Test 9: Timezone offsets must be handled correctly
    def test_timezone_offset(self):

        tickets = [
            {
                "id": "T006",
                "status": "open",
                "priority": "high",
                "due_at": "2026-10-14T13:00:00+02:00",
                "escalation_cycle": 0
            }
        ]

        report = generate_enhanced_report(
            tickets,
            self.now
        )

        # 13:00 at UTC+02:00 equals 11:00 UTC
        self.assertEqual(report["overdue"], 1)

    # Test 10: Invalid escalation cycles must be rejected
    def test_invalid_escalation_cycle(self):

        tickets = [
            {
                "id": "T007",
                "status": "open",
                "priority": "low",
                "due_at": "2026-10-15T12:00:00+00:00",
                "escalation_cycle": -1
            }
        ]

        with self.assertRaises(ValueError):
            generate_enhanced_report(
                tickets,
                self.now
            )

    # Test 11: Invalid deadlines must be rejected
    def test_invalid_deadline(self):

        tickets = [
            {
                "id": "T008",
                "status": "open",
                "priority": "low",
                "due_at": "not-a-date",
                "escalation_cycle": 0
            }
        ]

        with self.assertRaises(ValueError):
            generate_enhanced_report(
                tickets,
                self.now
            )


if __name__ == "__main__":
    unittest.main()