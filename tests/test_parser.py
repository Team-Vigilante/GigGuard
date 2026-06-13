"""
Phase 5: Parser Prompt Stress Tests
====================================
Tests the PARSER_SYSTEM_PROMPT with 5 required input scenarios.

TWO TEST LAYERS:
  - TestParserPromptStructure: Offline tests (no API needed)
  - TestParserLive: Live API tests (requires ANTHROPIC_API_KEY with credits)

Run offline tests:   python3 -m unittest tests.test_parser.TestParserPromptStructure -v
Run live tests:      python3 -m unittest tests.test_parser.TestParserLive -v
Run all:             python3 -m unittest tests.test_parser -v
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.parser_prompt import PARSER_SYSTEM_PROMPT


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OFFLINE TESTS — no API key needed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestParserPromptStructure(unittest.TestCase):
    """Verify the parser prompt contains all required instructions."""

    def test_prompt_has_all_extraction_fields(self):
        """All 8 required fields must be mentioned in the prompt."""
        required_fields = [
            "platform", "event_type", "date", "reason",
            "worker_id", "earnings_withheld", "notice_provided", "appeal_offered"
        ]
        for field in required_fields:
            self.assertIn(field, PARSER_SYSTEM_PROMPT,
                          f"Missing extraction field: {field}")

    def test_prompt_has_language_support(self):
        """Prompt must mention all 4 supported languages."""
        for lang in ["Hindi", "Kannada", "Tamil", "English"]:
            self.assertIn(lang, PARSER_SYSTEM_PROMPT,
                          f"Missing language support: {lang}")

    def test_prompt_has_confidence_scoring(self):
        """Prompt must include confidence scoring instructions."""
        self.assertIn("confidence", PARSER_SYSTEM_PROMPT)
        self.assertIn("0.0", PARSER_SYSTEM_PROMPT)
        self.assertIn("1.0", PARSER_SYSTEM_PROMPT)

    def test_prompt_enforces_json_only(self):
        """Prompt must instruct strict JSON output."""
        self.assertIn("JSON", PARSER_SYSTEM_PROMPT)
        self.assertIn("No explanations", PARSER_SYSTEM_PROMPT)

    def test_prompt_handles_blurry_input(self):
        """Prompt must include blurry/degraded input handling."""
        self.assertIn("DEGRADED", PARSER_SYSTEM_PROMPT)
        self.assertIn("blurry", PARSER_SYSTEM_PROMPT.lower())

    def test_prompt_handles_irrelevant_input(self):
        """Prompt must handle non-complaint messages."""
        self.assertIn("NOT_A_COMPLAINT", PARSER_SYSTEM_PROMPT)

    def test_prompt_has_event_type_categories(self):
        """All event type categories must be defined."""
        categories = [
            "ACCOUNT_DEACTIVATION", "PAYMENT_WITHHELD",
            "UNFAIR_DEDUCTION", "FORCED_CANCELLATION",
            "RATING_MANIPULATION", "OTHER"
        ]
        for cat in categories:
            self.assertIn(cat, PARSER_SYSTEM_PROMPT,
                          f"Missing event category: {cat}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LIVE API TESTS — requires ANTHROPIC_API_KEY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 5 test inputs from Phase 5 spec
TEST_INPUTS = {
    "clean_english": (
        "I am a Swiggy delivery partner. On 2025-06-01 my account was "
        "suddenly deactivated without any warning. I had 3200 rupees "
        "in my wallet which they are not releasing. My partner ID is "
        "SWG-88432. They gave no reason and no option to appeal."
    ),
    "hindi_only": (
        "मैं ज़ोमैटो पर डिलीवरी करता हूँ। कल से मेरा अकाउंट बंद कर दिया "
        "गया है। कोई वजह नहीं बताई। मेरे 5000 रुपये अभी तक नहीं मिले हैं। "
        "कोई अपील का ऑप्शन भी नहीं दिया।"
    ),
    "mixed_hindi_english": (
        "Ola ne mera account deactivate kar diya bina kisi warning ke. "
        "Mera driver ID OLA-9921 hai. Last week ka 4500 rupees ka payment "
        "bhi rok liya hai. Unhone koi reason nahi diya. Bahut pareshaan hoon."
    ),
    "blurry_screenshot": (
        "I am sending a screenshot of the notification I received but "
        "it is very blurry. I can only make out that it says something "
        "about 'policy violation' and 'account suspended'. The platform "
        "name is not clearly visible but it might be Urban Company. "
        "The date and amounts are completely unreadable."
    ),
    "irrelevant_message": (
        "Hey, what's the weather like in Bangalore today? "
        "Also can you recommend a good restaurant nearby?"
    ),
}


def _call_parser(message: str) -> dict:
    """Helper: call Claude with the parser prompt and return parsed JSON."""
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=1024,
        temperature=0.0,
        system=PARSER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}]
    )
    text = response.content[0].text
    start = text.find('{')
    end = text.rfind('}') + 1
    return json.loads(text[start:end])


class TestParserLive(unittest.TestCase):
    """Live API stress tests — 5 scenarios from Phase 5 spec."""

    def setUp(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY is not set.")

    # ── Test 1: Clean English ──────────────────────────
    def test_1_clean_english_description(self):
        """Clean English input → all fields extracted with high confidence."""
        result = _call_parser(TEST_INPUTS["clean_english"])

        self.assertEqual(result["platform"], "Swiggy")
        self.assertEqual(result["event_type"], "ACCOUNT_DEACTIVATION")
        self.assertEqual(result["earnings_withheld"], 3200)
        self.assertEqual(result["notice_provided"], False)
        self.assertEqual(result["appeal_offered"], False)
        self.assertEqual(result["input_quality"], "CLEAR")
        self.assertGreaterEqual(result["confidence"]["overall"], 0.7)

    # ── Test 2: Hindi Only ─────────────────────────────
    def test_2_hindi_text_message(self):
        """Hindi-only message → correct extraction, language_detected=Hindi."""
        result = _call_parser(TEST_INPUTS["hindi_only"])

        self.assertEqual(result["platform"], "Zomato")
        self.assertEqual(result["event_type"], "ACCOUNT_DEACTIVATION")
        self.assertIn(result["language_detected"].lower(), ["hindi", "hi"])
        self.assertEqual(result["appeal_offered"], False)
        self.assertEqual(result["input_quality"], "CLEAR")

    # ── Test 3: Mixed Hindi-English ────────────────────
    def test_3_mixed_hindi_english(self):
        """Mixed Hinglish input → correct extraction."""
        result = _call_parser(TEST_INPUTS["mixed_hindi_english"])

        self.assertEqual(result["platform"], "Ola")
        self.assertEqual(result["event_type"], "ACCOUNT_DEACTIVATION")
        self.assertIsNotNone(result.get("worker_id"))
        self.assertEqual(result["input_quality"], "CLEAR")

    # ── Test 4: Blurry Screenshot ──────────────────────
    def test_4_blurry_incomplete_screenshot(self):
        """Blurry screenshot → DEGRADED quality, low confidence, nulls."""
        result = _call_parser(TEST_INPUTS["blurry_screenshot"])

        self.assertEqual(result["input_quality"], "DEGRADED")
        self.assertLessEqual(result["confidence"]["overall"], 0.5)
        # Date and earnings should be null since unreadable
        self.assertIsNone(result.get("date"))
        self.assertIsNone(result.get("earnings_withheld"))

    # ── Test 5: Irrelevant Message ─────────────────────
    def test_5_irrelevant_message(self):
        """Non-complaint message → NOT_A_COMPLAINT, confidence 0.0."""
        result = _call_parser(TEST_INPUTS["irrelevant_message"])

        self.assertEqual(result["input_quality"], "NOT_A_COMPLAINT")
        self.assertIsNone(result.get("event_type"))
        self.assertEqual(result["confidence"]["overall"], 0.0)


if __name__ == '__main__':
    unittest.main()