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
Schema aligned with Person 4's `confidence_gate_rules.py`:
```json
{
  "legal_analysis": {
    "case_strength": "STRONG|MODERATE|WEAK|INSUFFICIENT_BASIS",
    "confidence": 0.95,
    "violations": [
      {
        "violation_description": "string — what was violated",
        "source": "string — exact source name from retrieved context",
        "section": "string — exact section number",
        "retrieved_text": "string — exact text from retrieved context"
      }
    ],
    "clarifying_question": "string or null — question to ask worker if confidence < 0.6",
    "reasoning": "string — brief explanation of assessment"
  }
}
```

**Error Handling Behavior:**
If the LLM fails to return valid JSON or encounters an API error, the node catches the exception and returns a safe fallback with `case_strength = "INSUFFICIENT_BASIS"` and `violations = []`.

**Anti-Hallucination Enforcement:**
Person 4's grounding prompt is slotted in verbatim. The model is instructed to ONLY cite laws from the retrieved ChromaDB context. If no relevant law is found, it returns `INSUFFICIENT_BASIS`.

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
    "hindi_letter": "string (Formal Hindi — complete translation, not summary)",
    "english_letter": "string (Formal English — standard Indian legal notice format)",
    "demands": ["string", "string"],
    "escalation_warning": "string",
    "disclaimer": "This document was prepared with AI assistance. Cited provisions are based on publicly available policy documents. For complex cases, consult a legal professional."
  }
}
```

**Error Handling Behavior:**
- Forcefully overrides any AI-generated disclaimer with the hardcoded `MANDATORY_DISCLAIMER` constant.
- On JSON parse failure, returns an error string in the letter fields but maintains the strict dictionary structure so LangGraph does not crash.

---

## 3. Integration Flow

```
Agent 1 (Parser) → parsed_data
        ↓
Agent 2 (Researcher) → legal_analysis
        ↓
Person 4's confidence_gate → proceed/clarify/insufficient
        ↓
Agent 3 (Drafter) → grievance_letter
        ↓
Person 4's Navigator → filing_result
```

**Important:** Person 1 should import `evaluate_confidence_gate()` from Person 4's `knowledge_base/confidence_gate_rules.py` and run it between Agent 2 and Agent 3. Agent 3 should only run if the gate returns `{"proceed": True}`.
