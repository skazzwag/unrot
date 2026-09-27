"""Tests for session management."""

import tempfile
from pathlib import Path

import pytest

from src.database.connection import get_connection, initialize_database, reset_connection
from src.database.queries import insert_question
from src.questions.models import Difficulty, MCQQuestion, SessionConfig
from src.session.manager import SessionManager


@pytest.fixture
def conn_with_questions():
    """Create a temporary database with some test questions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        reset_connection()
        conn = get_connection(db_path)
        initialize_database(conn)

        for i in range(5):
            insert_question(
                conn,
                topic="dbt",
                subtopic="models",
                difficulty="intermediate",
                type="multiple_choice",
                question_text=f"Test question {i}?",
                option_a="Option A",
                option_b="Option B",
                option_c="Option C",
                option_d="Option D",
                correct_answer="A" if i % 2 == 0 else "B",
                explanation=f"Explanation {i}",
                why_wrong_a="Wrong A",
                why_wrong_b="Wrong B",
                why_wrong_c="Wrong C",
                why_wrong_d="Wrong D",
            )

        yield conn
        conn.close()
        reset_connection()


def test_session_lifecycle(conn_with_questions):
    """Test a full session lifecycle: start, answer, end."""
    manager = SessionManager(conn_with_questions)
    config = SessionConfig(
        topics=["dbt"],
        difficulty=Difficulty.INTERMEDIATE,
        question_count=3,
    )

    questions = manager.start_session(config)
    assert len(questions) == 3
    assert manager.session_id is not None
    assert manager.current_index == 0
    assert not manager.is_complete

    q = manager.current_question
    assert q is not None
    assert isinstance(q, MCQQuestion)

    correct_answer = q.correct_answer
    result = manager.evaluate_answer(q, correct_answer)
    assert result.is_correct
    manager.record_answer(q, correct_answer, result, time_spent=10)

    assert manager.score == 1
    assert manager.streak == 1
    assert manager.current_index == 1

    assert not manager.is_complete

    while not manager.is_complete:
        q = manager.current_question
        result = manager.evaluate_answer(q, "D")
        manager.record_answer(q, "D", result, time_spent=5)

    assert manager.is_complete
    assert manager.current_index == 3

    summary = manager.end_session()
    assert summary.total_questions == 3
    assert summary.correct == 1
    assert summary.incorrect == 2
    assert 0 < summary.accuracy <= 100
    assert summary.duration_seconds >= 0


def test_streak_tracking(conn_with_questions):
    """Test that streaks are tracked correctly."""
    manager = SessionManager(conn_with_questions)
    config = SessionConfig(
        topics=["dbt"],
        difficulty=Difficulty.INTERMEDIATE,
        question_count=5,
    )

    manager.start_session(config)

    for i, q in enumerate(manager.questions):
        if isinstance(q, MCQQuestion):
            if i < 3:
                result = manager.evaluate_answer(q, q.correct_answer)
            else:
                result = manager.evaluate_answer(q, "D")
            manager.record_answer(q, q.correct_answer if i < 3 else "D", result)

    assert manager.score == 3
    assert manager.max_streak == 3
    assert manager.streak == 0
