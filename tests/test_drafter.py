"""
Phase 5: Drafter Stress Tests
===============================
Tests drafter_node() with 3 required scenarios.

TWO TEST LAYERS:
  - TestDrafterStructure: Offline tests (no API needed)
  - TestDrafterLive: Live API tests (requires ANTHROPIC_API_KEY)

Run offline tests:   python3 -m unittest tests.test_drafter.TestDrafterStructure -v
Run live tests:      python3 -m unittest tests.test_drafter.TestDrafterLive -v
Run all:             python3 -m unittest tests.test_drafter -v
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.drafter_node import (
    drafter_node,
    DRAFTER_SYSTEM_PROMPT,
    MANDATORY_DISCLAIMER
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OFFLINE TESTS — no API key needed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestDrafterStructure(unittest.TestCase):
    """Verify the drafter prompt and constants are correct."""

    def test_disclaimer_constant_is_correct(self):
        """MANDATORY_DISCLAIMER must match the spec exactly."""
        expected = (
            "This document was prepared with AI assistance. "
            "Cited provisions are based on publicly available "
            "policy documents. For complex cases, consult a "
            "legal professional."
        )
        self.assertEqual(MANDATORY_DISCLAIMER, expected)

    def test_prompt_has_citation_rule(self):
        """Prompt must enforce citations only from legal_analysis."""
        self.assertIn("MUST come", DRAFTER_SYSTEM_PROMPT)
        self.assertIn("legal_analysis.violations", DRAFTER_SYSTEM_PROMPT)
        self.assertIn("MUST NOT cite any law", DRAFTER_SYSTEM_PROMPT)

    def test_prompt_has_insufficient_basis_rule(self):
        """Prompt must handle INSUFFICIENT_BASIS case."""
        self.assertIn("INSUFFICIENT_BASIS", DRAFTER_SYSTEM_PROMPT)
        self.assertIn("Do NOT cite any laws", DRAFTER_SYSTEM_PROMPT)

    def test_prompt_has_hindi_translation_rule(self):
        """Prompt must require full Hindi translation, not summary."""
        self.assertIn("complete translation", DRAFTER_SYSTEM_PROMPT)
        self.assertIn("Not a summary", DRAFTER_SYSTEM_PROMPT)

    def test_prompt_has_letter_format(self):
        """Prompt must include the 11-section letter format."""
        sections = [
            "HEADER", "FROM", "TO", "DATE", "SUBJECT",
            "FACTS", "LEGAL BASIS", "RELIEF SOUGHT",
            "ESCALATION WARNING", "CLOSING", "DISCLAIMER"
        ]
        for section in sections:
            self.assertIn(section, DRAFTER_SYSTEM_PROMPT,
                          f"Missing letter section: {section}")

    def test_prompt_has_15_day_deadline(self):
        """15 day response deadline must be in the prompt."""
        self.assertIn("15 days", DRAFTER_SYSTEM_PROMPT)

    def test_prompt_enforces_json_output(self):
        """Prompt must enforce strict JSON output."""
        self.assertIn("STRICT JSON ONLY", DRAFTER_SYSTEM_PROMPT)
        self.assertIn("hindi_letter", DRAFTER_SYSTEM_PROMPT)
        self.assertIn("english_letter", DRAFTER_SYSTEM_PROMPT)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LIVE API TESTS — requires ANTHROPIC_API_KEY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRONG_CASE_STATE = {
    "parsed_data": {
        "platform": "Swiggy",
        "event_type": "ACCOUNT_DEACTIVATION",
        "date": "2025-06-01",
        "reason": "NO_REASON_PROVIDED",
        "worker_id": "SWG-88432",
        "earnings_withheld": 5000,
        "notice_provided": False,
        "appeal_offered": False
    },
    "legal_analysis": {
        "case_strength": "STRONG",
        "confidence": 0.92,
        "violations": [
            {
                "violation_description": "Arbitrary termination without notice violates worker protections",
                "source": "Code on Social Security 2020",
                "section": "Section 114",
                "retrieved_text": "No aggregator shall terminate the services of a gig worker without providing adequate notice."
            },
            {
                "violation_description": "Withholding earned wages is prohibited",
                "source": "Karnataka Platform-based Gig Workers Act 2025",
                "section": "Section 12",
                "retrieved_text": "Every platform-based gig worker shall be entitled to timely payment of wages earned."
            },
            {
                "violation_description": "Failure to provide grievance redressal mechanism",
                "source": "Code on Social Security 2020",
                "section": "Section 109",
                "retrieved_text": "The Central Government shall formulate suitable social security schemes for gig workers."
            }
        ],
        "clarifying_question": None,
        "reasoning": "Multiple clear violations found with direct citations."
    }
}

INSUFFICIENT_CASE_STATE = {
    "parsed_data": {
        "platform": "Swiggy",
        "event_type": "OTHER",
        "date": None,
        "reason": "Worker unhappy with assigned delivery zone",
        "worker_id": None,
        "earnings_withheld": None,
        "notice_provided": None,
        "appeal_offered": None
    },
    "legal_analysis": {
        "case_strength": "INSUFFICIENT_BASIS",
        "confidence": 0.85,
        "violations": [],
        "clarifying_question": None,
        "reasoning": "No relevant law found for zone assignment complaints."
    }
}


class TestDrafterLive(unittest.TestCase):
    """Live API stress tests — 3 scenarios from Phase 5 spec."""

    def setUp(self):
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("GROQ_API_KEY"):
            self.skipTest("No API key set (need Anthropic or Groq).")

    # ── Test 1: STRONG Case → Full Formal Letter ──────
    def test_1_strong_case_full_letter(self):
        """STRONG case → formal letter with citations from violations."""
        result = drafter_node(STRONG_CASE_STATE)
        letter = result.get("grievance_letter", {})

        # Must have all required keys
        self.assertIn("english_letter", letter)
        self.assertIn("hindi_letter", letter)
        self.assertIn("demands", letter)
        self.assertIn("escalation_warning", letter)
        self.assertIn("disclaimer", letter)

        eng = letter["english_letter"]

        # Must cite the laws from violations, not from model memory
        self.assertIn("Code on Social Security 2020", eng)
        self.assertIn("Karnataka Platform-based Gig Workers Act 2025", eng)

        # Must have the grievance notice header
        self.assertIn("GRIEVANCE", eng.upper())

        # Must mention 15 day deadline
        self.assertIn("15", eng)

        # Hindi letter must not be empty
        self.assertTrue(len(letter["hindi_letter"]) > 100,
                        "Hindi letter seems too short — may not be a full translation")

    # ── Test 2: INSUFFICIENT_BASIS → Honest Limited Letter ──
    def test_2_insufficient_basis_honest_letter(self):
        """INSUFFICIENT_BASIS → no legal citations, honest factual account."""
        result = drafter_node(INSUFFICIENT_CASE_STATE)
        letter = result.get("grievance_letter", {})

        eng = letter["english_letter"]

        # Must NOT cite any laws since there are no violations
        self.assertNotIn("Section 114", eng)
        self.assertNotIn("Section 109", eng)
        self.assertNotIn("Section 12", eng)

        # Should document the incident factually
        self.assertIn("Swiggy", eng)

    # ── Test 3: Disclaimer Appears in Every Output ────
    def test_3_disclaimer_always_present(self):
        """Disclaimer must be the hardcoded MANDATORY_DISCLAIMER in all outputs."""
        # Test with STRONG case
        result1 = drafter_node(STRONG_CASE_STATE)
        letter1 = result1.get("grievance_letter", {})
        self.assertEqual(letter1["disclaimer"], MANDATORY_DISCLAIMER)

        # Test with INSUFFICIENT case
        result2 = drafter_node(INSUFFICIENT_CASE_STATE)
        letter2 = result2.get("grievance_letter", {})
        self.assertEqual(letter2["disclaimer"], MANDATORY_DISCLAIMER)


if __name__ == '__main__':
    unittest.main()