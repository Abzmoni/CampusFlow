"""Acceptance tests for Engineer A's scope."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from campusflow.tickets import calculate_priority, create_ticket


class PriorityTests(unittest.TestCase):
    def test_required_examples(self):
        for urgency, count, expected in [
            ('high', 12, 'critical'), ('high', 2, 'high'),
            ('low', 4, 'medium'), ('low', 1, 'low'),
        ]:
            with self.subTest(urgency=urgency, count=count):
                self.assertEqual(calculate_priority(urgency, count), expected)

    def test_all_urgencies_at_boundaries(self):
        expected = {
            'low': ['low', 'low', 'medium', 'medium', 'high', 'high'],
            'medium': ['medium', 'medium', 'medium', 'medium', 'high', 'high'],
            'high': ['high', 'high', 'high', 'high', 'critical', 'critical'],
        }
        for urgency, priorities in expected.items():
            for count, priority in zip([1, 2, 3, 9, 10, 11], priorities):
                with self.subTest(urgency=urgency, count=count):
                    self.assertEqual(calculate_priority(urgency, count), priority)

    def test_normalizes_urgency(self):
        self.assertEqual(calculate_priority(' HiGh ', 10), 'critical')

    def test_rejects_invalid_urgency(self):
        for urgency in ['', ' ', 'urgent', None, 1]:
            with self.subTest(urgency=urgency), self.assertRaises(ValueError):
                calculate_priority(urgency, 1)

    def test_rejects_invalid_counts(self):
        for count in [0, -1, 1.0, 2.5, '2', 'text', None, True, False]:
            with self.subTest(count=count), self.assertRaises(ValueError):
                calculate_priority('low', count)


class CreationTests(unittest.TestCase):
    def setUp(self):
        self.tickets = []

    def create(self, **changes):
        values = dict(title='Wi-Fi is down', category='Network',
                      urgency='high', affected_users=15)
        values.update(changes)
        return create_ticket(self.tickets, **values)

    def test_complete_record_and_return_value(self):
        ticket = self.create()
        self.assertEqual(ticket['id'], 'T001')
        self.assertEqual(ticket['title'], 'Wi-Fi is down')
        self.assertEqual(ticket['category'], 'Network')
        self.assertEqual(ticket['urgency'], 'high')
        self.assertEqual(ticket['affected_users'], 15)
        self.assertEqual(ticket['priority'], 'critical')
        self.assertEqual(ticket['status'], 'open')
        self.assertIsNone(ticket['assigned_to'])
        self.assertIn('created_at', ticket)
        self.assertEqual(ticket['updated_at'], ticket['created_at'])
        self.assertIn('due_at', ticket)
        self.assertEqual(ticket['escalation_cycle'], 0)
        self.assertEqual(len(self.tickets), 1)
        self.assertIs(ticket, self.tickets[0])

    def test_normalizes_title_category_and_urgency(self):
        for category in ['Network', 'Hardware', 'Software', 'Other']:
            with self.subTest(category=category):
                ticket = self.create(title='  Broken Laptop  ',
                                     category=f' {category.swapcase()} ', urgency=' LOW ')
                self.assertEqual(ticket['title'], 'Broken Laptop')
                self.assertEqual(ticket['category'], category)
                self.assertEqual(ticket['urgency'], 'low')

    def test_sequential_unique_ids(self):
        self.assertEqual([self.create()['id'] for _ in range(3)],
                         ['T001', 'T002', 'T003'])

    def test_uses_numeric_max_for_unordered_gapped_ids(self):
        self.tickets = [{'id': 'T1000'}, {'id': 'T002'}, {'id': 'T099'}]
        self.assertEqual(self.create()['id'], 'T1001')

    def test_grows_beyond_three_digits(self):
        self.tickets = [{'id': 'T999'}]
        self.assertEqual(self.create()['id'], 'T1000')

    def test_invalid_creation_leaves_existing_records_unchanged(self):
        self.create()
        before = copy.deepcopy(self.tickets)
        cases = [
            {'title': ''}, {'title': '  '}, {'title': None}, {'title': 7},
            {'category': 'Finance'}, {'category': ''}, {'category': None},
            {'urgency': 'urgent'}, {'urgency': None},
        ] + [{'affected_users': value} for value in
             [0, -1, 1.0, 2.5, '2', 'text', True, False, None]]
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self.create(**changes)
                self.assertEqual(self.tickets, before)
        self.assertEqual(self.create()['id'], 'T002')

    def test_rejects_invalid_collection(self):
        for collection in [None, {}, ()]:
            with self.subTest(collection=collection), self.assertRaises(ValueError):
                create_ticket(collection, 'Title', 'Other', 'low', 1)

    def test_rejects_invalid_existing_ids_without_mutation(self):
        for records in [[{}], [None], [{'id': 'T000'}], [{'id': 'T-01'}],
                        [{'id': 'T1'}], [{'id': 1}], [{'id': 'T001x'}],
                        [{'id': 'T001'}, {'id': 'T001'}],
                        [{'id': 'T001'}, {'id': 'T0001'}]]:
            with self.subTest(records=records):
                self.tickets = copy.deepcopy(records)
                with self.assertRaises(ValueError):
                    self.create()
                self.assertEqual(self.tickets, records)

    def test_json_round_trip_then_create_preserves_unique_ids(self):
        self.create()
        self.create(title='Broken laptop', category='Hardware')
        before = copy.deepcopy(self.tickets)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tickets.json'
            with path.open('w', encoding='utf-8') as handle:
                json.dump(self.tickets, handle)
            with path.open(encoding='utf-8') as handle:
                self.tickets = json.load(handle)
        self.assertEqual(self.tickets, before)
        self.assertEqual(self.create()['id'], 'T003')
        self.assertEqual(self.tickets[:2], before)
        self.assertEqual(len({ticket['id'] for ticket in self.tickets}), 3)


if __name__ == '__main__':
    unittest.main()
