from __future__ import annotations

import re
from typing import Any, Optional


class MemoryRanker:
    """Deterministic ranking for memory retrieval candidates."""

    def __init__(self) -> None:
        self._category_priority = {
            "location": 8,
            "preference": 7,
            "device": 6,
            "identity": 6,
            "goal": 6,
            "project": 5,
            "relationship": 5,
            "career": 4,
            "education": 4,
            "skill": 4,
            "routine": 3,
            "contact": 3,
            "other": 1,
        }

    def rank(self, query: str, memories: list[tuple[Any, ...]]) -> Optional[tuple[Any, ...]]:
        """Return the single best memory candidate or None."""
        if not query or not memories:
            return None

        normalized_query = self._normalize(query)
        ranked = []

        for memory in memories:
            text, category, importance = memory
            score = self._score(normalized_query, text, category, importance)
            ranked.append((score, memory))

        ranked.sort(key=lambda item: (-item[0], item[1][0]))
        if not ranked:
            return None

        return ranked[0][1] if ranked[0][0] > 0 else None

    def _score(self, query: str, memory_text: str, category: str, importance: int) -> int:
        text = self._normalize(memory_text)
        category_key = (category or "other").lower()
        score = 0

        score += self._category_match_score(query, category_key)
        score += self._intent_match_score(query, text)
        score += self._keyword_match_score(query, text)
        score += self._priority_bonus(category_key)
        score += self._importance_bonus(importance)

        return score

    def _category_match_score(self, query: str, category: str) -> int:
        if category in {"location", "preference", "device", "identity"}:
            if any(token in query for token in ["where", "favorite", "language", "name", "laptop", "phone", "computer"]):
                return 3
        if category in {"career", "education"} and any(token in query for token in ["work", "job", "graduate", "study"]):
            return 2
        return 0

    def _intent_match_score(self, query: str, memory_text: str) -> int:
        if not query:
            return 0

        if any(token in query for token in ["favorite", "like", "love", "prefer"]) and any(token in memory_text for token in ["like", "love", "favorite", "prefer"]):
            return 3
        if any(token in query for token in ["where", "live", "home", "located"]) and any(token in memory_text for token in ["live", "home", "location", "located"]):
            return 3
        if any(token in query for token in ["laptop", "phone", "computer", "device"]) and any(token in memory_text for token in ["laptop", "phone", "computer", "device"]):
            return 3
        if any(token in query for token in ["graduate", "graduated", "study", "school"]) and any(token in memory_text for token in ["graduate", "graduated", "study", "school", "college", "university"]):
            return 3
        return 0

    def _keyword_match_score(self, query: str, memory_text: str) -> int:
        query_words = set(re.findall(r"\w+", query.lower()))
        memory_words = set(re.findall(r"\w+", memory_text.lower()))
        overlap = query_words & memory_words
        if not overlap:
            return 0
        return min(3, len(overlap))

    def _priority_bonus(self, category: str) -> int:
        return self._category_priority.get(category, 1)

    def _importance_bonus(self, importance: int) -> int:
        if importance >= 8:
            return 3
        if importance >= 5:
            return 2
        return 1

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip().lower())
