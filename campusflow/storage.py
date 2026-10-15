"""JSON persistence module for CampusFlow Pro (Version 2 Schema)."""

import json
import os
import re
from pathlib import Path

SCHEMA_VERSION = 2

REQUIRED_TICKET_FIELDS = {
    "id",
    "title",
    "category",
    "urgency",
    "affected_users",
    "priority",
    "status",
    "assigned_to",
}

REQUIRED_EVENT_FIELDS = {
    "event_id",
    "ticket_id",
    "event_type",
    "actor",
    "timestamp",
    "before_status",
    "after_status",
    "details",
}


def validate_ticket_schema(ticket):
    """Validate that a ticket dictionary conforms to the required schema."""
    if not isinstance(ticket, dict):
        raise ValueError("Ticket record must be a dictionary.")
    missing = REQUIRED_TICKET_FIELDS - ticket.keys()
    if missing:
        raise ValueError(f"Ticket missing required field(s): {sorted(missing)}")
    if not isinstance(ticket["id"], str) or not re.fullmatch(r"T[0-9]{3,}", ticket["id"]):
        raise ValueError(f"Invalid ticket ID format: '{ticket.get('id')}'")
    if type(ticket["affected_users"]) is not int or ticket["affected_users"] <= 0:
        raise ValueError(f"Ticket {ticket['id']}: affected_users must be a positive integer.")
    return True


def validate_event_schema(event):
    """Validate that an event dictionary conforms to the required schema."""
    if not isinstance(event, dict):
        raise ValueError("Event record must be a dictionary.")
    missing = REQUIRED_EVENT_FIELDS - event.keys()
    if missing:
        raise ValueError(f"Event missing required field(s): {sorted(missing)}")
    if not isinstance(event["event_id"], str) or not str(event["event_id"]).strip():
        raise ValueError("Event event_id must be non-empty string.")
    return True


def load_data(filepath="data/tickets.json"):
    """Load Version 2 schema data from JSON file.

    Returns a dictionary:
      {"schema_version": 2, "tickets": [...], "events": [...]}

    If file does not exist, returns an empty V2 structure (fresh start).
    If file contains malformed JSON or invalid schema, raises ValueError
    with a clear message without altering any in-memory state.
    """
    path = Path(filepath)
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "tickets": [], "events": []}

    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to load data: malformed JSON in '{filepath}'.") from exc
    except Exception as exc:
        raise ValueError(f"Failed to read data file '{filepath}': {exc}") from exc

    # Legacy V1 detection: if root is a list, validate tickets
    if isinstance(raw, list):
        for ticket in raw:
            validate_ticket_schema(ticket)
        return {"schema_version": SCHEMA_VERSION, "tickets": raw, "events": []}

    if not isinstance(raw, dict) and not isinstance(raw, list):
        raise ValueError(f"Invalid data format in '{filepath}': expected a list of tickets.")

    version = raw.get("schema_version") if isinstance(raw, dict) else None
    if version != SCHEMA_VERSION:
        raise ValueError(f"Invalid data in '{filepath}': expected a list of tickets or schema_version {SCHEMA_VERSION}.")

    tickets = raw.get("tickets")
    if not isinstance(tickets, list):
        raise ValueError(f"Invalid data in '{filepath}': 'tickets' must be a list.")

    events = raw.get("events")
    if not isinstance(events, list):
        raise ValueError(f"Invalid data in '{filepath}': 'events' must be a list.")

    # Validate all tickets and events before accepting
    for ticket in tickets:
        validate_ticket_schema(ticket)

    for event in events:
        validate_event_schema(event)

    return {"schema_version": SCHEMA_VERSION, "tickets": tickets, "events": events}


def save_data(data, filepath="data/tickets.json"):
    """Save Version 2 schema data to JSON file atomically.

    Validates schema before writing. Writes to a temporary file (.tmp)
    and uses atomic replacement to prevent partial-write corruption.
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary.")

    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Data schema_version must be {SCHEMA_VERSION}.")

    tickets = data.get("tickets")
    events = data.get("events")
    if not isinstance(tickets, list) or not isinstance(events, list):
        raise ValueError("Data 'tickets' and 'events' must be lists.")

    for ticket in tickets:
        validate_ticket_schema(ticket)

    for event in events:
        validate_event_schema(event)

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(".tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        temp_path.replace(path)
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        raise ValueError(f"Failed to save data to '{filepath}': {exc}") from exc


def migrate_legacy_file(legacy_filepath, target_filepath):
    """Explicitly migrate an original list-style CampusFlow JSON file to Version 2.

    Preserves the original legacy file completely unchanged.
    Never fabricates historical events or timestamps.
    """
    legacy_path = Path(legacy_filepath)
    if not legacy_path.exists():
        raise ValueError(f"Legacy file '{legacy_filepath}' not found.")

    with legacy_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, list):
        raise ValueError(f"Expected legacy list-style JSON in '{legacy_filepath}'.")

    for ticket in raw:
        validate_ticket_schema(ticket)

    v2_data = {
        "schema_version": SCHEMA_VERSION,
        "tickets": raw,
        "events": [],
    }
    save_data(v2_data, target_filepath)
    return v2_data


# Backward-compatibility wrappers for original CampusFlow operations:
def load_tickets(filepath="data/tickets.json"):
    """Backward-compatible load returning ticket list from storage."""
    data = load_data(filepath)
    return data["tickets"]


def save_tickets(tickets, filepath="data/tickets.json"):
    """Backward-compatible save storing ticket list in Version 2 schema."""
    if not isinstance(tickets, list):
        raise ValueError("Tickets collection must be a list.")
    # Check if existing events exist to avoid erasing them
    existing_events = []
    path = Path(filepath)
    if path.exists():
        try:
            existing = load_data(filepath)
            existing_events = existing.get("events", [])
        except Exception:
            existing_events = []

    v2_data = {
        "schema_version": SCHEMA_VERSION,
        "tickets": tickets,
        "events": existing_events,
    }
    save_data(v2_data, filepath)
