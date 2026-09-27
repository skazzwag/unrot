# Implementation Plan: dbt Brain Training CLI with Textual TUI

## Overview

Build a Python TUI app using **Textual** for the interactive quiz interface and **Typer** for non-interactive CLI commands. Quiz questions are scoped to dbt Core topics covering the dbt Analytics Engineering Certification and dbt Fundamentals. Progress is tracked in DuckDB at `~/.unrot/unrot.duckdb`. Question generation and open-ended answer evaluation use an opencode agent (no default model — inherits the user's global opencode setting).

## Directory Structure

```
unrot/
├── src/
│   ├── __init__.py
│   ├── __main__.py               # `python -m src`
│   ├── cli.py                    # Typer entry point for non-TUI commands
│   ├── app.py                    # Main Textual App class, screen management
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── welcome.py            # Welcome + session config screen
│   │   ├── quiz.py                # Quiz session screen (question loop)
│   │   ├── summary.py             # Session summary screen
│   │   └── stats.py               # Historical stats screen
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── question_card.py       # Bordered question display widget
│   │   ├── feedback_panel.py      # Feedback display widget
│   │   └── stats_table.py         # Stats DataTable wrapper
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py         # DuckDB connection management
│   │   ├── schema.py              # DDL for all tables
│   │   └── queries.py             # CRUD + analytics queries
│   ├── questions/
│   │   ├── __init__.py
│   │   ├── models.py              # Pydantic: Question, MCQQuestion, OpenEndedQuestion, EvaluationResult
│   │   ├── bank.py                # Load/filter questions from DuckDB
│   │   └── generator.py           # LLM question generation interface (calls opencode agent)
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── mcq.py                 # Exact match evaluation
│   │   └── open_ended.py          # LLM-powered evaluation interface
│   ├── session/
│   │   ├── __init__.py
│   │   └── manager.py             # Session lifecycle: start, Q&A loop, end, summary
│   └── styles/
│       └── app.tcss               # Textual CSS for theming
├── .opencode/
│   ├── agent/
│   │   └── dbt-quiz-master.md     # Agent: question gen + open-ended eval
│   └── command/
│       └── quiz.md                # /quiz command
├── data/
│   └── topics.yaml                # dbt topic/subtopic taxonomy
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_models.py
│   └── test_session.py
├── pyproject.toml
├── opencode.json                  # Project config (no default model specified)
├── AGENTS.md
└── README.md
```

## Implementation Steps

### Phase 1: Project Setup

#### 1.1 pyproject.toml
```toml
[project]
name = "unrot"
version = "0.1.0"
description = "Terminal-based brain training for analytics engineers"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "textual>=3.0.0",
    "typer>=0.12.0",
    "duckdb>=1.0.0",
    "pydantic>=2.5.0",
    "pyyaml>=6.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.6.0",
    "mypy>=1.10.0",
]

[project.scripts]
unrot = "src.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.10"
strict = true
```

#### 1.2 data/topics.yaml
dbt topic taxonomy covering certification areas:
- project_structure
- models (materializations, staging/intermediate/marts, ref())
- jinja_macros (templating, macros, variables)
- tests (generic, singular, custom, severity)
- snapshots (SCD Type 2)
- seeds (static data)
- sources (freshness, metadata)
- documentation (docs blocks, catalog, lineage)
- incremental_models (strategies, partitioning)
- packages (dbt-utils, dependencies)
- artifacts (manifest, run_results, catalog)
- commands (build vs run vs test)
- environments (profiles, targets)
- best_practices (idempotence, DRY, CI/CD)

### Phase 2: Database Layer

#### 2.1 src/database/schema.py
DDL for 5 tables:
- `questions` — question bank with provenance (source, source_url, generation_prompt)
- `sessions` — quiz session metadata
- `session_questions` — per-question answers within sessions
- `performance_stats` — aggregated stats by topic/difficulty
- `question_provenance` — tracks where questions came from (search query, URLs, model, timestamp)

#### 2.2 src/database/connection.py
- `get_connection()` — singleton DuckDB connection to `~/.unrot/unrot.duckdb`
- `initialize_database()` — create tables if not exist
- `close_connection()` — cleanup

#### 2.3 src/database/queries.py
- Insert/fetch questions
- Record sessions and session_questions
- Compute performance stats (by topic, by difficulty, weak areas)
- Session history

### Phase 3: Questions

#### 3.1 src/questions/models.py
Pydantic models:
- `Question` (base)
- `MCQQuestion` (4 options, correct answer, explanations)
- `OpenEndedQuestion` (sample answer, evaluation criteria, resources)
- `EvaluationResult` (is_correct, score, feedback, strengths, improvements)

#### 3.2 src/questions/bank.py
- Load questions from DuckDB
- Filter by topic, subtopic, difficulty
- Track asked questions to avoid repeats
- Random selection

#### 3.3 src/questions/generator.py
- Interface to call opencode agent for question generation
- The agent searches dbt docs, generates questions with provenance
- Stores generated questions in DuckDB

### Phase 4: Evaluation

#### 4.1 src/evaluation/mcq.py
- Exact match A/B/C/D
- Return correct/incorrect + explanation + why-wrong breakdown from question record

#### 4.2 src/evaluation/open_ended.py
- Calls opencode agent with question + user answer + rubric
- Returns 0-3 score + structured feedback (strengths, improvements, resources)

### Phase 5: Session Management

#### 5.1 src/session/manager.py
- `SessionConfig` — topics, difficulty, question count, web search settings
- `Session` — state: current question index, score, streak, start time
- `start_session()` — create session record in DuckDB
- `record_answer()` — save answer + evaluation to DuckDB
- `end_session()` — compute summary, update stats
- `get_session_summary()` — aggregate results by topic/difficulty

### Phase 6: Textual TUI

#### 6.1 src/styles/app.tcss
Textual CSS for:
- Color scheme (blue questions, green correct, red incorrect, yellow warnings)
- Bordered panels for questions and feedback
- Progress bar styling
- DataTable styling

#### 6.2 src/screens/welcome.py
- Header: "unrot — dbt brain training"
- Topic selection (SelectionList for subtopics)
- Difficulty selector (Select widget)
- Question count (Input widget)
- Web search toggle (Switch widget)
- "Start Session" button
- Footer with keybindings

#### 6.3 src/screens/quiz.py
- ProgressBar at top showing question N/total
- Question card widget (bordered Static/Markdown)
- For MCQ: RadioSet with 4 options
- For open-ended: TextArea for free-form answer
- `?` key shows hint (Collapsible)
- Submit on Enter or button
- After submit: feedback panel replaces question
  - Green border if correct, red if incorrect
  - Explanation, why-wrong breakdown, source link
- "Next" button or Enter to continue

#### 6.4 src/screens/summary.py
- DataTable: overall stats (total, correct, accuracy, streak, time)
- DataTable: per-subtopic performance
- Weak areas highlighted
- Buttons: "New Session", "View Stats", "Quit"

#### 6.5 src/screens/stats.py
- Historical performance DataTable
- Per-topic accuracy breakdown
- Session history

#### 6.6 src/widgets/
- `question_card.py` — bordered question display with topic/difficulty/type header
- `feedback_panel.py` — feedback with color-coded border, explanation, why-wrong
- `stats_table.py` — DataTable wrapper for stats display

#### 6.7 src/app.py
- Main `UnrotApp(App)` class
- Screen stack management: welcome → quiz → summary
- CSS_PATH = "styles/app.tcss"
- Keybindings: `q` quit, `s` stats

### Phase 7: CLI Entry Points

#### 7.1 src/cli.py (Typer)
```python
app = typer.Typer()

@app.command()
def start():
    """Start the TUI quiz app."""
    from src.app import UnrotApp
    UnrotApp().run()

@app.command()
def generate_questions(topic: str, difficulty: str, count: int = 5):
    """Generate questions via the opencode agent."""
    ...

@app.command()
def stats():
    """Show stats (non-TUI, prints to terminal)."""
    ...

@app.command()
def export(format: str = "csv"):
    """Export progress data."""
    ...

@app.command()
def config():
    """Configure default settings."""
    ...
```

#### 7.2 src/__main__.py
```python
from src.cli import app
app()
```

### Phase 8: opencode Integration

#### 8.1 .opencode/agent/dbt-quiz-master.md
Agent instructions adapted from the original markdown but scoped to dbt only:
- Question generation: search dbt docs, generate MCQ + open-ended with provenance
- Open-ended evaluation: 0-3 rubric, structured feedback
- Store questions in DuckDB with source URLs

#### 8.2 .opencode/command/quiz.md
`/quiz` command to launch the TUI

#### 8.3 opencode.json
```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["AGENTS.md"]
}
```
No `model` field — inherits user's global setting.

#### 8.4 AGENTS.md
Repo-level instructions for any opencode agent:
- Project structure
- How to run tests (`uv run pytest`)
- How to lint (`uv run ruff check`)
- DuckDB schema overview
- How question generation works

### Phase 9: Testing

#### 9.1 tests/test_database.py
- Schema creation
- Insert/fetch questions
- Session recording
- Stats computation

#### 9.2 tests/test_models.py
- Pydantic model validation
- Serialization/deserialization

#### 9.3 tests/test_session.py
- Session lifecycle
- Score tracking
- Streak calculation

### Phase 10: Verification
- `uv run ruff check`
- `uv run mypy src/`
- `uv run pytest`
- Manual TUI test: `uv run unrot start`

## Key Design Decisions

1. **Textual** for TUI (interactive quiz), **Typer** for non-interactive CLI (generate-questions, export, config)
2. **YAML** for topic taxonomy (`data/topics.yaml`), questions stored in **DuckDB**
3. **LLM via opencode agent** for question generation and open-ended evaluation — no default model specified
4. **DuckDB** at `~/.unrot/unrot.duckdb` for all progress tracking
5. **Agent-led question generation** with full provenance tracking (source URLs, search queries, model used)
6. **dbt-only** for initial scope; architecture supports adding more topics via `topics.yaml`
7. **Web search** included — agent searches dbt docs before generating questions
