"""Question card widget — bordered display for quiz questions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from src.questions.models import MCQQuestion, OpenEndedQuestion, Question


class QuestionCard(Vertical):
    """A bordered widget that displays a question with metadata header."""

    DEFAULT_CSS = """
    QuestionCard {
        border: solid $primary;
        border-title-color: $primary;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
    }
    """

    def __init__(self, question: Question, question_number: int, total: int) -> None:
        super().__init__()
        self.question = question
        self.question_number = question_number
        self.total = total
        self.border_title = f"Question {question_number}/{total}"

    def compose(self) -> ComposeResult:
        type_str = (
            "Multiple Choice"
            if self.question.type.value == "multiple_choice"
            else "Open Ended"
        )
        meta_text = (
            f"[Topic: {self.question.topic}"
            f"{' / ' + self.question.subtopic if self.question.subtopic else ''}] "
            f"[Difficulty: {self.question.difficulty.value}] "
            f"[Type: {type_str}]"
        )
        yield Static(meta_text, classes="question-meta")
        yield Static(self.question.question_text, classes="question-text")

        if isinstance(self.question, MCQQuestion):
            options = self.question.options
            for letter in ("A", "B", "C", "D"):
                yield Static(f"  [bold]{letter})[/bold] {options[letter]}")

        elif isinstance(self.question, OpenEndedQuestion):
            yield Static(
                "\n[dim]Please provide a detailed answer. I will evaluate it based on "
                "accuracy, completeness, and adherence to best practices.[/dim]"
            )
