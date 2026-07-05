# Agent 2 — Legal Researcher Node
# Owner: Person 2 (AI Agents + Prompt Engineering)
# Integrated into: app/agents/graph.py → "researcher" node
# LLM: Groq — LLaMA 3.3 70B Versatile

import json
from typing import Dict, Any
from groq import Groq
from app.agents.chromadb_query import build_case_facts_string, query_knowledge_base
from app.config import GROQ_API_KEY


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


def researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 2 — Legal Researcher Node

    Reads parsed_data from state, queries ChromaDB for relevant
    legal context, then uses Groq (LLaMA 3.3 70B) to analyze
    violations using RAG.

    Input:  state["parsed_data"] — dict from Agent 1
    Output: {"legal_analysis": {...}} — merged into GigGuardState
    """

    parsed_data = state.get("parsed_data", {})

    if not parsed_data:
        print("[researcher_node] No parsed_data — returning INSUFFICIENT_BASIS")
        return {"legal_analysis": {
            "violations": [],
            "case_strength": "INSUFFICIENT_BASIS",
            "confidence": 0.0,
            "worker_message": (
                "Aapke case ki details abhi tak extract nahi hui hain. "
                "Kripya apni samasya dobara batayein."
            )
        }}

    # ── Step 1: Build case facts string for semantic search ────────
    try:
        case_facts_str = build_case_facts_string(parsed_data)
        print(f"[researcher_node] case_facts: {case_facts_str}")
    except Exception as e:
        print(f"[researcher_node] build_case_facts error: {e}")
        case_facts_str = ""

    # ── Step 2: Query ChromaDB for relevant legal chunks ──────────
    try:
        retrieved_chunks = query_knowledge_base(case_facts_str, n_results=5)
        context_str = json.dumps(retrieved_chunks, indent=2)
        chunk_count = len(retrieved_chunks)
        print(f"[researcher_node] retrieved {chunk_count} chunks from ChromaDB")
    except Exception as e:
        print(f"[researcher_node] ChromaDB error: {e}")
        retrieved_chunks = []
        context_str = "No legal context retrieved."
        chunk_count = 0

    # ── Step 3: Build user prompt with case facts + context ───────
    user_prompt = f"""Analyze the following gig worker's case based ONLY on the
retrieved legal context. Follow every rule in your system prompt.

CASE FACTS:
{json.dumps(parsed_data, indent=2)}

RETRIEVED LEGAL CONTEXT ({chunk_count} chunks):
{context_str}

Return your analysis as a strict JSON object."""

    # ── Step 4: Call Groq LLM with system/user separation ─────────
    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": RESEARCHER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=2048
        )

        response_text = response.choices[0].message.content
        print(f"[researcher_node] raw response length: {len(response_text)}")

        # Extract JSON from response (handle potential prose)
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1

        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON object found in response")

        json_str = response_text[start_idx:end_idx]
        legal_analysis = json.loads(json_str)

        # ── Guardrail: Force INSUFFICIENT_BASIS if no chunks ──────
        if chunk_count == 0:
            legal_analysis["violations"] = []
            legal_analysis["case_strength"] = "INSUFFICIENT_BASIS"
            legal_analysis["confidence"] = 0.0
            print("[researcher_node] Forced INSUFFICIENT_BASIS — no context")

        # ── Guardrail: Validate case_strength value ───────────────
        valid_strengths = {"STRONG", "MODERATE", "WEAK", "INSUFFICIENT_BASIS"}
        if legal_analysis.get("case_strength") not in valid_strengths:
            legal_analysis["case_strength"] = "WEAK"
            print("[researcher_node] Invalid case_strength — defaulted to WEAK")

        # ── Guardrail: Ensure violations is a list ────────────────
        if not isinstance(legal_analysis.get("violations"), list):
            legal_analysis["violations"] = []

        print(
            f"[researcher_node] case_strength={legal_analysis['case_strength']} | "
            f"violations={len(legal_analysis['violations'])} | "
            f"confidence={legal_analysis.get('confidence', 0)}"
        )

    except json.JSONDecodeError as e:
        print(f"[researcher_node] JSON parse error: {e}")
        legal_analysis = {
            "violations": [],
            "case_strength": "INSUFFICIENT_BASIS",
            "confidence": 0.0,
            "worker_message": (
                "Legal analysis mein ek technical error aayi. "
                "Aapka case document ho gaya hai aur hum "
                "dobara try karenge."
            )
        }
    except Exception as e:
        print(f"[researcher_node] error: {e}")
        legal_analysis = {
            "violations": [],
            "case_strength": "INSUFFICIENT_BASIS",
            "confidence": 0.0,
            "worker_message": f"Error during legal analysis: {str(e)}"
        }

    return {"legal_analysis": legal_analysis}