"""
Prompt Stress Tests — Agent 3 (Drafter)
Owner: Person 2 (AI Agents + Prompt Engineering)

Tests Drafter generation across:
  - STRONG case (Full letters with citations)
  - INSUFFICIENT_BASIS case (Letters without citations)
  - Mandatory disclaimer enforcement
  - Missing field handling
  - Bilingual output verification

Run with:  python -m pytest tests/test_drafter.py -v
    or:    python tests/test_drafter.py
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.drafter_node import MANDATORY_DISCLAIMER


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MOCK LLM RESPONSES — Simulate Groq outputs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MOCK_STRONG_RESPONSE = json.dumps({
    "hindi_letter": "शिकायत सूचना\n...",
    "english_letter": "GRIEVANCE NOTICE\n...\nAs per Social Security Rules...",
    "demands": [
        "Immediate release of withheld payment of Rs 1840",
        "Written explanation of deactivation within 15 days"
    ],
    "escalation_warning": "Failure to respond within 15 days will compel the complainant to escalate this matter to the appropriate labour authorities and consumer forums.",
    "disclaimer": "Some LLM generated disclaimer that should be overridden"
})


MOCK_INSUFFICIENT_RESPONSE = json.dumps({
    "hindi_letter": "शिकायत सूचना (केवल रिकॉर्ड के लिए)\n...",
    "english_letter": "GRIEVANCE NOTICE (For Record)\n...\nThis notice documents the incident for official record.",
    "demands": [
        "Written explanation of action taken",
        "Response within 15 days of receipt of this notice"
    ],
    "escalation_warning": "Failure to respond within 15 days will compel the complainant to escalate this matter to the appropriate labour authorities and consumer forums.",
    "disclaimer": "Some LLM generated disclaimer"
})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER MOCKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _make_groq_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


def _run_drafter_with_mock(parsed_data: dict, legal_analysis: dict, mock_response_json: str) -> dict:
    from app.agents.drafter_node import drafter_node

    state = {
        "parsed_data": parsed_data,
        "legal_analysis": legal_analysis
    }
    
    with patch("app.agents.drafter_node.Groq") as mock_groq_class:
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = _make_groq_response(mock_response_json)
        mock_groq_class.return_value = mock_client_instance
        
        result = drafter_node(state)
        
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST CASES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_strong_case_generation():
    """Drafter generates full letter for STRONG case and enforces disclaimer."""
    parsed = {"platform": "Swiggy", "event_type": "ACCOUNT_DEACTIVATION"}
    analysis = {
        "case_strength": "STRONG",
        "violations": [{"law": "Test Law"}]
    }
    
    result = _run_drafter_with_mock(parsed, analysis, MOCK_STRONG_RESPONSE)
    letter_data = result.get("grievance_letter", {})
    
    # Check bilingual presence
    assert "GRIEVANCE NOTICE" in letter_data["english_letter"]
    assert "शिकायत" in letter_data["hindi_letter"]
    
    # Check demands
    assert len(letter_data["demands"]) == 2
    
    # Check MANDATORY_DISCLAIMER override (critical rule)
    assert letter_data["disclaimer"] == MANDATORY_DISCLAIMER
    print("✅ test_strong_case_generation passed")


def test_insufficient_basis_generation():
    """Drafter generates honest record for INSUFFICIENT_BASIS case."""
    parsed = {"platform": "Uber", "event_type": "OTHER"}
    analysis = {
        "case_strength": "INSUFFICIENT_BASIS",
        "violations": []
    }
    
    result = _run_drafter_with_mock(parsed, analysis, MOCK_INSUFFICIENT_RESPONSE)
    letter_data = result.get("grievance_letter", {})
    
    assert "record" in letter_data["english_letter"].lower()
    assert letter_data["disclaimer"] == MANDATORY_DISCLAIMER
    print("✅ test_insufficient_basis_generation passed")


def test_missing_fields_recovery():
    """Drafter recovers if LLM forgets to output some fields."""
    bad_json = json.dumps({
        "english_letter": "Only english was generated"
        # missing hindi_letter, demands, escalation_warning, disclaimer
    })
    
    result = _run_drafter_with_mock({}, {}, bad_json)
    letter_data = result.get("grievance_letter", {})
    
    # Guardrails should auto-fill missing fields
    assert letter_data["hindi_letter"] == ""
    assert letter_data["english_letter"] == "Only english was generated"
    assert letter_data["demands"] == []
    assert "Failure to respond" in letter_data["escalation_warning"]
    assert letter_data["disclaimer"] == MANDATORY_DISCLAIMER
    print("✅ test_missing_fields_recovery passed")


def test_json_parse_error_fallback():
    """Drafter returns safe fallback dictionary if LLM outputs garbage."""
    result = _run_drafter_with_mock({}, {}, "This is not JSON at all")
    letter_data = result.get("grievance_letter", {})
    
    assert "Error" in letter_data["english_letter"]
    assert "त्रुटि" in letter_data["hindi_letter"]
    assert letter_data["demands"] == []
    assert letter_data["disclaimer"] == MANDATORY_DISCLAIMER
    print("✅ test_json_parse_error_fallback passed")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RUNNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DRAFTER PROMPT STRESS TESTS")
    print("=" * 60)
    
    test_strong_case_generation()
    test_insufficient_basis_generation()
    test_missing_fields_recovery()
    test_json_parse_error_fallback()
    
    print("\n" + "=" * 60)
    print("ALL DRAFTER TESTS PASSED ✅")
    print("=" * 60)
