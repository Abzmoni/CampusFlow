"""Ticket operations with automatic audit history."""

from copy import deepcopy

from campusflow.workflow import (
    assign_ticket,
    find_ticket,
    update_status,
)

from campusflow.history import record_event


# Assign a ticket and record the assignment
def assign_with_history(
    tickets,
    events,
    ticket_id,
    staff_name,
    actor,
    now=None
):
    # Validate the collections
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list")

    if not isinstance(events, list):
        raise ValueError("Events must be a list")

    # Create independent copies
    tickets_copy = deepcopy(tickets)
    events_copy = deepcopy(events)

    # Assign the ticket on the copied data
    ticket = assign_ticket(
        tickets_copy,
        ticket_id,
        staff_name
    )

    # Record the successful assignment
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

    # Apply both changes after successful validation
    tickets[:] = tickets_copy
    events[:] = events_copy

    return find_ticket(tickets, ticket_id)


# Change a ticket's status and record its history
def update_status_with_history(
    tickets,
    events,
    ticket_id,
    new_status,
    actor,
    now=None
):
    # Validate the collections
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list")

    if not isinstance(events, list):
        raise ValueError("Events must be a list")

    # Create independent copies
    tickets_copy = deepcopy(tickets)
    events_copy = deepcopy(events)

    # Find the ticket before changing its status
    ticket = find_ticket(tickets_copy, ticket_id)

    # Remember the previous status
    before_status = ticket["status"]

    # Change the status on the copied data
    updated_ticket = update_status(
        tickets_copy,
        ticket_id,
        new_status
    )

    # Get the new status
    after_status = updated_ticket["status"]

    # Determine which event to record
    if before_status == "open" and after_status == "in_progress":
        event_type = "START"

    elif before_status == "in_progress" and after_status == "resolved":
        event_type = "RESOLVE"

    else:
        raise ValueError("Unsupported status transition")

    # Record the successful status change
    record_event(
        events_copy,
        updated_ticket["id"],
        event_type,
        actor,
        before_status,
        after_status,
        f"Status changed from {before_status} to {after_status}",
        now=now
    )

    # Apply changes only when both operations succeed
    tickets[:] = tickets_copy
    events[:] = events_copy

    return find_ticket(tickets, ticket_id)