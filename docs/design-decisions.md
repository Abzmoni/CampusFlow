# Proposed shared design decisions

Status: Engineer A implementation proposal. Engineer B has not confirmed these contracts yet.

## Ownership

Engineer A (Moses): campusflow/tickets.py and tests/test_tickets.py.
Engineer B: assignment, lifecycle, queue and reporting, with matching tests.
Both: list/view, CLI integration, JSON storage, integration tests and genuine cross-review.

## Data and contracts

The caller owns a list of ticket dictionaries. No global mutable counter or interactive input lives in the business logic.

`create_ticket(tickets, title, category, urgency, affected_users)` validates all inputs, appends one dictionary and returns that same dictionary. Failure raises ValueError with a useful message and leaves the collection unchanged.

`calculate_priority(urgency, affected_users)` returns critical, high, medium or low. It checks the exact ordered rules from the guide and validates its own inputs.

Titles are trimmed while preserving case. Categories are trimmed and normalized to Network, Hardware, Software or Other. Urgency is trimmed and lowercased. Counts must be positive Python integers. Booleans, floats and strings are rejected by the business API. The future CLI should parse numeric input with int(raw_input), catch ValueError, and pass the resulting integer. Do not convert through float, which can truncate decimals.

IDs use T plus a positive integer padded to at least three digits. New IDs use the highest numeric existing ID plus one, including after JSON reload. Invalid or duplicate existing numeric IDs raise ValueError. No deletion feature is specified. A future deletion feature would need a persisted high-water mark to prevent reuse of deleted IDs.

New tickets have status open and assigned_to None. Engineer B can update the returned dictionaries through the shared collection. Creation does not modify existing records.

## Proposed integration

storage.py should own load/save. main.py should load once, call business functions, save successful changes and display useful errors. Missing files should return an empty list; malformed JSON must produce an error and must not be overwritten automatically. These storage functions are not implemented in this branch.

The JSON round-trip test proves creation remains compatible with reloaded records. It is not evidence that a production persistence module or the full CLI exists.

Before integration, agree on Engineer B's signatures, who implements list/view and main.py, and whether the queue includes only open tickets or also in_progress tickets. The guide's queue wording should be clarified together.
