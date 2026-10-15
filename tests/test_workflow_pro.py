import unittest

from campusflow.workflow import (
    assign_ticket,
    update_status,
    reopen_ticket
)


class TestWorkflowPro(unittest.TestCase):

    def setUp(self):
        self.tickets = [
            {
                "id": "T001",
                "status": "open",
                "assigned_to": "John"
            }
        ]

    # Test 1: An open ticket cannot be resolved directly
    def test_open_cannot_resolve_directly(self):

        with self.assertRaises(ValueError):
            update_status(self.tickets, "T001", "resolved")

        self.assertEqual(self.tickets[0]["status"], "open")

    # Test 2: A resolved ticket cannot be assigned
    def test_resolved_ticket_cannot_be_assigned(self):

        self.tickets[0]["status"] = "resolved"

        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T001", "Mary")

        self.assertEqual(
            self.tickets[0]["assigned_to"],
            "John"
        )

    # Test 3: Reopening must use reopen_ticket()
    def test_reopen_requires_explicit_function(self):

        self.tickets[0]["status"] = "resolved"

        with self.assertRaises(ValueError):
            update_status(self.tickets, "T001", "open")

        result = reopen_ticket(self.tickets, "T001")

        self.assertEqual(result["status"], "open")


if __name__ == "__main__":
    unittest.main()