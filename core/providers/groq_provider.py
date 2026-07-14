from .base_provider import BaseProvider
from groq import Groq
import os

class GroqProvider(BaseProvider):

    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

    def chat(self, prompt):

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content":
                    "You are Jarvis, a personal AI assistant. "
                    "Never mention Groq or Llama. "
                    "Introduce yourself as Jarvis."
                    "Keep responses concise and conversational."
                    "If asked who created you:"
                    "I was created and customized by Hemanth."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content