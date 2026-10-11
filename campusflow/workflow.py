"""Engineer B's ticket workflow, assignment, and work queue management."""

import re

ALLOWED_STATUSES = ("open", "in_progress", "resolved")
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def find_ticket(tickets, ticket_id):
    """Find a ticket by ID in tickets list. Raise ValueError if not found."""
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list.")
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise ValueError("Ticket ID must be non-empty text.")
    target_id = ticket_id.strip().upper()
    for ticket in tickets:
        if isinstance(ticket, dict) and ticket.get("id", "").upper() == target_id:
            return ticket
    raise ValueError(f"Ticket '{ticket_id}' not found.")


def assign_ticket(tickets, ticket_id, staff_name):
    """Assign a ticket to a staff member.

    Validates that staff_name is non-empty text and ticket_id exists.
    """
    if not isinstance(staff_name, str) or not staff_name.strip():
        raise ValueError("Staff member name must be non-empty text.")
    ticket = find_ticket(tickets, ticket_id)
    ticket["assigned_to"] = staff_name.strip()
    return ticket


def update_status(tickets, ticket_id, new_status):
    """Transition ticket to a new status obeying lifecycle rules.

    Rules:
    1. Allowed statuses: open, in_progress, resolved.
    2. Unassigned ticket cannot be moved to in_progress.
    3. A resolved ticket cannot be modified directly unless explicitly reopened to open.
    """
    if not isinstance(new_status, str) or not new_status.strip():
        raise ValueError("Status must be non-empty text.")
    target_status = new_status.strip().lower()
    if target_status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Allowed statuses: open, in_progress, resolved.")

    ticket = find_ticket(tickets, ticket_id)
    current_status = ticket.get("status", "open")

    if current_status == "resolved" and target_status != "open":
        raise ValueError("Resolved tickets cannot be modified directly. Explicitly reopen the ticket first.")

    if target_status == "in_progress":
        assigned_to = ticket.get("assigned_to")
        if not assigned_to or not str(assigned_to).strip():
            raise ValueError("Cannot move unassigned ticket to in_progress. Assign a staff member first.")

    ticket["status"] = target_status
    return ticket


def reopen_ticket(tickets, ticket_id):
    """Explicitly reopen a resolved ticket by setting its status back to open."""
    ticket = find_ticket(tickets, ticket_id)
    if ticket.get("status") != "resolved":
        raise ValueError(f"Ticket '{ticket.get('id')}' is not resolved (current status: '{ticket.get('status')}').")
    ticket["status"] = "open"
    return ticket


def _extract_id_number(ticket):
    ticket_id = ticket.get("id", "")
    match = re.search(r"\d+", ticket_id)
    return int(match.group()) if match else 0


def get_work_queue(tickets):
    """Return open, unresolved tickets ordered by priority and numeric ID tie-breakers.

    Sort order: critical -> high -> medium -> low.
    Ties are broken using the earlier numeric ticket ID.
    Returns a new list without mutating the original collection order.
    """
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list.")
    unresolved = [t for t in tickets if isinstance(t, dict) and t.get("status") != "resolved"]
    return sorted(
        unresolved,
        key=lambda t: (
            PRIORITY_ORDER.get(t.get("priority", "low").lower(), 4),
            _extract_id_number(t),
        ),
    )
