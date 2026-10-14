# Engineer A Checkpoints & Audit Defense — CampusFlow Pro

**Fellow / Engineer A:** David Abah (@Abzmoni)  
**Role:** Time Handling, SLA Engine, Escalation Idempotency, Version-2 JSON Storage & Data Integrity  
**Branches:** `feat/11-sla-engine`, `feat/12-data-integrity`  

---

## 1. Automated Checkpoint Demonstrations (A1 – A6)

| Checkpoint | Requirement | Test Function | Test File | Verification Command |
| :--- | :--- | :--- | :--- | :--- |
| **A1** | Show a critical ticket exactly 60 minutes old. Is it overdue? | `test_checkpoint_a1_critical_at_exact_60_minutes_is_not_overdue` | `tests/test_sla.py` | `python -m unittest tests.test_sla.SlaEngineTests.test_checkpoint_a1_critical_at_exact_60_minutes_is_not_overdue` |
| **A2** | Show the SAME ticket at 61 minutes. Is it overdue? | `test_checkpoint_a2_critical_at_61_minutes_is_overdue` | `tests/test_sla.py` | `python -m unittest tests.test_sla.SlaEngineTests.test_checkpoint_a2_critical_at_61_minutes_is_overdue` |
| **A3** | Run escalation twice: what event count do you expect? | `test_checkpoint_a3_escalation_idempotency_within_cycle` | `tests/test_sla.py` | `python -m unittest tests.test_sla.SlaEngineTests.test_checkpoint_a3_escalation_idempotency_within_cycle` |
| **A4** | After resolve and reopen, how does the due date change? | `test_checkpoint_a4_reopen_starts_fresh_sla_cycle_and_clears_escalation` | `tests/test_sla.py` | `python -m unittest tests.test_sla.SlaEngineTests.test_checkpoint_a4_reopen_starts_fresh_sla_cycle_and_clears_escalation` |
| **A5** | Demonstrate safe restart and corruption rejection. | `test_checkpoint_a5_corrupt_json_rejects_and_preserves_valid_state` | `tests/test_storage_v2.py` | `python -m unittest tests.test_storage_v2.StorageV2Tests.test_checkpoint_a5_corrupt_json_rejects_and_preserves_valid_state` |
| **A6** | Prove that an invalid operation cannot leave a partial event or malformed file. | `test_checkpoint_a6_invalid_schema_rejects_without_partial_writes` | `tests/test_storage_v2.py` | `python -m unittest tests.test_storage_v2.StorageV2Tests.test_checkpoint_a6_invalid_schema_rejects_without_partial_writes` |

---

## 2. Deep Dive: Implementation Rationale for Checkpoints

### Checkpoint A1 & A2: Strict Boundary Evaluation
* **Code Reference:** `campusflow.sla.is_overdue(ticket, now=None)`
* **Rule:** A ticket is overdue if and only if `now > due_at` (strict inequality) AND `ticket['status'] != 'resolved'`.
* **Behavior at 60m:** `now == due_at`. Strict inequality evaluates to `False`. At the exact deadline instant, the support team still has that zero-second window before breach.
* **Behavior at 61m:** `now > due_at`. Evaluates to `True`. The ticket is officially breached and eligible for escalation.

### Checkpoint A3: Escalation Idempotency
* **Code Reference:** `campusflow.sla.escalate_overdue(tickets, events, now=None, actor="system")`
* **Rule:** Evaluating an overdue ticket once sets `ticket['escalation_cycle'] = 1` and appends an `ESCALATE` event.
* **Behavior on Rerun:** On second execution at the same or later time, the ticket has `escalation_cycle == 1`. It is categorized as `already_escalated` and skipped. Zero duplicate events are appended. Returns `{"newly_escalated": 0, "already_escalated": 1}`.

### Checkpoint A4: Reopening & SLA Cycle Reset
* **Code Reference:** `campusflow.workflow.reopen_ticket(tickets, ticket_id, now=None)`
* **Rule:** Reopening a resolved ticket begins a fresh SLA cycle.
  - `created_at` is preserved unchanged (audit continuity).
  - `status` transitions to `"open"`.
  - `due_at` is recalculated from the reopening instant: `calculate_due_at(priority, reopen_time)`.
  - `escalation_cycle` is reset to `0` (clearing per-cycle escalation flag).
  - If the reopened ticket breaches SLA in its new cycle, it may legitimately escalate once more.

### Checkpoint A5: Corrupt File Rejection & In-Memory State Preservation
* **Code Reference:** `campusflow.storage.load_data(filepath)`
* **Rule:** When attempting to load a file containing malformed JSON syntax or schema violations, `load_data` raises `ValueError` upfront.
* **Defense:** In-memory runtime data structures (`tickets` and `events`) are never modified, cleared, or overwritten with empty defaults when loading fails.

### Checkpoint A6: Atomic Persistence & No Partial Writes
* **Code Reference:** `campusflow.storage.save_data(data, filepath)`
* **Rule:** Saving uses a two-phase transaction:
  1. Validates the entire payload (`schema_version: 2`, ticket fields, event fields) before disk operations.
  2. Writes to a hidden temporary file (`.tmp`) in the same filesystem directory and flushes buffers (`temp.flush()`, `os.fsync`).
  3. Atomically swaps the temporary file into place using `os.replace`.
* **Defense:** A crash, power cut, or invalid schema cannot leave half-written files, partial records, or damaged target documents.

---

## 3. Defense Questions for Engineer A

### Question 1: Why UTC instead of naive local time?
> **Answer:** Naive datetimes contain no timezone offset or daylight saving time (DST) awareness. When servers operate across timezones or experience DST clock shifts (springing forward or falling back), naive timestamps become ambiguous or non-monotonic (e.g. 1:30 AM occurring twice in one night). In Python, comparing naive and aware datetimes raises an uncatchable `TypeError`. By standardizing on timezone-aware UTC (`timezone.utc`) serialized as ISO-8601 strings with explicit offsets (`+00:00` or `Z`), timestamps represent absolute, universally comparable moments in physical time.

### Question 2: Why inject a clock into tests?
> **Answer:** Calling `datetime.now()` directly inside business logic couples code execution to physical wall-clock time. To test whether a ticket breaches SLA after 60 minutes, a test would have to execute `time.sleep(3600)`, which is infeasible for automated test suites. Moreover, tests become flaky due to CPU execution jitter. By designing time-dependent functions with an optional parameter `now=None` (falling back to `datetime.now(timezone.utc)` only when omitted), unit tests can deterministically inject exact timestamps (e.g. `T + 60m`, `T + 61m`) and verify millisecond boundary behavior instantly.

### Question 3: How is SLA cycle start different from ticket creation time?
> **Answer:** `created_at` marks the immutable instant when the incident was originally reported to the helpdesk. It must never change throughout the lifetime of the ticket. In contrast, the active SLA cycle start represents the beginning of the current commitment window. For a new ticket, `cycle_start == created_at`. However, when a previously resolved ticket is reopened, the campus support team enters a *new* service commitment window starting at the reopening timestamp. Thus, `due_at` is calculated from the reopening time, not the original creation time, while `created_at` remains intact for historical audit integrity.

### Question 4: How do you guarantee 'one escalation per cycle'?
> **Answer:** Rather than using a global scan for historical `ESCALATE` events (which would incorrectly block legitimate escalations if a ticket was resolved and reopened into a second cycle), we maintain an explicit per-cycle marker `escalation_cycle` on the ticket record:
> 1. Initialized to `0` on creation.
> 2. When overdue, escalation checks `if ticket.get("escalation_cycle", 0) == 0`. It transitions `escalation_cycle = 1` and appends an `ESCALATE` event.
> 3. Repeated escalation checks see `escalation_cycle == 1` and skip the ticket, ensuring idempotency.
> 4. Upon `reopen_ticket()`, the flag is reset to `0`, allowing exactly one new escalation in cycle 2.

### Question 5: What happens to valid in-memory data when malformed JSON is loaded?
> **Answer:** Nothing happens to the valid in-memory data. Defensive programming requires validating both file syntax and semantic schema into temporary structures *before* touching application state. In `campusflow/storage.py`, `load_data()` opens the file, parses JSON, and validates every ticket and event dictionary. If parsing fails (`json.JSONDecodeError`) or schema validation fails (`ValueError`), an exception is raised immediately. Because no in-memory collections were modified during parsing, the caller's active state remains 100% intact.

### Question 6: Where would a crash during file writing cause data loss?
> **Answer:** In naive implementations that open the target file with `open(filepath, "w")`, the operating system immediately truncates the file to 0 bytes before writing. If the process is terminated, loses power, or runs out of disk space halfway through `json.dump()`, the original data is destroyed and replaced by an incomplete, corrupted file. CampusFlow Pro eliminates this risk by writing to a temporary file (`tempfile.NamedTemporaryFile`) on the same filesystem and invoking `os.replace(temp_path, target_path)`, which is an atomic filesystem operation on POSIX and modern Windows NTFS. At no point does a half-written file ever exist at the target path.
