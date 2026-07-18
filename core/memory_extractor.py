from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class MemoryExtraction:
    """Structured result of memory extraction for a user message."""

    should_remember: bool
    category: str
    importance: int
    memory_text: str
    reason: str


class MemoryExtractor:
    """Rule-based memory extraction engine for deterministic memory decisions."""

    CATEGORY_PATTERNS = {
        "Identity": [
            r"\bmy name is\b",
            r"\bi am\b",
            r"\bi'm\b",
            r"\bmy birthday\b",
            r"\bmy age\b",
        ],
        "Preference": [
            r"\bi like\b",
            r"\bi love\b",
            r"\bi prefer\b",
            r"\bmy favorite\b",
            r"\bmy favourite\b",
            r"\bi hate\b",
        ],
        "Project": [
            r"\bi am building\b",
            r"\bi'm building\b",
            r"\bi am working on\b",
            r"\bmy project\b",
        ],
        "Education": [
            r"\bstudying\b",
            r"\bstudent\b",
            r"\bschool\b",
            r"\bcollege\b",
            r"\buniversity\b",
        ],
        "Career": [
            r"\bwork at\b",
            r"\bmy job\b",
            r"\bmy company\b",
            r"\bcareer\b",
        ],
        "Device": [
            r"\bmy laptop\b",
            r"\bmy phone\b",
            r"\bmy computer\b",
            r"\bmy device\b",
            r"\busing\s+\w+",
        ],
        "Location": [
            r"\bi live in\b",
            r"\bi live at\b",
            r"\bmy home\b",
            r"\bmy office\b",
        ],
        "Relationship": [
            r"\bmy mother\b",
            r"\bmy father\b",
            r"\bmy friend\b",
            r"\bmy brother\b",
            r"\bmy sister\b",
            r"\bmy partner\b",
        ],
        "Routine": [
            r"\bi usually\b",
            r"\bi always\b",
            r"\bi often\b",
            r"\bmy routine\b",
        ],
        "Goal": [
            r"\bi want to\b",
            r"\bmy goal\b",
            r"\bi plan\b",
            r"\bi am preparing\b",
        ],
        "Skill": [
            r"\bi know\b",
            r"\bi can\b",
            r"\bskilled in\b",
            r"\blearned\b",
            r"\bpractice\b",
        ],
        "Contact": [
            r"\bmy contact\b",
            r"\bphone number\b",
            r"\bemail address\b",
        ],
    }

    def extract(self, text: str) -> MemoryExtraction:
        """Analyze a message and decide whether it should be remembered."""
        normalized = (text or "").strip()
        lowered = normalized.lower()

        if not normalized:
            return MemoryExtraction(False, "Other", 0, "", "Empty input")

        category = self._detect_category(lowered)
        importance = self._detect_importance(lowered, category)
        should_remember = importance >= 7 or category in {"Identity", "Goal", "Project", "Relationship"}

        memory_text = normalized
        reason = self._build_reason(category, importance, should_remember)

        return MemoryExtraction(
            should_remember=should_remember,
            category=category,
            importance=importance,
            memory_text=memory_text,
            reason=reason,
        )

    def _detect_category(self, text: str) -> str:
        for category, patterns in self.CATEGORY_PATTERNS.items():
            if any(re.search(pattern, text) for pattern in patterns):
                return category
        return "Other"

    def _detect_importance(self, text: str, category: str) -> int:
        if category in {"Identity", "Relationship", "Goal", "Project"}:
            return 9
        if category in {"Preference", "Career", "Education", "Skill", "Location"}:
            return 7
        if category in {"Device", "Routine", "Contact"}:
            return 5
        return 3

    def _build_reason(self, category: str, importance: int, should_remember: bool) -> str:
        if not should_remember:
            return f"Low-value message; category={category}, importance={importance}"
        return f"High-value personal information; category={category}, importance={importance}"