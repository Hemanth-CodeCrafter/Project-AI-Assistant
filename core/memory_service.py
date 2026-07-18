from __future__ import annotations

from typing import Any, Optional

from core.context_manager import ContextManager
from core.conversation_memory import ConversationMemory
from core.memory_db import MemoryDB
from core.memory_extractor import MemoryExtractor
from core.memory_manager import MemoryManager
from core.memory_ranker import MemoryRanker
from core.memory_record import MemoryRecord
from core.memory_retrieval import MemoryRetrievalEngine
from core.memory_update import MemoryUpdateResolver


class MemoryService:
    """Coordinate short-term, conversation, context, and long-term memory."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        memory_db: MemoryDB,
        conversation_memory: ConversationMemory,
        context_manager: ContextManager,
        memory_extractor: Optional[MemoryExtractor] = None,
        memory_update_resolver: Optional[MemoryUpdateResolver] = None,
        memory_retrieval_engine: Optional[MemoryRetrievalEngine] = None,
        memory_ranker: Optional[MemoryRanker] = None,
    ) -> None:
        self._memory_manager = memory_manager
        self._memory_db = memory_db
        self._conversation_memory = conversation_memory
        self._context_manager = context_manager
        self._memory_extractor = memory_extractor or MemoryExtractor()
        self._memory_update_resolver = memory_update_resolver or MemoryUpdateResolver(self._memory_db)
        self._memory_retrieval_engine = memory_retrieval_engine or MemoryRetrievalEngine(self._memory_db)
        self._memory_ranker = memory_ranker or MemoryRanker()
        
    def _format_acknowledgement(self, memory: str) -> str:
        """
        Convert stored first-person memories into acknowledgement text.
        """

        replacements = [
            ("My name is ", "your name is "),
            ("my name is ", "your name is "),
            ("I am ", "you are "),
            ("i am ", "you are "),
            ("I'm ", "you are "),
            ("i'm ", "you are "),
            ("I live in ", "you live in "),
            ("i live in ", "you live in "),
            ("I like ", "you like "),
            ("i like ", "you like "),
            ("I love ", "you love "),
            ("i love ", "you love "),
            ("My favorite ", "your favorite "),
            ("my favorite ", "your favorite "),
            ("My favourite ", "your favourite "),
            ("my favourite ", "your favourite "),
        ]

        for old, new in replacements:
            if memory.startswith(old):
                return new + memory[len(old):]

        return memory
    
    def remember(self, text: str) -> Optional[str]:
        """Persist a memory if the current rules consider it important."""
        extraction = self._memory_extractor.extract(text)
        if not extraction.should_remember:
            return None

        record = MemoryRecord.from_legacy(
            text=extraction.memory_text,
            category=extraction.category,
            importance=extraction.importance,
        )

        action, existing = self._memory_update_resolver.resolve(record)
        if action == "IGNORE":
            return None

        if action == "UPDATE" and existing is not None:
            updated = MemoryRecord.from_legacy(
                text=record.text,
                category=existing.category,
                importance=max(existing.importance, record.importance),
            )
            self._memory_db.delete(existing.text)
            self._memory_db.save(
                memory=updated,
                category=updated.category,
                importance=updated.importance,
            )
            return f"Okay, I'll remember that {self._format_acknowledgement(updated.text)}."

        self._memory_db.save(
            memory=record,
            category=extraction.category,
            importance=extraction.importance,
        )
        return f"Okay, I'll remember that {self._format_acknowledgement(record.text)}."

    def retrieve(self, query: str) -> list[tuple[Any, ...]]:
        """Retrieve relevant long-term memories for a query."""
        return self._memory_manager.search(query)

    def retrieve_best_memory(self, query: str) -> Optional[str]:
        """Return the single best matching memory for a personal-information question."""
        # memories = self._memory_manager.search(query)
        # if not memories:
        #     return None
        # ranked_memory = self._memory_ranker.rank(query, memories)
        # return ranked_memory[0] if ranked_memory else None
        return self._memory_retrieval_engine.retrieve(query)
    
    def update(
        self,
        text: str,
        category: Optional[str] = None,
        importance: Optional[int] = None,
    ) -> bool:
        """Update or create a memory while preserving the existing behavior."""
        if category is not None or importance is not None:
            self._memory_db.save(
                memory=text,
                category=category or "general",
                importance=importance or 5,
            )
            return True

        return self.remember(text)

    def forget(self, memory: str) -> None:
        """Remove a memory from long-term storage."""
        self._memory_manager.forget(memory)

    def get_context(self, key: Optional[str] = None) -> Any:
        """Return the current context state or a single context field."""
        if key is None:
            return self._context_manager.context

        return self._context_manager.get(key)

    def add_conversation_turn(self, user: str, assistant: Optional[str] = None) -> None:
        """Add a turn to the short-term conversation history."""
        self._conversation_memory.add(user=user, assistant=assistant)

    def resolve_reference(self, command: str) -> str:
        """Resolve pronouns and short-term references using the existing resolver."""
        # The conversation_memory.resolve method is more comprehensive and handles
        # both topic ("it") and person ("he"/"she") resolution. The separate
        # pronoun_resolver was redundant and caused interference.
        return self._conversation_memory.resolve(command)

    def get_conversation_history(self) -> list[dict[str, Optional[str]]]:
        """Expose the current conversation history."""
        return self._conversation_memory.get_history()

    def get_topic(self) -> Optional[str]:
        """Return the active conversation topic."""
        return self._conversation_memory.get_topic()

    def set_topic(self, topic: str) -> None:
        """Set the active conversation topic."""
        self._conversation_memory.set_topic(topic)

    def extract_topic(self, text: str) -> Optional[str]:
        """Extract the likely topic from a message using the existing logic."""
        return self._conversation_memory.extract_topic(text)
    def update_entities(self, text: str) -> None:
        """Update conversational entities (person, topic, etc.) from assistant replies."""
        self._conversation_memory.update_entities(text)