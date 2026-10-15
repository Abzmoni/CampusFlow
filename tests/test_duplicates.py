import unittest

from campusflow.duplicates import detect_duplicates, normalize_title


class TestDuplicates(unittest.TestCase):

    def setUp(self):
        # Sample tickets used for each test
        self.tickets = [
            {
                "id": "T001",
                "title": "Campus Wi-Fi Down",
                "category": "Network",
                "status": "open"
            },
            {
                "id": "T002",
                "title": "Broken Projector",
                "category": "Hardware",
                "status": "resolved"
            },
            {
                "id": "T003",
                "title": "Campus Wi-Fi Down",
                "category": "Network",
                "status": "in_progress"
            }
        ]

    # Test 1: Check title normalization
    def test_normalize_title(self):
        result = normalize_title("  Campus   Wi-Fi Down ")

        self.assertEqual(result, "campus wi-fi down")

    # Test 2: Find duplicate tickets
    def test_matching_duplicates(self):
        result = detect_duplicates(
            self.tickets,
            "network",
            "campus wi-fi down"
        )

        self.assertEqual(result, ["T001", "T003"])

    # Test 3: Ignore different categories
    def test_different_category(self):
        result = detect_duplicates(
            self.tickets,
            "Hardware",
            "Campus Wi-Fi Down"
        )

        self.assertEqual(result, [])

    # Test 4: Ignore resolved tickets
    def test_resolved_ticket_ignored(self):
        result = detect_duplicates(
            self.tickets,
            "Hardware",
            "Broken Projector"
        )

        self.assertEqual(result, [])

    # Test 5: Handle missing matches
    def test_no_matching_ticket(self):
        result = detect_duplicates(
            self.tickets,
            "Software",
            "Login failed"
        )

        self.assertEqual(result, [])

    # Test 6: Ensure existing tickets remain unchanged
    def test_original_tickets_unchanged(self):
        original = [ticket.copy() for ticket in self.tickets]

        detect_duplicates(
            self.tickets,
            "Network",
            "Campus Wi-Fi Down"
        )

        self.assertEqual(self.tickets, original)


if __name__ == "__main__":
    unittest.main()