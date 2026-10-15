"""Engineer A's ticket creation, SLA initialization, and priority rules."""

import re
from campusflow.sla import calculate_due_at, get_now, to_iso_utc

CATEGORIES = ("Network", "Hardware", "Software", "Other")
URGENCIES = ("low", "medium", "high")


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text.")
    return value.strip()


def _urgency(value):
    value = _text(value, "Urgency").lower()
    if value not in URGENCIES:
        raise ValueError("Urgency must be low, medium or high.")
    return value


def _affected_users(value):
    # bool is an int subclass, but is not a valid count in this contract.
    if type(value) is not int or value <= 0:
        raise ValueError("Affected users must be a positive integer.")
    return value


def calculate_priority(urgency, affected_users):
    """Validate inputs and return the first matching priority rule."""
    urgency = _urgency(urgency)
    affected_users = _affected_users(affected_users)
    if urgency == "high" and affected_users >= 10:
        return "critical"
    if urgency == "high" or affected_users >= 10:
        return "high"
    if urgency == "medium" or affected_users >= 3:
        return "medium"
    return "low"


def _next_ticket_id(tickets):
    numbers = set()
    for ticket in tickets:
        ticket_id = ticket.get("id") if isinstance(ticket, dict) else None
        if not isinstance(ticket_id, str) or not re.fullmatch(r"T[0-9]{3,}", ticket_id):
            raise ValueError("Existing tickets must have IDs such as T001.")
        number = int(ticket_id[1:])
        if number <= 0 or number in numbers:
            raise ValueError("Existing ticket IDs must be positive and unique.")
        numbers.add(number)
    return f"T{max(numbers, default=0) + 1:03d}"


def create_ticket(tickets, title, category, urgency, affected_users, now=None):
    """Append and return a validated ticket; leave the list unchanged on error.

    In CampusFlow Pro, each ticket records:
      - id, title, category, urgency, affected_users, priority, status, assigned_to
      - created_at, updated_at, due_at (ISO-8601 UTC strings)
      - escalation_cycle (integer, initially 0)
    """
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list.")
    title = _text(title, "Title")
    category = _text(category, "Category").capitalize()
    if category not in CATEGORIES:
        raise ValueError("Category must be Network, Hardware, Software or Other.")
    urgency = _urgency(urgency)
    priority = calculate_priority(urgency, affected_users)

    now_dt = get_now(now)
    now_iso = to_iso_utc(now_dt)
    due_at_iso = calculate_due_at(priority, now_dt)

    ticket = {
        "id": _next_ticket_id(tickets),
        "title": title,
        "category": category,
        "urgency": urgency,
        "affected_users": affected_users,
        "priority": priority,
        "status": "open",
        "assigned_to": None,
        "created_at": now_iso,
        "updated_at": now_iso,
        "due_at": due_at_iso,
        "escalation_cycle": 0,
    }
    tickets.append(ticket)
    return ticket
