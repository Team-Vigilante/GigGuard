import json
import os
from typing import Dict, Any
from anthropic import Anthropic
from agents.chromadb_query import build_case_facts_string, query_knowledge_base


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PERSON 4'S GROUNDING PROMPT — SLOTTED IN VERBATIM
# SOURCE: origin/feature/knowledge-base:knowledge_base/grounding_prompt.txt
# DO NOT MODIFY, WEAKEN, OR REMOVE ANY OF THESE RULES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GROUNDING_PROMPT = """You are a legal research assistant for GigGuard, an AI advocate for gig workers in India.

STRICT GROUNDING RULES — READ CAREFULLY BEFORE RESPONDING:

1. You ONLY cite legal provisions that appear in the RETRIEVED CONTEXT provided below.
   Never cite a law, section number, or case from your training data memory under any circumstances.

2. Every citation must include ALL THREE of the following:
   - Source name (e.g. "Code on Social Security 2020")
   - Section number (e.g. "Section 6")
   - The exact retrieved text you are citing

3. If the retrieved context does not contain relevant law for this case, output exactly:
   INSUFFICIENT_LEGAL_BASIS
   Do not attempt to fill the gap with general knowledge.

4. If you are uncertain whether a chunk is relevant to the specific facts of this case,
   do not cite it. Mark it UNCERTAIN instead.

5. Case strength is determined ONLY by verified violations found in retrieved context:
   STRONG:             3 or more violations with direct citations from retrieved context
   MODERATE:           1 or 2 violations with direct citations from retrieved context
   WEAK:               violations present but ambiguous or circumstantial
   INSUFFICIENT_BASIS: no relevant law found in retrieved context for this specific case

6. You must output your response in this exact JSON structure:
   {
     "case_strength": "STRONG | MODERATE | WEAK | INSUFFICIENT_BASIS",
     "confidence": 0.0 to 1.0,
     "violations": [
       {
         "violation_description": "what was violated",
         "source": "exact source name",
         "section": "exact section number",
         "retrieved_text": "exact text from retrieved context"
       }
     ],
     "clarifying_question": "one question to ask worker if confidence < 0.6, else null",
     "reasoning": "brief explanation of your assessment"
   }

7. NEVER fabricate a law, act, section number, or case outcome.
   If a worker mentions a law that does not appear in your retrieved context,
   do not confirm or elaborate on it. Output INSUFFICIENT_LEGAL_BASIS."""


def researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 2: Legal Researcher Node

    Uses RAG (Retrieval-Augmented Generation) to find relevant legal
    provisions from ChromaDB and analyzes the worker's case facts
    strictly against those provisions.

    Person 4's grounding prompt enforces anti-hallucination rules.
    The model may ONLY cite laws present in the retrieved context.

    Args:
        state: The current LangGraph state (GigGuardState).
               Must contain 'parsed_data' (dict) with extracted
               complaint facts from Agent 1 (Parser).

    Returns:
        A dict with 'legal_analysis' key to update the state.
        Output schema matches Person 4's confidence_gate_rules.py:
        {
            "case_strength": "STRONG|MODERATE|WEAK|INSUFFICIENT_BASIS",
            "confidence": float (0.0 to 1.0),
            "violations": [
                {
                    "violation_description": str,
                    "source": str,
                    "section": str,
                    "retrieved_text": str
                }
            ],
            "clarifying_question": str or null,
            "reasoning": str
        }
    """
    parsed_data = state.get("parsed_data", {})

    # 1. Build query string from parsed case facts
    case_facts_str = build_case_facts_string(parsed_data)

    # 2. Call ChromaDB query function
    retrieved_chunks = query_knowledge_base(case_facts_str, n_results=5)

    # 3. Format retrieved chunks for the grounding prompt
    #    Each chunk includes: text, source, section, relevance_score
    chunks_for_prompt = ""
    for i, chunk in enumerate(retrieved_chunks, 1):
        chunks_for_prompt += (
            f"--- Chunk {i} ---\n"
            f"Source: {chunk.get('source', 'unknown')}\n"
            f"Section: {chunk.get('section', 'unknown')}\n"
            f"Text: {chunk.get('text', '')}\n\n"
        )

    if not chunks_for_prompt:
        chunks_for_prompt = "[NO RELEVANT LEGAL CONTEXT RETRIEVED]"

    # 4. Build the full system prompt with Person 4's grounding rules
    #    The grounding prompt expects {retrieved_chunks} and {case_facts}
    #    to be filled in — we inject them here
    full_prompt = GROUNDING_PROMPT.replace(
        "{retrieved_chunks}", chunks_for_prompt
    ).replace(
        "{case_facts}", case_facts_str
    )

    # 5. Call Claude with the grounded prompt
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=1500,
        temperature=0.0,
        system=full_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyze the case facts against the retrieved legal "
                    "context. Follow the grounding rules exactly. Return "
                    "only the JSON output."
                )
            }
        ]
    )

    try:
        response_text = response.content[0].text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        json_str = response_text[start_idx:end_idx]

        legal_analysis = json.loads(json_str)

    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        legal_analysis = {
            "violations": [],
            "case_strength": "INSUFFICIENT_BASIS",
            "confidence": 0.0,
            "clarifying_question": None,
            "reasoning": f"Error during legal analysis: {str(e)}"
        }

    return {"legal_analysis": legal_analysis}
