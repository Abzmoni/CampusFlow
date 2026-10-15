"""Standalone Engineering Knowledge Lab for CampusFlow Pro.

Quiz sessions are saved separately from helpdesk tickets.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SESSION_PATH = "data/knowledge_sessions.json"

# The question wording and choices come from the CampusFlow Pro challenge.
QUESTIONS = [
    {
        "id": "Q1",
        "topic": "SLA boundaries",
        "question": "Critical SLA: A critical ticket is created at 10:00 UTC. At 11:00 UTC, is it overdue?",
        "options": {"A": "Yes", "B": "No, only strictly after 11:00", "C": "Only if assigned", "D": "Only if reopened"},
        "answer": "B",
        "explain": "Explain the difference between 'due' and 'overdue'.",
    },
    {
        "id": "Q2",
        "topic": "Priority calculation",
        "question": "Priority order: urgency=low and affected_users=10. What priority?",
        "options": {"A": "Critical", "B": "High", "C": "Medium", "D": "Low"},
        "answer": "B",
        "explain": "Explain which rule applies first.",
    },
    {
        "id": "Q3",
        "topic": "Workflow invariants",
        "question": "Illegal transition: an unassigned open ticket moves directly to in_progress. What should happen?",
        "options": {"A": "Transition succeeds", "B": "Status changes but history stays", "C": "Reject without changing ticket or events", "D": "Delete the ticket"},
        "answer": "C",
        "explain": "Explain the invariant.",
    },
    {
        "id": "Q4",
        "topic": "Reopening and SLA cycles",
        "question": "Reopening: a resolved high-priority ticket is reopened. Which SLA behavior is correct?",
        "options": {"A": "Keep old due_at always", "B": "Start a fresh SLA cycle while preserving created_at", "C": "Reset created_at to today's date", "D": "Delete previous events"},
        "answer": "B",
        "explain": "Explain why.",
    },
    {
        "id": "Q5",
        "topic": "Escalation idempotency",
        "question": "Escalation repeated: an overdue ticket is checked three times within one SLA cycle. How many new ESCALATE events?",
        "options": {"A": "Three", "B": "Two", "C": "One", "D": "Zero"},
        "answer": "C",
        "explain": "Explain idempotency.",
    },
    {
        "id": "Q6",
        "topic": "JSON corruption handling",
        "question": "JSON corrupted: the saved file has invalid JSON. What is the safest action?",
        "options": {"A": "Replace data with empty list", "B": "Use eval()", "C": "Ignore and keep running with partial data", "D": "Reject load and preserve existing valid state"},
        "answer": "D",
        "explain": "Explain your choice.",
    },
    {
        "id": "Q7",
        "topic": "Code review and boundary testing",
        "question": "Code review: a PR changes SLA calculations but adds no boundary tests. What should a reviewer do?",
        "options": {"A": "Approve because it runs locally", "B": "Request focused tests and explanation", "C": "Merge and test next week", "D": "Ask AI to approve automatically"},
        "answer": "B",
        "explain": "Explain your reasoning.",
    },
    {
        "id": "Q8",
        "topic": "AI suggestion verification",
        "question": "AI suggestion: an assistant says 'use eval() to parse stored JSON'. What should you do?",
        "options": {"A": "Copy it", "B": "Disable tests", "C": "Reject and use JSON parsing with validation", "D": "Share the whole file publicly"},
        "answer": "C",
        "explain": "Explain how you verified.",
    },
    {
        "id": "Q9",
        "topic": "Duplicate detection",
        "question": "Duplicate warning: titles ' Wi-Fi \u00a0 Down ' and 'wi-fi down' share category, both unresolved. What should the CLI do?",
        "options": {"A": "Silently delete original", "B": "Warn and require confirmation", "C": "Silently block forever", "D": "Ignore normalization"},
        "answer": "B",
        "explain": "Explain the trade-off.",
    },
    {
        "id": "Q10",
        "topic": "Audit-event atomicity",
        "question": "Audit log: an invalid return/status operation is rejected. What should happen to event count?",
        "options": {"A": "Increase by one", "B": "Increase twice", "C": "Reset to zero", "D": "Stay unchanged"},
        "answer": "D",
        "explain": "Explain the reason.",
    },
]


def score_choices(choices):
    """Return the number of correct answers; reject invalid answer sets."""
    expected_ids = {question["id"] for question in QUESTIONS}
    if not isinstance(choices, dict) or set(choices) != expected_ids:
        raise ValueError("Choices must contain exactly Q1 through Q10")
    if any(choice not in ("A", "B", "C", "D") for choice in choices.values()):
        raise ValueError("Each choice must be exactly A, B, C, or D")
    return sum(choices[q["id"]] == q["answer"] for q in QUESTIONS)


def revision_topics(choices):
    """List topics answered incorrectly."""
    score_choices(choices)  # Also validates the input.
    return [q["topic"] for q in QUESTIONS if choices[q["id"]] != q["answer"]]


def build_session(participant, choices, explanations, now=None):
    """Build a validated, serializable session record."""
    if participant not in ("A", "B"):
        raise ValueError("Participant must be A or B")
    score = score_choices(choices)
    if not isinstance(explanations, dict):
        raise ValueError("Explanations must be a dictionary")
    if not set(explanations).issubset(choices):
        raise ValueError("Unknown question in explanations")
    if any(not isinstance(value, str) for value in explanations.values()):
        raise ValueError("Explanations must be text")
    cleaned = {key: value.strip() for key, value in explanations.items() if value.strip()}
    if len(cleaned) < 3:
        raise ValueError("At least three written explanations are required")
    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Session time must be timezone-aware")
    return {
        "participant": participant,
        "timestamp": now.astimezone(timezone.utc).isoformat(),
        "choices": dict(choices),
        "score": score,
        "total_questions": len(QUESTIONS),
        "explanations": cleaned,
        "revision_topics": revision_topics(choices),
    }


def save_session(session, filepath=SESSION_PATH):
    """Append a quiz record using an atomic JSON file replacement."""
    path = Path(filepath)
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as file:
                existing = json.load(file)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("Cannot load existing quiz sessions") from exc
        if not isinstance(existing, list) or not all(isinstance(item, dict) for item in existing):
            raise ValueError("Existing quiz sessions must be a list of records")
    else:
        existing = []

    if not isinstance(session, dict):
        raise ValueError("Session must be a dictionary")

    updated = existing + [session]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as temp:
            tmp_name = temp.name
            json.dump(updated, temp, indent=2, ensure_ascii=False)
            temp.flush()
            os.fsync(temp.fileno())
        os.replace(tmp_name, path)
    finally:
        if tmp_name is not None and os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return path


def run_knowledge_lab(filepath=SESSION_PATH, input_func=None, output_func=None):
    """Run the interactive quiz, save its result, and display a review."""
    if input_func is None:
        input_func = input
    if output_func is None:
        output_func = print

    output_func("\n=== Engineering Knowledge Lab ===")
    while True:
        participant = input_func("Participant (A or B): ")
        if participant in ("A", "B"):
            break
        output_func("Invalid participant. Enter exactly A or B.")

    choices = {}
    explanations = {}
    for index, question in enumerate(QUESTIONS):
        output_func(f"\n{question['id']}: {question['question']}")
        for letter, label in question["options"].items():
            output_func(f"  {letter}. {label}")
        while True:
            answer = input_func("Your choice (A/B/C/D): ")
            if answer in ("A", "B", "C", "D"):
                break
            output_func("Invalid choice. Enter exactly A, B, C, or D.")
        choices[question["id"]] = answer

        remaining_questions = len(QUESTIONS) - index - 1
        explanations_needed = max(0, 3 - len(explanations))
        required_now = explanations_needed > remaining_questions
        while True:
            label = " (required)" if required_now else " (optional)"
            explanation = input_func(f"{question['explain']}{label}: ").strip()
            if explanation:
                explanations[question["id"]] = explanation
                break
            if not required_now:
                break
            output_func("A written explanation is required for this question.")

    session = build_session(participant, choices, explanations)
    save_session(session, filepath)
    output_func(f"\nScore: {session['score']}/{session['total_questions']}")
    if session["revision_topics"]:
        output_func("Topics to revise: " + ", ".join(session["revision_topics"]))
    else:
        output_func("No missed topics. Review any answers you found difficult.")
    for question in QUESTIONS:
        qid = question["id"]
        output_func(f"{qid}: Answer {choices[qid]} | Correct {question['answer']}")
        if qid in explanations:
            output_func(f"  Your explanation: {explanations[qid]}")
    output_func(f"Quiz session saved to {filepath}")
    return session


if __name__ == "__main__":
    run_knowledge_lab()
