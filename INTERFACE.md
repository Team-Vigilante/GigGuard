# AI Agents Integration Handoff Document

**Owner:** Person 2 (AI Agents + Prompt Engineering)  
**Target Audience:** Person 1 (LangGraph Integration) & Person 4 (Navigator)

This document outlines the interfaces for the AI nodes developed in the `feature/ai-agents` branch.

---

## 1. Agent 2: Legal Researcher (`researcher_node.py`)

**Function Signature:**
```python
def researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
```

**Input Requirements:**
The LangGraph `GigGuardState` must contain a populated `parsed_data` dictionary.
Expected keys in `parsed_data`: `platform`, `event_type`, `notice_provided`, `appeal_offered`, `earnings_withheld`, `reason`.

**Output Format (State Update):**
Returns a dictionary to update `legal_analysis` in the state.
```json
{
  "legal_analysis": {
    "violations": [
      {
        "law": "string",
        "section": "string",
        "retrieved_text": "string",
        "violation_description": "string"
      }
    ],
    "case_strength": "STRONG|MODERATE|WEAK|INSUFFICIENT_BASIS",
    "confidence": 0.95,
    "worker_message": "string"
  }
}
```

**Error Handling Behavior:**
If the LLM fails to return valid JSON or encounters an API error, the node catches the exception and returns a safe fallback with `case_strength = "INSUFFICIENT_BASIS"` and `violations = []`.

---

## 2. Agent 3: Drafter (`drafter_node.py`)

**Function Signature:**
```python
def drafter_node(state: Dict[str, Any]) -> Dict[str, Any]:
```

**Input Requirements:**
The LangGraph `GigGuardState` must contain both `parsed_data` AND `legal_analysis`.

**Output Format (State Update):**
Returns a dictionary to update `grievance_letter` in the state.
```json
{
  "grievance_letter": {
    "hindi_letter": "string (Formal Hindi)",
    "english_letter": "string (Formal English)",
    "demands": ["string", "string"],
    "escalation_warning": "string",
    "disclaimer": "This document was prepared with AI assistance. Cited provisions are based on publicly available policy documents. For complex cases, consult a legal professional."
  }
}
```

**Error Handling Behavior:**
- Forcefully overrides any AI-generated disclaimer with the hardcoded `MANDATORY_DISCLAIMER` to prevent hallucination.
- On JSON parse failure, returns an error string in the letter fields but maintains the strict dictionary structure so LangGraph does not crash.
