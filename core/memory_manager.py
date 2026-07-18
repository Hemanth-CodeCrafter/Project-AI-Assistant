import re
from typing import Any

from core.memory_db import MemoryDB
from core.memory_record import MemoryRecord


class MemoryManager:
    def __init__(self, db: MemoryDB):
        self._db = db

    def should_remember(self, text):

        text = text.lower()

        score = 0
        category = "general"

        personal = [
            "my name",
            "i am",
            "i'm",
            "i live",
            "my birthday",
            "my age"
        ]

        preferences = [
            "i like",
            "i love",
            "i prefer",
            "my favorite",
            "my favourite",
            "i hate"
        ]

        goals = [
            "i want to",
            "my goal",
            "i plan",
            "i am preparing"
        ]

        projects = [
            "i am building",
            "i'm building",
            "i am working on",
            "my project"
        ]

        relationships = [
            "my mother",
            "my father",
            "my friend",
            "my brother",
            "my sister"
        ]

        if any(x in text for x in personal):
            score = 10
            category = "personal"

        elif any(x in text for x in preferences):
            score = 8
            category = "preference"

        elif any(x in text for x in goals):
            score = 8
            category = "goal"

        elif any(x in text for x in projects):
            score = 8
            category = "project"

        elif any(x in text for x in relationships):
            score = 8
            category = "relationship"

        return score, category

    def remember(self, text):

        score, category = self.should_remember(text)

        if score >= 7:

            self._db.save(
                memory=MemoryRecord.from_legacy(
                    text=text,
                    category=category,
                    importance=score,
                ),
                category=category,
                importance=score,
            )

            print(
                f"[Memory Saved] ({category}) {text}"
            )

            return True

        return False

    def search(self, query):

        words = re.findall(
            r"\w+",
            query.lower()
        )

        results = []

        for word in words:

            if len(word) < 3:
                continue

            results.extend(
                self._db.search(word)
            )

        unique = []

        seen = set()

        for r in results:

            if r[0] not in seen:

                unique.append(r)

                seen.add(r[0])

        return unique

    def forget(self, memory):

        self._db.delete(memory)

    def all(self):

        return self._db.get_all()