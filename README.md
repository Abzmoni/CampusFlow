# CampusFlow

A Python command-line helpdesk manager for technical support requests across Learn2Earn campus facilities (Wi-Fi outages, faulty hardware, software access, and technical environments).

Built during the **6-Hour Engineering Sprint**.

---

## Engineering Team & Ownership

- **Engineer A (Moses Kingsworth / Moe-Kingsworth)**:
  - Ticket creation and normalization (`campusflow/tickets.py`).
  - Strict input validation and atomic state management.
  - Ordered business priority engine (`calculate_priority`).
  - JSON persistence and atomic storage operations (`campusflow/storage.py`).
  - Unit test suite (`tests/test_tickets.py`, `tests/test_storage.py`).
  - Technical investigation and verification log (`docs/ai-learning-log.md`).
- **Engineer B (David Abah / Abzmoni)**:
  - Ticket assignment and lifecycle workflow management (`campusflow/workflow.py`).
  - Prioritized work queue with numeric ID tie-breakers.
  - System status and priority summary reports (`campusflow/reports.py`).
  - Interactive CLI main menu loop (`main.py`).
  - Workflow unit tests (`tests/test_workflow.py`).
  - Partner PR code review and technical defense.

---

## Quick Start & Setup

### Requirements
- Python 3.10+ (tested on Python 3.13)
- Uses Python standard library only (no external pip dependencies needed)

### Installation
Clone the repository and enter the directory:
```bash
git clone https://github.com/Moe-Kingsworth/CampusFlow.git
cd CampusFlow
```

### Running Automated Tests
Run the comprehensive test suite with verbose output:
```bash
python -m unittest discover -s tests -v
```

### Running the CLI Helpdesk
Launch the interactive console menu:
```bash
python main.py
```

Available Menu Options:
1. **Create Ticket**: Prompts for title, category, urgency, and affected users with priority auto-calculation.
2. **List / View Tickets**: Lists all tickets and inspects details for any selected ticket ID.
3. **Assign Ticket**: Assigns an existing ticket to a campus staff member.
4. **Update Status**: Manages status lifecycle (`open` -> `in_progress` -> `resolved`) or reopens resolved tickets.
5. **View Work Queue**: Displays open/in-progress tickets ordered by priority and numeric ID tie-breakers.
6. **Summary Reports**: Displays total counts and status/priority breakdown metrics.
7. **Exit**: Saves state to `data/tickets.json` and exits.

---

## Business Logic & Rules

### 1. Priority Calculation Engine
Priority is calculated by evaluating these rules **in strict order** (first match wins):
1. **Critical**: `urgency == 'high'` **AND** `affected_users >= 10`
2. **High**: `urgency == 'high'` **OR** `affected_users >= 10`
3. **Medium**: `urgency == 'medium'` **OR** `affected_users >= 3`
4. **Low**: All remaining valid tickets

### 2. Validation & Normalization
- **Title**: Required, non-empty text, whitespace trimmed.
- **Category**: Allowed values are `Network`, `Hardware`, `Software`, `Other` (case-insensitive input normalized).
- **Urgency**: Allowed values are `low`, `medium`, `high` (case-insensitive input normalized).
- **Affected Users**: Must be a strict positive integer (> 0). Booleans, decimals, strings, negative numbers, and zero are strictly rejected.
- **Ticket ID**: Sequentially generated (`T001`, `T002`, `T003`...) using `max(existing_numeric_ids) + 1` to guarantee uniqueness even across JSON reloads and gapped collections.

### 3. Workflow & Lifecycle Transitions
- Valid states: `open` -> `in_progress` -> `resolved`.
- An unassigned ticket **cannot** be transitioned to `in_progress`.
- A `resolved` ticket cannot be modified directly without an explicit reopen operation setting it back to `open`.

---

## Storage & Persistence

- Data is persisted to `data/tickets.json` using atomic file writes (temporary file write followed by replace) to prevent corruption.
- Missing file triggers a graceful fresh start with an empty ticket queue.
- Malformed JSON produces a clear `ValueError` rather than silently overwriting corrupted data.
- To reset state and start completely fresh, simply delete `data/tickets.json`.

---

## Project Structure

```
CampusFlow/
├── README.md                  # Project overview, architecture, and running guide
├── .gitignore                 # Ignores runtime data, __pycache__, and venv
├── main.py                    # Interactive CLI application
├── campusflow/
│   ├── __init__.py
│   ├── tickets.py             # Ticket creation, validation, priority calculation (Eng A)
│   ├── storage.py             # JSON load/save persistence engine (Eng A)
│   ├── workflow.py            # Assignment, status transitions, work queue (Eng B)
│   └── reports.py             # Metrics and reporting breakdowns (Eng B)
├── tests/
│   ├── test_tickets.py        # 14 unit tests for creation and priority (Eng A)
│   ├── test_storage.py        # 5 unit tests for JSON persistence (Eng A)
│   └── test_workflow.py       # Workflow, queue, and reporting tests (Eng B)
└── docs/
    ├── ai-learning-log.md     # Technical investigation and learning logs with experiments
    └── design-decisions.md    # Agreed architecture, contracts, and data models
```

---

## Current Verification Status
- **Integrated Test Suite**: **35 automated tests passing**:
  - 14 tests in `tests/test_tickets.py` (Required priority scenarios, boundary values, case normalization, atomic creation, sequential & gapped IDs).
  - 5 tests in `tests/test_storage.py` (Missing file handling, save/load round-trips, malformed JSON detection, atomic saves).
  - 16 tests in `tests/test_workflow.py` (Assignment, lifecycle progression, resolved ticket reopen locks, priority queue tie-breakers, report aggregations).

---

## Known Limitations & Future Enhancements
- **Storage Scope**: CampusFlow stores records in a single local JSON document (`data/tickets.json`), suitable for single-instance campus helpdesk operations. A concurrent multi-terminal setup would benefit from a file lock or database backend.
- **Search & Filtering**: Ticket inspection is currently keyed by ID. Future work could introduce title/description keyword searching.
- **Ticket Deletion / Archival**: The current specification does not specify ticket deletion. If deletion is implemented, a persisted high-water mark counter will prevent ID reuse.

---

## Pull Requests & Issue Tracking

- **Issue #1**: [Ticket Creation and Priority Engine](https://github.com/Moe-Kingsworth/CampusFlow/issues/1)
- **Engineer A PR**: Branch `feat/1-ticket-creation` (Moses Kingsworth)
- **Engineer B PR**: Branch `feat/2-ticket-workflow-reporting` (David Abah)
- **PR Index**: [GitHub Pull Requests](https://github.com/Moe-Kingsworth/CampusFlow/pulls)
