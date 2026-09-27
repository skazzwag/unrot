"""Stats screen — historical performance statistics."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Static


class StatsScreen(Screen[None]):
    """Screen showing historical performance statistics."""

    DEFAULT_CSS = """
    StatsScreen {
        padding: 1 2;
    }
    #stats-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 1 0;
    }
    .stats-table {
        margin: 1 2;
    }
    .button-row {
        align: center middle;
        height: 3;
        padding-top: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit"), ("escape", "back", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Overall Statistics", id="stats-title")

        with VerticalScroll():
            yield Label("Overall Performance:", classes="config-label")
            yield DataTable(id="overall-history", classes="stats-table")

            yield Label("Performance by Subtopic:", classes="config-label")
            yield DataTable(id="topic-breakdown", classes="stats-table")

            yield Label("Performance by Difficulty:", classes="config-label")
            yield DataTable(id="difficulty-breakdown", classes="stats-table")

            yield Label("Recent Sessions:", classes="config-label")
            yield DataTable(id="session-history", classes="stats-table")

            with Vertical(classes="button-row"):
                yield Button("New Session", id="new-session-btn", variant="primary")
                yield Button("Back", id="back-btn", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        self._populate_tables()

    def _populate_tables(self) -> None:
        from src.database.connection import get_connection, initialize_database
        from src.database.queries import (
            fetch_overall_stats,
            fetch_session_history,
            fetch_stats_by_difficulty,
            fetch_stats_by_topic,
        )

        conn = get_connection()
        initialize_database(conn)

        overall = self.query_one("#overall-history", DataTable)
        overall.clear(columns=True)
        overall.add_column("Metric")
        overall.add_column("Value")

        stats = fetch_overall_stats(conn)
        if stats:
            overall.add_row("Total Questions", str(stats.get("total_questions", 0) or 0))
            overall.add_row("Total Correct", str(stats.get("correct", 0) or 0))
            overall.add_row(
                "Overall Accuracy",
                f"{stats.get('accuracy', 0) or 0:.1f}%",
            )
            overall.add_row("Total Sessions", str(stats.get("total_sessions", 0) or 0))

        topic_table = self.query_one("#topic-breakdown", DataTable)
        topic_table.clear(columns=True)
        topic_table.add_column("Topic")
        topic_table.add_column("Subtopic")
        topic_table.add_column("Correct")
        topic_table.add_column("Total")
        topic_table.add_column("Accuracy")

        topic_stats = fetch_stats_by_topic(conn)
        for stat in topic_stats:
            topic_table.add_row(
                str(stat.get("topic", "")),
                str(stat.get("subtopic", "general")),
                str(stat.get("correct", 0)),
                str(stat.get("total", 0)),
                f"{stat.get('accuracy', 0) or 0:.1f}%",
            )

        diff_table = self.query_one("#difficulty-breakdown", DataTable)
        diff_table.clear(columns=True)
        diff_table.add_column("Difficulty")
        diff_table.add_column("Correct")
        diff_table.add_column("Total")
        diff_table.add_column("Accuracy")

        diff_stats = fetch_stats_by_difficulty(conn)
        for stat in diff_stats:
            diff_table.add_row(
                str(stat.get("difficulty", "")),
                str(stat.get("correct", 0)),
                str(stat.get("total", 0)),
                f"{stat.get('accuracy', 0) or 0:.1f}%",
            )

        history = self.query_one("#session-history", DataTable)
        history.clear(columns=True)
        history.add_column("Timestamp")
        history.add_column("Difficulty")
        history.add_column("Questions")
        history.add_column("Correct")
        history.add_column("Accuracy")
        history.add_column("Duration")

        sessions = fetch_session_history(conn)
        for session in sessions:
            duration = session.get("duration_seconds") or 0
            history.add_row(
                str(session.get("timestamp", "")),
                str(session.get("difficulty", "")),
                str(session.get("questions_answered", 0)),
                str(session.get("correct", 0)),
                f"{session.get('accuracy', 0) or 0:.1f}%",
                f"{duration // 60}m {duration % 60}s",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-session-btn":
            self.app.switch_screen("welcome")
        elif event.button.id == "back-btn":
            self.app.switch_screen("welcome")

    def action_back(self) -> None:
        self.app.switch_screen("welcome")
