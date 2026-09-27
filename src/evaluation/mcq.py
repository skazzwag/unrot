"""Multiple choice question evaluation."""

from __future__ import annotations

from src.questions.models import EvaluationResult, MCQQuestion


def evaluate_mcq(question: MCQQuestion, user_answer: str) -> EvaluationResult:
    """Evaluate a multiple choice answer.

    Args:
        question: The MCQ question.
        user_answer: The user's answer (A, B, C, or D).

    Returns:
        EvaluationResult with correctness, feedback, and explanations.
    """
    answer = user_answer.strip().upper()

    if answer not in ("A", "B", "C", "D"):
        return EvaluationResult(
            is_correct=False,
            score=0,
            feedback=f"Invalid answer '{user_answer}'. Please answer with A, B, C, or D.",
            correct_answer=question.correct_answer,
        )

    is_correct = answer == question.correct_answer

    wrong_explanations = question.get_wrong_explanations()

    if is_correct:
        feedback_parts = [f"Correct!\n\nExplanation: {question.explanation}\n"]
        feedback_parts.append("Why the other options are incorrect:")
        for letter in ("A", "B", "C", "D"):
            if letter == question.correct_answer:
                continue
            why = wrong_explanations.get(letter)
            if why:
                feedback_parts.append(f"  {letter}) {why}")
        feedback = "\n".join(feedback_parts)
    else:
        feedback_parts = [
            f"Incorrect. The correct answer is {question.correct_answer}.\n",
            f"Explanation: {question.explanation}\n",
            f"Why {answer} is a common misconception: "
            f"{wrong_explanations.get(answer, 'Not specified.')}\n",
            "Why the other options are incorrect:",
        ]
        for letter in ("A", "B", "C", "D"):
            if letter == answer or letter == question.correct_answer:
                continue
            why = wrong_explanations.get(letter)
            if why:
                feedback_parts.append(f"  {letter}) {why}")
        feedback = "\n".join(feedback_parts)

    return EvaluationResult(
        is_correct=is_correct,
        score=3 if is_correct else 0,
        feedback=feedback,
        correct_answer=question.correct_answer,
    )
