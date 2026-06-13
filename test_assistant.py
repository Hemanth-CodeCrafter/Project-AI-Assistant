from core.router import Router
from core.search import Search

router = Router()
search = Search()

print("Jarvis Ready.")

while True:

    user_input = input("\nYou: ")

    if user_input.lower() == "exit":
        break

    # Try action first
    result = router.route(user_input)

    # If no action found, use AI
    if result is None:

        result = search.search(user_input)

    print("\nJarvis:")
    print(result)