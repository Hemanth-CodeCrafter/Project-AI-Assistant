from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class MemoryRecord:
    """Structured representation of a persisted memory."""

    text: str
    category: str = "general"
    importance: int = 5
    confidence: float = 0.5
    source: str = "user"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_accessed: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if not self.last_accessed:
            self.last_accessed = now

    @classmethod
    def from_legacy(cls, text: str, category: str = "general", importance: int = 5) -> "MemoryRecord":
        """Create a record from the existing simple memory format."""
        return cls(text=text, category=category, importance=importance)

    def to_tuple(self) -> tuple[str, str, int]:
        """Preserve the existing tuple shape expected by the rest of the project."""
        return (self.text, self.category, self.importance)
