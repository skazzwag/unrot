"""Tests for the database layer."""

import tempfile
from pathlib import Path

import pytest

from src.database.connection import get_connection, initialize_database, reset_connection
from src.database.queries import (
    count_questions,
    fetch_questions,
    fetch_session_summary,
    insert_question,
    insert_session,
    insert_session_question,
)


@pytest.fixture
def conn():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        reset_connection()
        conn = get_connection(db_path)
        initialize_database(conn)
        yield conn
        conn.close()
        reset_connection()


def test_initialize_database_creates_tables(conn):
    """Test that initialize_database creates all expected tables."""
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    table_names = {t[0] for t in tables}
    assert "user_preferences" in table_names
    assert "questions" in table_names
    assert "question_provenance" in table_names
    assert "sessions" in table_names
    assert "session_questions" in table_names
    assert "performance_stats" in table_names


def test_default_user_created(conn):
    """Test that the default user is created on initialization."""
    result = conn.execute("SELECT username FROM user_preferences WHERE id = 1").fetchone()
    assert result is not None
    assert result[0] == "default"


def test_insert_and_fetch_question(conn):
    """Test inserting and fetching a question."""
    qid = insert_question(
        conn,
        topic="dbt",
        subtopic="snapshots",
        difficulty="intermediate",
        type="multiple_choice",
        question_text="What is an SCD Type 2 snapshot?",
        option_a="A snapshot that only keeps the latest version",
        option_b="A snapshot that tracks historical changes with validity dates",
        option_c="A snapshot that merges all versions",
        option_d="A snapshot that deletes old records",
        correct_answer="B",
        explanation=(
            "SCD Type 2 tracks changes by keeping historical records "
            "with valid_from/valid_to dates."
        ),
        why_wrong_a="This describes SCD Type 1, which overwrites.",
        why_wrong_c="This describes merge strategy, not SCD Type 2.",
        why_wrong_d="This would lose history entirely.",
    )
    assert qid

    questions = fetch_questions(conn, topic="dbt")
    assert len(questions) == 1
    assert questions[0]["question_text"] == "What is an SCD Type 2 snapshot?"
    assert questions[0]["correct_answer"] == "B"


def test_count_questions(conn):
    """Test counting questions."""
    assert count_questions(conn, topic="dbt") == 0

    insert_question(
        conn,
        topic="dbt",
        difficulty="beginner",
        type="multiple_choice",
        question_text="Test question 1",
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="A",
        explanation="Because A.",
    )

    insert_question(
        conn,
        topic="dbt",
        difficulty="advanced",
        type="multiple_choice",
        question_text="Test question 2",
        option_a="A",
        option_b="B",
        option_c="C",
        option_d="D",
        correct_answer="B",
        explanation="Because B.",
    )

    assert count_questions(conn, topic="dbt") == 2
    assert count_questions(conn, topic="dbt", difficulty="beginner") == 1
    assert count_questions(conn, topic="dbt", difficulty="advanced") == 1


def test_insert_session_and_questions(conn):
    """Test inserting a session with questions."""
    sid = insert_session(conn, topics=["dbt"], difficulty="mixed", question_count=2)
    assert sid

    insert_session_question(
        conn,
        session_id=sid,
        question_id=None,
        topic="dbt",
        subtopic="models",
        difficulty="intermediate",
        question_type="multiple_choice",
        question_text="What does ref() do?",
        correct_answer="A",
        user_answer="A",
        is_correct=True,
        score=3,
    )

    insert_session_question(
        conn,
        session_id=sid,
        question_id=None,
        topic="dbt",
        subtopic="tests",
        difficulty="beginner",
        question_type="multiple_choice",
        question_text="What is a generic test?",
        correct_answer="B",
        user_answer="A",
        is_correct=False,
        score=0,
    )

    summary = fetch_session_summary(conn, sid)
    assert summary["total_questions"] == 2
    assert summary["correct"] == 1
    assert summary["incorrect"] == 1
    assert 50.0 == float(summary["accuracy"])
