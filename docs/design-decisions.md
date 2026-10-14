# Shared Design Decisions — CampusFlow Pro

## 1. Team Ownership & Responsibilities (CampusFlow Pro)

| Area | Owner | Branches & Files |
|------|-------|------------------|
| **Engineer A (David Abah / Abzmoni)** | Time handling, SLA engine, overdue detection, escalation idempotency, version-2 JSON persistence, corruption defense | `feat/11-sla-engine`<br>`feat/12-data-integrity`<br>`campusflow/sla.py`<br>`campusflow/storage.py`<br>`tests/test_sla.py`<br>`tests/test_storage_v2.py` |
| **Engineer B (Mohammed)** | Event history recording, duplicate ticket detection, SLA attention queue, metrics, CLI Knowledge Lab | `feat/13-audit-queues`<br>`feat/14-cli-knowledge-lab`<br>`campusflow/history.py`<br>`campusflow/knowledge_lab.py`<br>`tests/test_workflow_pro.py`<br>`tests/test_knowledge_lab.py` |
| **Shared / Team** | CLI integration, cross-PR reviews & approvals, regression test suite, documentation | `main.py`<br>`README.md`<br>`docs/ai-learning-log.md`<br>`docs/design-decisions.md`<br>`docs/learning-reflections.md` |

---

## 2. Upgraded Ticket Data Structure (CampusFlow Pro)

Every ticket preserves the original 8 fields and adds 4 SLA-tracking fields:

```python
{
    # Original 8 Base Fields:
    "id": "T001",                   # String: 'T' + 3 or more digits (e.g. 'T001', 'T1000')
    "title": "Campus Wi-Fi is down", # String: Non-empty, leading/trailing whitespace stripped
    "category": "Network",           # String: Exactly one of: 'Network', 'Hardware', 'Software', 'Other'
    "urgency": "high",               # String: Exactly one of: 'low', 'medium', 'high'
    "affected_users": 15,            # Int: Strict positive integer (> 0, type(x) is int)
    "priority": "critical",          # String: Calculated: 'critical', 'high', 'medium', or 'low'
    "status": "open",                # String: 'open', 'in_progress', or 'resolved'
    "assigned_to": None,             # String or None: None when new; staff name string when assigned

    # CampusFlow Pro SLA Fields:
    "created_at": "2026-10-14T10:00:00+00:00",  # String: ISO-8601 UTC timestamp
    "updated_at": "2026-10-14T10:00:00+00:00",  # String: ISO-8601 UTC timestamp of last modification
    "due_at": "2026-10-14T11:00:00+00:00",      # String: ISO-8601 UTC timestamp based on SLA cycle start
    "escalation_cycle": 0                        # Int: Per-cycle escalation marker (0 = not escalated, 1 = escalated in current cycle)
}
```

---

## 3. SLA Engine & Overdue Detection Contracts (Engineer A)

### SLA Threshold Durations
- **Critical**: 60 minutes (`timedelta(minutes=60)`)
- **High**: 240 minutes (`timedelta(minutes=240)`)
- **Medium**: 1440 minutes (`timedelta(minutes=1440)`, 24 hours)
- **Low**: 2880 minutes (`timedelta(minutes=2880)`, 48 hours)

### Function Signatures & Behavior

#### `campusflow.sla.calculate_due_at(priority: str, cycle_start: datetime | str) -> str`
- Adds the SLA duration matching `priority.lower()` to `cycle_start`.
- Returns ISO-8601 UTC string with explicit timezone.

#### `campusflow.sla.is_overdue(ticket: dict, now=None) -> bool`
- **Rule 1 (Resolved exemption)**: Tickets in status `"resolved"` are NEVER overdue, regardless of how much time has passed.
- **Rule 2 (Strict boundary)**: A ticket is overdue ONLY when current UTC time is STRICTLY LATER than `due_at` (`now > due_dt`). At the exact `due_at` instant, it is NOT overdue.

#### `campusflow.sla.escalate_overdue(tickets: list, events: list, now=None, actor="system") -> dict`
- **Idempotency**: Evaluates unresolved tickets. If a ticket is overdue and has `escalation_cycle == 0`, it transitions `escalation_cycle = 1`, updates `updated_at`, and appends an `ESCALATE` event to `events`.
- Re-running the command at the same or later time detects `escalation_cycle == 1` and creates NO duplicate events.
- **Invariant**: Escalation does NOT change ticket status, priority, or assignment.
- **Return value**: `{"newly_escalated": count_new, "already_escalated": count_already}`.

#### SLA Reopen Cycle Semantics
- When a resolved ticket is reopened via `reopen_ticket()`:
  - `created_at` is preserved unchanged.
  - `status` is set to `"open"`.
  - `updated_at` is updated to reopening timestamp.
  - A NEW SLA cycle begins: `due_at = calculate_due_at(priority, reopen_time)`.
  - The per-cycle escalation flag is cleared: `escalation_cycle = 0`.
  - If the ticket becomes overdue in this new cycle, it may legitimately escalate again.

---

## 4. History, Queues & Duplicate Detection Contracts (Engineer B)

### `campusflow.history.record_event(events: list, ticket_id: str, event_type: str, actor: str, before_status: str, after_status: str, details: str, now=None)`
- Appends an immutable audit event only after the business operation succeeds.
- Rejection of an operation leaves both tickets and events unchanged.

### `campusflow.workflow.detect_duplicates(tickets: list, category: str, title: str) -> list`
- Normalizes title (lowercase, strip, collapse repeated whitespace) and category.
- Compares against unresolved tickets (`status != 'resolved'`).
- Returns list of matching ticket IDs for operator confirmation (warn, do not block).
