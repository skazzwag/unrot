"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from src.questions.models import (
    Difficulty,
    EvaluationResult,
    MCQQuestion,
    OpenEndedQuestion,
    QuestionType,
    SessionConfig,
)


def test_mcq_question_creation():
    """Test creating a valid MCQ question."""
    q = MCQQuestion(
        id="test-1",
        topic="dbt",
        subtopic="snapshots",
        difficulty=Difficulty.INTERMEDIATE,
        question_text="What is SCD Type 2?",
        option_a="Overwrites old values",
        option_b="Tracks history with validity dates",
        option_c="Merges all versions",
        option_d="Deletes old records",
        correct_answer="B",
        explanation="SCD Type 2 keeps historical records.",
    )
    assert q.type == QuestionType.MULTIPLE_CHOICE
    assert q.correct_answer == "B"
    assert q.options["A"] == "Overwrites old values"


def test_mcq_invalid_answer():
    """Test that invalid correct_answer raises ValidationError."""
    with pytest.raises(ValidationError):
        MCQQuestion(
            id="test-2",
            topic="dbt",
            difficulty=Difficulty.BEGINNER,
            question_text="Test?",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="E",
            explanation="Test",
        )


def test_open_ended_question():
    """Test creating an open-ended question."""
    q = OpenEndedQuestion(
        id="test-3",
        topic="dbt",
        subtopic="best_practices",
        difficulty=Difficulty.EXPERT,
        question_text="Explain idempotence in dbt.",
        sample_answer="Idempotence means running a model multiple times produces the same result.",
        evaluation_criteria=["Mentions deterministic results", "References incremental models"],
        resources=["https://docs.getdbt.com/best-practices/idempotence"],
    )
    assert q.type == QuestionType.OPEN_ENDED
    assert "deterministic" in q.evaluation_criteria[0]


def test_evaluation_result():
    """Test creating an evaluation result."""
    r = EvaluationResult(
        is_correct=True,
        score=3,
        feedback="Great answer!",
        strengths=["Accurate", "Comprehensive"],
        improvements=[],
    )
    assert r.is_correct
    assert r.score == 3


def test_evaluation_result_score_range():
    """Test that score must be 0-3."""
    with pytest.raises(ValidationError):
        EvaluationResult(is_correct=True, score=5, feedback="Test")
    with pytest.raises(ValidationError):
        EvaluationResult(is_correct=False, score=-1, feedback="Test")


def test_session_config_defaults():
    """Test SessionConfig default values."""
    config = SessionConfig()
    assert config.topics == ["dbt"]
    assert config.difficulty == Difficulty.MIXED
    assert config.question_count == 10
    assert config.use_web_search is True


def test_difficulty_enum():
    """Test Difficulty enum values."""
    assert Difficulty("beginner") == Difficulty.BEGINNER
    assert Difficulty("mixed") == Difficulty.MIXED
    assert Difficulty.MIXED.value == "mixed"
