"""SLA attention queue for CampusFlow Pro."""

from copy import deepcopy
from datetime import datetime, timezone
import re


def parse_utc(timestamp):
    """Convert an ISO timestamp into a UTC datetime."""

    if not isinstance(timestamp, str):
        raise ValueError("Timestamp must be a string")

    try:
        parsed = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )
    except ValueError:
        raise ValueError("Invalid timestamp format")

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone")

    return parsed.astimezone(timezone.utc)


def get_sla_attention_queue(tickets, now=None):
    """
    Return unresolved tickets sorted by:
    1. Overdue tickets first
    2. Earliest deadline
    3. Numeric ticket ID
    """

    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list")

    # Use the current UTC time when none is provided
    if now is None:
        now = datetime.now(timezone.utc)

    if not isinstance(now, datetime):
        raise ValueError("Current time must be a datetime")

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Current time must include a timezone")

    now = now.astimezone(timezone.utc)

    attention_tickets = []

    for ticket in tickets:

        if not isinstance(ticket, dict):
            raise ValueError("Every ticket must be a dictionary")

        status = ticket.get("status")

        # Resolved tickets do not belong in the attention queue
        if status == "resolved":
            continue

        if status not in ("open", "in_progress"):
            raise ValueError("Invalid ticket status")

        # Read the ticket deadline
        due_at = parse_utc(ticket.get("due_at"))

        # Overdue only when the current time is strictly later
        overdue = now > due_at

        # Extract the numeric part of the ticket ID
        ticket_id = ticket.get("id")

        if not isinstance(ticket_id, str):
            raise ValueError("Invalid ticket ID")

        match = re.fullmatch(r"T(\d+)", ticket_id)

        if not match:
            raise ValueError("Invalid ticket ID")

        ticket_number = int(match.group(1))

        # Store everything needed for sorting
        attention_tickets.append(
            (
                overdue,
                due_at,
                ticket_number,
                ticket_id,
                ticket
            )
        )

    # Sort overdue tickets first, then deadline, then ID
    attention_tickets.sort(
        key=lambda item: (
            not item[0],
            item[1],
            item[2],
            item[3]
        )
    )

    # Return copies so callers cannot modify the original tickets
    return [
        deepcopy(item[4])
        for item in attention_tickets
    ]