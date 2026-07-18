import unittest
from unittest.mock import patch
import os
import sys
import threading
import time
from fastapi.testclient import TestClient

# Ensure the app's root directory is in the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app

class TestApiConcurrency(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.responses = {}

    def user1_request(self):
        """User 1 asks the initial question to establish context."""
        response = self.client.post("/command", json={"text": "Who is the CEO of Microsoft?"})
        self.responses['user1'] = response.json()

    def user2_request(self):
        """User 2 asks a follow-up question that would require context."""
        time.sleep(0.1) # Stagger the request slightly
        response = self.client.post("/command", json={"text": "How old is he?"})
        self.responses['user2'] = response.json()

    @patch('core.brain.Brain.think')
    def test_concurrent_requests_do_not_share_context(self, mock_think):
        """
        Tests that two concurrent users do not share conversation context.
        - User 1 establishes a context ("Who is the CEO of Microsoft?").
        - User 2 asks a pronoun-based follow-up ("How old is he?").
        - Verifies that User 2's response does not use context from User 1.
        """
        # --- Arrange ---
        # Define the mocked brain responses
        def side_effect(prompt):
            if "Microsoft" in prompt and "CEO" in prompt:
                # User 1's prompt will be enriched with memories/context, but this is the core part
                return "Satya Nadella is the CEO of Microsoft."
            elif "he" in prompt.lower() and "old" in prompt.lower():
                # This is the key check. If context leaked, the prompt would be resolved to "How old is Satya Nadella?".
                # We want to ensure the brain receives the raw, unresolved "How old is he?".
                if "Satya Nadella" in prompt:
                     # This should NOT happen. We fail the test if context leaks.
                    return "Context leaked! The prompt was resolved."
                else:
                    # This is the expected outcome for the isolated User 2.
                    return "I'm not sure who 'he' is. Could you please provide more context?"
            else:
                return "An unexpected prompt was received."
        
        mock_think.side_effect = side_effect

        # --- Act ---
        thread1 = threading.Thread(target=self.user1_request)
        thread2 = threading.Thread(target=self.user2_request)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # --- Assert ---
        # Check User 1's response is correct
        user1_response = self.responses.get('user1', {})
        self.assertEqual(user1_response.get('source'), 'brain')
        self.assertIn("Satya Nadella", user1_response.get('text', ''))

        # Check User 2's response to ensure context did NOT leak
        user2_response = self.responses.get('user2', {})
        self.assertEqual(user2_response.get('source'), 'brain')
        self.assertNotIn("Satya Nadella", user2_response.get('text', ''), "User 2's response should not contain info from User 1's context.")
        self.assertIn("not sure who 'he' is", user2_response.get('text', ''), "User 2 should have received a response indicating a lack of context.")

        # Verify the brain was called for both requests
        self.assertEqual(mock_think.call_count, 2)

        # Optional: More detailed check on the prompts sent to the brain
        calls = mock_think.call_args_list
        user1_prompt = calls[0][0][0]
        user2_prompt = calls[1][0][0]
        
        self.assertIn("Microsoft", user1_prompt)
        self.assertNotIn("Satya Nadella", user2_prompt, "The raw prompt to the brain for user 2 should not have been resolved.")

if __name__ == '__main__':
    unittest.main()
