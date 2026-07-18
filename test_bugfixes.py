import unittest
from unittest.mock import patch
import os
import sys

# Ensure the app's root directory is in the system path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.command_processor import CommandProcessor, ProcessOptions


class TestConversationBugs(unittest.TestCase):

    @patch('services.command_processor.Brain')
    def test_bug_1_context_loss_on_follow_up(self, MockBrain):
        """
        Verifies Bug #1 fix.
        Flow:
        1. "What is Python?" (Establishes 'Python' as topic)
        2. "Who invented it?" (Should resolve 'it' to 'Python')
        Assert: The Brain is queried about 'Python', not 'it'.
        """
        # Arrange: Instantiate the CommandProcessor and mock the brain's think method
        processor = CommandProcessor()
        mock_brain_instance = processor._brain
        mock_brain_instance.think.return_value = "A mocked response."

        # Act: Simulate the conversation
        # First turn to establish context
        processor.process("What is Python?", options=ProcessOptions.for_cli())

        # Second turn with the pronoun
        processor.process("Who invented it?", options=ProcessOptions.for_cli())

        # Assert: Check what the brain was asked to think about
        self.assertTrue(mock_brain_instance.think.called, "The brain's think method was not called.")
        
        # The input to think() might be a formatted prompt, so we check for substrings.
        last_call_args = mock_brain_instance.think.call_args
        brain_input_text = last_call_args[0][0]

        # The core of the test: was the context carried over?
        self.assertIn("Python", brain_input_text, "The word 'Python' was not in the input to the brain.")
        self.assertNotIn(" it ", f" {brain_input_text} ", "The unresolved pronoun 'it' was found in the input to the brain.")

    @patch('services.command_processor.Brain')
    def test_bug_2_pronoun_resolution_for_assistant_reply(self, MockBrain):
        """
        Verifies Bug #2 fix.
        Flow:
        1. User asks a question.
        2. Assistant's reply contains a person's name ('Guido van Rossum').
        3. User asks a follow-up: "When was he born?".
        Assert: The Brain is queried about 'Guido van Rossum', not 'he'.
        """
        # Arrange
        processor = CommandProcessor()
        mock_brain_instance = processor._brain
        # The first call to think will establish the context.
        mock_brain_instance.think.return_value = "Guido van Rossum is the inventor."

        # Act
        # First turn: user asks, assistant replies, context is stored.
        processor.process("Who invented Python?", options=ProcessOptions.for_cli())

        # Second turn: user asks follow-up question with a pronoun.
        processor.process("When was he born?", options=ProcessOptions.for_cli())

        # Assert
        self.assertEqual(mock_brain_instance.think.call_count, 2, "Brain was not called twice.")
        
        last_call_args = mock_brain_instance.think.call_args
        brain_input_text = last_call_args[0][0]

        self.assertIn("Guido van Rossum", brain_input_text, "The name 'Guido van Rossum' was not in the input to the brain.")
        self.assertNotIn(" he ", f" {brain_input_text} ", "The unresolved pronoun 'he' was found in the input to the brain.")

    @patch('services.command_processor.Router')
    @patch('services.command_processor.Brain')
    def test_bug_3_affirm_follow_up_to_question(self, MockBrain, MockRouter):
        """
        Verifies Bug #3 fix.
        Flow:
        1. Assistant asks a question.
        2. User replies "Yes".
        Assert: The Brain is queried with a synthesized command containing context.
        """
        # Arrange
        # We need to mock the router to simulate it returning an 'affirm' intent.
        mock_router_instance = MockRouter.return_value
        mock_router_instance.route.return_value = {"intent": "affirm"}
        
        processor = CommandProcessor(router=mock_router_instance)
        mock_brain_instance = processor._brain
        
        # Manually add a turn to history to simulate the assistant asking a question.
        assistant_question = "Would you like to know more?"
        processor._memory_service.add_conversation_turn(user="Some previous query", assistant=assistant_question)

        # Act
        processor.process("Yes", options=ProcessOptions.for_cli())

        # Assert
        self.assertTrue(mock_brain_instance.think.called, "Brain was not called.")
        last_call_args = mock_brain_instance.think.call_args
        brain_input_text = last_call_args[0][0]

        # Check that the synthesized prompt was sent to the brain
        self.assertIn("replied 'Yes'", brain_input_text)
        self.assertIn(assistant_question, brain_input_text)
        self.assertIn("Please respond appropriately", brain_input_text, "The synthesized command should contain the expected instruction.")





if __name__ == '__main__':
    # Adding a bit more structure to the test runner
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestConversationBugs))
    runner = unittest.TextTestRunner()
    print("Running Conversation Bug Fix Tests...")
    result = runner.run(suite)
    if result.wasSuccessful():
        print("All tests passed successfully.")
    else:
        print("Some tests failed.")
