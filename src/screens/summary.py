"""Summary screen — displays session results."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Static

from src.questions.models import SessionSummary


class SummaryScreen(Screen[None]):
    """Screen showing session summary statistics."""

    DEFAULT_CSS = """
    SummaryScreen {
        padding: 1 2;
    }
    #summary-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 1 0;
    }
    .summary-table {
        margin: 1 2;
    }
    .weak-area {
        color: $warning;
        padding: 0 2;
    }
    .button-row {
        align: center middle;
        height: 3;
        padding-top: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit"), ("s", "stats", "Stats")]

    def __init__(self) -> None:
        super().__init__()
        self.summary: SessionSummary | None = None

    def set_summary(self, summary: SessionSummary) -> None:
        self.summary = summary
        try:
            self._populate_tables()
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Session Summary", id="summary-title")

        with VerticalScroll():
            yield DataTable(id="overall-stats", classes="summary-table")
            yield Label("Performance by Subtopic:", classes="config-label")
            yield DataTable(id="topic-stats", classes="summary-table")

            if self.summary and self.summary.weak_areas:
                yield Label("Areas to Review:", classes="config-label")
                for area in self.summary.weak_areas:
                    subtopic = area.get("subtopic", "unknown")
                    accuracy = area.get("accuracy", 0)
                    yield Static(
                        f"  ▸ {subtopic} — {accuracy:.1f}% accuracy",
                        classes="weak-area",
                    )

            with Vertical(classes="button-row"):
                yield Button("New Session", id="new-session-btn", variant="primary")
                yield Button("View Stats", id="stats-btn", variant="default")
                yield Button("Quit", id="quit-btn", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        from src.app import UnrotApp

        app = self.app
        if isinstance(app, UnrotApp) and app.pending_summary is not None:
            self.summary = app.pending_summary
            app.pending_summary = None
        self._populate_tables()

    def _populate_tables(self) -> None:
        overall = self.query_one("#overall-stats", DataTable)
        overall.clear(columns=True)
        overall.add_column("Metric")
        overall.add_column("Value")

        if self.summary is None:
            overall.add_row("No data", "")
            return

        overall.add_row("Total Questions", str(self.summary.total_questions))
        overall.add_row("Correct", str(self.summary.correct))
        overall.add_row("Incorrect", str(self.summary.incorrect))
        overall.add_row(
            "Accuracy",
            f"{self.summary.accuracy:.1f}%",
        )
        overall.add_row(
            "Time Spent",
            f"{self.summary.duration_seconds // 60}m {self.summary.duration_seconds % 60}s",
        )

        topic_table = self.query_one("#topic-stats", DataTable)
        topic_table.clear(columns=True)
        topic_table.add_column("Subtopic")
        topic_table.add_column("Correct")
        topic_table.add_column("Total")
        topic_table.add_column("Accuracy")

        for stat in self.summary.by_subtopic:
            subtopic = stat.get("subtopic", "general")
            correct = stat.get("correct", 0)
            total = stat.get("total", 0)
            accuracy = stat.get("accuracy", 0)
            topic_table.add_row(
                str(subtopic),
                str(correct),
                str(total),
                f"{accuracy:.1f}%",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-session-btn":
            self.app.switch_screen("welcome")
        elif event.button.id == "stats-btn":
            self.app.switch_screen("stats")
        elif event.button.id == "quit-btn":
            self.app.exit()

    def action_stats(self) -> None:
        self.app.switch_screen("stats")
