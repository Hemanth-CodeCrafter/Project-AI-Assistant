from core.provider_manager import ProviderManager

manager = ProviderManager()

class Brain:
    def __init__(self):
        self.manager = ProviderManager()

    def think(self, prompt):
        return manager.think(prompt)
