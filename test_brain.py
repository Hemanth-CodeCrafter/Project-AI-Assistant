from core.brain import Brain
import time

brain = Brain()

while True:

    question = input("\nYou: ")

    if question.lower() == "exit":
        break

    start = time.time()

    answer = brain.think(question)

    end = time.time()

    print(f"\nResponse Time: {end - start:.2f} seconds")

    print("\nJarvis:")
    print(answer)