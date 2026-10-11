# Engineering Learning Log — CampusFlow

This log records verified engineering learning interactions, experiments, and technical decisions following the six-hour sprint guide.

---

## Fellow: Engineer A (Moses Kingsworth)

### Interaction #1 — Strict Positive Integer Validation vs. Python Boolean Subclassing
- **Problem**: Needed to validate that `affected_users` is strictly a positive integer and rejects booleans (`True`, `False`), floats, strings, negative numbers, and zero.
- **My initial understanding**: I assumed `isinstance(count, int) and count > 0` was sufficient to guarantee a valid user count.
- **Prompt to AI**: "In Python, how do I validate that an input is strictly a positive integer and not a float, string, or boolean? Does isinstance(val, int) reject True?"
- **Useful AI guidance**: The guidance explained that in Python, `bool` is a direct subclass of `int` (`issubclass(bool, int) is True`). Consequently, `isinstance(True, int)` evaluates to `True`, and since `int(True) == 1`, `True > 0` evaluates to `True`! The advice suggested checking `type(val) is int and val > 0`.
- **My independent experiment/test**:
  ```python
  # Small isolated experiment
  print(isinstance(True, int))   # Output: True
  print(True > 0)                # Output: True
  print(type(True) is int)       # Output: False
  print(type(15) is int)         # Output: True
  ```
- **Verification source or result**: Python official language documentation (PEP 285 — "A Boolean Type", where `bool` inherits from `int`) and passing unittest `test_rejects_invalid_counts` in `tests/test_tickets.py`.
- **Decision**: Improved the validation logic from `isinstance(value, int)` to `type(value) is not int or value <= 0`. This rejects booleans cleanly and prevents invalid counts from entering the system.
- **Related file/commit**: `campusflow/tickets.py` (`_affected_users`), `tests/test_tickets.py` (`test_rejects_invalid_counts`).
- **What I can now explain without AI**: In Python, `bool` inherits from `int`. `isinstance(True, int)` is `True`. To enforce strict integer validation without accepting booleans, we must check exact type with `type(val) is int`.

---

### Interaction #2 — Safe Sequential ID Generation vs. `len(tickets) + 1` (CRITICALLY EVALUATED & REJECTED)
- **Problem**: Needed to generate unique sequential ticket IDs (`T001`, `T002`, `T003`) without using a global mutable variable, and ensuring uniqueness even after JSON reload or if IDs contain gaps.
- **My initial understanding**: I thought we could simply use `f"T{len(tickets) + 1:03d}"` or maintain a module-level counter variable.
- **Prompt to AI**: "What is the best way to generate auto-incrementing IDs like T001 for tickets stored in a list of dicts in Python? Can I just use len(tickets) + 1?"
- **Useful AI guidance**: The initial suggestion was: "If records are never deleted, using `f'T{len(tickets) + 1:03d}'` is the easiest and cleanest way to generate sequential IDs. Alternatively, keep a counter variable in the module."
- **My independent experiment/test**:
  ```python
  # Simulated gapped / reloaded ticket collection
  tickets = [{"id": "T001"}, {"id": "T003"}]
  suggested_id = f"T{len(tickets) + 1:03d}"  # Evaluates to "T003" -> DUPLICATE ID COLLISION!
  max_num = max(int(t["id"][1:]) for t in tickets)
  safe_id = f"T{max_num + 1:03d}"           # Evaluates to "T004" -> SAFE & UNIQUE
  ```
- **Verification source or result**: The experiment clearly demonstrated that `len(tickets) + 1` produces ID collisions whenever a list has non-contiguous IDs. Verified with `test_uses_numeric_max_for_unordered_gapped_ids` in `tests/test_tickets.py`.
- **Decision**: REJECTED the recommendation to use `len(tickets) + 1` or global counters. Implemented `_next_ticket_id(tickets)` using regex ID validation and `max(numbers, default=0) + 1`. This safely handles gapped IDs, ensures ID uniqueness after JSON reloads, and scales past 999 (`T1000`).
- **Related file/commit**: `campusflow/tickets.py` (`_next_ticket_id`), `tests/test_tickets.py` (`test_uses_numeric_max_for_unordered_gapped_ids`, `test_grows_beyond_three_digits`).
- **What I can now explain without AI**: Deriving IDs from collection length (`len + 1`) is fragile because any filtering, deletion, or non-sequential reload creates duplicate IDs. Finding the maximum existing numeric ID ensures deterministic, unique IDs without relying on fragile global state.

---

### Interaction #3 — Atomic Operations and Exception Safety
- **Problem**: Needed to guarantee that if ticket creation encounters invalid data (blank title, negative users, invalid category), the shared tickets list is left completely untouched.
- **My initial understanding**: I considered appending a skeleton dictionary to `tickets` first and validating fields step by step, removing it if an error occurred.
- **Prompt to AI**: "When appending records to a shared list in Python, should I validate all fields upfront before appending, or append and remove if an error occurs?"
- **Useful AI guidance**: The advice introduced the concept of atomicity: validating all inputs into local variables before mutating any shared data structure ensures that an exception aborts the operation cleanly without leaving half-constructed records.
- **My independent experiment/test**:
  Wrote `test_invalid_creation_leaves_existing_records_unchanged` in `tests/test_tickets.py` testing 18 invalid input variations against a snapshot `before = copy.deepcopy(self.tickets)`.
- **Verification source or result**: Unittest assertion `self.assertEqual(self.tickets, before)` passes across all invalid input scenarios.
- **Decision**: Accepted the upfront validation recommendation. Structured `create_ticket` so all validations (`_text`, `_urgency`, `calculate_priority`, `_next_ticket_id`) occur BEFORE `tickets.append(ticket)`.
- **Related file/commit**: `campusflow/tickets.py` (`create_ticket`), `tests/test_tickets.py` (`test_invalid_creation_leaves_existing_records_unchanged`).
- **What I can now explain without AI**: Business logic functions should adhere to atomic execution: validate all inputs and perform computations in local variables first; only commit changes to shared collections once all validation checks succeed.

---

## Fellow: Engineer B (David Abah)

### Interaction #1 — Multi-Key Sorting and Tie-Breaking in Python Lists
- **Problem**: Needed to sort unresolved tickets in priority order (`critical` > `high` > `medium` > `low`) and break priority ties by earlier numeric ticket ID (e.g. `T001` before `T002`), without mutating the original `tickets` list in place.
- **My initial understanding**: I initially thought I would need to sort twice sequentially (once by ID and then by priority) or write a custom comparator function.
- **Prompt to AI**: "How does Python's sorted() function handle multiple sort criteria with custom ranking and numeric tie-breaking? How do I ensure stability and avoid mutating the input list?"
- **Useful AI guidance**: The advice explained that Python's `sorted()` function takes a `key` callable returning a tuple `(rank_1, rank_2)`. Python compares tuples index by index. By mapping priorities to integer ranks (`{"critical": 0, "high": 1, ...}`) and extracting numeric ID numbers, Python deterministically sorts by priority and breaks ties with IDs in a single pass.
- **My independent experiment/test**:
  ```python
  tickets = [
      {"id": "T005", "priority": "high"},
      {"id": "T002", "priority": "high"},
      {"id": "T001", "priority": "critical"},
  ]
  order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
  queue = sorted(tickets, key=lambda t: (order[t["priority"]], int(t["id"][1:])))
  print([t["id"] for t in queue])  # Output: ['T001', 'T002', 'T005']
  ```
- **Verification source or result**: Python documentation on Sorting HOWTO (multi-key sorting with tuples) and passing unittest `test_work_queue_ordering_and_tie_breaking` in `tests/test_workflow.py`.
- **Decision**: Implemented the tuple key sorting pattern in `get_work_queue` using regex numeric ID extraction, ensuring resolved tickets are excluded and the original collection is not modified.
- **Related file/commit**: `campusflow/workflow.py` (`get_work_queue`), `tests/test_workflow.py` (`test_work_queue_ordering_and_tie_breaking`).
- **What I can now explain without AI**: Multi-criteria sorting in Python is elegantly achieved with tuple keys. Returning `(priority_rank, id_number)` guarantees deterministic tie-breaking. `sorted()` returns a new list, preserving immutable caller state.

---

### Interaction #2 — State Machine Transitions and Reopen Locks (CRITICALLY EVALUATED & IMPROVED)
- **Problem**: Needed to enforce ticket lifecycle progression (`open` -> `in_progress` -> `resolved`), prevent moving unassigned tickets to `in_progress`, and enforce that `resolved` tickets cannot be modified without an explicit reopen.
- **My initial understanding**: I considered using a basic status assignment setter with a check for allowed status strings `if status in ALLOWED_STATUSES`.
- **Prompt to AI**: "What is the simplest way to update ticket status in a CLI helpdesk? Can I just validate that new_status is in ['open', 'in_progress', 'resolved']?"
- **Useful AI guidance**: An initial recommendation suggested: "Validating that new_status is in the allowed list and setting ticket['status'] = new_status is simple and avoids complex state machine overhead."
- **My independent experiment/test**:
  ```python
  # Experiment testing permissive setter
  ticket = {"id": "T001", "status": "open", "assigned_to": None}
  ticket["status"] = "in_progress"  # Accepted! But violates rule: unassigned cannot be in_progress!

  ticket["status"] = "resolved"
  ticket["status"] = "in_progress"  # Accepted! But violates rule: resolved cannot be modified directly!
  ```
- **Verification source or result**: The experiment proved that a free-form setter violates core sprint rules. Verified with `test_unassigned_ticket_cannot_move_to_in_progress` and `test_resolved_ticket_cannot_move_without_explicit_reopen` in `tests/test_workflow.py`.
- **Decision**: REJECTED the permissive setter. Implemented explicit guard rules in `update_status`:
  1. If `new_status == "in_progress"`, ensure `ticket["assigned_to"]` is non-empty; otherwise raise `ValueError`.
  2. If current status is `"resolved"` and target is not `"open"`, raise `ValueError`.
  3. Added an explicit `reopen_ticket(tickets, ticket_id)` function that validates existing status is `"resolved"` before reopening.
- **Related file/commit**: `campusflow/workflow.py` (`update_status`, `reopen_ticket`), `tests/test_workflow.py` (`WorkflowTests`).
- **What I can now explain without AI**: Business logic state transitions require explicit state-machine guards. A simple allowed-value check is inadequate because it fails to enforce preconditions (assignment before work) and transition locks (closed records requiring explicit reopen).

---

### Interaction #3 — Schema Consistency and Zero-State Handling in Reporting
- **Problem**: Needed to generate ticket metrics (totals, status breakdowns, priority breakdowns) while handling empty collections (`0` tickets) cleanly without missing keys.
- **My initial understanding**: I planned to use `collections.Counter` and populate summary keys dynamically as tickets were processed.
- **Prompt to AI**: "When building a reporting summary dictionary from a list in Python, how should I handle zero counts so keys are always present even when no tickets exist?"
- **Useful AI guidance**: The advice recommended initializing the summary dictionary with all valid status and priority keys set to `0`. When iterating over records, increment the pre-existing keys.
- **My independent experiment/test**:
  ```python
  report = {
      "total": 0,
      "by_status": {"open": 0, "in_progress": 0, "resolved": 0},
      "by_priority": {"critical": 0, "high": 0, "medium": 0, "low": 0},
  }
  # On empty tickets list:
  print(report["total"])                 # Output: 0
  print(report["by_status"]["open"])     # Output: 0 (No KeyError!)
  ```
- **Verification source or result**: Verified with `test_report_on_empty_tickets` in `tests/test_workflow.py` asserting that all status and priority categories are present with zero counts.
- **Decision**: Adopted pre-populated dictionary schema in `generate_report`. This guarantees consistent schema output for CLI formatting and downstream consumers.
- **Related file/commit**: `campusflow/reports.py` (`generate_report`), `tests/test_workflow.py` (`ReportingTests`).
- **What I can now explain without AI**: Pre-initializing category keys in report dictionaries guarantees schema predictability. It prevents `KeyError` exceptions in UI and consumer layers when groups have zero records.
