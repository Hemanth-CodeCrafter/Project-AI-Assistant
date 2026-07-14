import re
from core.context_manager import context_manager

PRONOUNS = [
    "it",
    "that",
    "this",
    "them",
    "him",
    "her"
]


def resolve(command):
    print("Context:", context_manager.context)

    text = command.lower().strip()
    text = text.rstrip(".?!,")

    if not any(
        p in text.split()
        for p in PRONOUNS
    ):
        return command

    app = context_manager.get("app")
    print("Current app:", app)

    if not app:
        return text
     
    text = re.sub(r"\bit\b", app, text)
    text = re.sub(r"\bthis\b", app, text)
    text = re.sub(r"\bthat\b", app, text)
    print("After: ", text)
    return text