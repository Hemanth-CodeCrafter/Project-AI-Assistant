from core.provider_manager import ProviderManager
from dotenv import load_dotenv

load_dotenv()

brain = ProviderManager()

print(brain.get_provider())

print(
    brain.switch_provider("gemini")
)

print(brain.get_provider())

print(
    brain.think("Who created you?")
)