import wikipedia


class Search:

    def search(self, query):

        try:

            result = wikipedia.summary(
                query,
                sentences=2
            )

            return result

        except Exception:

            return "I couldn't find information about that."