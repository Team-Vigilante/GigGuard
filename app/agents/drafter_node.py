import json
from typing import Dict, Any
from groq import Groq
from app.config import GROQ_API_KEY

MANDATORY_DISCLAIMER = (
    "This document was prepared with AI assistance. "
    "Cited provisions are based on publicly available "
    "policy documents. For complex cases, consult a "
    "legal professional."
)

DRAFTER_SYSTEM_PROMPT = """
You are a legal document drafting agent for GigGuard for gig workers in India.
Write a formal grievance letter in both Hindi and English.
Cite ONLY laws from legal_analysis.violations — never from memory.
If case_strength is INSUFFICIENT_BASIS, do not cite any laws.

Return ONLY a valid JSON object:
{
  "hindi_letter": "string",
  "english_letter": "string",
  "demands": ["string", "string"],
  "escalation_warning": "string",
  "disclaimer": "string"
}
"""

def drafter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    parsed_data = state.get("parsed_data", {})
    legal_analysis = state.get("legal_analysis", {})
    case_strength = legal_analysis.get("case_strength", "INSUFFICIENT_BASIS")

    client = Groq(api_key=GROQ_API_KEY)

    user_prompt = f"""
{DRAFTER_SYSTEM_PROMPT}

CASE FACTS:
{json.dumps(parsed_data, indent=2)}

LEGAL ANALYSIS:
{json.dumps(legal_analysis, indent=2)}

CASE STRENGTH: {case_strength}
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
        draft_result = json.loads(json_str)
        draft_result["disclaimer"] = MANDATORY_DISCLAIMER
    except Exception as e:
        print(f"[drafter_node] error: {e}")
        draft_result = {
            "hindi_letter": "Error generating letter.",
            "english_letter": f"Error generating letter: {str(e)}",
            "demands": [],
            "escalation_warning": "",
            "disclaimer": MANDATORY_DISCLAIMER
        }

    return {"grievance_letter": draft_result}