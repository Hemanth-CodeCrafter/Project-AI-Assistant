from core.providers.ollama_provider import OllamaProvider
from core.internet import is_connected
from core.providers.gemini_provider import GeminiProvider
from core.providers.groq_provider import GroqProvider
from core.providers.openrouter_provider import OpenRouterProvider

class ProviderManager:

    def __init__(self):
        self.providers = {
            "gemini": GeminiProvider(),
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider(),
            "ollama": OllamaProvider()
        }

        self.current_provider = "gemini"

    def think(self, prompt):

        # No internet
        if not is_connected():
            self.current_provider = "ollama"

            return self.providers[
                "ollama"
            ].chat(prompt)

        # Internet available
        try:
            self.current_provider = "gemini"

            return self.providers[
                "gemini"
            ].chat(prompt)

        except Exception as e:
            print(f"Gemini failed: {e}")

        try:
            self.current_provider = "groq"

            return self.providers[
                "groq"
            ].chat(prompt)

        except Exception as e:
            print(f"Groq failed: {e}")

        # Final fallback
        self.current_provider = "ollama"

        return self.providers[
            "ollama"
        ].chat(prompt)
    
    def switch_provider(self, provider_name):

        provider_name = provider_name.lower()

        if provider_name in self.providers:
            self.current_provider = provider_name

            return (
                f"Switched to {provider_name}"
            )

        return (
            f"Provider {provider_name} not found"
        )

    def get_provider(self):
        return self.current_provider