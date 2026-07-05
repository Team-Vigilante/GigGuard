"""
Prompt Stress Tests — Agent 2 (Legal Researcher)
Owner: Person 2 (AI Agents + Prompt Engineering)

Tests researcher RAG logic and anti-hallucination guardrails across:
  - STRONG case (multiple direct text matches)
  - MODERATE case (partial matches)
  - INSUFFICIENT_BASIS case (no matching legal text)
  - Anti-hallucination verification (no extra laws cited)

Run with:  python -m pytest tests/test_researcher.py -v
    or:    python tests/test_researcher.py
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MOCK RAG RESPONSES — Simulate Groq RAG outputs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Case 1: STRONG case — Clear violations with text support
MOCK_STRONG_RESPONSE = json.dumps({
    "violations": [
        {
            "law": "Social Security (Central) Rules 2026",
            "section": "Rule 9 - Deactivation Notice Requirements",
            "retrieved_text": "No aggregator shall deactivate or terminate the account of any gig worker or platform worker without giving prior written notice of not less than seven days",
            "violation_description": "The platform deactivated the worker's account instantly without the mandatory 7-day prior written notice."
        },
        {
            "law": "Social Security (Central) Rules 2026",
            "section": "Rule 9 - Deactivation Notice Requirements",
            "retrieved_text": "Any wages or dues payable to the worker shall be released within forty-eight hours of deactivation",
            "violation_description": "The platform withheld Rs. 1840 which should have been released within 48 hours of deactivation."
        }
    ],
    "case_strength": "STRONG",
    "confidence": 0.95,
    "worker_message": "Aapke case mein 2 clear violations mile hain. Platform ne bina 7 din ke notice ke account band kiya aur aapke paise rok liye jo ki niyam ke khilaf hai."
})

# Case 2: MODERATE case — Partial support / one violation
MOCK_MODERATE_RESPONSE = json.dumps({
    "violations": [
        {
            "law": "Swiggy Delivery Partner Agreement",
            "section": "Section 6 - Performance Standards",
            "retrieved_text": "Deactivation for low ratings shall only occur after three such notices have been issued and the partner has been given reasonable opportunity to improve performance.",
            "violation_description": "Platform deactivated account for low rating without issuing the required three notices."
        }
    ],
    "case_strength": "MODERATE",
    "confidence": 0.80,
    "worker_message": "Aapka case theek lag raha hai kyunki platform ne apni hi policy follow nahi ki. Hum appeal file kar sakte hain."
})

# Case 3: INSUFFICIENT_BASIS case — Empty context handling
MOCK_INSUFFICIENT_RESPONSE = json.dumps({
    "violations": [],
    "case_strength": "INSUFFICIENT_BASIS",
    "confidence": 0.0,
    "worker_message": "Aapke case mein koi direct legal violation nahi mila. Humne complaint document kar li hai par legal claim strong nahi hai."
})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER MOCKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _make_groq_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


def _run_researcher_with_mock(parsed_data: dict, mock_response_json: str, chunks_count: int = 2) -> dict:
    from app.agents.researcher_node import researcher_node

    state = {"parsed_data": parsed_data}

    # Mock ChromaDB returning dummy chunks
    dummy_chunks = [{"text": "dummy chunk text"} for _ in range(chunks_count)]
    
    with patch("app.agents.researcher_node.query_knowledge_base") as mock_chroma, \
         patch("app.agents.researcher_node.Groq") as mock_groq_class:
        
        mock_chroma.return_value = dummy_chunks
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = _make_groq_response(mock_response_json)
        mock_groq_class.return_value = mock_client_instance
        
        result = researcher_node(state)
        
    return result


def _run_researcher_with_empty_context(parsed_data: dict) -> dict:
    from app.agents.researcher_node import researcher_node

    state = {"parsed_data": parsed_data}
    
    with patch("app.agents.researcher_node.query_knowledge_base") as mock_chroma, \
         patch("app.agents.researcher_node.Groq") as mock_groq_class:
        
        # Simulate empty ChromaDB results
        mock_chroma.return_value = []
        
        # The LLM shouldn't even try to find violations if chunk_count == 0,
        # but if it does, the guardrail will override it.
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = _make_groq_response(MOCK_STRONG_RESPONSE)
        mock_groq_class.return_value = mock_client_instance
        
        result = researcher_node(state)
        
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST CASES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_strong_case_extraction():
    """Researcher extracts multiple well-supported violations."""
    parsed = {"platform": "Swiggy", "event_type": "ACCOUNT_DEACTIVATION"}
    result = _run_researcher_with_mock(parsed, MOCK_STRONG_RESPONSE)
    analysis = result.get("legal_analysis", {})
    
    assert analysis["case_strength"] == "STRONG"
    assert len(analysis["violations"]) == 2
    assert analysis["violations"][0]["law"] == "Social Security (Central) Rules 2026"
    assert "retrieved_text" in analysis["violations"][0]
    assert analysis["confidence"] == 0.95
    print("✅ test_strong_case_extraction passed")


def test_moderate_case_extraction():
    """Researcher extracts single partial violation."""
    parsed = {"platform": "Swiggy", "event_type": "RATING_MANIPULATION"}
    result = _run_researcher_with_mock(parsed, MOCK_MODERATE_RESPONSE)
    analysis = result.get("legal_analysis", {})
    
    assert analysis["case_strength"] == "MODERATE"
    assert len(analysis["violations"]) == 1
    assert "Swiggy Delivery Partner Agreement" in analysis["violations"][0]["law"]
    print("✅ test_moderate_case_extraction passed")


def test_empty_context_handling():
    """If ChromaDB returns no chunks, it MUST force INSUFFICIENT_BASIS."""
    parsed = {"platform": "Unknown", "event_type": "OTHER"}
    # Even if LLM returns a STRONG response, the chunk_count == 0 guardrail should override it
    result = _run_researcher_with_empty_context(parsed)
    analysis = result.get("legal_analysis", {})
    
    assert analysis["case_strength"] == "INSUFFICIENT_BASIS"
    assert len(analysis["violations"]) == 0
    assert analysis["confidence"] == 0.0
    print("✅ test_empty_context_handling passed")


def test_missing_parsed_data_handling():
    """If parsed_data is empty, immediately return INSUFFICIENT_BASIS."""
    from app.agents.researcher_node import researcher_node
    
    result = researcher_node({"parsed_data": None})
    analysis = result.get("legal_analysis", {})
    
    assert analysis["case_strength"] == "INSUFFICIENT_BASIS"
    assert len(analysis["violations"]) == 0
    print("✅ test_missing_parsed_data_handling passed")


def test_invalid_json_handling():
    """If Groq returns broken JSON, fallback gracefully."""
    parsed = {"platform": "Swiggy"}
    result = _run_researcher_with_mock(parsed, "This is broke { JSON")
    analysis = result.get("legal_analysis", {})
    
    assert analysis["case_strength"] == "INSUFFICIENT_BASIS"
    assert "error" in analysis["worker_message"].lower()
    print("✅ test_invalid_json_handling passed")


def test_invalid_case_strength_fallback():
    """If LLM returns a made-up case_strength, fallback to WEAK."""
    bad_strength_response = json.dumps({
        "violations": [],
        "case_strength": "SUPER_STRONG_DEFINITELY_WIN",
        "confidence": 0.9,
        "worker_message": "test"
    })
    
    result = _run_researcher_with_mock({"platform": "Swiggy"}, bad_strength_response)
    analysis = result.get("legal_analysis", {})
    
    assert analysis["case_strength"] == "WEAK"
    print("✅ test_invalid_case_strength_fallback passed")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RUNNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RESEARCHER PROMPT STRESS TESTS")
    print("=" * 60)
    
    test_strong_case_extraction()
    test_moderate_case_extraction()
    test_empty_context_handling()
    test_missing_parsed_data_handling()
    test_invalid_json_handling()
    test_invalid_case_strength_fallback()
    
    print("\n" + "=" * 60)
    print("ALL RESEARCHER TESTS PASSED ✅")
    print("=" * 60)
