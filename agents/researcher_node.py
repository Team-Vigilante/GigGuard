# Agent 2 — Legal Researcher System Prompt + Standalone Logic
# Owner: Person 2 (AI Agents + Prompt Engineering)
# This is the standalone reference module in the top-level agents/ directory.
# The integrated version lives at app/agents/researcher_node.py.
#
# This module can be imported by:
#   - pdf_generator/ for schema reference
#   - tests/ for prompt testing
#   - Any standalone demo scripts

import json
from typing import Dict, Any, List, Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESEARCHER SYSTEM PROMPT — Full Anti-Hallucination RAG Prompt
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESEARCHER_SYSTEM_PROMPT = """
You are the Legal Researcher Agent for GigGuard, a legal advocacy
system for gig workers in India.

Your job is to analyze a gig worker's case facts against ONLY the
retrieved legal context provided below, and determine whether any
laws or platform terms were violated.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES — NEVER VIOLATE THESE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULE 1 — NO HALLUCINATION:
You MUST NOT cite, reference, or mention ANY law, section, rule,
act, or regulation that is NOT present in the RETRIEVED LEGAL
CONTEXT below. If a law is not in the context, it does not exist
for the purpose of this analysis. This is the single most important
rule. Violating it makes the entire analysis legally dangerous.

RULE 2 — GROUNDING:
Every violation you identify MUST include a direct quote
("retrieved_text") from the retrieved context that supports it.
If you cannot quote the exact text that supports a violation,
do not include that violation.

RULE 3 — HONEST ASSESSMENT:
If the retrieved context does not contain any laws that clearly
apply to the worker's situation, you MUST set case_strength to
"INSUFFICIENT_BASIS". Do not stretch or misapply laws to make
a case appear stronger than it is.

RULE 4 — CASE STRENGTH CLASSIFICATION:
  STRONG — 2 or more clear violations with direct textual support
           from the retrieved context
  MODERATE — 1 clear violation with direct support, or 2+ violations
             with partial support
  WEAK — Only indirect or tangential legal support found
  INSUFFICIENT_BASIS — No applicable legal provisions found in the
                       retrieved context, or the case facts are
                       too vague to match any legal provision

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSIS PROCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Read the case facts carefully.
Step 2: Read each retrieved legal chunk.
Step 3: For each chunk, determine if the platform's action
        violated the specific provision quoted.
Step 4: Only include violations where you can directly quote
        the supporting text from the context.
Step 5: Classify case_strength based on the rules above.
Step 6: Write a plain-language worker_message explaining what
        you found in simple, empathetic Hindi-English (Hinglish)
        that a worker would understand.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIDENCE SCORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Assign a confidence score from 0.0 to 1.0:
  1.0 — Every violation is directly supported by quoted text,
        case facts are clear and complete
  0.7 — Most violations are well-supported, minor ambiguity
        in case facts
  0.4 — Some violations are only partially supported, or
        case facts are vague
  0.1 — Very weak support, mostly inference
  0.0 — No legal basis found (INSUFFICIENT_BASIS)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EMPTY CONTEXT HANDLING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the RETRIEVED LEGAL CONTEXT is empty, contains no documents,
or says "No legal context retrieved":
  - Set violations to an empty list []
  - Set case_strength to "INSUFFICIENT_BASIS"
  - Set confidence to 0.0
  - Write a helpful worker_message explaining that no relevant
    legal provisions were found but the case has been documented

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT — STRICT JSON ONLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ONLY a valid JSON object. No explanations. No prose.
No markdown. No code blocks. Nothing outside the JSON.

{
  "violations": [
    {
      "law": "Full name of the law or agreement",
      "section": "Specific section or rule number",
      "retrieved_text": "EXACT quote from the retrieved context",
      "violation_description": "How the platform violated this provision based on the case facts"
    }
  ],
  "case_strength": "STRONG" | "MODERATE" | "WEAK" | "INSUFFICIENT_BASIS",
  "confidence": float between 0.0 and 1.0,
  "worker_message": "A plain language explanation for the worker in simple Hinglish"
}
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OUTPUT SCHEMA — For LangGraph integration reference
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LEGAL_ANALYSIS_SCHEMA = {
    "violations": [
        {
            "law": "str — Full name of the law or agreement",
            "section": "str — Specific section or rule number",
            "retrieved_text": "str — EXACT quote from retrieved context",
            "violation_description": "str — How platform violated this"
        }
    ],
    "case_strength": "STRONG | MODERATE | WEAK | INSUFFICIENT_BASIS",
    "confidence": "float — 0.0 to 1.0",
    "worker_message": "str — Plain language explanation for worker"
}


def build_researcher_messages(
    parsed_data: dict,
    retrieved_chunks: list,
    chunk_count: int
) -> list:
    """
    Build the system + user messages for the researcher LLM call.

    Args:
        parsed_data:      The parsed_data dict from Agent 1 (Parser)
        retrieved_chunks: List of dicts from ChromaDB query
        chunk_count:      Number of chunks retrieved

    Returns:
        List of message dicts for the LLM API call:
        [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
    """
    context_str = json.dumps(retrieved_chunks, indent=2)

    user_prompt = f"""Analyze the following gig worker's case based ONLY on the
retrieved legal context. Follow every rule in your system prompt.

CASE FACTS:
{json.dumps(parsed_data, indent=2)}

RETRIEVED LEGAL CONTEXT ({chunk_count} chunks):
{context_str}

Return your analysis as a strict JSON object."""

    return [
        {"role": "system", "content": RESEARCHER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]


def validate_legal_analysis(analysis: dict) -> dict:
    """
    Validate and sanitize the legal analysis output from the LLM.
    Ensures all required fields exist and have valid values.

    Args:
        analysis: Raw parsed JSON from LLM response

    Returns:
        Validated and sanitized legal analysis dict
    """
    valid_strengths = {"STRONG", "MODERATE", "WEAK", "INSUFFICIENT_BASIS"}

    # Ensure violations is a list
    if not isinstance(analysis.get("violations"), list):
        analysis["violations"] = []

    # Validate each violation has required fields
    valid_violations = []
    for v in analysis["violations"]:
        if isinstance(v, dict) and all(
            k in v for k in ("law", "section", "violation_description")
        ):
            if "retrieved_text" not in v:
                v["retrieved_text"] = ""
            valid_violations.append(v)
    analysis["violations"] = valid_violations

    # Validate case_strength
    if analysis.get("case_strength") not in valid_strengths:
        analysis["case_strength"] = "WEAK"

    # Validate confidence
    try:
        analysis["confidence"] = float(analysis.get("confidence", 0.0))
        analysis["confidence"] = max(0.0, min(1.0, analysis["confidence"]))
    except (TypeError, ValueError):
        analysis["confidence"] = 0.0

    # Ensure worker_message exists
    if not analysis.get("worker_message"):
        analysis["worker_message"] = (
            "Aapke case ka analysis ho gaya hai. "
            "Kripya aage ke steps ke liye intezar karein."
        )

    return analysis


def make_insufficient_basis_response(reason: str = "") -> dict:
    """
    Return a standard INSUFFICIENT_BASIS response.

    Args:
        reason: Optional reason string for the worker message

    Returns:
        Legal analysis dict with INSUFFICIENT_BASIS
    """
    message = (
        "Aapke case mein applicable legal provisions nahi mil sake. "
        "Aapka case document ho gaya hai."
    )
    if reason:
        message = reason

    return {
        "violations": [],
        "case_strength": "INSUFFICIENT_BASIS",
        "confidence": 0.0,
        "worker_message": message
    }
