import json
import os
from typing import Dict, Any
from groq import Groq
from app.agents.chromadb_query import build_case_facts_string, query_knowledge_base
from app.config import GROQ_API_KEY

RESEARCHER_SYSTEM_PROMPT = """
You are the Legal Researcher Agent for GigGuard, a legal advocacy system
for gig workers in India.

Your job is to analyze the worker's case facts strictly against the retrieved
legal context and determine if there are any legal violations.

OUTPUT FORMAT — STRICT JSON ONLY
Return ONLY a valid JSON object. No prose. No markdown.
No code blocks. Nothing outside the JSON.

{
  "violations": [
    {
      "law": "Name of the law",
      "section": "Specific section number",
      "retrieved_text": "Exact quote from context used as basis",
      "violation_description": "Clear explanation of how the platform violated this"
    }
  ],
  "case_strength": "STRONG|MODERATE|WEAK|INSUFFICIENT_BASIS",
  "confidence": 0.0,
  "worker_message": "A plain language explanation for the worker."
}
"""

def researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    parsed_data = state.get("parsed_data", {})

    try:
        case_facts_str = build_case_facts_string(parsed_data)
        retrieved_chunks = query_knowledge_base(case_facts_str, n_results=5)
        context_str = json.dumps(retrieved_chunks, indent=2)
    except Exception as e:
        print(f"[researcher_node] ChromaDB error: {e}")
        context_str = "No legal context retrieved."

    client = Groq(api_key=GROQ_API_KEY)

    user_prompt = f"""
Analyze the following case based ONLY on the provided legal context.

CASE FACTS:
{json.dumps(parsed_data, indent=2)}

RETRIEVED LEGAL CONTEXT:
{context_str}

{RESEARCHER_SYSTEM_PROMPT}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.0
        )
        response_text = response.choices[0].message.content
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        json_str = response_text[start_idx:end_idx]
        legal_analysis = json.loads(json_str)
    except Exception as e:
        print(f"[researcher_node] error: {e}")
        legal_analysis = {
            "violations": [],
            "case_strength": "INSUFFICIENT_BASIS",
            "confidence": 0.0,
            "worker_message": f"Error during legal analysis: {str(e)}"
        }

    return {"legal_analysis": legal_analysis}