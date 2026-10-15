# CampusFlow Pro — Engineering Learning Reflections

**Repository:** [Abzmoni/CampusFlow](https://github.com/Abzmoni/CampusFlow)  
**Engineer A:** David Abah (`Abzmoni`)  
**Engineer B:** Mohammed (`midi2154`)

## Engineer A — Escalation idempotency and SLA cycles

**Knowledge Lab question:** Q5 — Repeated checks of an overdue ticket within one SLA cycle.  
**Relevant modules:** `campusflow/sla.py`, `campusflow/workflow.py`  
**Test evidence:** `tests/test_sla.py`

### What I initially believed

I first thought that checking whether a ticket had ever been escalated would be enough to prevent duplicate escalation events. That seemed reasonable until I considered what happens when a resolved ticket is reopened.

### How I checked

I examined a scenario where a ticket was escalated, resolved, reopened, and later became overdue again. A check against *all past* escalation events would incorrectly block the new escalation. I compared this with the tests for repeated escalation and reopening into a new SLA cycle.

### What I learned and changed

Idempotency must apply **within the current SLA cycle**, not across the ticket's entire history. The `escalation_cycle` marker prevents duplicate events during one cycle and resets when a resolved ticket is reopened. The old audit events remain intact, and reopening creates a fresh deadline while preserving `created_at`.

**What I can demonstrate:** A second escalation check in the same cycle produces no new event; after reopening and another SLA breach, a new escalation is permitted.

## Engineer B — Audit history and rejected operations

**Knowledge Lab question:** Q10 — Event count after an invalid status operation.  
**Relevant modules:** `campusflow/history.py`, `campusflow/audited_workflow.py`  
**Test evidence:** `tests/test_audited_workflow.py`, especially `test_invalid_transition_creates_no_event`

### What I initially believed

I initially considered changing a ticket's status first and recording the event afterwards. I had not fully considered that an error between those two steps could leave the ticket and its history inconsistent.

### How I checked

I tested an invalid status transition and compared the ticket data and audit-event count before and after the attempt. I also studied how `deepcopy` can prepare changes without touching the original records.

### What I learned and changed

An audit event should record **what successfully happened**, not what someone merely attempted. The audited workflow prepares ticket and event changes on copies. Only after validation and event creation succeed are the original lists updated. A rejected operation therefore changes neither the ticket nor its history.

**What I can demonstrate:** Reject an illegal transition and show that the ticket status and event count remain unchanged.

## Engineering Knowledge Lab results

The supplied CLI transcripts record completed sessions under participant labels **A** and **B**. Each session answered all ten questions, provided ten written explanations, scored 10/10, and reported successful saving to `data/knowledge_sessions.json`.

| Evidence | Participant A | Participant B |
| --- | --- | --- |
| Questions answered | 10 of 10 | 10 of 10 |
| Score | **10/10** | **10/10** |
| Written explanations | 10 | 10 |
| Minimum three explanations | Met | Met |
| Question reflected upon | Q5 — escalation idempotency | Q10 — rejected-operation audit history |
| Saved session | `data/knowledge_sessions.json` | `data/knowledge_sessions.json` |

*Participant selection is a label, not identity verification. These results document the recorded A- and B-labelled sessions; each engineer's personal participation is separate from what the CLI transcript alone proves.*

## Verification and supporting documentation

The merged `main` branch passed **113 automated tests** using:

```bash
python3 -m unittest discover -s tests -v
```

Additional technical evidence is available in [`ai-learning-log.md`](ai-learning-log.md), [`design-decisions.md`](design-decisions.md), and [`engineer_a_checkpoints_defense.md`](engineer_a_checkpoints_defense.md).
