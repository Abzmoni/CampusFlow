"""Ticket operations that also record audit history."""

from copy import deepcopy

from campusflow.workflow import assign_ticket, find_ticket
from campusflow.history import record_event


def assign_with_history(
    tickets,
    events,
    ticket_id,
    staff_name,
    actor,
    now=None
):
    """Assign a ticket and record a successful ASSIGN event."""

    # Validate the collections
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list")

    if not isinstance(events, list):
        raise ValueError("Events must be a list")

    # Create copies of the current data
    tickets_copy = deepcopy(tickets)
    events_copy = deepcopy(events)

    # Perform the assignment on the copy
    ticket = assign_ticket(
        tickets_copy,
        ticket_id,
        staff_name
    )

    # Record the event on the copy
    record_event(
        events_copy,
        ticket["id"],
        "ASSIGN",
        actor,
        ticket["status"],
        ticket["status"],
        f"Assigned to {ticket['assigned_to']}",
        now=now
    )

    # Both steps succeeded, so update the original lists
    tickets[:] = tickets_copy
    events[:] = events_copy

    # Return the updated ticket
    return find_ticket(tickets, ticket_id)