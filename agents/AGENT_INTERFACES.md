# GigGuard Agent Interfaces (LangGraph Integration)

This document outlines the exact input/output schemas, function signatures, and integration requirements for the LangGraph pipeline in `app/agents/graph.py`.

## 1. GigGuardState Schema
All agents must accept and mutate this shared `TypedDict` state.

```python
class GigGuardState(TypedDict):
    phone: str
    message: str
    media_url: Optional[str]
    conversation_state: str
    parsed_data: Optional[dict]      # Mutated by parser_node
    legal_analysis: Optional[dict]   # Mutated by researcher_node
    grievance_letter: Optional[dict] # Mutated by drafter_node
    filing_result: Optional[dict]    # Mutated by navigator_node
    confirmation_pending: bool
    case_id: Optional[str]
    error: Optional[str]
```

## 2. Agent 1: Parser Node
Extracts structured facts from the worker's text or image.

**Signature:** `def parser_node(state: GigGuardState) -> dict:`
**Reads:** `state["message"]`, `state["media_url"]`
**Writes:** `{"parsed_data": dict, "error": str | None}`

**Output Schema (`parsed_data`):**
```json
{
  "platform": "string | null",
  "event_type": "string | null",
  "date": "string | null",
  "reason": "string | null",
  "worker_id": "string | null",
  "earnings_withheld": "number | null",
  "notice_provided": "boolean | null",
  "appeal_offered": "boolean | null",
  "language_detected": "string",
  "input_quality": "CLEAR | DEGRADED | NOT_A_COMPLAINT",
  "confidence": {
    "platform": "float",
    "...": "float",
    "overall": "float"
  }
}
```

## 3. Agent 2: Legal Researcher Node
Performs ChromaDB RAG against legal knowledge base to find violations.

**Signature:** `def researcher_node(state: GigGuardState) -> dict:`
**Reads:** `state["parsed_data"]`
**Writes:** `{"legal_analysis": dict}`

**Output Schema (`legal_analysis`):**
```json
{
  "violations": [
    {
      "law": "string",
      "section": "string",
      "retrieved_text": "string (direct quote)",
      "violation_description": "string"
    }
  ],
  "case_strength": "STRONG | MODERATE | WEAK | INSUFFICIENT_BASIS",
  "confidence": "float",
  "worker_message": "string"
}
```

## 4. Agent 3: Drafter Node
Drafts bilingual grievance letters strictly using the violations found.

**Signature:** `def drafter_node(state: GigGuardState) -> dict:`
**Reads:** `state["parsed_data"]`, `state["legal_analysis"]`
**Writes:** `{"grievance_letter": dict}`

**Output Schema (`grievance_letter`):**
```json
{
  "hindi_letter": "string",
  "english_letter": "string",
  "demands": ["string", "string"],
  "escalation_warning": "string",
  "disclaimer": "string (MANDATORY_DISCLAIMER)"
}
```

## 5. Integration Notes for Person 1 (Backend Core)
- Ensure the LLM temperature is set to `0.0` for Researcher and Drafter to prevent hallucinations.
- `MANDATORY_DISCLAIMER` must always be explicitly overridden in the code, regardless of what the LLM outputs.
- If ChromaDB returns no results, the Researcher node must force `case_strength = "INSUFFICIENT_BASIS"`.
- The Drafter node relies on `case_strength`. If it is `"INSUFFICIENT_BASIS"`, it will skip legal citations and generate a "For Record" notice instead.
