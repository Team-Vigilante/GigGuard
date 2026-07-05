# Agent 3 — Drafter Node
# Owner: Person 2 (AI Agents + Prompt Engineering)
# Integrated into: app/agents/graph.py → "drafter" node
# LLM: Groq — LLaMA 3.3 70B Versatile

import json
from typing import Dict, Any
from groq import Groq
from app.config import GROQ_API_KEY


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MANDATORY DISCLAIMER — Hardcoded, never LLM-generated
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MANDATORY_DISCLAIMER = (
    "This document was prepared with AI assistance. "
    "Cited provisions are based on publicly available "
    "policy documents. For complex cases, consult a "
    "legal professional."
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DRAFTER SYSTEM PROMPT — Full Indian Legal Notice Format
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DRAFTER_SYSTEM_PROMPT = """
You are a legal document drafting agent for GigGuard, a legal
advocacy system for gig workers in India.

Your job is to write a formal grievance letter in both Hindi and
English based on the worker's complaint and legal analysis
provided to you.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES — NEVER VIOLATE THESE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULE 1 — CITATIONS:
Every legal section or law you cite in the letter MUST come
from the legal_analysis.violations list provided to you.
You MUST NOT cite any law, section, or regulation from your
own memory or training data.
If a law is not in legal_analysis.violations → do not cite it.
Ever.

RULE 2 — DISCLAIMER:
You MUST include the following disclaimer verbatim at the end
of both letters. Do not change a single word:
"This document was prepared with AI assistance. Cited
provisions are based on publicly available policy documents.
For complex cases, consult a legal professional."

RULE 3 — INSUFFICIENT BASIS:
If case_strength is INSUFFICIENT_BASIS:
  - Do NOT cite any laws or legal sections
  - Do NOT make any legal claims
  - Write an honest factual account of what happened
  - State clearly that the worker is documenting the incident
  - Still follow the standard format for all other sections

RULE 4 — LANGUAGE:
The Hindi letter must be a complete translation of the English
letter. Not a summary. Not a simplified version.
Use formal Hindi (not casual Hinglish).
Legal terms may be kept in English within the Hindi letter
where no standard Hindi equivalent exists.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LETTER FORMAT — FOLLOW EXACTLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Both letters must follow this standard Indian legal notice
format:

1. HEADER
   "GRIEVANCE NOTICE" (English) / "शिकायत सूचना" (Hindi)

2. FROM
   [Worker Name if provided, otherwise "The Complainant"]
   GigGuard Legal Advocacy Platform

3. TO
   The Grievance Officer
   [Platform Name]

4. DATE
   [Use date from parsed_data if available, otherwise
   "Date of Filing"]

5. SUBJECT
   One clear line describing the complaint.
   Example: "Wrongful Account Deactivation Without Notice
   and Withholding of Earned Wages"

6. FACTS (numbered, chronological)
   - State each fact clearly and objectively
   - Use only information from parsed_data
   - Do not add facts not present in parsed_data
   - Each fact on its own numbered line

7. LEGAL BASIS (only if case_strength != INSUFFICIENT_BASIS)
   - For each violation in legal_analysis.violations:
     "As per [law], [section]: [violation_description]"
   - Cite ONLY from legal_analysis.violations
   - If INSUFFICIENT_BASIS: replace this section with
     "This notice documents the incident for official record."

8. RELIEF SOUGHT (numbered demands)
   - Always include:
     a. Immediate reinstatement or payment (as applicable)
     b. Written explanation of action taken
     c. Response within 15 days of receipt of this notice

9. ESCALATION WARNING
   "Failure to respond within 15 days will compel the
   complainant to escalate this matter to the appropriate
   labour authorities and consumer forums."

10. CLOSING
    "Yours faithfully,
    The Complainant
    Via GigGuard Legal Advocacy Platform"

11. DISCLAIMER (verbatim, mandatory)
    "This document was prepared with AI assistance. Cited
    provisions are based on publicly available policy
    documents. For complex cases, consult a legal
    professional."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT YOU WILL RECEIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You will receive a JSON object with:
  - parsed_data: extracted complaint facts
  - legal_analysis: violations, case_strength, confidence
  - case_strength: the overall strength classification

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT — STRICT JSON ONLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ONLY a valid JSON object. No prose. No markdown.
No code blocks. Nothing outside the JSON.

{
  "hindi_letter": string,
  "english_letter": string,
  "demands": list of strings,
  "escalation_warning": string,
  "disclaimer": string
}
"""


def drafter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 3 — Drafter Node

    Reads parsed_data and legal_analysis from state, then uses
    Groq (LLaMA 3.3 70B) to generate a formal grievance letter
    in both Hindi and English.

    Input:
        state["parsed_data"]      — dict from Agent 1
        state["legal_analysis"]   — dict from Agent 2
    Output:
        {"grievance_letter": {...}} — merged into GigGuardState
    """

    parsed_data = state.get("parsed_data", {})
    legal_analysis = state.get("legal_analysis", {})
    case_strength = legal_analysis.get("case_strength", "INSUFFICIENT_BASIS")

    print(
        f"[drafter_node] case_strength={case_strength} | "
        f"violations={len(legal_analysis.get('violations', []))}"
    )

    # ── Build user prompt with case context ───────────────────────
    user_prompt = f"""Draft a formal grievance letter based on the following case.
Follow every rule in your system prompt exactly.

CASE FACTS (from Agent 1 — Parser):
{json.dumps(parsed_data, indent=2)}

LEGAL ANALYSIS (from Agent 2 — Researcher):
{json.dumps(legal_analysis, indent=2)}

CASE STRENGTH: {case_strength}

Generate both Hindi and English letters. Return as strict JSON."""

    # ── Call Groq LLM with system/user separation ─────────────────
    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": DRAFTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=4096
        )

        response_text = response.choices[0].message.content
        print(f"[drafter_node] raw response length: {len(response_text)}")

        # Extract JSON from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1

        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON object found in response")

        json_str = response_text[start_idx:end_idx]
        draft_result = json.loads(json_str)

        # ── Guardrail: ALWAYS override disclaimer with hardcoded ──
        draft_result["disclaimer"] = MANDATORY_DISCLAIMER

        # ── Guardrail: Ensure all required fields exist ───────────
        if "hindi_letter" not in draft_result:
            draft_result["hindi_letter"] = ""
        if "english_letter" not in draft_result:
            draft_result["english_letter"] = ""
        if "demands" not in draft_result:
            draft_result["demands"] = []
        if "escalation_warning" not in draft_result:
            draft_result["escalation_warning"] = (
                "Failure to respond within 15 days will compel the "
                "complainant to escalate this matter to the appropriate "
                "labour authorities and consumer forums."
            )

        print(
            f"[drafter_node] generated letters | "
            f"english_len={len(draft_result['english_letter'])} | "
            f"hindi_len={len(draft_result['hindi_letter'])} | "
            f"demands={len(draft_result['demands'])}"
        )

    except json.JSONDecodeError as e:
        print(f"[drafter_node] JSON parse error: {e}")
        draft_result = {
            "hindi_letter": "शिकायत पत्र बनाने में त्रुटि हुई।",
            "english_letter": f"Error generating grievance letter: {str(e)}",
            "demands": [],
            "escalation_warning": "",
            "disclaimer": MANDATORY_DISCLAIMER
        }

    except Exception as e:
        print(f"[drafter_node] error: {e}")
        draft_result = {
            "hindi_letter": "शिकायत पत्र बनाने में त्रुटि हुई।",
            "english_letter": f"Error generating grievance letter: {str(e)}",
            "demands": [],
            "escalation_warning": "",
            "disclaimer": MANDATORY_DISCLAIMER
        }

    return {"grievance_letter": draft_result}