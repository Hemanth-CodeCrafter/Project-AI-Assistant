"""
Text-to-Speech (TTS) service for Jarvis.

Encapsulates pyttsx3 usage with consistent voice settings.

This module creates a fresh pyttsx3 engine for each speak() call,
ensuring reliable speech output across multiple interactions.
Configuration is applied consistently every time.
"""

import pyttsx3
from typing import Optional


class TextToSpeech:
    """
    TTS engine wrapper that speaks text with consistent voice settings.

    Configuration:
    - Rate: 165 words per minute (slightly faster for clarity)
    - Voice: Second voice if available (typically female), else first voice
    - Volume: 1.0 (maximum)

    A fresh engine is created for each speak() call to ensure reliability.
    pyttsx3 works better on Windows when engines are created per-use rather
    than reused, despite being slightly less efficient.
    """

    @staticmethod
    def _get_configured_engine() -> pyttsx3.Engine:
        """
        Create and configure a fresh pyttsx3 engine.

        Returns:
            pyttsx3.Engine: Engine with Jarvis voice preferences applied.
        """
        engine = pyttsx3.init()
        
        # Set speaking rate (words per minute)
        engine.setProperty("rate", 165)
        
        # Select voice: prefer voice index 1 (typically female), fall back to 0
        voices = engine.getProperty("voices")
        voice_id = voices[1].id if len(voices) > 1 else voices[0].id
        engine.setProperty("voice", voice_id)
        
        # Set volume (0.0 to 1.0)
        engine.setProperty("volume", 1.0)
        
        return engine

    @staticmethod
    def speak(text: str) -> None:
        """
        Speak the given text using a configured pyttsx3 engine.

        Behavior:
        - If text is empty, does nothing
        - Strips '__LLM__:' prefix (for robustness)
        - Prints to console with Jarvis emoji
        - Plays audio (blocks until speech finishes)

        Args:
            text: The text to speak.
        """
        if not text:
            return

        # Normalize text
        text_str = str(text).replace("__LLM__:", "").strip()

        if not text_str:
            return

        # Print to console
        print(f"\n🤖 Jarvis: {text_str}")

        # Create fresh engine for this utterance
        engine = TextToSpeech._get_configured_engine()
        
        # Play speech
        engine.say(text_str)
        engine.runAndWait()
        engine.stop()


# Module-level convenience function for easier imports
def speak(text: str) -> None:
    """
    Speak text using the Jarvis TTS service.

    This is a convenience function that creates a configured pyttsx3 engine
    and speaks the provided text.

    Args:
        text: The text to speak.

    Example:
        from core.tts import speak
        speak("Hello, world!")
    """
    TextToSpeech.speak(text)
