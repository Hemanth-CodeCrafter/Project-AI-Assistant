"""
FastAPI server for Jarvis AI Assistant.

This module provides HTTP endpoints for remote clients (Android, TV, etc.)
to interact with the assistant. All command orchestration is delegated to
CommandProcessor to maintain a single source of truth for the assistant's
logic.

Endpoints:
    GET  /          - Serve frontend
    POST /command   - Process user command (text input)
    GET  /health    - Health check
"""

from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from services.command_processor import (
    CommandProcessor,
    ProcessOptions,
)

# ── FastAPI App Setup ──────────────────────────────
app = FastAPI(
    title="Jarvis API",
    description="Personal AI Assistant backend for multiple clients",
    version="1.0.0",
)

# Mount frontend static files (if available)
try:
    app.mount("/frontend", StaticFiles(directory="Frontend"), name="frontend")
except RuntimeError:
    # Frontend directory may not exist; API-only mode is valid
    pass

# ── Dependency Provider ─────────────────────────────
def get_command_processor() -> CommandProcessor:
    """
    FastAPI dependency provider for the CommandProcessor.
    
    Creates a new instance for each request, ensuring thread-safety.
    """
    return CommandProcessor()

# ── Request Models ─────────────────────────────────
class CommandRequest(BaseModel):
    """HTTP request body for the /command endpoint."""

    text: str = Field(
        ...,
        min_length=0,
        description="User command text (from STT, voice input, or typed text)",
        example="play music on spotify",
    )


# ── Endpoints ──────────────────────────────────────
@app.get("/")
async def home() -> FileResponse:
    """
    Serve the frontend home page.

    Returns:
        FileResponse: index.html from the Frontend directory.
    """
    return FileResponse("Frontend/index.html")


@app.post("/command")
async def command(
    request: CommandRequest,
    processor: CommandProcessor = Depends(get_command_processor),
) -> dict[str, Any]:
    """
    Process a user command through the unified assistant pipeline.

    This endpoint:
    1. Validates incoming command text
    2. Routes through CommandProcessor with API-specific options
    3. Returns the assistant's response as JSON

    The CommandProcessor internally:
    - Routes structured intents (tell_time, open_youtube, etc.)
    - Falls back to the LLM (Gemini/Groq/Ollama) for free-form questions
    - Handles provider switching on failure

    Args:
        request: HTTP request containing 'text' field with user command.

    Returns:
        dict[str, Any]: Response from router or brain:
        - If router handled intent: returns action response
        - If LLM answered: {"source": "brain", "response": "..."}

    Raises:
        HTTPException: If command is empty (400) or processing fails (500).

    Examples:
        POST /command
        {"text": "what time is it"}
        → {"source": "brain", "response": "The time is 3:45 PM"}

        POST /command
        {"text": "open youtube"}
        → "Opening YouTube"  (from router action)
    """
    try:
        # Validate and normalize input
        text: str = (request.text or "").strip()

        if not text:
            return {"error": "No command provided"}

        # Process through unified CommandProcessor pipeline
        # ProcessOptions.for_api() disables memory/conversation handling
        # and optimizes for HTTP response formatting
        result = processor.process(
            text,
            options=ProcessOptions.for_api(),
        )

        # Extract the structured response
        # api_response is always a dict for HTTP clients
        if result.api_response is not None:
            return result.api_response

        # Fallback (should not occur if CommandProcessor works correctly)
        return {"error": "Command processing returned no response"}

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        # Log unexpected errors and return 500
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error in /command endpoint")
        print(f"[ERROR] Command processing failed: {e}")

        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing command",
        ) from e


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for monitoring and load balancing.

    Useful for:
    - Docker health checks
    - Load balancer verification
    - Client connectivity testing

    Returns:
        dict: Status indicator with "healthy" status.
    """
    return {"status": "healthy"}

