from __future__ import annotations

import re
from typing import Any, Optional


class MemoryRetrievalEngine:
    """Deterministic retrieval for personal-information questions."""

    def __init__(self, memory_db: Any) -> None:
        self._memory_db = memory_db
    
    def _format_response(self, memory: str) -> str:
        """
        Convert stored first-person memories into natural second-person replies.
        """

        memory = memory.strip()

        replacements = [
            ("My name is ", "Your name is "),
            ("my name is ", "Your name is "),
            ("I'm ", "You are "),
            ("i'm ", "You are "),
            ("I am ", "You are "),
            ("i am ", "You are "),
            ("I live in ", "You live in "),
            ("i live in ", "You live in "),
            ("I like ", "You like "),
            ("i like ", "You like "),
            ("I love ", "You love "),
            ("i love ", "You love "),
            ("My favourite ", "Your favourite "),
            ("My favorite ", "Your favorite "),
            ("my favourite ", "Your favourite "),
            ("my favorite ", "Your favorite "),
            ("I use ", "You use "),
            ("i use ", "You use "),
            ("I work at ", "You work at "),
            ("i work at ", "You work at "),
            ("I study at ", "You study at "),
            ("i study at ", "You study at "),
        ]

        for old, new in replacements:
            if memory.startswith(old):
                return new + memory[len(old):]

        return memory

    def retrieve(self, query: str) -> Optional[str]:
        """Return the best matching personal memory or None."""

        if not query or not query.strip():
            return None

        normalized = self._normalize(query)

        # Only answer PERSONAL questions from memory.
        if not self._is_personal_question(normalized):
            return None

        memories = self._memory_db.get_all()

        best_match = None
        best_score = -1

        for item in memories:
            text, category, importance = item

            score = self._score_match(
                normalized,
                text,
                category,
                importance,
            )

            if score > best_score:
                best_score = score
                best_match = item

        if best_score < 4:
            return None

        #return best_match[0] if best_match else None
        return self._format_response(best_match[0]) if best_match else None

    # def retrieve(self, query: str) -> Optional[str]:
    #     """Return the best matching memory text or None if no suitable match exists."""
    #     if not query or not str(query).strip():
    #         return None

    #     normalized = self._normalize(query)
    #     memories = self._memory_db.get_all()

    #     best_match: Optional[tuple[str, str, int]] = None
    #     best_score = -1

    #     for item in memories:
    #         text, category, importance = item
    #         score = self._score_match(normalized, text, category, importance)
    #         if score > best_score:
    #             best_score = score
    #             best_match = item

    #     if best_score < 3:
    #         return None

    #     return best_match[0] if best_match else None

    def _score_match(self, query: str, memory_text: str, category: str, importance: int) -> int:
        text = self._normalize(memory_text)
        if not text:
            return 0

        score = 0

        if self._contains_question(query):
            if self._is_personal_question(query):
                score += 2
            else:
                score -= 2

        if self._matches_category(query, category):
            score += 2

        if self._contains_keywords(query, text):
            score += 2

        if self._contains_related_terms(query, text):
            score += 1

        if importance >= 8:
            score += 2
        elif importance >= 5:
            score += 1

        return score

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    def _contains_question(self, query: str) -> bool:
        return any(token in query for token in ["what", "where", "when", "which", "who", "why", "how"])

    def _is_personal_question(self, query: str) -> bool:
        personal_patterns = [
            "my ",
            "me ",
            "mine",
            "myself",

            "what is my",
            "what's my",
            "who am i",
            "where do i",
            "where am i",
            "what do i",
            "which do i",
            "when did i",
            "where was i",
            "which is my",
        ]

        return any(pattern in query for pattern in personal_patterns)

    # def _is_personal_question(self, query: str) -> bool:
    #     personal_markers = [
    #         "my ",
    #         "i ",
    #         "me ",
    #         "mine",
    #         "myself",
    #     ]
    #     return any(marker in query for marker in personal_markers)

    def _matches_category(self, query: str, category: str) -> bool:
        category_map = {
            "personal": ["name", "age", "birthday", "live", "home", "location"],
            "preference": ["like", "love", "favorite", "prefer", "language", "music"],
            "goal": ["goal", "plan", "want"],
            "project": ["project", "building", "working"],
            "relationship": ["friend", "mother", "father", "sister", "brother"],
            "education": ["study", "school", "college", "graduate"],
            "career": ["job", "work", "company"],
            "device": ["laptop", "phone", "computer", "device"],
            "location": ["live", "home", "office", "where"],
            "routine": ["routine", "usually", "often"],
            "skill": ["know", "can", "skill"],
            "contact": ["contact", "phone", "email"],
        }
        lowered_query = self._normalize(query)
        if category.lower() not in category_map:
            return False
        return any(term in lowered_query for term in category_map[category.lower()])

    # def _contains_keywords(self, query: str, memory_text: str) -> bool:
    #     query_words = set(re.findall(r"\w+", self._normalize(query)))
    #     memory_words = set(re.findall(r"\w+", self._normalize(memory_text)))
    #     if not query_words or not memory_words:
    #         return False
    #     return bool(query_words & memory_words)

    def _contains_keywords(self, query: str, memory_text: str) -> bool:

        stop_words = {
            "what",
            "where",
            "when",
            "who",
            "which",
            "how",
            "is",
            "are",
            "do",
            "does",
            "did",
            "the",
            "a",
            "an",
            "my",
            "i",
            "me",
        }

        query_words = {
            w for w in re.findall(r"\w+", self._normalize(query))
            if w not in stop_words
        }

        memory_words = {
            w for w in re.findall(r"\w+", self._normalize(memory_text))
            if w not in stop_words
        }

        return bool(query_words & memory_words)

    def _contains_related_terms(self, query: str, memory_text: str) -> bool:
        related_map = {
            "name": ["called", "named"],
            "live": ["reside", "stay"],
            "favorite": ["like", "love", "prefer"],
            "graduate": ["graduated", "studied", "education"],
            "language": ["programming", "code"],
        }
        lowered_query = self._normalize(query)
        lowered_memory = self._normalize(memory_text)
        for key, terms in related_map.items():
            if key in lowered_query and any(term in lowered_memory for term in terms):
                return True
        return False
