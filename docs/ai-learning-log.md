# Engineering Learning Log — CampusFlow Pro

This log records verified engineering learning interactions, experiments, and technical decisions following the CampusFlow Pro engineering challenge.

---

## Fellow: Engineer A (David Abah / Abzmoni)

### Interaction #1 — Timezone-Aware UTC Datetimes, ISO-8601 Serialization, and Clock Injection
- **Problem**: Needed to implement robust time handling for SLA calculations and overdue detection without introducing flaky, non-deterministic tests or timezone bugs.
- **My initial understanding**: I initially considered calling `datetime.now()` directly inside `calculate_due_at()` and `is_overdue()`, and using `time.sleep()` in unit tests to test overdue transitions.
- **Prompt to AI**: "Why does calling datetime.now() everywhere make unit tests unreliable, and how does dependency injection of a clock parameter solve this in Python? How should timezone-aware UTC datetimes and ISO-8601 strings be formatted and compared?"
- **Useful AI guidance**: The AI explained that calling `datetime.now()` directly creates non-deterministic tests that depend on system clock speed, latency, and wall-clock execution time. Furthermore, comparing naive datetimes with aware datetimes raises `TypeError`. The AI suggested designing every time-dependent function to accept an optional `now=None` argument (defaulting to `datetime.now(timezone.utc)` when omitted), and serializing to standard ISO-8601 strings.
- **My independent experiment/test**:
  ```python
  from datetime import datetime, timezone, timedelta
  # Experiment comparing naive and aware datetimes:
  naive = datetime.now()
  aware = datetime.now(timezone.utc)
  try:
      _ = naive > aware
  except TypeError as e:
      print("Caught expected TypeError:", e)

  # Experiment simulating time deterministically with clock injection:
  t0 = datetime(2026, 10, 14, 10, 0, 0, tzinfo=timezone.utc)
  due = t0 + timedelta(minutes=60)
  print("At 60m exact (overdue?):", (t0 + timedelta(minutes=60)) > due)   # False
  print("At 61m past (overdue?):", (t0 + timedelta(minutes=61)) > due)    # True
  ```
- **Verification source or result**: Python documentation on `datetime.timezone` and passing test cases `test_checkpoint_a1_critical_at_exact_60_minutes_is_not_overdue` and `test_checkpoint_a2_critical_at_61_minutes_is_overdue` in `tests/test_sla.py`.
- **Decision**: Implemented `get_now(now=None)`, `to_iso_utc(dt)`, and `from_iso_utc(ts)` in `campusflow/sla.py`. All SLA functions accept `now=None`, enabling 100% deterministic, instant testing of boundaries without sleeping.
- **Related file/commit**: `campusflow/sla.py`, `tests/test_sla.py` (`feat/11-sla-engine`).
- **What I can now explain without AI**: Wall-clock calls inside business logic couple code to physical time, making boundary testing impossible without sleeping. Injecting an optional clock parameter (`now=None`) preserves ergonomic production calls while allowing tests to simulate arbitrary time instants with millisecond precision.

---

### Interaction #2 — SLA Escalation Idempotency & Per-Cycle Markers (CRITICALLY EVALUATED & REJECTED)
- **Problem**: Needed to design an escalation mechanism that evaluates overdue tickets, creates exactly ONE escalation event in a given SLA cycle, and does not create duplicate events when rerun, while still allowing legitimate escalations if a ticket is resolved and reopened into a new cycle.
- **My initial understanding**: I thought we could check the global `events` list: if an event with `event_type == "ESCALATE"` and matching `ticket_id` exists anywhere in history, do not escalate.
- **Prompt to AI**: "How do I ensure an escalation function is idempotent so calling it multiple times does not produce duplicate events? Can I just check if an ESCALATE event exists for the ticket in the events list?"
- **Useful AI guidance**: The AI initially suggested: "Yes, you can simply scan `events` for `event['ticket_id'] == ticket_id and event['event_type'] == 'ESCALATE'`. If found, skip escalation."
- **My independent experiment/test**:
  ```python
  # Testing the AI's global event check against the reopen requirement:
  events = [{"ticket_id": "T001", "event_type": "ESCALATE", "details": "Escalated in cycle 1"}]
  # Ticket is later resolved and reopened into cycle 2, becoming overdue again:
  ticket = {"id": "T001", "status": "open", "due_at": "2026-10-14T15:00:00Z"}
  # AI's global check:
  has_escalated_ai = any(e["ticket_id"] == "T001" and e["event_type"] == "ESCALATE" for e in events)
  print("AI check permits cycle 2 escalation?", not has_escalated_ai) # False! LEGITIMATE ESCALATION BLOCKED!
  ```
- **Verification source or result**: The experiment proved that the AI's global event scan breaks Section 3's requirement: *"If a ticket is reopened and becomes overdue in its new cycle, it may legitimately escalate again."* Verified with `test_checkpoint_a4_reopen_starts_fresh_sla_cycle_and_clears_escalation` in `tests/test_sla.py`.
- **Decision**: REJECTED the AI's recommendation to use a global event scan. Instead, implemented a per-cycle marker `escalation_cycle` directly on the ticket record:
  1. `escalation_cycle = 0` on ticket creation.
  2. Escalation checks `if ticket.get("escalation_cycle", 0) == 0`. When escalated, sets `escalation_cycle = 1` and appends an event. Subsequent runs see `escalation_cycle == 1` and skip (idempotent).
  3. When a ticket is reopened via `reopen_ticket()`, it resets `escalation_cycle = 0` ("clears per-cycle escalation flag"). If the ticket breaches SLA in the new cycle, it escalates once more legitimately.
- **Related file/commit**: `campusflow/sla.py` (`escalate_overdue`), `campusflow/workflow.py` (`reopen_ticket`), `tests/test_sla.py`.
- **What I can now explain without AI**: Idempotency cannot be implemented as a global blanket check when business entities have discrete lifecycles. A stateful per-cycle marker scoped to the active SLA window guarantees idempotency within the active cycle without preventing future valid operations in subsequent cycles.

---

### Interaction #3 — Defensive Version-2 JSON Schema Validation & Atomic File Replacement
- **Problem**: Needed to upgrade JSON storage to schema version 2 (`schema_version: 2`, `tickets: [...]`, `events: [...]`) while guaranteeing that loading corrupt data never overwrites or clears valid in-memory state, and crashes during save never corrupt storage.
- **My initial understanding**: I considered reading the file and directly replacing the in-memory lists, relying on `except Exception: pass`.
- **Prompt to AI**: "What are the common pitfalls when migrating JSON persistence to a versioned schema with multiple collections? How can atomic writes and schema pre-validation prevent data loss?"
- **Useful AI guidance**: The AI outlined the risks of in-place mutation: if a file has valid JSON syntax but invalid schema (e.g. missing required fields), partially updating in-memory structures leaves the application in an undefined state. The AI recommended validating the entire data structure into fresh local lists before returning, and writing to disk using a temporary file with `os.replace`.
- **My independent experiment/test**:
  Wrote `tests/test_storage_v2.py` testing invalid schema versions, missing ticket fields, malformed JSON, and atomic `.tmp` replacement. Verified that an invalid file raises `ValueError` while leaving the caller's existing ticket collection completely intact.
- **Verification source or result**: Unittest execution in `tests/test_storage_v2.py` passing across all corruption and schema-violation scenarios.
- **Decision**: Implemented `load_data(filepath)` and `save_data(data, filepath)` in `campusflow/storage.py` with strict schema validation and atomic temporary-file replacement.
- **Related file/commit**: `campusflow/storage.py`, `tests/test_storage_v2.py` (`feat/12-data-integrity`).
- **What I can now explain without AI**: Defensive persistence requires validating both syntax and semantic schema before touching runtime state. Saving must be atomic via temporary file swap so that interruptions or out-of-disk errors leave the original database document undamaged.

---

## Fellow: Engineer B (Mohammed)

### Interaction #1 — <concept/topic>
- **Problem**: 
- **My initial understanding**: 
- **Prompt to AI**: 
- **Useful AI guidance**: 
- **My independent experiment/test**: 
- **Verification source or result**: 
- **Decision**: 
- **Related file/commit**: 
- **What I can now explain without AI**: 

### Interaction #2 — <concept/topic>
- **Problem**: 
- **My initial understanding**: 
- **Prompt to AI**: 
- **Useful AI guidance**: 
- **My independent experiment/test**: 
- **Verification source or result**: 
- **Decision**: 
- **Related file/commit**: 
- **What I can now explain without AI**: 

### Interaction #3 — <concept/topic>
- **Problem**: 
- **My initial understanding**: 
- **Prompt to AI**: 
- **Useful AI guidance**: 
- **My independent experiment/test**: 
- **Verification source or result**: 
- **Decision**: 
- **Related file/commit**: 
- **What I can now explain without AI**: 
