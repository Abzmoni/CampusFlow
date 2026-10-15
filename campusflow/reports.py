"""Engineer B's reporting and metrics engine for CampusFlow."""

from datetime import datetime, timezone

from campusflow.sla_queue import parse_utc


def generate_report(tickets):
    """Generate the original ticket summary statistics."""

    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list.")

    report = {
        "total": len(tickets),
        "by_status": {
            "open": 0,
            "in_progress": 0,
            "resolved": 0,
        },
        "by_priority": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        },
    }

    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue

        status = str(ticket.get("status", "")).lower()

        if status in report["by_status"]:
            report["by_status"][status] += 1

        priority = str(ticket.get("priority", "")).lower()

        if priority in report["by_priority"]:
            report["by_priority"][priority] += 1

    return report


def generate_enhanced_report(tickets, now=None):
    """
    Generate an enhanced ticket report.

    Includes:
    - Total tickets
    - Status counts
    - Priority counts
    - Overdue tickets
    - Tickets escalated in their current SLA cycle

    Does not modify the original tickets.
    """

    # Start with the original report
    report = generate_report(tickets)

    # Use the current UTC time if none is provided
    if now is None:
        now = datetime.now(timezone.utc)

    # Validate the supplied time
    if not isinstance(now, datetime):
        raise ValueError("Current time must be a datetime")

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Current time must include a timezone")

    now = now.astimezone(timezone.utc)

    # Add the new reporting fields
    report["overdue"] = 0
    report["escalated_this_cycle"] = 0

    # Examine every ticket
    for ticket in tickets:

        if not isinstance(ticket, dict):
            continue

        status = str(ticket.get("status", "")).lower()

        # Check escalation status
        escalation_cycle = ticket.get("escalation_cycle", 0)

        if type(escalation_cycle) is not int or escalation_cycle < 0:
            raise ValueError("Invalid escalation cycle")

        # Engineer A currently uses 1 to mark escalation
        if escalation_cycle == 1:
            report["escalated_this_cycle"] += 1

        # Resolved tickets cannot be overdue
        if status == "resolved":
            continue

        # Only open and in-progress tickets are eligible
        if status not in ("open", "in_progress"):
            continue

        due_at = ticket.get("due_at")

        # Legacy tickets may not have a deadline
        if due_at is None:
            continue

        # Convert the deadline into a UTC datetime
        deadline = parse_utc(due_at)

        # A ticket is overdue strictly after its deadline
        if now > deadline:
            report["overdue"] += 1

    return report