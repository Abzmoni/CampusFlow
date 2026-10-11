# CampusFlow 🎓⚡

A Python command-line helpdesk manager for technical support requests across Learn2Earn campus facilities (Wi-Fi outages, faulty hardware, software access, and technical environments).

Built during the **6-Hour Engineering Sprint**.

---

## 👥 Engineering Team & Ownership

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

## 🚀 Quick Start & Setup

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

---

## 🧠 Business Logic & Rules

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
- Valid states: `open` ➔ `in_progress` ➔ `resolved`.
- An unassigned ticket **cannot** be transitioned to `in_progress`.
- A `resolved` ticket cannot be modified directly without an explicit reopen operation setting it back to `open`.

---

## 💾 Storage & Persistence

- Data is persisted to `data/tickets.json` using atomic file writes (temporary file write followed by replace) to prevent corruption.
- Missing file triggers a graceful fresh start with an empty ticket queue.
- Malformed JSON produces a clear `ValueError` rather than silently overwriting corrupted data.
- To reset state and start completely fresh, simply delete `data/tickets.json`.

---

## 📂 Project Structure

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

## 🧪 Current Verification Status

- **Engineer A Tests Passing**: 19 automated tests passing:
  - 14 tests in `tests/test_tickets.py` (Required priority scenarios, boundary values at 1, 2, 3, 9, 10, 11, case normalization, atomic creation, sequential & gapped IDs).
  - 5 tests in `tests/test_storage.py` (Missing file handling, save/load round-trips, malformed JSON detection, atomic saves).

---

## 🔗 Pull Requests & Issue Tracking

- **Issue #1**: [Ticket Creation and Priority Engine](https://github.com/Moe-Kingsworth/CampusFlow/issues/1)
- **Engineer A PR**: Branch `feat/1-ticket-creation` (Moses Kingsworth)
- **Engineer B PR**: Branch `feat/2-ticket-workflow-reporting` (David Abah)
- **PR Index**: [GitHub Pull Requests](https://github.com/Moe-Kingsworth/CampusFlow/pulls)
