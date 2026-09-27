"""Session lifecycle management — start, run, and end quiz sessions."""

from __future__ import annotations

import time
from typing import Any

import duckdb

from src.database.queries import (
    fetch_session_by_topic,
    fetch_session_summary,
    fetch_weak_areas,
    insert_session,
    insert_session_question,
    update_session_duration,
)
from src.evaluation.mcq import evaluate_mcq
from src.questions.bank import QuestionBank
from src.questions.models import (
    EvaluationResult,
    MCQQuestion,
    OpenEndedQuestion,
    Question,
    SessionConfig,
    SessionSummary,
)


class SessionManager:
    """Manages a quiz session lifecycle."""

    def __init__(self, conn: duckdb.DuckDBPyConnection, user_id: int = 1):
        self.conn = conn
        self.user_id = user_id
        self.bank = QuestionBank(conn)
        self.session_id: str | None = None
        self.config: SessionConfig | None = None
        self.questions: list[Question] = []
        self.current_index: int = 0
        self.start_time: float | None = None
        self.score: int = 0
        self.streak: int = 0
        self.max_streak: int = 0
        self.results: list[dict[str, Any]] = []

    def start_session(self, config: SessionConfig) -> list[Question]:
        """Start a new quiz session.

        Args:
            config: Session configuration.

        Returns:
            List of questions for the session.
        """
        self.config = config
        self.session_id = insert_session(
            self.conn,
            user_id=self.user_id,
            topics=config.topics,
            difficulty=config.difficulty.value,
            question_count=config.question_count,
            web_search_enabled=config.use_web_search,
            web_search_recency_months=config.web_search_recency_months,
        )
        self.start_time = time.time()

        self.questions = self.bank.get_questions(
            topics=config.topics,
            subtopics=config.subtopics,
            difficulty=config.difficulty,
            count=config.question_count,
        )
        self.current_index = 0
        self.score = 0
        self.streak = 0
        self.max_streak = 0
        self.results = []

        return self.questions

    @property
    def current_question(self) -> Question | None:
        """Get the current question or None if session is over."""
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all questions have been answered."""
        return self.current_index >= len(self.questions)

    @property
    def progress(self) -> tuple[int, int]:
        """Get current progress as (answered_count, total_count)."""
        return (self.current_index, len(self.questions))

    def record_answer(
        self,
        question: Question,
        user_answer: str,
        result: EvaluationResult,
        time_spent: int | None = None,
    ) -> None:
        """Record an answer and its evaluation result.

        Args:
            question: The question that was answered.
            user_answer: The user's answer text.
            result: The evaluation result.
            time_spent: Time spent on the question in seconds.
        """
        if result.is_correct:
            self.score += 1
            self.streak += 1
            self.max_streak = max(self.max_streak, self.streak)
        else:
            self.streak = 0

        assert self.session_id is not None
        insert_session_question(
            self.conn,
            session_id=self.session_id,
            question_id=question.id,
            topic=question.topic,
            subtopic=question.subtopic,
            difficulty=question.difficulty.value,
            question_type=question.type.value,
            question_text=question.question_text,
            option_a=getattr(question, "option_a", None),
            option_b=getattr(question, "option_b", None),
            option_c=getattr(question, "option_c", None),
            option_d=getattr(question, "option_d", None),
            correct_answer=getattr(question, "correct_answer", None),
            user_answer=user_answer,
            is_correct=result.is_correct,
            score=result.score,
            time_spent_seconds=time_spent,
            feedback=result.feedback,
            source=question.source.value,
            source_url=question.source_url,
        )

        self.results.append(
            {
                "question": question,
                "user_answer": user_answer,
                "result": result,
                "time_spent": time_spent,
            }
        )
        self.current_index += 1

    def evaluate_answer(self, question: Question, user_answer: str) -> EvaluationResult:
        """Evaluate a user's answer to a question.

        Args:
            question: The question to evaluate.
            user_answer: The user's answer.

        Returns:
            EvaluationResult with score and feedback.
        """
        if isinstance(question, MCQQuestion):
            return evaluate_mcq(question, user_answer)
        elif isinstance(question, OpenEndedQuestion):
            from src.evaluation.open_ended import build_evaluation_prompt

            prompt = build_evaluation_prompt(question, user_answer)
            return EvaluationResult(
                is_correct=False,
                score=0,
                feedback=f"Open-ended evaluation requires the opencode agent.\n\n"
                f"Evaluation prompt:\n{prompt}\n\n"
                f"Sample answer:\n{question.sample_answer}",
            )
        else:
            return EvaluationResult(
                is_correct=False,
                score=0,
                feedback="Unknown question type.",
            )

    def end_session(self) -> SessionSummary:
        """End the session and return a summary.

        Returns:
            SessionSummary with aggregated statistics.
        """
        duration = int(time.time() - self.start_time) if self.start_time else 0

        session_id = self.session_id or ""
        if session_id:
            update_session_duration(self.conn, session_id, duration)

        summary = fetch_session_summary(self.conn, session_id)
        by_subtopic = fetch_session_by_topic(self.conn, session_id)
        weak_areas = fetch_weak_areas(self.conn, self.user_id)

        return SessionSummary(
            session_id=session_id,
            total_questions=int(summary.get("total_questions", 0)),
            correct=int(summary.get("correct", 0)),
            incorrect=int(summary.get("incorrect", 0)),
            accuracy=float(summary.get("accuracy", 0) or 0),
            duration_seconds=duration,
            by_subtopic=by_subtopic,
            weak_areas=weak_areas,
        )

    def get_current_score(self) -> tuple[int, int]:
        """Get current score as (correct, total_answered)."""
        return (self.score, self.current_index)

    def get_current_streak(self) -> int:
        """Get the current answer streak."""
        return self.streak

    def get_max_streak(self) -> int:
        """Get the maximum streak achieved in this session."""
        return self.max_streak
