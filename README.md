# J.A.R.V.I.S — Personal AI Assistant

An extensible Python-based personal assistant with a command-processing pipeline, voice interaction, a FastAPI interface, browser chat UI, LLM provider integrations, and SQLite-backed memory components.

> **Project status:** This repository contains the implementation described below. It has not been independently validated on a clean machine as part of this README update; please check setup and supported features in your environment before relying on them.

## Highlights

- **Voice workflow:** wake-word detection, audio recording, speech-to-text using Faster-Whisper, and text-to-speech using pyttsx3.
- **Command pipeline:** a shared `CommandProcessor` coordinates memory/context processing, intent routing, and LLM responses.
- **HTTP API:** FastAPI endpoints for command processing and health checks.
- **Web UI:** a lightweight browser chat interface with browser speech recognition where supported.
- **Memory modules:** SQLite-backed persistent memory and modules for conversation context, memory retrieval, and updates.
- **LLM integrations:** Gemini and Groq provider modules; Ollama is present as a provider module but is currently commented out of the active provider registry. OpenRouter is a placeholder provider.

## Architecture

```text
Voice CLI (main.py) ─┐
                     ├─> CommandProcessor (services/command_processor.py)
Browser / API ───────┘                │
                                      ├─ Memory / conversation context
                                      ├─ Intent classifier and router
                                      └─ Brain / provider integrations
                                           ├─ Gemini
                                           ├─ Groq fallback
                                           └─ Other provider modules (status varies)
```

### Main modules

| Path | Purpose |
|---|---|
| `main.py` | Voice, text, and push-to-talk CLI modes |
| `api.py` | FastAPI app with `POST /command` and `GET /health` |
| `server.py` | Alternate FastAPI chat entry point with `POST /chat` |
| `services/command_processor.py` | Shared orchestration for command processing |
| `core/wake_word.py` | Wake-word listener using openWakeWord |
| `core/stt.py` | Speech transcription using Faster-Whisper |
| `core/recorder.py` | Audio recording |
| `core/tts.py` | Local speech synthesis using pyttsx3 |
| `core/intent_classifier.py`, `core/router.py` | Intent classification and action routing |
| `core/memory_*.py`, `core/conversation_memory.py` | Memory and conversation support |
| `core/provider_manager.py`, `core/providers/` | LLM provider selection and adapters |
| `Frontend/` | Browser-based chat UI |

## Requirements

- Python version compatible with the pinned dependencies in `requirements.txt`.
- A microphone and working audio input for the voice mode.
- API credentials for the configured cloud LLM providers (for example, `GEMINI_API_KEY` and/or `GROQ_API_KEY`) when using those providers.
- The spaCy English model used by the intent classifier (`en_core_web_sm`).
- Optional local model setup is needed if you configure a local Ollama workflow; Ollama is not currently enabled in the provider registry.

## Setup (Windows PowerShell)

1. Clone this repository and enter the project directory:

   ```powershell
   git clone https://github.com/Hemanth-CodeCrafter/Project-AI-Assistant.git
   cd Project-AI-Assistant
   ```

2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

   Audio dependencies such as PyAudio and packages involving native binaries may require platform-specific setup. If installation fails, resolve those dependencies for your Python version and operating system before continuing.

4. Create a local `.env` file (do not commit it) and add the credentials needed by the providers you plan to use:

   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

5. Start in text mode first to verify the command-processing pipeline:

   ```powershell
   python main.py text
   ```

   Other CLI modes in `main.py` are:
   - `python main.py voice` — press Enter to record each command.
   - `python main.py` — wake-word mode (microphone and wake-word/audio dependencies required).

## Run the API and web UI

Start the FastAPI app:

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

Then open:

- API health: http://127.0.0.1:8000/health
- API documentation: http://127.0.0.1:8000/docs
- Web UI: http://127.0.0.1:8000/

Example request:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/command -Method Post -ContentType 'application/json' -Body '{"text":"What time is it?"}'
```

The API requires the applicable model provider credentials for LLM-based requests. The browser UI uses browser speech recognition if supported; voice availability depends on browser and permission support.

## Tests

The repository includes Python test scripts such as `test_api_concurrency.py`, `test_bugfixes.py`, and several module-level tests. Run tests only after installing dependencies:

```powershell
python -m unittest discover -p "test_*.py"
```

Test coverage and passing status have not been independently verified on a clean environment.

## Configuration and security notes

- Keep API keys in a local `.env` file; never place real credentials in source control.
- Do not share a live `jarvis_memory.db` if it contains personal conversation or memory data. Use a clean demo database for portfolio sharing.
- Do not expose the API publicly without appropriate authentication, request limits, logging, and security review.
- The actual behavior of each provider depends on its implementation and configuration; see `core/provider_manager.py` and `core/providers/`.

## Repository

Source code: https://github.com/Hemanth-CodeCrafter/Project-AI-Assistant
