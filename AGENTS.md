# AGENTS.md

## Project: unrot

Terminal-based brain training app for analytics engineers. Built with Python, Textual (TUI), Typer (CLI), and DuckDB.

## Quick Start

```bash
# Install dependencies
uv sync

# Run the TUI
uv run unrot start

# List topics
uv run unrot topics

# Show stats
uv run unrot stats

# Generate questions (prints prompt for the opencode agent)
uv run unrot generate-questions --topic dbt --difficulty intermediate --count 5

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

## Architecture

- **TUI Framework:** Textual (screens: welcome → quiz → summary → stats)
- **CLI Framework:** Typer (for non-interactive commands: generate-questions, stats, config, topics)
- **Database:** DuckDB at `~/.unrot/unrot.duckdb`
- **Models:** Pydantic v2
- **Question Generation:** opencode agent (`.opencode/agent/dbt-quiz-master.md`) — no default model, inherits user's global opencode setting
- **Topics:** Defined in `data/topics.yaml`

## Key Modules

- `src/app.py` — Main Textual App class, screen management
- `src/cli.py` — Typer CLI for non-TUI commands
- `src/screens/` — Textual screens (welcome, quiz, summary, stats)
- `src/widgets/` — Custom Textual widgets (question card, feedback panel, stats table)
- `src/database/` — DuckDB connection, schema, queries
- `src/questions/` — Pydantic models, question bank, generator interface
- `src/evaluation/` — MCQ evaluation (exact match), open-ended evaluation (LLM interface)
- `src/session/` — Session lifecycle management

## DuckDB Schema

5 tables: `questions`, `question_provenance`, `sessions`, `session_questions`, `performance_stats`, `user_preferences`.

See `src/database/schema.py` for DDL.

## Conventions

- Python 3.10+
- Type hints everywhere (mypy strict)
- Ruff for linting (E, F, I, N, W, UP rules)
- Line length: 100
- No comments in code unless asked
