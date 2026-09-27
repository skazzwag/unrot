"""Pydantic models for questions and evaluation results."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MIXED = "mixed"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"


class QuestionSource(str, Enum):
    STATIC = "static"
    WEB_SEARCH = "web_search"
    CUSTOM = "custom"


class Question(BaseModel):
    """Base question model."""

    id: str
    topic: str
    subtopic: str | None = None
    difficulty: Difficulty
    type: QuestionType
    question_text: str
    source: QuestionSource = QuestionSource.STATIC
    source_url: str | None = None
    tags: list[str] = Field(default_factory=list)


class MCQQuestion(Question):
    """Multiple choice question with exactly 4 options."""

    type: QuestionType = QuestionType.MULTIPLE_CHOICE
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str = Field(pattern="^[A-D]$")
    explanation: str
    why_wrong_a: str | None = None
    why_wrong_b: str | None = None
    why_wrong_c: str | None = None
    why_wrong_d: str | None = None

    @property
    def options(self) -> dict[str, str]:
        return {
            "A": self.option_a,
            "B": self.option_b,
            "C": self.option_c,
            "D": self.option_d,
        }

    def get_wrong_explanations(self) -> dict[str, str | None]:
        return {
            "A": self.why_wrong_a,
            "B": self.why_wrong_b,
            "C": self.why_wrong_c,
            "D": self.why_wrong_d,
        }


class OpenEndedQuestion(Question):
    """Open-ended question requiring a detailed answer."""

    type: QuestionType = QuestionType.OPEN_ENDED
    sample_answer: str
    evaluation_criteria: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    """Result of evaluating a user's answer."""

    is_correct: bool
    score: int = Field(ge=0, le=3)
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    correct_answer: str | None = None
    resources: list[str] = Field(default_factory=list)


class SessionConfig(BaseModel):
    """Configuration for a quiz session."""

    topics: list[str] = Field(default_factory=lambda: ["dbt"])
    subtopics: list[str] | None = None
    difficulty: Difficulty = Difficulty.MIXED
    question_count: int = 10
    use_web_search: bool = True
    web_search_recency_months: int = 6


class SessionSummary(BaseModel):
    """Summary of a completed quiz session."""

    session_id: str
    total_questions: int
    correct: int
    incorrect: int
    accuracy: float
    duration_seconds: int
    by_subtopic: list[dict[str, object]] = Field(default_factory=list)
    weak_areas: list[dict[str, object]] = Field(default_factory=list)


class TopicConfig(BaseModel):
    """Configuration for a topic from topics.yaml."""

    name: str
    description: str
    certifications: list[str] = Field(default_factory=list)
    subtopics: list[dict[str, str]] = Field(default_factory=list)
