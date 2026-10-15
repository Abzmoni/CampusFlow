"""Automated tests for SLA engine, time handling, and overdue escalation (Engineer A)."""

from datetime import datetime, timezone, timedelta
import unittest

from campusflow.sla import (
    SLA_MINUTES,
    calculate_due_at,
    escalate_overdue,
    from_iso_utc,
    get_now,
    is_overdue,
    to_iso_utc,
)
from campusflow.tickets import create_ticket
from campusflow.workflow import assign_ticket, reopen_ticket, update_status


class SlaEngineTests(unittest.TestCase):
    def setUp(self):
        self.tickets = []
        self.events = []
        self.base_time = datetime(2026, 10, 14, 10, 0, 0, tzinfo=timezone.utc)

    def test_sla_threshold_durations(self):
        """Verify standard SLA duration constants in minutes."""
        self.assertEqual(SLA_MINUTES["critical"], 60)
        self.assertEqual(SLA_MINUTES["high"], 240)
        self.assertEqual(SLA_MINUTES["medium"], 1440)
        self.assertEqual(SLA_MINUTES["low"], 2880)

    def test_calculate_due_at_exact_times(self):
        """Verify due_at calculations across all priority levels."""
        cycle_start = self.base_time
        expected_critical = cycle_start + timedelta(minutes=60)
        expected_high = cycle_start + timedelta(minutes=240)
        expected_medium = cycle_start + timedelta(minutes=1440)
        expected_low = cycle_start + timedelta(minutes=2880)

        self.assertEqual(calculate_due_at("critical", cycle_start), to_iso_utc(expected_critical))
        self.assertEqual(calculate_due_at("high", cycle_start), to_iso_utc(expected_high))
        self.assertEqual(calculate_due_at("medium", cycle_start), to_iso_utc(expected_medium))
        self.assertEqual(calculate_due_at("low", cycle_start), to_iso_utc(expected_low))

    def test_checkpoint_a1_critical_at_exact_60_minutes_is_not_overdue(self):
        """Checkpoint A1: Critical ticket at exact 60 minutes is NOT overdue."""
        ticket = create_ticket(
            self.tickets,
            title="Campus backbone outage",
            category="Network",
            urgency="high",
            affected_users=15,  # critical priority
            now=self.base_time,
        )
        self.assertEqual(ticket["priority"], "critical")
        exact_60m = self.base_time + timedelta(minutes=60)

        # At the exact due_at instant, current time is not strictly later
        self.assertFalse(is_overdue(ticket, now=exact_60m))

    def test_checkpoint_a2_critical_at_61_minutes_is_overdue(self):
        """Checkpoint A2: Critical ticket at 61 minutes IS overdue."""
        ticket = create_ticket(
            self.tickets,
            title="Campus backbone outage",
            category="Network",
            urgency="high",
            affected_users=15,  # critical priority
            now=self.base_time,
        )
        at_61m = self.base_time + timedelta(minutes=61)
        self.assertTrue(is_overdue(ticket, now=at_61m))

    def test_all_priority_boundary_conditions(self):
        """Test exact boundary vs boundary+1 minute across all priorities."""
        cases = [
            ("critical", 60),
            ("high", 240),
            ("medium", 1440),
            ("low", 2880),
        ]
        for priority, duration in cases:
            with self.subTest(priority=priority):
                due_at = to_iso_utc(self.base_time + timedelta(minutes=duration))
                dummy = {"id": "T001", "status": "open", "priority": priority, "due_at": due_at}

                # Exact due time -> not overdue
                exact = self.base_time + timedelta(minutes=duration)
                self.assertFalse(is_overdue(dummy, now=exact))

                # 1 minute past due time -> overdue
                past = self.base_time + timedelta(minutes=duration, seconds=1)
                self.assertTrue(is_overdue(dummy, now=past))

    def test_resolved_tickets_are_never_overdue(self):
        """Resolved tickets must never be reported as overdue even past due_at."""
        ticket = create_ticket(
            self.tickets,
            title="DNS glitch",
            category="Network",
            urgency="high",
            affected_users=15,
            now=self.base_time,
        )
        ticket["status"] = "resolved"
        two_days_later = self.base_time + timedelta(days=2)
        self.assertFalse(is_overdue(ticket, now=two_days_later))

    def test_checkpoint_a3_escalation_idempotency_within_cycle(self):
        """Checkpoint A3: Running escalation twice generates exactly 1 event."""
        ticket = create_ticket(
            self.tickets,
            title="Core switch failure",
            category="Network",
            urgency="high",
            affected_users=20,
            now=self.base_time,
        )
        at_65m = self.base_time + timedelta(minutes=65)

        # First escalation run
        res1 = escalate_overdue(self.tickets, self.events, now=at_65m, actor="cron_bot")
        self.assertEqual(res1["newly_escalated"], 1)
        self.assertEqual(res1["already_escalated"], 0)
        self.assertEqual(len(self.events), 1)
        self.assertEqual(self.events[0]["event_type"], "ESCALATE")
        self.assertEqual(self.events[0]["actor"], "cron_bot")
        self.assertEqual(ticket["escalation_cycle"], 1)

        # Second escalation run at same or later time
        at_70m = self.base_time + timedelta(minutes=70)
        res2 = escalate_overdue(self.tickets, self.events, now=at_70m, actor="cron_bot")
        self.assertEqual(res2["newly_escalated"], 0)
        self.assertEqual(res2["already_escalated"], 1)
        self.assertEqual(len(self.events), 1)  # No duplicate event created!

    def test_escalation_preserves_ticket_status_priority_and_assignment(self):
        """Escalation must not automatically assign or alter status/priority."""
        ticket = create_ticket(
            self.tickets,
            title="Auth server reboot",
            category="Software",
            urgency="high",
            affected_users=25,
            now=self.base_time,
        )
        ticket["assigned_to"] = "Alice"
        overdue_time = self.base_time + timedelta(minutes=65)

        escalate_overdue(self.tickets, self.events, now=overdue_time)

        self.assertEqual(ticket["status"], "open")
        self.assertEqual(ticket["priority"], "critical")
        self.assertEqual(ticket["assigned_to"], "Alice")

    def test_checkpoint_a4_reopen_starts_fresh_sla_cycle_and_clears_escalation(self):
        """Checkpoint A4: Reopening sets a new due_at and allows escalation in new cycle."""
        ticket = create_ticket(
            self.tickets,
            title="Library Wi-Fi down",
            category="Network",
            urgency="high",
            affected_users=15,  # critical (60m)
            now=self.base_time,
        )
        orig_created_at = ticket["created_at"]
        orig_due_at = ticket["due_at"]

        # Escalate in first cycle
        t_esc1 = self.base_time + timedelta(minutes=65)
        escalate_overdue(self.tickets, self.events, now=t_esc1)
        self.assertEqual(ticket["escalation_cycle"], 1)
        self.assertEqual(len(self.events), 1)

        # Progress and resolve
        assign_ticket(self.tickets, ticket["id"], "David")
        update_status(self.tickets, ticket["id"], "in_progress")
        update_status(self.tickets, ticket["id"], "resolved")

        # Reopen 3 hours later -> starts NEW SLA cycle
        reopen_time = self.base_time + timedelta(hours=3)
        reopened = reopen_ticket(self.tickets, ticket["id"], now=reopen_time)

        # Assert created_at preserved, new due_at calculated, cycle flag cleared
        self.assertEqual(reopened["created_at"], orig_created_at)
        self.assertEqual(reopened["status"], "open")
        self.assertEqual(reopened["escalation_cycle"], 0)
        expected_new_due = to_iso_utc(reopen_time + timedelta(minutes=60))
        self.assertEqual(reopened["due_at"], expected_new_due)
        self.assertNotEqual(reopened["due_at"], orig_due_at)

        # Overdue in new cycle (70 minutes after reopen) -> should legitimately escalate again
        t_esc2 = reopen_time + timedelta(minutes=70)
        res = escalate_overdue(self.tickets, self.events, now=t_esc2, actor="sla_guard")
        self.assertEqual(res["newly_escalated"], 1)
        self.assertEqual(len(self.events), 2)  # Exactly 2 total events across 2 distinct cycles!
        self.assertEqual(self.events[1]["event_type"], "ESCALATE")

    def test_utc_timezone_awareness_and_conversion(self):
        """Ensure time utilities handle and convert naive and aware datetimes."""
        naive = datetime(2026, 10, 14, 12, 0, 0)
        aware = get_now(naive)
        self.assertIsNotNone(aware.tzinfo)
        self.assertEqual(aware.tzinfo, timezone.utc)

        # ISO string round trip
        iso_str = to_iso_utc(aware)
        parsed = from_iso_utc(iso_str)
        self.assertEqual(aware, parsed)


if __name__ == "__main__":
    unittest.main()
