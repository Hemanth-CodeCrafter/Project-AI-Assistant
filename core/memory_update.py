from __future__ import annotations

import re
from typing import Any, Optional

from core.memory_record import MemoryRecord


class MemoryUpdateResolver:
    """Deterministic conflict resolution for memory updates."""

    def __init__(self, memory_db: Any) -> None:
        self._memory_db = memory_db

    def resolve(self, record: MemoryRecord) -> tuple[str, Optional[MemoryRecord]]:
        """Return action and existing record if an update candidate exists."""
        existing = self._find_candidate(record)
        if existing is None:
            return "CREATE", None

        if self._should_update(existing, record):
            return "UPDATE", existing

        return "IGNORE", existing

    def _find_candidate(self, record: MemoryRecord) -> Optional[MemoryRecord]:
        all_memories = self._memory_db.get_all()
        for item in all_memories:
            text, category, importance = item
            if category != record.category:
                continue
            if self._is_same_memory(text, record.text):
                return MemoryRecord.from_legacy(text=text, category=category, importance=importance)
            if self._is_replacement(text, record.text) or self._is_replacement(record.text, text):
                return MemoryRecord.from_legacy(text=text, category=category, importance=importance)
        return None

    def _should_update(self, existing: MemoryRecord, incoming: MemoryRecord) -> bool:
        if existing.category != incoming.category:
            return False

        if self._is_same_memory(existing.text, incoming.text):
            return False

        if self._is_replacement(existing.text, incoming.text):
            return True

        return False

    def _is_same_memory(self, existing_text: str, incoming_text: str) -> bool:
        existing_norm = self._normalize(existing_text)
        incoming_norm = self._normalize(incoming_text)
        if existing_norm == incoming_norm:
            return True
        return incoming_norm in existing_norm or existing_norm in incoming_norm

    def _is_replacement(self, existing_text: str, incoming_text: str) -> bool:
        existing_norm = self._normalize(existing_text)
        incoming_norm = self._normalize(incoming_text)
        if not existing_norm or not incoming_norm:
            return False

        replacement_prefixes = (
            "my favorite",
            "i like",
            "i love",
            "i prefer",
            "my name is",
            "i am",
            "i'm",
            "i live",
            "my laptop",
            "my phone",
            "my computer",
            "my home",
            "my office",
            "my contact",
            "my birthday",
            "my age",
        )

        for prefix in replacement_prefixes:
            if existing_norm.startswith(prefix) and incoming_norm.startswith(prefix):
                return True

        if existing_norm.startswith("i now live") and incoming_norm.startswith("i live"):
            return True
        return False

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip().lower())
