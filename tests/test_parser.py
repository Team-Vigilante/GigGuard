"""
Prompt Stress Tests — Agent 1 (Parser)
Owner: Person 2 (AI Agents + Prompt Engineering)

Tests parser prompt behavior across:
  - Hindi messages
  - English messages
  - Mixed Hindi-English (Hinglish)
  - Degraded/blurry screenshot descriptions
  - Non-complaint messages
  - Confidence score validation
  - Missing fields handling

Run with:  python -m pytest tests/test_parser.py -v
    or:    python tests/test_parser.py
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MOCK LLM RESPONSES — Simulate Groq/Gemini outputs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Case 1: Clear Hindi message — Swiggy deactivation
MOCK_HINDI_RESPONSE = json.dumps({
    "platform": "Swiggy",
    "event_type": "ACCOUNT_DEACTIVATION",
    "date": "2026-06-07",
    "reason": "Customer rating fell below minimum threshold",
    "worker_id": "SWG-BLR-228194",
    "earnings_withheld": 1840,
    "notice_provided": False,
    "appeal_offered": False,
    "language_detected": "hi",
    "input_quality": "CLEAR",
    "confidence": {
        "platform": 0.98,
        "event_type": 0.95,
        "date": 0.97,
        "reason": 0.90,
        "worker_id": 0.92,
        "earnings_withheld": 0.96,
        "notice_provided": 0.85,
        "appeal_offered": 0.85,
        "overall": 0.92
    }
})

# Case 2: Clear English message — Zomato payment withheld
MOCK_ENGLISH_RESPONSE = json.dumps({
    "platform": "Zomato",
    "event_type": "PAYMENT_WITHHELD",
    "date": "2026-07-01",
    "reason": "Pending verification of delivery records",
    "worker_id": None,
    "earnings_withheld": 3200,
    "notice_provided": False,
    "appeal_offered": False,
    "language_detected": "en",
    "input_quality": "CLEAR",
    "confidence": {
        "platform": 1.0,
        "event_type": 0.95,
        "date": 1.0,
        "reason": 0.7,
        "worker_id": 0.0,
        "earnings_withheld": 1.0,
        "notice_provided": 0.85,
        "appeal_offered": 0.80,
        "overall": 0.90
    }
})

# Case 3: Mixed Hinglish message — Ola rating manipulation
MOCK_HINGLISH_RESPONSE = json.dumps({
    "platform": "Ola",
    "event_type": "RATING_MANIPULATION",
    "date": "approximately 1 week before complaint",
    "reason": "NO_REASON_PROVIDED",
    "worker_id": "OLA-HYD-91827",
    "earnings_withheld": None,
    "notice_provided": None,
    "appeal_offered": False,
    "language_detected": "hi-en",
    "input_quality": "CLEAR",
    "confidence": {
        "platform": 1.0,
        "event_type": 0.7,
        "date": 0.4,
        "reason": 0.7,
        "worker_id": 0.95,
        "earnings_withheld": 0.0,
        "notice_provided": 0.0,
        "appeal_offered": 0.7,
        "overall": 0.72
    }
})

# Case 4: Degraded/blurry screenshot
MOCK_DEGRADED_RESPONSE = json.dumps({
    "platform": "Swiggy",
    "event_type": None,
    "date": None,
    "reason": None,
    "worker_id": None,
    "earnings_withheld": None,
    "notice_provided": None,
    "appeal_offered": None,
    "language_detected": "en",
    "input_quality": "DEGRADED",
    "confidence": {
        "platform": 0.4,
        "event_type": 0.0,
        "date": 0.0,
        "reason": 0.0,
        "worker_id": 0.0,
        "earnings_withheld": 0.0,
        "notice_provided": 0.0,
        "appeal_offered": 0.0,
        "overall": 0.2
    }
})

# Case 5: Not a complaint — random message
MOCK_NOT_COMPLAINT_RESPONSE = json.dumps({
    "platform": None,
    "event_type": None,
    "date": None,
    "reason": None,
    "worker_id": None,
    "earnings_withheld": None,
    "notice_provided": None,
    "appeal_offered": None,
    "language_detected": "en",
    "input_quality": "NOT_A_COMPLAINT",
    "confidence": {
        "platform": 0.0,
        "event_type": 0.0,
        "date": 0.0,
        "reason": 0.0,
        "worker_id": 0.0,
        "earnings_withheld": 0.0,
        "notice_provided": 0.0,
        "appeal_offered": 0.0,
        "overall": 0.0
    }
})

# Case 6: Low confidence — vague message with few extractable fields
MOCK_LOW_CONFIDENCE_RESPONSE = json.dumps({
    "platform": "Uber",
    "event_type": "OTHER",
    "date": None,
    "reason": None,
    "worker_id": None,
    "earnings_withheld": None,
    "notice_provided": None,
    "appeal_offered": None,
    "language_detected": "hi",
    "input_quality": "CLEAR",
    "confidence": {
        "platform": 0.7,
        "event_type": 0.4,
        "date": 0.0,
        "reason": 0.0,
        "worker_id": 0.0,
        "earnings_withheld": 0.0,
        "notice_provided": 0.0,
        "appeal_offered": 0.0,
        "overall": 0.2
    }
})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER: Create mock Groq response
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _make_groq_response(content: str):
    """Create a mock Groq API response object."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


def _run_parser_with_mock(message: str, mock_response_json: str) -> dict:
    """Run parser_node with a mocked Groq response."""
    from app.agents.parser import parser_node

    state = {
        "phone": "+919999999999",
        "message": message,
        "media_url": None,
        "conversation_state": "awaiting_screenshot",
        "parsed_data": None,
        "legal_analysis": None,
        "grievance_letter": None,
        "filing_result": None,
        "confirmation_pending": False,
        "case_id": None,
        "error": None
    }

    with patch("app.agents.parser.groq_client") as mock_client:
        mock_client.chat.completions.create.return_value = (
            _make_groq_response(mock_response_json)
        )
        result = parser_node(state)

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST CASES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_hindi_message_parsing():
    """Parser extracts structured data from a Hindi complaint."""
    result = _run_parser_with_mock(
        "Mera Swiggy account band ho gaya hai bina koi notice ke. "
        "Mera ID SWG-BLR-228194 hai aur 1840 rupaye ruke hain.",
        MOCK_HINDI_RESPONSE
    )
    parsed = result.get("parsed_data", {})
    assert parsed["platform"] == "Swiggy"
    assert parsed["event_type"] == "ACCOUNT_DEACTIVATION"
    assert parsed["earnings_withheld"] == 1840
    assert parsed["notice_provided"] is False
    assert parsed["language_detected"] == "hi"
    assert parsed["input_quality"] == "CLEAR"
    print("✅ test_hindi_message_parsing passed")


def test_english_message_parsing():
    """Parser extracts structured data from an English complaint."""
    result = _run_parser_with_mock(
        "Zomato has not paid me Rs 3200 for deliveries done on July 1st. "
        "They said verification is pending but gave no warning.",
        MOCK_ENGLISH_RESPONSE
    )
    parsed = result.get("parsed_data", {})
    assert parsed["platform"] == "Zomato"
    assert parsed["event_type"] == "PAYMENT_WITHHELD"
    assert parsed["earnings_withheld"] == 3200
    assert parsed["language_detected"] == "en"
    print("✅ test_english_message_parsing passed")


def test_hinglish_mixed_language():
    """Parser handles mixed Hindi-English (Hinglish) input."""
    result = _run_parser_with_mock(
        "Ola ka rating system bahut unfair hai, meri rating girate "
        "jaa rahi hai but customer ke fake complaints ki wajah se. "
        "My ID is OLA-HYD-91827. Koi appeal ka option nahi diya.",
        MOCK_HINGLISH_RESPONSE
    )
    parsed = result.get("parsed_data", {})
    assert parsed["platform"] == "Ola"
    assert parsed["event_type"] == "RATING_MANIPULATION"
    assert parsed["worker_id"] == "OLA-HYD-91827"
    assert parsed["appeal_offered"] is False
    assert parsed["language_detected"] == "hi-en"
    print("✅ test_hinglish_mixed_language passed")


def test_degraded_screenshot_handling():
    """Parser handles blurry/degraded screenshot with low confidence."""
    result = _run_parser_with_mock(
        "[Screenshot description: Blurry image showing Swiggy app "
        "notification. Text partially readable. Some numbers visible "
        "but unclear.]",
        MOCK_DEGRADED_RESPONSE
    )
    parsed = result.get("parsed_data", {})
    assert parsed["input_quality"] == "DEGRADED"
    assert parsed["confidence"]["overall"] == 0.2
    # Low confidence should trigger AWAITING_SCREENSHOT
    assert result.get("error") == "low_confidence"
    assert result.get("conversation_state") == "AWAITING_SCREENSHOT"
    print("✅ test_degraded_screenshot_handling passed")


def test_non_complaint_rejection():
    """Parser rejects non-complaint messages."""
    result = _run_parser_with_mock(
        "Hello, what is the weather today? I want to order some food.",
        MOCK_NOT_COMPLAINT_RESPONSE
    )
    parsed = result.get("parsed_data", {})
    assert parsed["input_quality"] == "NOT_A_COMPLAINT"
    assert parsed["event_type"] is None
    assert parsed["confidence"]["overall"] == 0.0
    # Zero confidence should trigger low_confidence error
    assert result.get("error") == "low_confidence"
    print("✅ test_non_complaint_rejection passed")


def test_confidence_score_structure():
    """Confidence scores have the correct nested structure."""
    result = _run_parser_with_mock(
        "Swiggy mera account band kar diya",
        MOCK_HINDI_RESPONSE
    )
    parsed = result.get("parsed_data", {})
    confidence = parsed.get("confidence", {})

    # Check all required confidence fields exist
    required_fields = [
        "platform", "event_type", "date", "reason",
        "worker_id", "earnings_withheld", "notice_provided",
        "appeal_offered", "overall"
    ]
    for field in required_fields:
        assert field in confidence, f"Missing confidence field: {field}"
        assert isinstance(confidence[field], (int, float)), (
            f"Confidence '{field}' should be numeric, got {type(confidence[field])}"
        )
        assert 0.0 <= confidence[field] <= 1.0, (
            f"Confidence '{field}' out of range: {confidence[field]}"
        )
    print("✅ test_confidence_score_structure passed")


def test_low_confidence_penalty():
    """
    When fewer than 3 fields are extracted, overall confidence
    should be set to 0.2 (penalty rule).
    """
    result = _run_parser_with_mock(
        "Uber mein kuch problem hai",
        MOCK_LOW_CONFIDENCE_RESPONSE
    )
    parsed = result.get("parsed_data", {})
    assert parsed["confidence"]["overall"] == 0.2
    # This should also trigger low_confidence since 0.2 < 0.75
    assert result.get("error") == "low_confidence"
    print("✅ test_low_confidence_penalty passed")


def test_high_confidence_proceeds():
    """High-confidence parse moves to AWAITING_CONFIRMATION."""
    result = _run_parser_with_mock(
        "Swiggy mera account band kar diya, 1840 rupay ruke hain",
        MOCK_HINDI_RESPONSE
    )
    assert result.get("error") is None
    assert result.get("conversation_state") == "AWAITING_CONFIRMATION"
    print("✅ test_high_confidence_proceeds passed")


def test_json_parse_error_handling():
    """Parser handles invalid JSON from LLM gracefully."""
    result = _run_parser_with_mock(
        "Swiggy account band hua",
        "This is not valid JSON at all {broken"
    )
    assert result.get("error") == "parse_failed"
    assert result.get("conversation_state") == "AWAITING_SCREENSHOT"
    print("✅ test_json_parse_error_handling passed")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RUNNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PARSER PROMPT STRESS TESTS")
    print("=" * 60)

    test_hindi_message_parsing()
    test_english_message_parsing()
    test_hinglish_mixed_language()
    test_degraded_screenshot_handling()
    test_non_complaint_rejection()
    test_confidence_score_structure()
    test_low_confidence_penalty()
    test_high_confidence_proceeds()
    test_json_parse_error_handling()

    print("\n" + "=" * 60)
    print("ALL PARSER TESTS PASSED ✅")
    print("=" * 60)
