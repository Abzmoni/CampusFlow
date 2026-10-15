"""Engineer B's ticket workflow, assignment, and work queue management."""

import re
from campusflow.sla import calculate_due_at, get_now, to_iso_utc


# Allowed ticket statuses
ALLOWED_STATUSES = ("open", "in_progress", "resolved")


# Priority ranking
PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3
}


# Find a ticket using its ID
def find_ticket(tickets, ticket_id):

    # Check that tickets is a list
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list.")

    # Check that ticket ID is valid
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise ValueError("Ticket ID must be non-empty text.")

    # Remove spaces and convert ID to uppercase
    target_id = ticket_id.strip().upper()

    # Search for the ticket
    for ticket in tickets:

        if (
            isinstance(ticket, dict)
            and ticket.get("id", "").upper() == target_id
        ):
            return ticket

    # Raise error if ticket is not found
    raise ValueError(f"Ticket '{ticket_id}' not found.")


# Assign a staff member to a ticket
def assign_ticket(tickets, ticket_id, staff_name, now=None):

    # Validate staff name
    if not isinstance(staff_name, str) or not staff_name.strip():
        raise ValueError("Staff member name must be non-empty text.")

    # Find the requested ticket
    ticket = find_ticket(tickets, ticket_id)

    # Prevent assigning resolved tickets
    if ticket["status"] == "resolved":
        raise ValueError(
            "Cannot assign a resolved ticket. Reopen it first."
        )

    # Assign staff member
    ticket["assigned_to"] = staff_name.strip()

    if "updated_at" in ticket or now is not None:
        ticket["updated_at"] = to_iso_utc(get_now(now))

    return ticket


# Change a ticket's status
def update_status(tickets, ticket_id, new_status, now=None):

    # Define valid status transitions
    allowed_transitions = {
        "open": ["in_progress"],
        "in_progress": ["resolved"],
        "resolved": []
    }

    # Validate new status
    if not isinstance(new_status, str) or not new_status.strip():
        raise ValueError("Status must be non-empty text.")

    # Normalize status
    target_status = new_status.strip().lower()

    # Check if the requested status exists
    if target_status not in ALLOWED_STATUSES:
        raise ValueError(
            "Invalid status. Use open, in_progress or resolved."
        )

    # Find the ticket
    ticket = find_ticket(tickets, ticket_id)

    # Get the ticket's current status
    current_status = ticket.get("status")

    # Check whether current status is valid
    if current_status not in allowed_transitions:
        raise ValueError("Invalid current ticket status.")

    # Check whether the transition is allowed
    if target_status not in allowed_transitions[current_status]:
        raise ValueError(
            f"Invalid status transition: "
            f"{current_status} to {target_status}."
        )

    # A ticket must be assigned before work begins
    if target_status == "in_progress":

        assigned_to = ticket.get("assigned_to")

        if (
            not isinstance(assigned_to, str)
            or not assigned_to.strip()
        ):
            raise ValueError(
                "Cannot start work on an unassigned ticket."
            )

    # Update ticket status
    ticket["status"] = target_status

    if "updated_at" in ticket or now is not None:
        ticket["updated_at"] = to_iso_utc(get_now(now))

    return ticket


# Reopen a resolved ticket
def reopen_ticket(tickets, ticket_id, now=None):

    # Find the ticket
    ticket = find_ticket(tickets, ticket_id)

    # Only resolved tickets can be reopened
    if ticket.get("status") != "resolved":
        raise ValueError(
            f"Ticket '{ticket.get('id')}' is not resolved "
            f"(current status: '{ticket.get('status')}')."
        )

    # Reopen the ticket
    ticket["status"] = "open"

    now_dt = get_now(now)
    ticket["updated_at"] = to_iso_utc(now_dt)

    if "priority" in ticket:
        ticket["due_at"] = calculate_due_at(ticket["priority"], now_dt)

    ticket["escalation_cycle"] = 0

    return ticket


# Extract the numeric part of a ticket ID
def _extract_id_number(ticket):

    ticket_id = ticket.get("id", "")

    # Find numbers inside the ticket ID
    match = re.search(r"\d+", ticket_id)

    # Return the number if found
    return int(match.group()) if match else 0


# Display tickets according to priority
def get_work_queue(tickets):

    # Validate tickets collection
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list.")

    # Get unresolved tickets
    unresolved = [
        ticket
        for ticket in tickets
        if (
            isinstance(ticket, dict)
            and ticket.get("status") != "resolved"
        )
    ]

    # Sort tickets by priority and numeric ticket ID
    return sorted(
        unresolved,
        key=lambda ticket: (
            PRIORITY_ORDER.get(
                ticket.get("priority", "low").lower(),
                4
            ),
            _extract_id_number(ticket)
        )
    )