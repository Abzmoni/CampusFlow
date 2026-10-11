"""Unit tests for Engineer B's workflow, assignment, queue, and reporting scope."""

import unittest
from campusflow.workflow import (
    assign_ticket,
    find_ticket,
    get_work_queue,
    reopen_ticket,
    update_status,
)
from campusflow.reports import generate_report


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tickets = [
            {
                "id": "T001",
                "title": "Wi-Fi outage in Lab A",
                "category": "Network",
                "urgency": "high",
                "affected_users": 15,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
            },
            {
                "id": "T002",
                "title": "Broken projector",
                "category": "Hardware",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": "Alice",
            },
            {
                "id": "T003",
                "title": "Portal login error",
                "category": "Software",
                "urgency": "high",
                "affected_users": 5,
                "priority": "high",
                "status": "in_progress",
                "assigned_to": "Bob",
            },
            {
                "id": "T004",
                "title": "Printer jammed",
                "category": "Hardware",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "resolved",
                "assigned_to": "Charlie",
            },
        ]

    def test_find_ticket_success_and_case_insensitive(self):
        ticket = find_ticket(self.tickets, "t001")
        self.assertEqual(ticket["id"], "T001")

    def test_find_ticket_unknown_id_raises_value_error(self):
        for bad_id in ["T999", "INVALID", "", " "]:
            with self.subTest(bad_id=bad_id), self.assertRaises(ValueError):
                find_ticket(self.tickets, bad_id)

    def test_assign_ticket_success(self):
        updated = assign_ticket(self.tickets, "T001", "  David Staff  ")
        self.assertEqual(updated["assigned_to"], "David Staff")
        self.assertEqual(self.tickets[0]["assigned_to"], "David Staff")

    def test_assign_ticket_rejects_blank_or_invalid_name(self):
        for bad_name in ["", "   ", None, 123]:
            with self.subTest(bad_name=bad_name), self.assertRaises(ValueError):
                assign_ticket(self.tickets, "T001", bad_name)

    def test_unassigned_ticket_cannot_move_to_in_progress(self):
        # T001 is unassigned
        self.assertIsNone(self.tickets[0]["assigned_to"])
        with self.assertRaises(ValueError) as ctx:
            update_status(self.tickets, "T001", "in_progress")
        self.assertIn("unassigned", str(ctx.exception).lower())

    def test_assigned_ticket_can_progress_through_lifecycle(self):
        # T002 is assigned to Alice and currently open
        self.assertEqual(self.tickets[1]["status"], "open")
        self.assertEqual(self.tickets[1]["assigned_to"], "Alice")

        update_status(self.tickets, "T002", "in_progress")
        self.assertEqual(self.tickets[1]["status"], "in_progress")

        update_status(self.tickets, "T002", "resolved")
        self.assertEqual(self.tickets[1]["status"], "resolved")

    def test_resolved_ticket_cannot_move_without_explicit_reopen(self):
        # T004 is resolved
        self.assertEqual(self.tickets[3]["status"], "resolved")
        for blocked_status in ["in_progress", "resolved"]:
            with self.subTest(blocked_status=blocked_status), self.assertRaises(ValueError):
                update_status(self.tickets, "T004", blocked_status)

    def test_reopen_ticket_sets_status_to_open(self):
        # T004 is resolved
        reopened = reopen_ticket(self.tickets, "T004")
        self.assertEqual(reopened["status"], "open")
        self.assertEqual(self.tickets[3]["status"], "open")

    def test_reopen_non_resolved_ticket_raises_value_error(self):
        for ticket_id in ["T001", "T002", "T003"]:
            with self.subTest(ticket_id=ticket_id), self.assertRaises(ValueError):
                reopen_ticket(self.tickets, ticket_id)

    def test_update_status_rejects_invalid_status_strings(self):
        for bad_status in ["closed", "pending", "done", "", None]:
            with self.subTest(bad_status=bad_status), self.assertRaises(ValueError):
                update_status(self.tickets, "T002", bad_status)


class WorkQueueTests(unittest.TestCase):
    def test_work_queue_ordering_and_tie_breaking(self):
        tickets = [
            {"id": "T005", "priority": "low", "status": "open"},
            {"id": "T003", "priority": "high", "status": "open"},
            {"id": "T001", "priority": "critical", "status": "open"},
            {"id": "T004", "priority": "high", "status": "in_progress"},
            {"id": "T002", "priority": "medium", "status": "open"},
            {"id": "T006", "priority": "critical", "status": "resolved"},  # resolved should be excluded
            {"id": "T007", "priority": "critical", "status": "open"},
        ]
        queue = get_work_queue(tickets)
        queue_ids = [t["id"] for t in queue]

        # Expected:
        # critical: T001, T007 (T006 excluded because resolved)
        # high: T003, T004 (ordered by numeric ID)
        # medium: T002
        # low: T005
        self.assertEqual(queue_ids, ["T001", "T007", "T003", "T004", "T002", "T005"])

    def test_work_queue_empty_collection(self):
        self.assertEqual(get_work_queue([]), [])

    def test_work_queue_does_not_mutate_original_list(self):
        tickets = [
            {"id": "T002", "priority": "low", "status": "open"},
            {"id": "T001", "priority": "critical", "status": "open"},
        ]
        original_ids = [t["id"] for t in tickets]
        queue = get_work_queue(tickets)
        self.assertEqual([t["id"] for t in queue], ["T001", "T002"])
        self.assertEqual([t["id"] for t in tickets], original_ids)


class ReportingTests(unittest.TestCase):
    def test_report_on_empty_tickets(self):
        report = generate_report([])
        self.assertEqual(report["total"], 0)
        self.assertEqual(report["by_status"], {"open": 0, "in_progress": 0, "resolved": 0})
        self.assertEqual(report["by_priority"], {"critical": 0, "high": 0, "medium": 0, "low": 0})

    def test_report_on_populated_tickets(self):
        tickets = [
            {"id": "T001", "status": "open", "priority": "critical"},
            {"id": "T002", "status": "open", "priority": "high"},
            {"id": "T003", "status": "in_progress", "priority": "high"},
            {"id": "T004", "status": "resolved", "priority": "medium"},
            {"id": "T005", "status": "resolved", "priority": "low"},
        ]
        report = generate_report(tickets)
        self.assertEqual(report["total"], 5)
        self.assertEqual(report["by_status"], {"open": 2, "in_progress": 1, "resolved": 2})
        self.assertEqual(report["by_priority"], {"critical": 1, "high": 2, "medium": 1, "low": 1})

    def test_report_rejects_non_list(self):
        for invalid in [None, {}, "text", 42]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                generate_report(invalid)


if __name__ == "__main__":
    unittest.main()
