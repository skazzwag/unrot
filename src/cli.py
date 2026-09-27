"""Typer CLI entry point for non-TUI commands."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="unrot",
    help="Terminal-based brain training for analytics engineers",
    no_args_is_help=True,
)


@app.command()
def start() -> None:
    """Start the interactive TUI quiz app."""
    from src.app import run

    run()


@app.command()
def generate_questions(
    topic: str = typer.Option("dbt", help="Topic to generate questions for"),
    difficulty: str = typer.Option(
        "intermediate",
        help="Difficulty level (beginner/intermediate/advanced/expert)",
    ),
    count: int = typer.Option(5, help="Number of questions to generate"),
    web_search: bool = typer.Option(True, help="Use web search for question generation"),
) -> None:
    """Generate quiz questions via the opencode agent.

    This command prints a prompt that the dbt-quiz-master agent uses to
    generate questions and store them in DuckDB.
    """
    from src.questions.generator import generate_questions_prompt
    from src.questions.models import Difficulty

    diff = Difficulty(difficulty)
    prompt = generate_questions_prompt(
        topic=topic,
        difficulty=diff,
        count=count,
        use_web_search=web_search,
    )
    typer.echo(prompt)


@app.command()
def stats() -> None:
    """Show overall statistics (non-TUI, prints to terminal)."""
    from src.database.connection import close_connection, get_connection, initialize_database
    from src.database.queries import (
        fetch_overall_stats,
        fetch_stats_by_difficulty,
        fetch_stats_by_topic,
        fetch_weak_areas,
    )

    conn = get_connection()
    initialize_database(conn)

    overall = fetch_overall_stats(conn)
    typer.echo("\n=== Overall Statistics ===")
    typer.echo(f"  Total Questions: {overall.get('total_questions', 0) or 0}")
    typer.echo(f"  Total Correct:   {overall.get('correct', 0) or 0}")
    typer.echo(f"  Overall Accuracy: {overall.get('accuracy', 0) or 0:.1f}%")
    typer.echo(f"  Total Sessions:  {overall.get('total_sessions', 0) or 0}")

    typer.echo("\n=== By Topic ===")
    topic_stats = fetch_stats_by_topic(conn)
    for stat in topic_stats:
        typer.echo(
            f"  {stat.get('topic', '')}/{stat.get('subtopic', 'general')}: "
            f"{stat.get('correct', 0)}/{stat.get('total', 0)} "
            f"({stat.get('accuracy', 0) or 0:.1f}%)"
        )

    typer.echo("\n=== By Difficulty ===")
    diff_stats = fetch_stats_by_difficulty(conn)
    for stat in diff_stats:
        typer.echo(
            f"  {stat.get('difficulty', '')}: "
            f"{stat.get('correct', 0)}/{stat.get('total', 0)} "
            f"({stat.get('accuracy', 0) or 0:.1f}%)"
        )

    typer.echo("\n=== Weak Areas (< 70% accuracy) ===")
    weak = fetch_weak_areas(conn)
    if weak:
        for area in weak:
            typer.echo(
                f"  {area.get('topic', '')}/{area.get('subtopic', 'general')}: "
                f"{area.get('accuracy', 0) or 0:.1f}%"
            )
    else:
        typer.echo("  None — great work!")

    close_connection(conn)


@app.command()
def config() -> None:
    """Show or update default configuration."""
    from src.database.connection import close_connection, get_connection, initialize_database

    conn = get_connection()
    initialize_database(conn)

    result = conn.execute("SELECT * FROM user_preferences WHERE id = 1").fetchone()
    if result:
        typer.echo("\n=== Current Configuration ===")
        typer.echo(f"  Username:              {result[1]}")
        typer.echo(f"  Default Topics:        {result[2]}")
        typer.echo(f"  Default Difficulty:    {result[3]}")
        typer.echo(f"  Default Question Count: {result[4]}")
        typer.echo(f"  Web Search:            {result[5]}")
        typer.echo(f"  Web Search Recency:    {result[6]} months")
    else:
        typer.echo("No configuration found. Run `unrot start` to initialize.")

    close_connection(conn)


@app.command()
def topics() -> None:
    """List all available topics and subtopics."""
    from pathlib import Path

    import yaml

    topics_path = Path(__file__).parent.parent / "data" / "topics.yaml"
    with open(topics_path) as f:
        data = yaml.safe_load(f)

    for topic_id, topic_data in data.get("topics", {}).items():
        typer.echo(f"\n=== {topic_data['name']} ({topic_id}) ===")
        typer.echo(f"  {topic_data['description']}")
        if topic_data.get("certifications"):
            typer.echo("  Certifications:")
            for cert in topic_data["certifications"]:
                typer.echo(f"    - {cert}")
        typer.echo("  Subtopics:")
        for subtopic in topic_data.get("subtopics", []):
            typer.echo(f"    - {subtopic['id']}: {subtopic['name']} — {subtopic['description']}")


def main() -> None:
    """Entry point for the unrot CLI."""
    app()


if __name__ == "__main__":
    main()
