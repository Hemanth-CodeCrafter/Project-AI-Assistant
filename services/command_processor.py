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
from core.context_manager import ContextManager
from core.conversation_memory import ConversationMemory
from core.memory_db import MemoryDB
from core.memory_manager import MemoryManager
from core.memory_service import MemoryService
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
        return cls(log_user_input=False)

    @classmethod
    def for_api(cls) -> ProcessOptions:
        """Options matching the current ``api.py`` pipeline."""
        return cls(
            client=ClientType.API,
            min_command_length=0,
            log_user_input=False,
            apply_memory_pipeline=True,
            resolve_llm_parts=True,
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
        memory_db: Optional[MemoryDB] = None,
        context_manager_instance: Optional[ContextManager] = None,
        memory_service: Optional[MemoryService] = None,
    ) -> None:
        """
        Initialize the processor with injectable dependencies.

        Args:
            router: Intent router. Defaults to a new :class:`Router`.
            brain: LLM facade. Defaults to a new :class:`Brain`.
            memory: Long-term memory manager. Defaults to module singleton.
            conversation: Short-term conversation memory. Defaults to singleton.
        """
        context_instance = context_manager_instance or ContextManager()
        self._router = router or Router(context_manager=context_instance)
        self._brain = brain or Brain()
        
        # If dependencies are not injected, create new instances.
        # This is crucial for thread-safety in the API.
        db_instance = memory_db or MemoryDB()
        conversation_instance = conversation or ConversationMemory()
        memory_instance = memory or MemoryManager(db=db_instance)

        self._conversation = conversation_instance
        self._memory = memory_instance

        self._memory_service = memory_service or MemoryService(
            memory_manager=self._memory,
            memory_db=db_instance,
            conversation_memory=self._conversation,
            context_manager=context_instance,
        )

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

        working_text, pre_route_memories  = self._apply_memory_pipeline(text, opts)
        memory_answer = self._memory_service.retrieve_best_memory(working_text)

        if memory_answer:
            if opts.client == ClientType.API:
                return ProcessResult(
                    api_response={
                        "success": True,
                        "source": "memory",
                        "text": memory_answer,
                        "intent": None,
                        "action": None,
                        "metadata": {},
                    }
                )

            return ProcessResult(cli_text=memory_answer)
        route_result = self._router.route(working_text)

        # If the user says "yes/no" to a question, we need to give the brain context.
        if route_result and route_result.get("intent") in ["affirm", "negate"]:
            history = self._memory_service.get_conversation_history()
            # The current user's turn has been added with a None assistant response.
            # We need to check the turn before that one.
            if len(history) > 1:
                previous_turn = history[-2]
                last_assistant_message = previous_turn.get('assistant')
                if last_assistant_message and last_assistant_message.endswith('?'):
                    # The user is replying to a direct question from the assistant.
                    # Synthesize a new command with full context for the brain.
                    contextual_command = (
                        f"The user replied '{working_text}' to your question: "
                        f"'{last_assistant_message}'. Please respond appropriately."
                    )
                    working_text = contextual_command
                    route_result = None  # Force brain fallback with the new context

        if route_result is None and opts.client == ClientType.CLI:
            resolved_followup = self._memory_service.resolve_reference(working_text)
            if resolved_followup != working_text:
                working_text = resolved_followup

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
        
        self._memory_service.remember(command)
        memories = self._memory_service.retrieve(command)

        resolved = self._memory_service.resolve_reference(command)
        topic = self._memory_service.extract_topic(resolved)

        if topic:
            self._memory_service.set_topic(topic)

        self._memory_service.add_conversation_turn(resolved)

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

        Enriches the command with conversation memory before sending to brain.
        """
        print("Sending to brain...")
        logger.info("Router returned None; falling back to brain")

        brain_input = working_command
        if opts.apply_memory_pipeline:
            # The memory pipeline is enabled, so we enrich the input with memories.
            memories = pre_route_memories or []
            brain_input = self._build_memory_prompt(working_command, memories)

        # Always use the enriched `brain_input` for all clients, which is based
        # on the processed `working_command`.
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
            # direct_memory_reply = self._memory_service.retrieve_best_memory(working_command)
            # if direct_memory_reply:
            #     return ProcessResult(cli_text=direct_memory_reply)

            response = self._invoke_brain_full_command(
                working_command,
                working_command,
                opts,
                pre_route_memories=pre_route_memories,
            )
            self._memory_service.add_conversation_turn(
                user=working_command,
                assistant=response,
            )
            self._memory_service.update_entities(response)
            assistant_topic = self._memory_service.extract_topic(response)

            if assistant_topic:
                self._memory_service.set_topic(assistant_topic)
            return ProcessResult(cli_text=response)

        responses: list[str] = list(route_result.get("responses", []))
        llm_parts: list[str] = list(route_result.get("llm_parts", []))

        if opts.resolve_llm_parts:
            for part in llm_parts:
                llm_response = self._invoke_brain_for_llm_part(part)
                if llm_response:
                    responses.append(llm_response)

        if responses:
            assistant_reply = " ".join(responses)

            self._memory_service.add_conversation_turn(
                user=working_command,
                assistant=assistant_reply,
            )

            self._memory_service.update_entities(assistant_reply)

            assistant_topic = self._memory_service.extract_topic(assistant_reply)

            if assistant_topic:
                self._memory_service.set_topic(assistant_topic)

            return ProcessResult(cli_text=assistant_reply)

        return ProcessResult(cli_text=None)

    def _build_api_result(
        self,
        original_text: str,
        working_text: str,
        route_result: Optional[dict[str, Any]],
        opts: ProcessOptions,
    ) -> ProcessResult:
        """
        Build a standardized JSON response for HTTP clients.

        Android should always receive the same response structure,
        regardless of whether the Router or Brain handled the request.
        """

        # Router handled the command
        if route_result is not None:
            logger.debug("API router result: %s", route_result)

            response = {
                "success": True,
                "source": "router",
                "text": "",
                "intent": None,
                "action": None,
                "metadata": {},
            }

            # Preserve router response if it's already a dictionary
            if isinstance(route_result, dict):
                response["text"] = (
                    route_result.get("response")
                    or route_result.get("message")
                    or route_result.get("text")
                    or ""
                )

                response["intent"] = route_result.get("intent")
                response["action"] = route_result.get("action")
                response["metadata"] = route_result.get("metadata", {})

            else:
                response["text"] = str(route_result)
            
            assistant_reply = response["text"]

            self._memory_service.add_conversation_turn(
                user=working_text,
                assistant=assistant_reply,
            )

            self._memory_service.update_entities(assistant_reply)

            assistant_topic = self._memory_service.extract_topic(assistant_reply)

            if assistant_topic:
                self._memory_service.set_topic(assistant_topic)

            return ProcessResult(api_response=response)

        # Brain fallback
        reply = self._invoke_brain_full_command(
            original_text,
            working_text,
            opts,
        )
        self._memory_service.add_conversation_turn(
            user=working_text,
            assistant=reply,
        )

        self._memory_service.update_entities(reply)

        assistant_topic = self._memory_service.extract_topic(reply)

        if assistant_topic:
            self._memory_service.set_topic(assistant_topic)

        return ProcessResult(
            api_response={
                "success": True,
                "source": "brain",
                "text": reply,
                "intent": None,
                "action": None,
                "metadata": {},
            }
        )
