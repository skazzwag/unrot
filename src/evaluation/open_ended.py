"""Open-ended question evaluation — delegates to the opencode agent.

The actual evaluation is performed by the dbt-quiz-master opencode agent
using the 0-3 scoring rubric. This module builds the evaluation prompt
that the agent uses to assess the user's answer.
"""

from __future__ import annotations

from src.questions.models import EvaluationResult, OpenEndedQuestion


def build_evaluation_prompt(question: OpenEndedQuestion, user_answer: str) -> str:
    """Build the prompt for the opencode agent to evaluate an open-ended answer.

    The agent reads this prompt and returns a structured evaluation.
    """
    criteria_str = (
        "\n".join(f"  - {c}" for c in question.evaluation_criteria)
        or "  - (none specified)"
    )
    resources_str = (
        "\n".join(f"  - {r}" for r in question.resources)
        or "  - (none provided)"
    )

    return f"""Evaluate the following answer to a dbt quiz question.

Question: {question.question_text}

Expected answer (sample):
{question.sample_answer}

User's answer:
{user_answer}

Evaluation criteria:
{criteria_str}

Resources for reference:
{resources_str}

Score using this rubric:
- 3 points: Complete, accurate, deep understanding, best practices,
  all relevant details
- 2 points: Mostly correct but missing some details, minor inaccuracies,
  or could be more comprehensive
- 1 point: Partially correct, significant gaps, misunderstandings,
  or major omissions
- 0 points: Completely incorrect, irrelevant, or no answer provided

Provide the evaluation as YAML:

```yaml
score: <0-3>
is_correct: <true if score >= 2, false otherwise>
feedback: |
  <detailed analysis>
strengths:
  - <what was correct>
  - <another strength>
improvements:
  - <what was missing>
  - <what was incorrect>
resources:
  - <relevant url>
```
"""


def parse_evaluation_response(response: str) -> EvaluationResult:
    """Parse the agent's YAML evaluation response into an EvaluationResult.

    This is a simple parser — the agent output is expected to be YAML.
    """
    import yaml

    yaml_block = response
    if "```yaml" in response:
        yaml_block = response.split("```yaml")[1].split("```")[0]
    elif "```" in response:
        yaml_block = response.split("```")[1].split("```")[0]

    data = yaml.safe_load(yaml_block)

    return EvaluationResult(
        is_correct=bool(data.get("is_correct", data.get("score", 0) >= 2)),
        score=int(data.get("score", 0)),
        feedback=data.get("feedback", ""),
        strengths=data.get("strengths", []),
        improvements=data.get("improvements", []),
        resources=data.get("resources", []),
    )
