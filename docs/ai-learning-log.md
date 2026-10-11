# AI Learning Log — CampusFlow

This log records verified, deliberate AI-assisted engineering learning interactions following the six-hour sprint guide.

---

## Fellow: Engineer A (Moses Kingsworth)

### Interaction #1 — Strict Positive Integer Validation vs. Python Boolean Subclassing
- **Problem**: Needed to validate that `affected_users` is strictly a positive integer and rejects booleans (`True`, `False`), floats, strings, negative numbers, and zero.
- **My initial understanding**: I assumed `isinstance(count, int) and count > 0` was sufficient to guarantee a valid user count.
- **Prompt to AI**: "In Python, how do I validate that an input is strictly a positive integer and not a float, string, or boolean? Does isinstance(val, int) reject True?"
- **Useful AI guidance**: The AI explained that in Python, `bool` is a direct subclass of `int` (`issubclass(bool, int) is True`). Consequently, `isinstance(True, int)` evaluates to `True`, and since `int(True) == 1`, `True > 0` evaluates to `True`! The AI suggested checking `type(val) is int and val > 0`.
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
- **Useful AI guidance**: The AI suggested: "If records are never deleted, using `f'T{len(tickets) + 1:03d}'` is the easiest and cleanest way to generate sequential IDs. Alternatively, keep a counter variable in the module."
- **My independent experiment/test**:
  ```python
  # Simulated gapped / reloaded ticket collection
  tickets = [{"id": "T001"}, {"id": "T003"}]
  ai_id = f"T{len(tickets) + 1:03d}"  # Evaluates to "T003" -> DUPLICATE ID COLLISION!
  max_num = max(int(t["id"][1:]) for t in tickets)
  safe_id = f"T{max_num + 1:03d}"     # Evaluates to "T004" -> SAFE & UNIQUE
  ```
- **Verification source or result**: The experiment clearly demonstrated that `len(tickets) + 1` produces ID collisions whenever a list has non-contiguous IDs. Verified with `test_uses_numeric_max_for_unordered_gapped_ids` in `tests/test_tickets.py`.
- **Decision**: REJECTED the AI's recommendation to use `len(tickets) + 1` or global counters. Implemented `_next_ticket_id(tickets)` using regex ID validation and `max(numbers, default=0) + 1`. This safely handles gapped IDs, ensures ID uniqueness after JSON reloads, and scales past 999 (`T1000`).
- **Related file/commit**: `campusflow/tickets.py` (`_next_ticket_id`), `tests/test_tickets.py` (`test_uses_numeric_max_for_unordered_gapped_ids`, `test_grows_beyond_three_digits`).
- **What I can now explain without AI**: Deriving IDs from collection length (`len + 1`) is fragile because any filtering, deletion, or non-sequential reload creates duplicate IDs. Finding the maximum existing numeric ID ensures deterministic, unique IDs without relying on fragile global state.

---

### Interaction #3 — Atomic Operations and Exception Safety
- **Problem**: Needed to guarantee that if ticket creation encounters invalid data (blank title, negative users, invalid category), the shared tickets list is left completely untouched.
- **My initial understanding**: I considered appending a skeleton dictionary to `tickets` first and validating fields step by step, removing it if an error occurred.
- **Prompt to AI**: "When appending records to a shared list in Python, should I validate all fields upfront before appending, or append and remove if an error occurs?"
- **Useful AI guidance**: The AI introduced the concept of atomicity: validating all inputs into local variables before mutating any shared data structure ensures that an exception aborts the operation cleanly without leaving half-constructed records.
- **My independent experiment/test**:
  Wrote `test_invalid_creation_leaves_existing_records_unchanged` in `tests/test_tickets.py` testing 18 invalid input variations against a snapshot `before = copy.deepcopy(self.tickets)`.
- **Verification source or result**: Unittest assertion `self.assertEqual(self.tickets, before)` passes across all invalid input scenarios.
- **Decision**: Accepted the upfront validation recommendation. Structured `create_ticket` so all validations (`_text`, `_urgency`, `calculate_priority`, `_next_ticket_id`) occur BEFORE `tickets.append(ticket)`.
- **Related file/commit**: `campusflow/tickets.py` (`create_ticket`), `tests/test_tickets.py` (`test_invalid_creation_leaves_existing_records_unchanged`).
- **What I can now explain without AI**: Business logic functions should adhere to atomic execution: validate all inputs and perform computations in local variables first; only commit changes to shared collections once all validation checks succeed.

---

## Fellow: Engineer B (To be completed by Partner)

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

### Interaction #3 — <concept/topic> (Critical evaluation/rejection)
- **Problem**: 
- **My initial understanding**: 
- **Prompt to AI**: 
- **Useful AI guidance**: 
- **My independent experiment/test**: 
- **Verification source or result**: 
- **Decision**: 
- **Related file/commit**: 
- **What I can now explain without AI**: 
