class ContextManager:

    def __init__(self):
        self.context = {
            "app": None,
            "last_intent": None,
            "last_query": None,
            "last_device": None
        }

    def update(
        self,
        app=None,
        intent=None,
        query=None,
        device=None
    ):

        if app is not None:
            self.context["app"] = app

        if intent is not None:
            self.context["last_intent"] = intent

        if query is not None:
            self.context["last_query"] = query

        if device is not None:
            self.context["last_device"] = device

    def get(self, key):
        return self.context.get(key)

    def clear(self):
        self.context = {
            "app": None,
            "last_intent": None,
            "last_query": None,
            "last_device": None
        }

context_manager = ContextManager()