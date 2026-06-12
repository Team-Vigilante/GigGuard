import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Assuming you will later wrap the PARSER_SYSTEM_PROMPT into a node function like parser_node
# For now, we'll just mock the structure or leave placeholders for the tests.

class TestParserNode(unittest.TestCase):
    def setUp(self):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.skipTest("ANTHROPIC_API_KEY is not set.")
            
    # PHASE 5 REQUIREMENTS:
    # Test Parser prompt with 5 inputs:
    
    def test_clean_english_description(self):
        # 1. Clean English screenshot description
        pass

    def test_hindi_text_message(self):
        # 2. Hindi text message only (no screenshot)
        pass

    def test_mixed_hindi_english_message(self):
        # 3. Mixed Hindi-English message
        pass

    def test_blurry_incomplete_screenshot(self):
        # 4. Blurry/incomplete screenshot description
        pass

    def test_irrelevant_message(self):
        # 5. Completely irrelevant message (not a complaint)
        pass

if __name__ == '__main__':
    unittest.main()