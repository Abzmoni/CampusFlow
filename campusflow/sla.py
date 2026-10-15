"""SLA, time-handling, and overdue escalation module for CampusFlow Pro."""

from datetime import datetime, timezone, timedelta

# SLA thresholds in minutes as specified by CampusFlow Pro
SLA_MINUTES = {
    "critical": 60,
    "high": 240,
    "medium": 1440,
    "low": 2880,
}


def get_now(now=None):
    """Return a timezone-aware UTC datetime.

    If `now` is None, returns datetime.now(timezone.utc).
    If `now` is provided:
      - If string, parses ISO-8601.
      - If naive datetime, attaches timezone.utc.
      - If aware datetime, converts to UTC.
    """
    if now is None:
        return datetime.now(timezone.utc)
    if isinstance(now, str):
        return from_iso_utc(now)
    if isinstance(now, datetime):
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc)
    raise ValueError(f"Invalid timestamp/datetime value: {now}")


def to_iso_utc(dt):
    """Format a datetime as an ISO-8601 string with explicit UTC timezone."""
    if not isinstance(dt, datetime):
        raise ValueError("Expected datetime object.")
    aware = get_now(dt)
    return aware.isoformat()


def from_iso_utc(timestamp_str):
    """Parse an ISO-8601 timestamp string into a timezone-aware UTC datetime."""
    if not isinstance(timestamp_str, str) or not timestamp_str.strip():
        raise ValueError("Timestamp must be a non-empty string.")
    normalized = timestamp_str.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except Exception as exc:
        raise ValueError(f"Invalid ISO-8601 timestamp: '{timestamp_str}'") from exc
    return get_now(dt)


def calculate_due_at(priority, cycle_start):
    """Calculate the due_at ISO-8601 timestamp given priority and cycle_start.

    SLA thresholds:
      - critical = 60 minutes
      - high     = 240 minutes
      - medium   = 1440 minutes (24h)
      - low      = 2880 minutes (48h)
    """
    if not isinstance(priority, str) or priority.lower() not in SLA_MINUTES:
        raise ValueError(f"Unknown priority '{priority}' for SLA calculation.")
    p_key = priority.lower()
    start_dt = get_now(cycle_start)
    duration = timedelta(minutes=SLA_MINUTES[p_key])
    due_dt = start_dt + duration
    return to_iso_utc(due_dt)


def is_overdue(ticket, now=None):
    """Determine whether a ticket is strictly overdue.

    A ticket is overdue only when current UTC time is STRICTLY LATER than
    due_at AND its status is not resolved. At the exact due_at instant,
    it is not overdue.
    """
    if not isinstance(ticket, dict):
        raise ValueError("Ticket must be a dictionary.")

    status = ticket.get("status", "open")
    if status == "resolved":
        return False

    due_at_raw = ticket.get("due_at")
    if not due_at_raw:
        return False

    current_dt = get_now(now)
    due_dt = from_iso_utc(due_at_raw)

    # Strictly later than due_at (at exact due_at, it is not overdue)
    return current_dt > due_dt


def escalate_overdue(tickets, events, now=None, actor="system"):
    """Evaluate unresolved tickets and record an idempotent escalation event per cycle.

    Each overdue ticket creates exactly ONE escalation event in a given SLA cycle.
    Re-running this function at the same or later time will NOT create duplicates.
    Escalation does NOT assign the ticket, change its priority, or change its status.

    Returns a summary dictionary:
      {"newly_escalated": int, "already_escalated": int}
    """
    if not isinstance(tickets, list) or not isinstance(events, list):
        raise ValueError("Tickets and events must be lists.")

    current_dt = get_now(now)
    now_iso = to_iso_utc(current_dt)

    newly_escalated = 0
    already_escalated = 0

    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        if ticket.get("status") == "resolved":
            continue

        if is_overdue(ticket, current_dt):
            current_cycle = ticket.get("escalation_cycle", 0)
            if current_cycle == 0:
                # Mark as escalated in current cycle
                ticket["escalation_cycle"] = 1
                ticket["updated_at"] = now_iso

                # Append immutable audit event
                next_id = f"E{len(events) + 1:03d}"
                event = {
                    "event_id": next_id,
                    "ticket_id": ticket.get("id"),
                    "event_type": "ESCALATE",
                    "actor": actor,
                    "timestamp": now_iso,
                    "before_status": ticket.get("status"),
                    "after_status": ticket.get("status"),
                    "details": (
                        f"SLA breached for {ticket.get('priority')} priority ticket "
                        f"(due {ticket.get('due_at')}); escalated in cycle."
                    ),
                }
                events.append(event)
                newly_escalated += 1
            else:
                already_escalated += 1

    return {"newly_escalated": newly_escalated, "already_escalated": already_escalated}
