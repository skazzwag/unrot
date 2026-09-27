"""Question generation interface — delegates to the opencode agent.

The actual question generation is performed by the dbt-quiz-master opencode agent.
This module provides the interface for the CLI to invoke the agent and store
generated questions in DuckDB.
"""

from __future__ import annotations

from src.questions.models import Difficulty, QuestionType


def generate_questions_prompt(
    topic: str = "dbt",
    subtopics: list[str] | None = None,
    difficulty: Difficulty = Difficulty.INTERMEDIATE,
    count: int = 5,
    question_types: list[QuestionType] | None = None,
    use_web_search: bool = True,
) -> str:
    """Build the prompt for the opencode agent to generate questions.

    This prompt is printed to stdout when the user runs
    `unrot generate-questions` — the opencode agent reads it and acts on it.
    """
    types = question_types or [QuestionType.MULTIPLE_CHOICE, QuestionType.OPEN_ENDED]
    type_names = [t.value for t in types]

    subtopic_str = ""
    if subtopics:
        subtopic_str = f"\nSubtopics to focus on: {', '.join(subtopics)}"

    search_instructions = ""
    if use_web_search:
        search_instructions = """
Before generating questions, perform web searches on the dbt documentation:
- Search for recent dbt features, best practices, and documentation
- Prioritize official docs at https://docs.getdbt.com
- Look for content from the last 6 months
- Record the URLs you used as provenance
"""

    return f"""Generate {count} quiz questions about {topic} for a lead data engineer.

Difficulty: {difficulty.value}
Question types: {', '.join(type_names)}{subtopic_str}

Requirements:
- 70% multiple choice (exactly 4 options A-D, exactly 1 correct answer)
- 30% open-ended (requiring detailed written answers)
- All options must be plausible — include common misconceptions as wrong options
- Test practical understanding, not memorization
- Include code snippets where appropriate
- For MCQ: provide explanation + why each wrong option is wrong
- For open-ended: provide a sample answer + evaluation criteria + resource URLs{search_instructions}

For each question, output as YAML:

```yaml
- topic: {topic}
  subtopic: <subtopic_id>
  difficulty: {difficulty.value}
  type: multiple_choice  # or open_ended
  question_text: |
    <question text>
  # MCQ fields:
  option_a: <text>
  option_b: <text>
  option_c: <text>
  option_d: <text>
  correct_answer: A  # or B, C, D
  explanation: |
    <detailed explanation>
  why_wrong_a: <why A is wrong>
  why_wrong_b: <why B is wrong>
  why_wrong_c: <why C is wrong>
  why_wrong_d: <why D is wrong>
  # Open-ended fields:
  sample_answer: |
    <sample answer>
  evaluation_criteria:
    - <criterion 1>
    - <criterion 2>
  resources:
    - <url 1>
    - <url 2>
  source: web_search  # or static
  source_url: <primary source url>
```

After generating, store each question in the DuckDB database by running
the Python code in src/database/queries.py insert_question() and
insert_provenance() functions. Record all source URLs used.
"""
