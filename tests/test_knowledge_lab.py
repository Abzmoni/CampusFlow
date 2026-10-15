"""Tests for CampusFlow Pro Engineering Knowledge Lab."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from campusflow.knowledge_lab import (
    QUESTIONS, build_session, revision_topics, run_knowledge_lab,
    save_session, score_choices,
)


class KnowledgeLabTests(unittest.TestCase):
    def setUp(self):
        self.answers = {q["id"]: q["answer"] for q in QUESTIONS}
        self.explanations = {"Q1": "At the deadline, overdue is false.",
                             "Q2": "Ten affected users means high priority.",
                             "Q3": "An unassigned ticket cannot be started."}
        self.now = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)

    def test_exactly_ten_questions_and_four_choices(self):
        self.assertEqual(len(QUESTIONS), 10)
        self.assertTrue(all(set(q["options"]) == set("ABCD") for q in QUESTIONS))

    def test_all_correct_score(self):
        self.assertEqual(score_choices(self.answers), 10)

    def test_one_incorrect_score(self):
        self.answers["Q1"] = "A"
        self.assertEqual(score_choices(self.answers), 9)

    def test_invalid_answer_rejected(self):
        for choice in ("E", "", "b", " B"):
            with self.subTest(choice=choice):
                invalid = dict(self.answers, Q1=choice)
                with self.assertRaises(ValueError):
                    score_choices(invalid)

    def test_missing_question_rejected(self):
        del self.answers["Q10"]
        with self.assertRaises(ValueError):
            score_choices(self.answers)

    def test_revision_topics(self):
        self.answers["Q1"] = "A"
        self.assertEqual(revision_topics(self.answers), ["SLA boundaries"])

    def test_session_requires_three_explanations(self):
        with self.assertRaises(ValueError):
            build_session("B", self.answers, {"Q1": "one"}, self.now)

    def test_session_utc_record(self):
        session = build_session("B", self.answers, self.explanations, self.now)
        self.assertEqual(session["score"], 10)
        self.assertEqual(session["participant"], "B")
        self.assertEqual(session["timestamp"], "2026-10-14T12:00:00+00:00")
        self.assertEqual(len(session["explanations"]), 3)

    def test_save_session_append_and_separate_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "quiz.json"
            session = build_session("A", self.answers, self.explanations, self.now)
            save_session(session, path)
            save_session(session, path)
            records = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["score"], 10)

    def test_corrupt_quiz_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "quiz.json"
            path.write_text("{bad json", encoding="utf-8")
            session = build_session("A", self.answers, self.explanations, self.now)
            with self.assertRaises(ValueError):
                save_session(session, path)
            self.assertEqual(path.read_text(encoding="utf-8"), "{bad json")

    def test_interactive_reprompt_and_save(self):
        # Three explanations are supplied for Q1, Q2, Q3.
        prompts = ["x", "B"]
        for number, q in enumerate(QUESTIONS):
            if number == 0:
                prompts.extend(["E", "", q["answer"]])
            else:
                prompts.append(q["answer"])
            prompts.append(self.explanations.get(q["id"], ""))
        answers = iter(prompts)
        output = []
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "quiz.json"
            session = run_knowledge_lab(path, input_func=lambda _: next(answers), output_func=output.append)
            self.assertEqual(session["score"], 10)
            self.assertEqual(len(json.loads(path.read_text(encoding="utf-8"))), 1)
            self.assertTrue(any("Invalid choice" in item for item in output))
            self.assertTrue(any("Score: 10/10" in item for item in output))

    def test_tickets_not_modified(self):
        tickets = [{"id": "T001", "status": "open"}]
        original = [dict(t) for t in tickets]
        with tempfile.TemporaryDirectory() as folder:
            session = build_session("B", self.answers, self.explanations, self.now)
            save_session(session, Path(folder) / "quiz.json")
        self.assertEqual(tickets, original)


if __name__ == "__main__":
    unittest.main()
