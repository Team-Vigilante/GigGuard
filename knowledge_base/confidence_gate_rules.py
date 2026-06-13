"""
GigGuard Confidence Gate Rules
================================
Person 1: import this file and call evaluate_confidence_gate(researcher_output)
before passing to Agent 3 (Drafter).
"""

from typing import TypedDict

class ResearcherOutput(TypedDict):
    case_strength: str
    confidence: float
    violations: list
    clarifying_question: str
    reasoning: str


INSUFFICIENT_BASIS_MESSAGE = (
    "I could not find a specific law that was clearly violated in your case. "
    "I can still help you document what happened and send a formal complaint, "
    "but I want to be honest that the legal basis may be limited. "
    "Do you want to proceed?"
)


def evaluate_confidence_gate(researcher_output: dict) -> dict:
    case_strength = researcher_output.get("case_strength", "")
    confidence = researcher_output.get("confidence", 0.0)
    violations = researcher_output.get("violations", [])

    if case_strength == "INSUFFICIENT_BASIS":
        return {"proceed": False, "action": "insufficient", "message_to_worker": INSUFFICIENT_BASIS_MESSAGE, "error": None}

    if len(violations) == 0 and case_strength != "INSUFFICIENT_BASIS":
        return {"proceed": False, "action": "error", "message_to_worker": "Something went wrong analyzing your case. Please try again.", "error": f"CONTRADICTION: case_strength={case_strength} but violations list is empty."}

    if confidence < 0.6:
        clarifying_question = researcher_output.get("clarifying_question") or "Can you provide additional details about what happened, such as whether you received any prior warnings?"
        return {"proceed": False, "action": "clarify", "message_to_worker": clarifying_question, "error": None}

    return {"proceed": True, "action": "draft", "message_to_worker": None, "error": None}
