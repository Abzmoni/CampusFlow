"""JSON persistence module for CampusFlow."""
import json
from pathlib import Path


def load_tickets(filepath="data/tickets.json"):
    """Load tickets from JSON file.

    If file does not exist, returns an empty list for a fresh start.
    If file contains malformed JSON or non-list root, raises ValueError with a clear message.
    """
    path = Path(filepath)
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to load tickets: malformed JSON in '{filepath}'.") from exc
    except Exception as exc:
        raise ValueError(f"Failed to read tickets file '{filepath}': {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(f"Invalid data in '{filepath}': expected a list of tickets.")

    return data


def save_tickets(tickets, filepath="data/tickets.json"):
    """Save tickets list to JSON file atomically.

    Ensures the parent directory exists, writes to a temporary file,
    and replaces the target file to avoid corruption.
    """
    if not isinstance(tickets, list):
        raise ValueError("Tickets collection must be a list.")

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(".tmp")
    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(tickets, handle, indent=2)
        temp_path.replace(path)
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        raise ValueError(f"Failed to save tickets to '{filepath}': {exc}") from exc
