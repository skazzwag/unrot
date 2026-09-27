"""Welcome screen — session configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    Switch,
)

from src.questions.models import Difficulty, SessionConfig

TOPICS_PATH = Path(__file__).parent.parent.parent / "data" / "topics.yaml"


def load_topics() -> dict[str, Any]:
    """Load topic definitions from YAML."""
    import yaml as yaml_module

    with open(TOPICS_PATH) as f:
        data = yaml_module.safe_load(f)
    return dict(data) if data else {}


class WelcomeScreen(Screen[Any]):
    """Welcome screen for configuring a new quiz session."""

    DEFAULT_CSS = """
    WelcomeScreen {
        align: center middle;
    }
    #welcome-scroll {
        width: 85%;
        max-width: 100;
        height: 85%;
        max-height: 85%;
        border: solid $primary;
        padding: 1 2;
    }
    #welcome-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 1 0;
    }
    .config-row {
        height: 3;
        padding: 0 1;
    }
    .config-label {
        color: $accent;
        text-style: bold;
        width: 20;
    }
    .config-input {
        width: 1fr;
    }
    .button-row {
        height: 3;
        align: center middle;
        padding-top: 1;
    }
    #question-count {
        width: 10;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll(id="welcome-scroll"):
            yield Static(
                " _   _  ___  _   _  ___ _____ ____\n"
                "| | | |/ _ \\| \\ | |/ _ \\_   _/ ___|\n"
                "| |_| | | | |  \\| | | | || |  \\___ \\\n"
                "|  _  | |_| | |\\  | |_| || |   ___) |\n"
                "|_| |_|\\___/|_| \\_|\\___/ |_|  |____/\n"
                "[dim]Brain training for analytics engineers[/dim]",
                id="welcome-title",
            )

            yield Static("")

            yield Label("Session Configuration", classes="config-label")

            yield Static("")

            with Horizontal(classes="config-row"):
                yield Label("Difficulty:", classes="config-label")
                yield Select(
                    [
                        ("Mixed", "mixed"),
                        ("Beginner", "beginner"),
                        ("Intermediate", "intermediate"),
                        ("Advanced", "advanced"),
                        ("Expert", "expert"),
                    ],
                    value="mixed",
                    id="difficulty-select",
                    classes="config-input",
                )

            with Horizontal(classes="config-row"):
                yield Label("Questions:", classes="config-label")
                yield Input(value="10", id="question-count")

            with Horizontal(classes="config-row"):
                yield Label("Web search:", classes="config-label")
                yield Switch(value=True, id="web-search-toggle")

            yield Static("")

            topics_data = load_topics()
            subtopics = topics_data.get("topics", {}).get("dbt", {}).get("subtopics", [])
            subtopic_labels = [(s["name"], s["id"]) for s in subtopics]

            yield Label("Subtopics (leave unselected for all):", classes="config-label")
            yield Static("")

            from textual.widgets import SelectionList

            yield SelectionList[str](
                *[(label, value) for label, value in subtopic_labels],
                id="subtopic-select",
            )

            yield Static("")

            with Horizontal(classes="button-row"):
                yield Button("Start Session", id="start-btn", variant="primary")

            yield Static("")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            self.start_session()

    def start_session(self) -> None:
        """Collect config and switch to quiz screen."""
        difficulty = Difficulty(self.query_one("#difficulty-select", Select).value)
        count_str = self.query_one("#question-count", Input).value
        try:
            question_count = int(count_str) if count_str else 10
        except ValueError:
            question_count = 10

        use_web_search = self.query_one("#web-search-toggle", Switch).value

        from textual.widgets import SelectionList

        selection_list = self.query_one("#subtopic-select", SelectionList)
        selected_subtopics: list[str] = [str(item.value) for item in selection_list.selected]

        config = SessionConfig(
            topics=["dbt"],
            subtopics=selected_subtopics if selected_subtopics else None,
            difficulty=difficulty,
            question_count=question_count,
            use_web_search=use_web_search,
        )

        quiz_screen = self.app.get_screen("quiz")
        from src.screens.quiz import QuizScreen

        if isinstance(quiz_screen, QuizScreen):
            quiz_screen.start_session(config)
        self.app.switch_screen("quiz")
