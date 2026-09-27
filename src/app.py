"""Main Textual TUI application for unrot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import App

from src.questions.models import SessionSummary
from src.screens.quiz import QuizScreen
from src.screens.stats import StatsScreen
from src.screens.summary import SummaryScreen
from src.screens.welcome import WelcomeScreen


class UnrotApp(App[Any]):
    """The main unrot brain training TUI application."""

    CSS_PATH = Path("styles/app.tcss")

    SCREENS = {
        "welcome": WelcomeScreen,
        "quiz": QuizScreen,
        "summary": SummaryScreen,
        "stats": StatsScreen,
    }

    BINDINGS = [("q", "quit", "Quit")]

    TITLE = "unrot"
    SUB_TITLE = "Brain training for analytics engineers"

    def __init__(self) -> None:
        super().__init__()
        self.pending_summary: SessionSummary | None = None

    def on_mount(self) -> None:
        self.push_screen("welcome")


def run() -> None:
    """Run the TUI application."""
    app = UnrotApp()
    app.run()
