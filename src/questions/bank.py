"""Question bank management — load and filter questions from DuckDB."""

from __future__ import annotations

import random
from typing import Any

import duckdb

from src.database.queries import count_questions, fetch_questions
from src.questions.models import (
    Difficulty,
    MCQQuestion,
    OpenEndedQuestion,
    Question,
    QuestionSource,
    QuestionType,
)


def _row_to_question(row: dict[str, Any]) -> Question:
    """Convert a database row to a Question model."""
    common = {
        "id": row["id"],
        "topic": row["topic"],
        "subtopic": row["subtopic"],
        "difficulty": Difficulty(row["difficulty"]),
        "type": QuestionType(row["type"]),
        "question_text": row["question_text"],
        "source": QuestionSource(row.get("source", "static")),
        "source_url": row.get("source_url"),
        "tags": row.get("tags", []),
    }

    if row["type"] == "multiple_choice":
        return MCQQuestion(
            **common,
            option_a=row["option_a"] or "",
            option_b=row["option_b"] or "",
            option_c=row["option_c"] or "",
            option_d=row["option_d"] or "",
            correct_answer=row["correct_answer"] or "A",
            explanation=row["explanation"] or "",
            why_wrong_a=row.get("why_wrong_a"),
            why_wrong_b=row.get("why_wrong_b"),
            why_wrong_c=row.get("why_wrong_c"),
            why_wrong_d=row.get("why_wrong_d"),
        )
    else:
        return OpenEndedQuestion(
            **common,
            sample_answer=row.get("sample_answer") or "",
            evaluation_criteria=row.get("evaluation_criteria", []),
            resources=row.get("resources", []),
        )


class QuestionBank:
    """Manages loading and selecting questions from DuckDB."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
        self._asked_ids: list[str] = []

    def get_questions(
        self,
        topics: list[str] | None = None,
        subtopics: list[str] | None = None,
        difficulty: Difficulty = Difficulty.MIXED,
        count: int = 10,
    ) -> list[Question]:
        """Get a list of questions for a session.

        Args:
            topics: List of topic IDs to filter by.
            subtopics: List of subtopic IDs to filter by.
            difficulty: Difficulty level (MIXED = any).
            count: Number of questions to return.

        Returns:
            List of Question objects.
        """
        questions: list[Question] = []

        topic_list = topics or ["dbt"]

        for topic in topic_list:
            if subtopics:
                for subtopic in subtopics:
                    rows = fetch_questions(
                        self.conn,
                        topic=topic,
                        subtopic=subtopic,
                        difficulty=None if difficulty == Difficulty.MIXED else difficulty.value,
                        limit=count * 2,
                        exclude_ids=self._asked_ids,
                    )
                    questions.extend(_row_to_question(r) for r in rows)
            else:
                rows = fetch_questions(
                    self.conn,
                    topic=topic,
                    difficulty=None if difficulty == Difficulty.MIXED else difficulty.value,
                    limit=count * 2,
                    exclude_ids=self._asked_ids,
                )
                questions.extend(_row_to_question(r) for r in rows)

        random.shuffle(questions)
        selected = questions[:count]

        for q in selected:
            self._asked_ids.append(q.id)

        return selected

    def has_questions(
        self,
        topics: list[str] | None = None,
        difficulty: Difficulty = Difficulty.MIXED,
    ) -> bool:
        """Check if the bank has any questions for the given filters."""
        topic_list = topics or ["dbt"]
        for topic in topic_list:
            if count_questions(
                self.conn,
                topic=topic,
                difficulty=None if difficulty == Difficulty.MIXED else difficulty.value,
            ) > 0:
                return True
        return False

    def question_count(
        self,
        topics: list[str] | None = None,
        difficulty: Difficulty = Difficulty.MIXED,
    ) -> int:
        """Count available questions for the given filters."""
        topic_list = topics or ["dbt"]
        total = 0
        for topic in topic_list:
            total += count_questions(
                self.conn,
                topic=topic,
                difficulty=None if difficulty == Difficulty.MIXED else difficulty.value,
            )
        return total

    def reset_asked(self) -> None:
        """Reset the list of asked question IDs."""
        self._asked_ids.clear()
