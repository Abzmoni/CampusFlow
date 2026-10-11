# CampusFlow

A Python command-line campus helpdesk project for the Learn2Earn engineering sprint.

## Current scope

This branch implements Engineer A's ticket creation, validation and priority engine. Engineer A: Moses Kingsworth. Engineer B: name to be added by the team. Assignment, lifecycle, queue, reporting, list/view, CLI and production JSON storage still require team integration. This is not yet the complete runnable helpdesk.

The initial implementation and tests were prepared with AI assistance. Individual understanding, contributions, learning experiments and partner approval remain required by the sprint guide.

## Run and test

Use Python 3.10 or newer. Only the standard library is needed.

From the repository root:

```sh
python -m unittest discover -s tests -v
```

Try the business API from a Python interpreter started in the repository root:

```python
from campusflow.tickets import create_ticket

tickets = []
ticket = create_ticket(tickets, 'Campus Wi-Fi is down', 'Network', 'high', 15)
print(ticket)
```

There is no main.py or interactive menu yet. The example stores tickets in memory only.

## Priority rules, evaluated in this order

1. High urgency and at least 10 affected users: critical.
2. High urgency or at least 10 affected users: high.
3. Medium urgency or at least 3 affected users: medium.
4. Otherwise: low.

Counts must be positive integers; invalid inputs raise ValueError. New tickets are open and unassigned. IDs are derived from the highest existing numeric ID.

## Verification and remaining work

The 14 automated tests cover required priority examples, all urgency levels at boundaries 1, 2, 3, 9, 10 and 11, normalization, invalid inputs, unchanged data after rejection, ID gaps and growth, invalid existing IDs, and creation after a temporary-file JSON round trip.

The complete team's acceptance scenarios still need workflow, queue, reporting and production storage tests. No passing-main result or human approval is claimed. Runtime data/tickets.json is ignored by Git; its production load/save behavior is pending.

See docs/design-decisions.md for proposed interfaces and docs/ai-learning-log.md for individual learning requirements. Both fellows must confirm the contracts. Each must author a PR and give at least two substantive observations on the other's PR before approval. Merge only after genuine partner approval and passing tests.

Issue: https://github.com/Moe-Kingsworth/CampusFlow/issues/1

PR index: https://github.com/Moe-Kingsworth/CampusFlow/pulls
