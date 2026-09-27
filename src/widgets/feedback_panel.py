"""Feedback panel widget — displays evaluation results."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from src.questions.models import EvaluationResult, Question


class FeedbackPanel(Vertical):
    """A bordered widget that displays answer feedback."""

    DEFAULT_CSS = """
    FeedbackPanel {
        border: solid $success;
        border-title-color: $success;
        padding: 1 2;
        margin-bottom: 1;
        height: auto;
    }
    FeedbackPanel.incorrect {
        border: solid $error;
        border-title-color: $error;
    }
    """

    def __init__(self, result: EvaluationResult, question: Question | None = None) -> None:
        super().__init__()
        self.result = result
        self.question = question
        if result.is_correct:
            self.border_title = "Feedback — Correct"
            self.add_class("incorrect") if False else None
        else:
            self.border_title = "Feedback — Incorrect"
            self.add_class("incorrect")

    def compose(self) -> ComposeResult:
        if self.result.is_correct:
            yield Static("[bold green]✓ Correct![/bold green]")
        else:
            correct = self.result.correct_answer or ""
            yield Static(f"[bold red]✗ Incorrect. The correct answer is {correct}.[/bold red]")

        yield Static(f"\n{self.result.feedback}", classes="feedback-explanation")

        if self.question and self.question.source_url:
            yield Static(
                f"\n[dim]Source: {self.question.source_url}[/dim]",
                classes="feedback-source",
            )
