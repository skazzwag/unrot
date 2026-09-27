"""SQL queries for the unrot brain training app."""

from __future__ import annotations

import uuid
from typing import Any

import duckdb


def insert_question(
    conn: duckdb.DuckDBPyConnection,
    question_id: str | None = None,
    topic: str = "",
    subtopic: str | None = None,
    difficulty: str = "",
    type: str = "",
    question_text: str = "",
    option_a: str | None = None,
    option_b: str | None = None,
    option_c: str | None = None,
    option_d: str | None = None,
    correct_answer: str | None = None,
    explanation: str | None = None,
    why_wrong_a: str | None = None,
    why_wrong_b: str | None = None,
    why_wrong_c: str | None = None,
    why_wrong_d: str | None = None,
    sample_answer: str | None = None,
    evaluation_criteria: list[str] | None = None,
    resources: list[str] | None = None,
    tags: list[str] | None = None,
    source: str = "static",
    source_url: str | None = None,
) -> str:
    """Insert a question into the database and return its ID."""
    qid = question_id or str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO questions (
            id, topic, subtopic, difficulty, type, question_text,
            option_a, option_b, option_c, option_d, correct_answer,
            explanation, why_wrong_a, why_wrong_b, why_wrong_c, why_wrong_d,
            sample_answer, evaluation_criteria, resources, tags, source, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            qid, topic, subtopic, difficulty, type, question_text,
            option_a, option_b, option_c, option_d, correct_answer,
            explanation, why_wrong_a, why_wrong_b, why_wrong_c, why_wrong_d,
            sample_answer, evaluation_criteria or [], resources or [], tags or [],
            source, source_url,
        ],
    )
    return qid


def insert_provenance(
    conn: duckdb.DuckDBPyConnection,
    question_id: str,
    search_query: str | None = None,
    source_urls: list[str] | None = None,
    model_used: str | None = None,
    generation_prompt: str | None = None,
) -> str:
    """Insert provenance record for a question."""
    pid = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO question_provenance
            (id, question_id, search_query, source_urls, model_used, generation_prompt)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [pid, question_id, search_query, source_urls or [], model_used, generation_prompt],
    )
    return pid


def fetch_questions(
    conn: duckdb.DuckDBPyConnection,
    topic: str | None = None,
    subtopic: str | None = None,
    difficulty: str | None = None,
    question_type: str | None = None,
    limit: int = 100,
    exclude_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Fetch questions with optional filters."""
    query = "SELECT * FROM questions WHERE 1=1"
    params: list[Any] = []

    if topic is not None:
        query += " AND topic = ?"
        params.append(topic)
    if subtopic is not None:
        query += " AND subtopic = ?"
        params.append(subtopic)
    if difficulty is not None and difficulty != "mixed":
        query += " AND difficulty = ?"
        params.append(difficulty)
    if question_type is not None:
        query += " AND type = ?"
        params.append(question_type)
    if exclude_ids:
        placeholders = ",".join("?" for _ in exclude_ids)
        query += f" AND id NOT IN ({placeholders})"
        params.extend(exclude_ids)

    query += " ORDER BY RANDOM()"
    if limit:
        query += f" LIMIT {limit}"

    result = conn.execute(query, params)
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row, strict=False)) for row in result.fetchall()]


def count_questions(
    conn: duckdb.DuckDBPyConnection,
    topic: str | None = None,
    difficulty: str | None = None,
) -> int:
    """Count questions with optional filters."""
    query = "SELECT COUNT(*) FROM questions WHERE 1=1"
    params: list[Any] = []

    if topic is not None:
        query += " AND topic = ?"
        params.append(topic)
    if difficulty is not None and difficulty != "mixed":
        query += " AND difficulty = ?"
        params.append(difficulty)

    result = conn.execute(query, params)
    row = result.fetchone()
    return int(row[0]) if row else 0


def insert_session(
    conn: duckdb.DuckDBPyConnection,
    user_id: int = 1,
    topics: list[str] | None = None,
    difficulty: str = "mixed",
    question_count: int = 10,
    web_search_enabled: bool = True,
    web_search_recency_months: int = 6,
) -> str:
    """Insert a new session and return its ID."""
    sid = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO sessions
            (id, user_id, topics, difficulty, question_count,
             web_search_enabled, web_search_recency_months)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            sid, user_id, topics or [], difficulty, question_count,
            web_search_enabled, web_search_recency_months,
        ],
    )
    return sid


def update_session_duration(
    conn: duckdb.DuckDBPyConnection,
    session_id: str,
    duration_seconds: int,
) -> None:
    """Update session duration when session ends."""
    conn.execute(
        "UPDATE sessions SET duration_seconds = ? WHERE id = ?",
        [duration_seconds, session_id],
    )


def insert_session_question(
    conn: duckdb.DuckDBPyConnection,
    session_id: str,
    question_id: str | None,
    topic: str,
    subtopic: str | None,
    difficulty: str,
    question_type: str,
    question_text: str,
    option_a: str | None = None,
    option_b: str | None = None,
    option_c: str | None = None,
    option_d: str | None = None,
    correct_answer: str | None = None,
    user_answer: str | None = None,
    is_correct: bool | None = None,
    score: int | None = None,
    time_spent_seconds: int | None = None,
    feedback: str | None = None,
    source: str | None = None,
    source_url: str | None = None,
) -> str:
    """Insert a session question record and return its ID."""
    sqid = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO session_questions (
            id, session_id, question_id, topic, subtopic, difficulty, type,
            question_text, option_a, option_b, option_c, option_d, correct_answer,
            user_answer, is_correct, score, time_spent_seconds, feedback, source, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            sqid, session_id, question_id, topic, subtopic, difficulty, question_type,
            question_text, option_a, option_b, option_c, option_d, correct_answer,
            user_answer, is_correct, score, time_spent_seconds, feedback, source, source_url,
        ],
    )
    return sqid


def fetch_session_summary(
    conn: duckdb.DuckDBPyConnection,
    session_id: str,
) -> dict[str, Any]:
    """Fetch summary statistics for a session."""
    result = conn.execute(
        """
        SELECT
            COUNT(*) as total_questions,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN is_correct = FALSE THEN 1 ELSE 0 END) as incorrect,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as accuracy,
            MAX(score) as max_score,
            SUM(score) as total_score
        FROM session_questions
        WHERE session_id = ?
        """,
        [session_id],
    )
    columns = [desc[0] for desc in result.description]
    row = result.fetchone()
    return dict(zip(columns, row, strict=False)) if row else {}


def fetch_session_by_topic(
    conn: duckdb.DuckDBPyConnection,
    session_id: str,
) -> list[dict[str, Any]]:
    """Fetch per-subtopic performance for a session."""
    result = conn.execute(
        """
        SELECT
            COALESCE(subtopic, 'general') as subtopic,
            COUNT(*) as total,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as accuracy
        FROM session_questions
        WHERE session_id = ?
        GROUP BY subtopic
        ORDER BY accuracy ASC
        """,
        [session_id],
    )
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row, strict=False)) for row in result.fetchall()]


def fetch_overall_stats(
    conn: duckdb.DuckDBPyConnection,
    user_id: int = 1,
) -> dict[str, Any]:
    """Fetch overall statistics for a user."""
    result = conn.execute(
        """
        SELECT
            COUNT(*) as total_questions,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0) as accuracy,
            COUNT(DISTINCT session_id) as total_sessions
        FROM session_questions sq
        JOIN sessions s ON sq.session_id = s.id
        WHERE s.user_id = ?
        """,
        [user_id],
    )
    columns = [desc[0] for desc in result.description]
    row = result.fetchone()
    return dict(zip(columns, row, strict=False)) if row else {}


def fetch_stats_by_topic(
    conn: duckdb.DuckDBPyConnection,
    user_id: int = 1,
) -> list[dict[str, Any]]:
    """Fetch per-topic accuracy for a user."""
    result = conn.execute(
        """
        SELECT
            sq.topic,
            COALESCE(sq.subtopic, 'general') as subtopic,
            COUNT(*) as total,
            SUM(CASE WHEN sq.is_correct THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN sq.is_correct THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as accuracy
        FROM session_questions sq
        JOIN sessions s ON sq.session_id = s.id
        WHERE s.user_id = ?
        GROUP BY sq.topic, sq.subtopic
        ORDER BY accuracy ASC
        """,
        [user_id],
    )
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row, strict=False)) for row in result.fetchall()]


def fetch_stats_by_difficulty(
    conn: duckdb.DuckDBPyConnection,
    user_id: int = 1,
) -> list[dict[str, Any]]:
    """Fetch per-difficulty accuracy for a user."""
    result = conn.execute(
        """
        SELECT
            sq.difficulty,
            COUNT(*) as total,
            SUM(CASE WHEN sq.is_correct THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN sq.is_correct THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as accuracy
        FROM session_questions sq
        JOIN sessions s ON sq.session_id = s.id
        WHERE s.user_id = ?
        GROUP BY sq.difficulty
        ORDER BY accuracy ASC
        """,
        [user_id],
    )
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row, strict=False)) for row in result.fetchall()]


def fetch_weak_areas(
    conn: duckdb.DuckDBPyConnection,
    user_id: int = 1,
    threshold: float = 70.0,
) -> list[dict[str, Any]]:
    """Fetch topics with accuracy below threshold."""
    result = conn.execute(
        """
        SELECT
            sq.topic,
            COALESCE(sq.subtopic, 'general') as subtopic,
            COUNT(*) as total,
            SUM(CASE WHEN sq.is_correct THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN sq.is_correct THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as accuracy
        FROM session_questions sq
        JOIN sessions s ON sq.session_id = s.id
        WHERE s.user_id = ?
        GROUP BY sq.topic, sq.subtopic
        HAVING accuracy < ?
        ORDER BY accuracy ASC
        """,
        [user_id, threshold],
    )
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row, strict=False)) for row in result.fetchall()]


def fetch_session_history(
    conn: duckdb.DuckDBPyConnection,
    user_id: int = 1,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Fetch recent session history for a user."""
    result = conn.execute(
        """
        SELECT
            s.id as session_id,
            s.timestamp,
            s.duration_seconds,
            s.difficulty,
            s.question_count,
            COUNT(sq.id) as questions_answered,
            SUM(CASE WHEN sq.is_correct THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN sq.is_correct THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(sq.id), 0) as accuracy
        FROM sessions s
        LEFT JOIN session_questions sq ON s.id = sq.session_id
        WHERE s.user_id = ?
        GROUP BY s.id, s.timestamp, s.duration_seconds, s.difficulty, s.question_count
        ORDER BY s.timestamp DESC
        LIMIT ?
        """,
        [user_id, limit],
    )
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row, strict=False)) for row in result.fetchall()]
