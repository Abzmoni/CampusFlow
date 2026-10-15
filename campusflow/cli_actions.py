"""Application actions shared by the CampusFlow Pro CLI."""

from copy import deepcopy

from campusflow.duplicates import detect_duplicates
from campusflow.history import record_event
from campusflow.tickets import create_ticket


def create_with_history(
    tickets,
    events,
    title,
    category,
    urgency,
    affected_users,
    actor,
    confirm_duplicates=None,
    now=None,
):
    """
    Create a ticket and record its CREATE event.

    If possible duplicates exist, request confirmation through
    confirm_duplicates.

    Returns the new ticket, or None when creation is cancelled.

    Invalid operations must not change tickets or events.
    """

    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list")

    if not isinstance(events, list):
        raise ValueError("Events must be a list")

    # Check for existing unresolved tickets with a matching
    # category and normalized title.
    duplicates = detect_duplicates(
        tickets,
        category,
        title,
    )

    if duplicates:
        # No confirmation means we must not create the duplicate.
        if confirm_duplicates is None:
            return None

        if not callable(confirm_duplicates):
            raise ValueError("Confirmation must be a function")

        # Ask for confirmation before creating anything.
        confirmed = confirm_duplicates(duplicates)

        if confirmed is not True:
            return None

    # Prepare the changes on independent copies.
    tickets_copy = deepcopy(tickets)
    events_copy = deepcopy(events)

    # Create the ticket on the copy.
    ticket = create_ticket(
        tickets_copy,
        title,
        category,
        urgency,
        affected_users,
    )

    # Record its CREATE event on the copied history.
    record_event(
        events_copy,
        ticket["id"],
        "CREATE",
        actor,
        None,
        "open",
        f"Ticket created: {ticket['title']}",
        now=now,
    )

    # Commit both changes to the original collections.
    tickets[:] = tickets_copy
    events[:] = events_copy

    return tickets[-1]


def confirm_duplicate_warning(duplicate_ids):
    """Display duplicate IDs and ask the user to continue."""

    print("\n[Warning] Similar unresolved tickets already exist.")

    for ticket_id in duplicate_ids:
        print(f"  - {ticket_id}")

    answer = input(
        "\nCreate another ticket anyway? (yes/no): "
    ).strip().casefold()

    return answer in ("yes", "y")