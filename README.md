# CampusFlow Pro

A Python command-line helpdesk manager for technical support requests across Learn2Earn campus facilities (Wi-Fi outages, faulty hardware, software access, and technical environments).

Upgraded during the **CampusFlow Pro AI-Native Engineering Challenge** with Service Level Agreements (SLAs), idempotent escalation, append-only audit trails, duplicate ticket warnings, enhanced queues, an interactive Engineering Knowledge Lab, and Version-2 atomic JSON persistence.

---

## Engineering Team & Ownership

- **Engineer A (David Abah / @Abzmoni)**:
  - Timezone-aware UTC time handling, clock injection (`now=None`), and ISO-8601 formatting (`campusflow/sla.py`).
  - SLA due date calculation and strict boundary overdue detection (`calculate_due_at`, `is_overdue`).
  - Idempotent ticket escalation engine (`escalate_overdue`).
  - Version-2 JSON schema persistence, validation, and corruption rejection (`campusflow/storage.py`).
  - Checkpoints A1 through A6 test suites (`tests/test_sla.py`, `tests/test_storage_v2.py`).
- **Engineer B (Mohammed / @midi2154)**:
  - Duplicate ticket detection and title normalisation (`campusflow/duplicates.py`).
  - Append-only event history logging and retrieval (`campusflow/history.py`).
  - Audited ticket workflow operations (`campusflow/audited_workflow.py`, `campusflow/cli_actions.py`).
  - SLA Attention Queue and enhanced summary reporting (`campusflow/sla_queue.py`, `campusflow/reports.py`).
  - Interactive Engineering Knowledge Lab module (`campusflow/knowledge_lab.py`).
  - Checkpoints B1 through B6 test suites (`tests/test_duplicates.py`, `tests/test_history.py`, `tests/test_audited_workflow.py`, `tests/test_sla_queue.py`, `tests/test_enhanced_reports.py`, `tests/test_knowledge_lab.py`).

---

## Quick Start & Setup

### Requirements
- Python 3.10+ (tested on Python 3.12 and 3.13)
- Uses Python standard library only (no third-party runtime frameworks)

### Installation
Clone the repository and enter the directory:
```bash
git clone https://github.com/Abzmoni/CampusFlow.git
cd CampusFlow
```

### Running Automated Tests
Run the entire comprehensive test suite (113+ tests) with verbose output:
```bash
python -m unittest discover -s tests -v
```

### Running the CLI Helpdesk
Launch the interactive console menu:
```bash
python main.py
```

Available Menu Options:
1. **Create Ticket (with Duplicate Warning)**: Prompts for title, category, urgency, affected users, and operator label; checks for duplicate open tickets before creation.
2. **List / View Tickets**: Lists all tickets and inspects details (priority, status, SLA due date, cycle escalation) for any selected ticket ID.
3. **Assign Ticket to Staff**: Assigns an unresolved ticket to a staff member with an audited `ASSIGN` event.
4. **Update Ticket Workflow Status**: Progresses tickets (`open` -> `in_progress` -> `resolved`) or reopens resolved tickets into a fresh SLA cycle with audited `START`, `RESOLVE`, and `REOPEN` events.
5. **View Prioritized Work Queue (Original)**: Displays unresolved tickets ordered by priority and numeric ID tie-breakers.
6. **View SLA Attention Queue (Pro)**: Displays unresolved tickets sorted by overdue items first, earliest deadline ascending, and numeric ID tie-breakers.
7. **Check and Escalate Overdue Tickets (Pro)**: Evaluates unresolved tickets against SLA deadlines and records idempotent `ESCALATE` events.
8. **View Ticket Audit History (Pro)**: Displays the chronological history of state changes and operator actions for any ticket.
9. **View Summary Reports (Enhanced SLA Analytics)**: Displays totals, status/priority distributions, overdue count, and cycle escalations.
10. **Engineering Knowledge Lab**: Interactive 10-question quiz with score tracking, revision topics, and written explanation logging.
11. **Exit**: Atomically persists runtime state to `data/tickets.json` and exits.

---

## Business Rules & Technical Specifications

### 1. Priority Calculation Matrix
Priority is determined strictly in precedence order:
1. **Critical**: `urgency == 'high'` AND `affected_users >= 10`
2. **High**: `urgency == 'high'` OR `affected_users >= 10`
3. **Medium**: `urgency == 'medium'` OR `affected_users >= 3`
4. **Low**: All remaining valid tickets

### 2. Service Level Agreements (SLAs) & Overdue Rules
- **Critical**: 60 minutes
- **High**: 240 minutes (4 hours)
- **Medium**: 1440 minutes (24 hours)
- **Low**: 2880 minutes (48 hours)
- **Strict Boundary**: A ticket is overdue if and only if `now > due_at` (strict inequality) AND its status is not `resolved`. At the exact `due_at` instant, it is not overdue.
- **Reopen SLA Cycle**: Reopening a resolved ticket begins a fresh SLA cycle starting at the reopening timestamp, updates `due_at`, preserves `created_at`, and clears the per-cycle escalation flag (`escalation_cycle = 0`).

### 3. Escalation Idempotency
- Running escalation evaluates overdue tickets.
- If an overdue ticket has `escalation_cycle == 0`, it transitions `escalation_cycle = 1` and creates exactly one `ESCALATE` event.
- Re-running the command at the same or later time detects `escalation_cycle == 1` and generates zero duplicate events.
- Escalation does not modify ticket status, priority, or assignment.

### 4. Append-Only Audit Trail
- Successful operations append an immutable event:
  - Required fields: `event_id` (`E001`, `E002`...), `ticket_id`, `event_type`, `actor`, `timestamp` (ISO-8601 UTC), `before_status`, `after_status`, `details`.
  - Allowed event types: `CREATE`, `ASSIGN`, `START`, `RESOLVE`, `REOPEN`, `ESCALATE`.
  - Failure Atomicity: Rejected or invalid operations leave tickets and events completely unchanged.

### 5. Duplicate Ticket Detection
- Compares normalized title (casefold, stripped, collapsed whitespace) and category against unresolved tickets.
- Warns the operator and presents matching IDs before creation.
- Confirmed duplicates may be created; declined warnings create neither a ticket nor an event.

### 6. Storage & Defensive Persistence (Schema Version 2)
- Saved to `data/tickets.json` with structure:
  ```json
  {
    "schema_version": 2,
    "tickets": [...],
    "events": [...]
  }
  ```
- Two-phase validation validates all tickets and events before modifying in-memory state.
- Atomic writes write to a hidden `.tmp` file and call `os.replace` to prevent partial writes.
- Malformed JSON raises `ValueError` and leaves active in-memory state intact.

---

## Project Structure

```
CampusFlow/
├── README.md                           # Project overview, architecture, and manual
├── .gitignore                          # Ignores runtime data, __pycache__, and venv
├── main.py                             # Interactive CLI application
├── campusflow/
│   ├── __init__.py
│   ├── tickets.py                      # Ticket creation and validation
│   ├── sla.py                          # SLA calculation, boundaries, and escalation
│   ├── storage.py                      # Version 2 JSON persistence and atomic write
│   ├── workflow.py                     # Status transitions and priority work queue
│   ├── duplicates.py                   # Title normalisation and duplicate detection
│   ├── history.py                      # Append-only audit trail and history retrieval
│   ├── audited_workflow.py             # Atomic audited ticket operations
│   ├── cli_actions.py                  # CLI actions with duplicate confirmation
│   ├── sla_queue.py                    # Time-critical SLA Attention Queue
│   ├── reports.py                      # Helpdesk analytics and enhanced SLA metrics
│   └── knowledge_lab.py                # Engineering Knowledge Lab quiz module
├── tests/
│   ├── test_tickets.py                 # Ticket creation & priority tests
│   ├── test_storage.py                 # Baseline storage tests
│   ├── test_workflow.py                # Baseline workflow and queue tests
│   ├── test_sla.py                     # SLA boundaries and escalation tests (A1-A4)
│   ├── test_storage_v2.py              # Version 2 schema and atomic tests (A5-A6)
│   ├── test_duplicates.py              # Title normalisation & duplicate guard tests
│   ├── test_history.py                 # Append-only event recording & history tests
│   ├── test_audited_workflow.py        # Failure atomicity & audited transition tests
│   ├── test_cli_actions.py             # Duplicate confirmation and creation tests
│   ├── test_sla_queue.py               # SLA attention queue sorting tests
│   ├── test_enhanced_reports.py        # Enhanced reporting and SLA metric tests
│   ├── test_workflow_pro.py            # Workflow guards and transition lock tests
│   └── test_knowledge_lab.py           # Knowledge Lab quiz and scoring tests
└── docs/
    ├── ai-learning-log.md              # Engineering learning interactions and experiments
    ├── design-decisions.md             # Contracts, data shapes, and architectural records
    └── engineer_a_checkpoints_defense.md # Checkpoints A1-A6 evidence and defense questions
```

---

## Verification & Test Suite Health

Run the full suite:
```bash
python -m unittest discover tests
```
**Current Test Health:** **113 passing tests** across 13 test modules covering all base features, SLA boundaries, escalation idempotency, audit trail invariants, duplicate detection, atomic file persistence, and the Knowledge Lab.
