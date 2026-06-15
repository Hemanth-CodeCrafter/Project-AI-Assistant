# test_intents.py

from core.intent_classifier import classify

while True:
    text = input("> ")

    intent, query, ents = classify(text)

    print()
    print("Intent:", intent)
    print("Query :", query)
    print("Entities:", ents)
    print()