# Shared Design Decisions — CampusFlow

## 1. Team Ownership & Responsibilities

| Area | Owner | Files |
|------|-------|-------|
| **Engineer A (Moses Kingsworth)** | Ticket creation, validation, priority calculation, JSON persistence | `campusflow/tickets.py`<br>`campusflow/storage.py`<br>`tests/test_tickets.py`<br>`tests/test_storage.py` |
| **Engineer B (David Abah)** | Assignment, lifecycle workflow, work queue, reporting | `campusflow/workflow.py`<br>`campusflow/reports.py`<br>`tests/test_workflow.py` |
| **Shared / Team** | CLI main menu loop, cross-PR reviews, system integration tests, documentation | `main.py`<br>`README.md`<br>`docs/ai-learning-log.md`<br>`docs/design-decisions.md` |

---

## 2. Shared Ticket Data Structure

Every ticket record is a Python dictionary with the following 8 required fields:

```python
{
    "id": "T001",                   # String: 'T' + 3 or more digits (e.g. 'T001', 'T099', 'T1000')
    "title": "Campus Wi-Fi is down", # String: Non-empty, leading/trailing whitespace stripped
    "category": "Network",           # String: Exactly one of: 'Network', 'Hardware', 'Software', 'Other'
    "urgency": "high",               # String: Exactly one of: 'low', 'medium', 'high'
    "affected_users": 15,            # Int: Strict positive integer (> 0, type(x) is int)
    "priority": "critical",          # String: Calculated: 'critical', 'high', 'medium', or 'low'
    "status": "open",                # String: 'open', 'in_progress', or 'resolved'
    "assigned_to": None              # String or None: None when new; staff name string when assigned
}
```

---

## 3. Function Contracts — Engineer A (Implemented & Verified)

### `campusflow.tickets.calculate_priority(urgency: str, affected_users: int) -> str`
- **Rules evaluated in strict order**:
  1. `urgency == "high" and affected_users >= 10` → `"critical"`
  2. `urgency == "high" or affected_users >= 10` → `"high"`
  3. `urgency == "medium" or affected_users >= 3` → `"medium"`
  4. All remaining valid combinations → `"low"`
- **Validation**: Rejects invalid urgency or non-positive integers with `ValueError`. Urgency is normalized (case-insensitive, whitespace trimmed).

### `campusflow.tickets.create_ticket(tickets: list, title: str, category: str, urgency: str, affected_users: int) -> dict`
- **Behavior**: Validates all arguments, derives unique sequential ID (`_next_ticket_id`), sets initial status to `"open"` and `assigned_to` to `None`.
- **Atomicity**: Validates all fields BEFORE mutating `tickets`. If any input is invalid, raises `ValueError` and leaves `tickets` unchanged.
- **Return value**: The newly created ticket dictionary.

### `campusflow.storage.load_tickets(filepath: str = "data/tickets.json") -> list`
- Returns empty list `[]` if the file does not exist (clean startup).
- If file contains malformed JSON or a non-list root, raises `ValueError` with a descriptive message to prevent data loss or silent erasure.

### `campusflow.storage.save_tickets(tickets: list, filepath: str = "data/tickets.json") -> None`
- Ensures parent directories exist.
- Performs an atomic write using a temporary file and replace to eliminate file corruption risks.

---

## 4. Function Contracts — Engineer B (Specification for Implementation)

### `campusflow.workflow.assign_ticket(tickets: list, ticket_id: str, staff_name: str) -> dict`
- **Inputs**: `tickets` list, `ticket_id` string, `staff_name` string.
- **Validation**:
  - `staff_name` must be non-empty text (whitespace trimmed).
  - `ticket_id` must match an existing ticket in `tickets`. If not found, raise `ValueError(f"Ticket '{ticket_id}' not found.")`.
- **Behavior**: Sets `ticket["assigned_to"] = staff_name.strip()`.
- **Return value**: The updated ticket dictionary.

### `campusflow.workflow.update_status(tickets: list, ticket_id: str, new_status: str) -> dict`
- **Allowed statuses**: `"open"`, `"in_progress"`, `"resolved"`.
- **Lifecycle rules**:
  - **Rule 1 (Assignment gate)**: An unassigned ticket (`assigned_to is None` or empty) CANNOT be moved to `"in_progress"`. Must raise `ValueError("Cannot move unassigned ticket to in_progress.")`.
  - **Rule 2 (Valid sequence)**: Normal progression is `"open"` → `"in_progress"` → `"resolved"`.
  - **Rule 3 (Resolved lock)**: A ticket in `"resolved"` status cannot be directly transitioned to `"in_progress"`. It must first be explicitly reopened to `"open"`.
- **Return value**: The updated ticket dictionary.

### `campusflow.workflow.reopen_ticket(tickets: list, ticket_id: str) -> dict`
- Reopens a `"resolved"` ticket by setting `ticket["status"] = "open"`.
- If ticket is not in `"resolved"` status, raises `ValueError`.

### `campusflow.workflow.get_work_queue(tickets: list) -> list`
- **Filter**: Returns open, unresolved tickets (`status != "resolved"`).
- **Sort Order**:
  1. Priority order: `"critical"` (1st), `"high"` (2nd), `"medium"` (3rd), `"low"` (4th).
  2. Tie-breaker: Numeric ID in ascending order (e.g. `T001` before `T003`).
- **Safety**: Returns a new list; does not mutate the in-memory order of `tickets`.

### `campusflow.reports.generate_report(tickets: list) -> dict`
- Returns a summary dictionary:
  ```python
  {
      "total": int,
      "by_status": {"open": int, "in_progress": int, "resolved": int},
      "by_priority": {"critical": int, "high": int, "medium": int, "low": int}
  }
  ```
- Handles empty ticket list (`len(tickets) == 0`) correctly with zeros.

---

## 5. CLI Interaction and Error Handling (`main.py`)

- `main.py` loads `tickets = load_tickets()` on startup.
- The interactive CLI runs in a loop until the user selects Exit.
- All user inputs are parsed at the CLI boundary (e.g., `int(raw_input)`).
- All business function calls are wrapped in `try...except ValueError as err:` blocks:
  - Error messages are printed in friendly format.
  - The shared collection is not corrupted.
- On successful mutating actions (`create_ticket`, `assign_ticket`, `update_status`, `reopen_ticket`), `save_tickets(tickets)` is called immediately.
