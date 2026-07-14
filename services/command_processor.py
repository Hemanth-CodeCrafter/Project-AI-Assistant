"""
Central command orchestration for Jarvis.

All clients (CLI, API, and future Android/TV agents) should route user
input through :class:`CommandProcessor` rather than duplicating pipeline
logic in entry-point modules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from core.brain import Brain
from core.conversation_memory import ConversationMemory, conversation_memory
from core.memory_manager import MemoryManager, memory_manager
from core.router import Router

logger = logging.getLogger(__name__)


class ClientType(str, Enum):
    """Identifies which client invoked command processing."""

    CLI = "cli"
    API = "api"
    # Reserved for future clients — not implemented yet.
    ANDROID = "android"
    TV = "tv"
    SMART_HOME = "smart_home"


@dataclass(frozen=True)
class ProcessOptions:
    """
    Per-client processing configuration.

    Defaults mirror the historical ``main.py`` CLI behavior. Use
    :meth:`for_api` to preserve the existing FastAPI response semantics.
    """

    client: ClientType = ClientType.CLI
    min_command_length: int = 2
    log_user_input: bool = True
    apply_memory_pipeline: bool = True
    resolve_llm_parts: bool = True

    @classmethod
    def for_cli(cls) -> ProcessOptions:
        """Options matching the current ``main.py`` pipeline."""
        return cls()

    @classmethod
    def for_api(cls) -> ProcessOptions:
        """Options matching the current ``api.py`` pipeline."""
        return cls(
            client=ClientType.API,
            min_command_length=0,
            log_user_input=False,
            apply_memory_pipeline=False,
            resolve_llm_parts=False,
        )


@dataclass
class ProcessResult:
    """
    Structured output from :meth:`CommandProcessor.process`.

    Attributes:
        cli_text: Final spoken/display text for CLI clients.
        api_response: JSON-serializable dict for HTTP clients.
        skipped: True when input was too short to process (CLI only).
    """

    cli_text: Optional[str] = None
    api_response: Optional[dict[str, Any]] = None
    skipped: bool = False


class CommandProcessor:
    """
    Single orchestration entry point for Jarvis command handling.

    Pipeline (when enabled via :class:`ProcessOptions`):

        User input
        → conversation memory (topic resolve / track)
        → long-term memory (remember / search)
        → router (pronoun resolve + intent routing)
        → brain (LLM fallback / multi-intent LLM parts)
        → structured result for the calling client

    TTS is intentionally **not** handled here; CLI entry points speak
    the returned ``cli_text`` themselves.
    """

    def __init__(
        self,
        router: Optional[Router] = None,
        brain: Optional[Brain] = None,
        memory: Optional[MemoryManager] = None,
        conversation: Optional[ConversationMemory] = None,
    ) -> None:
        """
        Initialize the processor with injectable dependencies.

        Args:
            router: Intent router. Defaults to a new :class:`Router`.
            brain: LLM facade. Defaults to a new :class:`Brain`.
            memory: Long-term memory manager. Defaults to module singleton.
            conversation: Short-term conversation memory. Defaults to singleton.
        """
        self._router = router or Router()
        self._brain = brain or Brain()
        self._memory = memory or memory_manager
        self._conversation = conversation or conversation_memory

    def process(
        self,
        command: str,
        options: Optional[ProcessOptions] = None,
    ) -> ProcessResult:
        """
        Run the full command pipeline and return a client-specific result.

        Args:
            command: Raw user text (from STT, keyboard, or HTTP body).
            options: Client-specific flags. Defaults to CLI behavior.

        Returns:
            :class:`ProcessResult` with ``cli_text`` or ``api_response`` set.
        """
        opts = options or ProcessOptions.for_cli()
        text = (command or "").strip()

        if opts.client == ClientType.CLI:
            if not text or len(text) < opts.min_command_length:
                logger.debug("CLI command skipped (too short): %r", command)
                return ProcessResult(skipped=True)

        if opts.log_user_input:
            print(f"\n👤 You: {text}")

        logger.info("Processing command for client=%s", opts.client.value)

        working_text, pre_route_memories = self._apply_memory_pipeline(text, opts)
        route_result = self._router.route(working_text)

        if opts.client == ClientType.API:
            return self._build_api_result(text, working_text, route_result, opts)

        return self._build_cli_result(
            working_text,
            route_result,
            opts,
            pre_route_memories=pre_route_memories,
        )

    # ------------------------------------------------------------------
    # Pipeline stages
    # ------------------------------------------------------------------

    def _apply_memory_pipeline(
        self,
        command: str,
        opts: ProcessOptions,
    ) -> tuple[str, list[tuple[Any, ...]]]:
        """
        Run conversation + long-term memory stages before routing.

        Pronoun resolution for app context still occurs inside
        :meth:`Router.route`; conversation memory resolves topic
        follow-ups here, matching the existing ``main.py`` order.

        Returns:
            Tuple of (resolved command text, memories searched before resolve).
        """
        if not opts.apply_memory_pipeline:
            return command, []

        self._memory.remember(command)
        memories = self._memory.search(command)

        resolved = self._conversation.resolve(command)
        topic = self._conversation.extract_topic(resolved)

        if topic:
            self._conversation.set_topic(topic)

        self._conversation.add(resolved)

        return resolved, memories

    def _build_memory_prompt(
        self,
        query: str,
        memories: list[tuple[Any, ...]],
    ) -> str:
        """Format retrieved memories into an LLM prompt."""
        if not memories:
            return query

        memory_text = "\n".join(f"- {m[0]}" for m in memories)
        return (
            f"\n        Relevant memories:\n\n"
            f"        {memory_text}\n\n"
            f"        User:\n"
            f"        {query}\n"
            f"        "
        )

    def _invoke_brain_for_llm_part(self, part: str) -> Optional[str]:
        """Send a multi-intent LLM fragment to the brain with memory context."""
        print(f"🤖 Brain handling: {part}")
        logger.info("Brain handling LLM part: %s", part)

        memories = self._memory.search(part)
        prompt = self._build_memory_prompt(part, memories)
        return self._brain.think(prompt)

    def _invoke_brain_full_command(
        self,
        original_command: str,
        working_command: str,
        opts: ProcessOptions,
        pre_route_memories: Optional[list[tuple[Any, ...]]] = None,
    ) -> Optional[str]:
        """
        Fallback when the router returns ``None`` (pure LLM path).

        Preserves existing client quirks:
        - CLI builds a memory prompt but calls ``think(working_command)``
        - API calls ``think(original_command)`` with no memory enrichment
        """
        print("🤖 Sending to brain...")
        logger.info("Router returned None; falling back to brain")

        if opts.apply_memory_pipeline:
            # main.py searches memories before resolve and reuses that list here.
            memories = pre_route_memories or []
            self._build_memory_prompt(working_command, memories)

        brain_input = (
            working_command
            if opts.client == ClientType.CLI and opts.apply_memory_pipeline
            else original_command
        )
        return self._brain.think(brain_input)

    # ------------------------------------------------------------------
    # Result builders
    # ------------------------------------------------------------------

    def _build_cli_result(
        self,
        working_command: str,
        route_result: Optional[dict[str, Any]],
        opts: ProcessOptions,
        pre_route_memories: Optional[list[tuple[Any, ...]]] = None,
    ) -> ProcessResult:
        """Build the string response expected by ``main.py``."""
        if route_result is None:
            response = self._invoke_brain_full_command(
                working_command,
                working_command,
                opts,
                pre_route_memories=pre_route_memories,
            )
            return ProcessResult(cli_text=response)

        responses: list[str] = list(route_result.get("responses", []))
        llm_parts: list[str] = list(route_result.get("llm_parts", []))

        if opts.resolve_llm_parts:
            for part in llm_parts:
                llm_response = self._invoke_brain_for_llm_part(part)
                if llm_response:
                    responses.append(llm_response)

        if responses:
            return ProcessResult(cli_text=" ".join(responses))

        return ProcessResult(cli_text=None)

    def _build_api_result(
        self,
        original_text: str,
        working_text: str,
        route_result: Optional[dict[str, Any]],
        opts: ProcessOptions,
    ) -> ProcessResult:
        """Build the JSON payload expected by ``api.py`` and the frontend."""
        if route_result is not None:
            logger.debug("API router result: %s", route_result)
            return ProcessResult(api_response=route_result)

        reply = self._invoke_brain_full_command(
            original_text,
            working_text,
            opts,
        )
        return ProcessResult(
            api_response={
                "source": "brain",
                "response": reply,
            }
        )
