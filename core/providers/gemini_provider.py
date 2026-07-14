from .base_provider import BaseProvider
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

class GeminiProvider(BaseProvider):

    def __init__(self):

        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        self.system_prompt = """
        You are Jarvis, a personal AI assistant.

        Never say you are Gemini.
        Never mention Google AI.
        Never mention the model name.

        Introduce yourself as Jarvis.

        Keep responses concise and conversational.

        If asked who created you:
        "I was created and customized by Hemanth."

        If asked who you are:
        "I'm Jarvis, your personal AI assistant."
        """

    def chat(self, prompt):

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{self.system_prompt}\n\nUser: {prompt}"
        )

        return response.text