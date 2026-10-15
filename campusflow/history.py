from datetime import datetime, timezone


# Record a successful ticket operation
def record_event(
    events,
    ticket_id,
    event_type,
    actor,
    before_status,
    after_status,
    details,
    now=None
):

    # Validate the events list
    if not isinstance(events, list):
        raise ValueError("Events must be a list")

    # Validate the ticket ID
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise ValueError("Ticket ID cannot be empty")

    # Define permitted event types
    allowed_events = (
        "CREATE",
        "ASSIGN",
        "START",
        "RESOLVE",
        "REOPEN",
        "ESCALATE"
    )

    if event_type not in allowed_events:
        raise ValueError("Invalid event type")

    # Validate the actor
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("Actor cannot be empty")

    # Validate details
    if not isinstance(details, str):
        raise ValueError("Details must be text")

    # Get the current UTC time
    if now is None:
        now = datetime.now(timezone.utc)

    # Validate the timestamp
    if not isinstance(now, datetime):
        raise ValueError("Invalid timestamp")

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone")

    now = now.astimezone(timezone.utc)

    # Find the next available event ID
    numbers = set()

    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Existing event must be a dictionary")

        event_id = event.get("event_id")

        if (
            not isinstance(event_id, str)
            or not event_id.startswith("E")
            or not event_id[1:].isdigit()
            or int(event_id[1:]) <= 0
        ):
            raise ValueError("Invalid existing event ID")

        number = int(event_id[1:])

        if number in numbers:
            raise ValueError("Duplicate event ID")

        numbers.add(number)

    next_number = max(numbers, default=0) + 1

    # Create the new event
    event = {
        "event_id": f"E{next_number:03d}",
        "ticket_id": ticket_id.strip().upper(),
        "event_type": event_type,
        "actor": actor.strip(),
        "timestamp": now.isoformat(),
        "before_status": before_status,
        "after_status": after_status,
        "details": details
    }

    # Append only after validation succeeds
    events.append(event)

    return event


# Get the history of a particular ticket
def get_ticket_history(events, ticket_id):

    if not isinstance(events, list):
        raise ValueError("Events must be a list")

    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise ValueError("Invalid ticket ID")

    ticket_id = ticket_id.strip().upper()

    history = []

    # Find events belonging to the ticket
    for event in events:
        if event["ticket_id"] == ticket_id:
            history.append(event.copy())

    # Sort by timestamp and numeric event ID
    return sorted(
        history,
        key=lambda event: (
            datetime.fromisoformat(event["timestamp"]),
            int(event["event_id"][1:])
        )
    )