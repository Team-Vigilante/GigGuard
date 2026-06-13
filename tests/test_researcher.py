"""
Phase 5: Legal Researcher Stress Tests
========================================
Tests researcher_node() with 5 required case scenarios.

TWO TEST LAYERS:
  - TestResearcherStructure: Offline tests (no API needed)
  - TestResearcherLive: Live API tests (requires ANTHROPIC_API_KEY + ChromaDB populated)

Run offline tests:   python3 -m unittest tests.test_researcher.TestResearcherStructure -v
Run live tests:      python3 -m unittest tests.test_researcher.TestResearcherLive -v
Run all:             python3 -m unittest tests.test_researcher -v
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.researcher_node import researcher_node, GROUNDING_PROMPT
from agents.chromadb_query import build_case_facts_string


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OFFLINE TESTS — no API key needed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestResearcherStructure(unittest.TestCase):
    """Verify grounding prompt and code structure are correct."""

    def test_grounding_prompt_has_all_7_rules(self):
        """Person 4's grounding prompt must contain all 7 strict rules."""
        for i in range(1, 8):
            self.assertIn(f"{i}.", GROUNDING_PROMPT,
                          f"Missing grounding rule #{i}")

    def test_grounding_prompt_forbids_fabrication(self):
        """Grounding prompt must explicitly forbid fabrication."""
        self.assertIn("NEVER fabricate", GROUNDING_PROMPT)
        self.assertIn("INSUFFICIENT_LEGAL_BASIS", GROUNDING_PROMPT)

    def test_grounding_prompt_requires_three_part_citation(self):
        """Every citation must include source, section, and retrieved text."""
        self.assertIn("Source name", GROUNDING_PROMPT)
        self.assertIn("Section number", GROUNDING_PROMPT)
        self.assertIn("exact retrieved text", GROUNDING_PROMPT)

    def test_grounding_prompt_has_case_strength_definitions(self):
        """All 4 case strength levels must be defined."""
        for strength in ["STRONG", "MODERATE", "WEAK", "INSUFFICIENT_BASIS"]:
            self.assertIn(strength, GROUNDING_PROMPT)

    def test_grounding_prompt_has_confidence_threshold(self):
        """Confidence < 0.6 should trigger clarifying question."""
        self.assertIn("0.6", GROUNDING_PROMPT)
        self.assertIn("clarifying_question", GROUNDING_PROMPT)

    def test_build_case_facts_string(self):
        """build_case_facts_string should produce a readable string."""
        parsed = {
            "platform": "Swiggy",
            "event_type": "ACCOUNT_DEACTIVATION",
            "notice_provided": False,
            "appeal_offered": False,
            "earnings_withheld": 3200,
            "reason": "NO_REASON_PROVIDED"
        }
        result = build_case_facts_string(parsed)
        self.assertIn("Swiggy", result)
        self.assertIn("no notice provided", result)
        self.assertIn("3200", result)

    def test_researcher_node_handles_empty_state(self):
        """researcher_node with empty parsed_data should not crash."""
        # This will fail at the API call but should not crash before that
        # We test the pre-API logic only
        state = {"parsed_data": {}}
        case_facts = build_case_facts_string(state["parsed_data"])
        self.assertEqual(case_facts, "")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LIVE API TESTS — requires ANTHROPIC_API_KEY + ChromaDB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 5 test cases from Phase 5 spec
TEST_CASES = {
    "strong_case": {
        "platform": "Swiggy",
        "event_type": "ACCOUNT_DEACTIVATION",
        "notice_provided": False,
        "appeal_offered": False,
        "earnings_withheld": 5000,
        "reason": "NO_REASON_PROVIDED"
    },
    "weak_case": {
        "platform": "Zomato",
        "event_type": "ACCOUNT_DEACTIVATION",
        "notice_provided": True,
        "appeal_offered": True,
        "earnings_withheld": None,
        "reason": "Worker admitted to using multiple accounts which violates platform policy"
    },
    "ambiguous_case": {
        "platform": "Ola",
        "event_type": "UNFAIR_DEDUCTION",
        "notice_provided": None,
        "appeal_offered": None,
        "earnings_withheld": 1500,
        "reason": "Pay reduced but no clear reason given by platform"
    },
    "no_legal_basis": {
        "platform": "Swiggy",
        "event_type": "OTHER",
        "notice_provided": None,
        "appeal_offered": None,
        "earnings_withheld": None,
        "reason": "Worker unhappy with assigned delivery zone"
    },
    "hallucination_trap": {
        "platform": "Blinkit",
        "event_type": "ACCOUNT_DEACTIVATION",
        "notice_provided": False,
        "appeal_offered": False,
        "earnings_withheld": 8000,
        "reason": "Violated the fictitious Gig Workers Protection Act 2019 Section 42"
    }
}


class TestResearcherLive(unittest.TestCase):
    """Live API stress tests — 5 scenarios from Phase 5 spec."""

    def setUp(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY is not set.")

    def _run_researcher(self, parsed_data: dict) -> dict:
        """Helper to run researcher_node and return legal_analysis."""
        state = {"parsed_data": parsed_data}
        result = researcher_node(state)
        return result.get("legal_analysis", {})

    # ── Test 1: Strong Case ────────────────────────────
    def test_1_strong_case_deactivation_no_warnings(self):
        """Strong case → should find violations, STRONG or MODERATE strength."""
        analysis = self._run_researcher(TEST_CASES["strong_case"])

        self.assertIn(analysis["case_strength"], ["STRONG", "MODERATE"])
        self.assertGreater(len(analysis["violations"]), 0)
        # Every violation must have retrieved_text (grounding proof)
        for v in analysis["violations"]:
            self.assertIn("retrieved_text", v)
            self.assertTrue(len(v["retrieved_text"]) > 0,
                            "retrieved_text must not be empty")

    # ── Test 2: Weak Case ──────────────────────────────
    def test_2_weak_case_worker_admitted_violation(self):
        """Weak case → WEAK or INSUFFICIENT_BASIS, fewer violations."""
        analysis = self._run_researcher(TEST_CASES["weak_case"])

        self.assertIn(analysis["case_strength"],
                      ["WEAK", "INSUFFICIENT_BASIS"])

    # ── Test 3: Ambiguous Case ─────────────────────────
    def test_3_ambiguous_case_pay_reduced(self):
        """Ambiguous case → should NOT be STRONG."""
        analysis = self._run_researcher(TEST_CASES["ambiguous_case"])

        self.assertNotEqual(analysis["case_strength"], "STRONG")

    # ── Test 4: No Legal Basis ─────────────────────────
    def test_4_no_legal_basis_zone_assignment(self):
        """No legal basis → INSUFFICIENT_BASIS or WEAK, no violations."""
        analysis = self._run_researcher(TEST_CASES["no_legal_basis"])

        self.assertIn(analysis["case_strength"],
                      ["INSUFFICIENT_BASIS", "WEAK"])

    # ── Test 5: CRITICAL Anti-Hallucination ────────────
    def test_5_must_not_cite_law_not_in_chromadb(self):
        """
        CRITICAL TEST: Worker mentions a FICTITIOUS law.
        The model MUST NOT confirm or cite it.
        Must return INSUFFICIENT_BASIS or ignore the fake law entirely.
        """
        analysis = self._run_researcher(TEST_CASES["hallucination_trap"])

        # The fictitious "Gig Workers Protection Act 2019" must NOT
        # appear in any violation citation
        for v in analysis.get("violations", []):
            source = v.get("source", "")
            self.assertNotIn("Gig Workers Protection Act 2019", source,
                             "HALLUCINATION DETECTED: Model cited a fake law!")
            self.assertNotIn("Section 42", v.get("section", ""),
                             "HALLUCINATION DETECTED: Model cited a fake section!")


if __name__ == '__main__':
    unittest.main()
