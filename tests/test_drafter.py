import unittest
import json
import sys
import os

# Ensure the agents module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.drafter_node import drafter_node, MANDATORY_DISCLAIMER

class TestDrafterNode(unittest.TestCase):
    
    def setUp(self):
        # We need an Anthropic API key to run these tests. 
        # If it's not set, the tests will fail at the API call.
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY is not set.")

    def test_strong_case(self):
        state = {
            "parsed_data": {
                "worker_id": "W123",
                "platform": "Swiggy",
                "event_type": "Deactivation",
                "reason": "Unknown",
                "earnings_withheld": "5000 INR"
            },
            "legal_analysis": {
                "violations": [
                    {
                        "law": "Code on Social Security 2020",
                        "section": "Section 109",
                        "violation_description": "Failure to provide social security benefits and arbitrary deactivation."
                    }
                ],
                "case_strength": "STRONG",
                "confidence": 0.9,
                "worker_message": "You have a strong case for arbitrary deactivation."
            }
        }
        
        result = drafter_node(state)
        letter = result.get("grievance_letter", {})
        
        # Verify JSON keys
        self.assertIn("english_letter", letter)
        self.assertIn("hindi_letter", letter)
        self.assertIn("demands", letter)
        self.assertIn("disclaimer", letter)
        
        # Verify Disclaimer
        self.assertEqual(letter["disclaimer"], MANDATORY_DISCLAIMER)
        
        # Verify Citations are included
        self.assertIn("Code on Social Security 2020", letter["english_letter"])
        
    def test_insufficient_basis_case(self):
        state = {
            "parsed_data": {
                "worker_id": "W456",
                "platform": "Zomato",
                "event_type": "Zone Change",
                "reason": "Worker unhappy with new delivery zone"
            },
            "legal_analysis": {
                "violations": [],
                "case_strength": "INSUFFICIENT_BASIS",
                "confidence": 0.8,
                "worker_message": "We cannot find a legal violation for a zone change."
            }
        }
        
        result = drafter_node(state)
        letter = result.get("grievance_letter", {})
        
        # Should not contain any legal claims or laws (unless explicitly mentioned in facts, which is not the case here)
        self.assertNotIn("Code on Social Security", letter["english_letter"])
        self.assertNotIn("Section", letter["english_letter"])
        
        # Verify Disclaimer is still present
        self.assertEqual(letter["disclaimer"], MANDATORY_DISCLAIMER)

if __name__ == '__main__':
    unittest.main()