"""Quiz screen — the main question loop."""

from __future__ import annotations

import time
from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    ProgressBar,
    RadioSet,
    Static,
    TextArea,
)

from src.questions.models import (
    MCQQuestion,
    OpenEndedQuestion,
    Question,
    SessionConfig,
)
from src.session.manager import SessionManager
from src.widgets.feedback_panel import FeedbackPanel
from src.widgets.question_card import QuestionCard


class QuizScreen(Screen[Any]):
    """The main quiz screen where questions are presented and answered."""

    DEFAULT_CSS = """
    QuizScreen {
        layout: vertical;
    }
    #quiz-progress-container {
        dock: top;
        height: 3;
        padding: 0 2;
    }
    #quiz-content {
        padding: 1 2;
        height: 1fr;
    }
    #quiz-status {
        dock: top;
        height: 1;
        padding: 0 2;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("enter", "submit", "Submit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.session_manager: SessionManager | None = None
        self.question_start_time: float = 0
        self.current_question: Question | None = None
        self.answered = False

    def start_session(self, config: SessionConfig) -> None:
        """Start a new quiz session with the given config."""
        from src.database.connection import get_connection, initialize_database

        conn = get_connection()
        initialize_database(conn)
        self.session_manager = SessionManager(conn)
        self.session_manager.start_session(config)
        self.current_question = self.session_manager.current_question
        self.question_start_time = time.time()
        self.answered = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="quiz-progress-container"):
            yield ProgressBar(total=100, id="quiz-progress")
        yield Label("", id="quiz-status")
        with VerticalScroll(id="quiz-content"):
            pass
        yield Footer()

    def on_mount(self) -> None:
        if self.session_manager is not None:
            self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the quiz display with the current question or feedback state."""
        content = self.query_one("#quiz-content", VerticalScroll)
        content.remove_children()
        status = self.query_one("#quiz-status", Label)

        if self.session_manager is None:
            status.update("[dim]No active session.[/dim]")
            return

        if self.current_question is None:
            answered_count, total = self.session_manager.progress
            progress = self.query_one("#quiz-progress", ProgressBar)
            progress.update(progress=100 if total == 0 else (answered_count / total * 100))
            status.update("[dim]Session complete or no questions available.[/dim]")
            content.mount(
                Static(
                    "[bold yellow]No questions found in the database.[/bold yellow]\n\n"
                    "You need to generate questions first. Run:\n"
                    "  [cyan]uv run unrot generate-questions --topic dbt --count 10[/cyan]\n\n"
                    "Then use the opencode agent to generate and store questions\n"
                    "in the DuckDB database at ~/.unrot/unrot.duckdb"
                )
            )
            content.mount(Button("Back to Menu", id="back-btn", variant="primary"))
            return

        answered_count, total = self.session_manager.progress
        progress = self.query_one("#quiz-progress", ProgressBar)
        progress.update(progress=(answered_count / total * 100) if total > 0 else 0)

        correct, _ = self.session_manager.get_current_score()
        streak = self.session_manager.get_current_streak()
        status.update(
            f"[dim]Score: {correct}/{answered_count} | Streak: {streak}[/dim]"
        )

        qnum = answered_count + 1 if not self.answered else answered_count

        if not self.answered:
            card = QuestionCard(self.current_question, qnum, total)
            content.mount(card)

            if isinstance(self.current_question, MCQQuestion):
                options = self.current_question.options
                radio = RadioSet(
                    *[
                        f"[bold]{letter})[/bold] {options[letter]}"
                        for letter in ("A", "B", "C", "D")
                    ],
                    id="answer-radioset",
                )
                content.mount(radio)
            elif isinstance(self.current_question, OpenEndedQuestion):
                content.mount(TextArea(id="answer-textarea"))
            else:
                content.mount(Label("Unknown question type."))

            content.mount(Button("Submit", id="submit-btn", variant="primary"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-btn":
            self._submit_answer()
        elif event.button.id == "next-btn":
            self._next_question()
        elif event.button.id == "summary-btn":
            self._go_to_summary()
        elif event.button.id == "back-btn":
            self.app.switch_screen("welcome")

    def action_submit(self) -> None:
        self._submit_answer()

    def _submit_answer(self) -> None:
        if self.answered or self.session_manager is None or self.current_question is None:
            return

        user_answer = ""

        if isinstance(self.current_question, MCQQuestion):
            radio = self.query_one("#answer-radioset", RadioSet)
            if radio.pressed_button is None:
                return
            user_answer = chr(ord("A") + radio.pressed_index)
        elif isinstance(self.current_question, OpenEndedQuestion):
            textarea = self.query_one("#answer-textarea", TextArea)
            user_answer = textarea.text.strip()
            if not user_answer:
                return

        time_spent = int(time.time() - self.question_start_time)
        result = self.session_manager.evaluate_answer(self.current_question, user_answer)
        self.session_manager.record_answer(
            self.current_question, user_answer, result, time_spent=time_spent
        )

        self.answered = True
        self._show_feedback(result)

    def _show_feedback(self, result: Any) -> None:
        content = self.query_one("#quiz-content", VerticalScroll)

        for child in list(content.children):
            child.remove()

        panel = FeedbackPanel(result, question=self.current_question)
        content.mount(panel)

        if self.session_manager and not self.session_manager.is_complete:
            content.mount(Button("Next Question", id="next-btn", variant="primary"))
        else:
            content.mount(Button("View Summary", id="summary-btn", variant="success"))

    def _next_question(self) -> None:
        if self.session_manager is None:
            return

        if self.session_manager.is_complete:
            self._go_to_summary()
        else:
            self.current_question = self.session_manager.current_question
            self.question_start_time = time.time()
            self.answered = False
            self._refresh_display()

    def _go_to_summary(self) -> None:
        if self.session_manager is None:
            return
        summary = self.session_manager.end_session()

        from src.app import UnrotApp

        app = self.app
        if isinstance(app, UnrotApp):
            app.pending_summary = summary

        self.app.switch_screen("summary")
