# main.py
import os
import sys
import time
import pyttsx3
import random

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from dotenv                   import load_dotenv
from core.brain               import Brain
from core.router              import Router
from core.stt                 import SpeechToText
from core.recorder            import Recorder
from core.wake_word           import WakeWordDetector
from core.conversation_memory import conversation_memory
from core.memory_manager      import memory_manager


# ── TTS — init ONCE, reuse ────────────────────────
# Reinitializing every speak() call was causing lag
'''
engine = pyttsx3.init()
engine.setProperty('rate', 165)
voices = engine.getProperty('voices')
engine.setProperty(
    'voice',
    voices[1].id if len(voices) > 1 else voices[0].id
)
engine.setProperty('volume', 1.0)
'''
# ── Response pools ────────────────────────────────
GREETINGS = [
    "Yes sir!",
    "Hello sir!",
    "I am listening.",
    "Ready, go ahead.",
    "How can I help?",
]



FAREWELLS = [
    "Goodbye! Have a great day.",
    "See you soon sir.",
    "Take care. Goodbye!",
]

# THINKING = [
#     "Let me think...",
#     "One moment...",
#     "Sure, give me a second...",
# ]

SESSION_TIMEOUT = 30   # seconds of silence before returning to wake word
AUDIO_PATH      = "data/recordings/command.wav"
os.makedirs("data/recordings", exist_ok=True)

load_dotenv()

# ── TTS ───────────────────────────────────────────
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 165)
    voices = engine.getProperty('voices')
    engine.setProperty(
        'voice',
        voices[1].id if len(voices) > 1 else voices[0].id
    )
    engine.setProperty('volume', 1.0)

    if not text:
        return
    # Strip __LLM__ tags if they leak through
    text = str(text).replace("__LLM__:", "").strip()
    print(f"\n🤖 Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# ── Init ──────────────────────────────────────────
def initialize():
    print("\n" + "="*45)
    print("       JARVIS - Personal AI Assistant")
    print("="*45)

    print("\n[1/4] Loading speech recognition...")
    stt = SpeechToText()

    print("[2/4] Loading recorder...")
    recorder = Recorder()

    print("[3/4] Loading AI brain...")
    brain = Brain()

    print("[4/4] Loading router...")
    router = Router()

    print("\n✅ All systems ready.\n")
    return stt, recorder, brain, router

# ── Process one command ───────────────────────────
def process_command(command, router, brain):
    """
    Router handles known commands instantly.
    Brain handles everything else.
    Returns response string.
    """
    if not command or len(command.strip()) < 2:
        return None

    print(f"\n👤 You: {command}")

    # Save important memories
    memory_manager.remember(command)

    # Search related memories
    memories = memory_manager.search(command)
    # Resolve follow-up questions
    command = conversation_memory.resolve(command)

    topic = conversation_memory.extract_topic(command)

    if topic:
        conversation_memory.set_topic(topic)

    conversation_memory.add(command)

    # Try router first — instant, no LLM
    result = router.route(command)

    if result is None:
        # Nothing matched — send full command to LLM
        if memories:

            memory_text = "\n".join(
                f"- {m[0]}"
                for m in memories
            )

            prompt = f"""
        Relevant memories:

        {memory_text}

        User:
        {command}
        """

        else:
            prompt = command

        print("🤖 Sending to brain...")
        #speak(random.choice(THINKING))
        response = brain.think(command)
        return response

    # Router returned a dict with responses + llm_parts
    responses = result.get("responses", [])
    llm_parts = result.get("llm_parts", [])

    # Handle any LLM parts from multi-intent
    for part in llm_parts:
        print(f"🤖 Brain handling: {part}")
        #speak(random.choice(THINKING))
        memories = memory_manager.search(part)

        if memories:

            memory_text = "\n".join(
                f"- {m[0]}"
                for m in memories
            )

            prompt = f"""
        Relevant memories:

        {memory_text}

        User:
        {part}
        """

        else:
            prompt = part

        llm_response = brain.think(prompt)
        
        if llm_response:
            responses.append(llm_response)

    if responses:
        return " ".join(responses)

    return None

# ── Is exit command ───────────────────────────────
def is_exit(command):
    exit_phrases = [
        "goodbye", "bye", "exit", "quit",
        "stop jarvis", "shutdown jarvis",
        "go to sleep", "sleep"
    ]
    return any(p in command.lower() for p in exit_phrases)

# ── Wake word mode ────────────────────────────────
def run_with_wakeword(stt, recorder, brain, router):
    """
    Continuously listens for wake word.
    After detection, stays in session until
    SESSION_TIMEOUT seconds of no activity,
    or user says goodbye.
    Then returns to wake word listening.
    Never exits — always ready.
    """
    wakeword = WakeWordDetector()

    print("🎙️  Jarvis is running. Say wake word to activate.\n")

    while True:  # ← outer loop: always returns here
        try:

            # ── Wait for wake word ─────────────────
            print("💤 Waiting for wake word...")
            detected = wakeword.listen()
            if not detected:
                continue

            # ── Session starts ─────────────────────
            print("\n🔔 Wake word detected!")
            speak(random.choice(GREETINGS))

            last_activity = time.time()

            # ── Inner loop: active session ─────────
            while True:

                # Check session timeout
                idle = time.time() - last_activity
                if idle > SESSION_TIMEOUT:
                    print(f"\n⏱️  Session timed out "
                          f"({SESSION_TIMEOUT}s idle)")
                    speak("Going back to sleep. "
                          "Say the wake word when you need me.")
                    break  # ← back to outer loop (wake word)

                # Record next command
                print("\n🎤 Listening for command...")
                recorder.record_until_silence(
                    AUDIO_PATH, max_seconds=8
                )

                # Transcribe
                command = stt.transcribe(AUDIO_PATH)

                if not command or len(command.strip()) < 2:
                    # Nothing heard — keep session alive
                    # but don't reset timer
                    continue

                # Check for exit
                if is_exit(command):
                    speak(random.choice(FAREWELLS))
                    break  # ← back to outer loop (wake word)

                # Process command
                response = process_command(
                    command, router, brain
                )

                if response:
                    speak(response)
                    last_activity = time.time() # reset timer

                # Stay in session — loop back for next command

        except KeyboardInterrupt:
            print("\n\nStopping Jarvis...")
            speak("Shutting down. Goodbye sir!")
            try:
                wakeword.close()
                recorder.close()
            except:
                pass
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            speak("Something went wrong. Listening again.")
            time.sleep(1)
            # Outer loop continues — back to wake word

# ── Text mode ─────────────────────────────────────
def run_text_mode(brain, router):
    """
    Type commands — for testing router/brain
    without needing mic or wake word.
    Continuous conversation — type 'exit' to quit.
    """
    print("⌨️  Text mode. Type commands. 'exit' to quit.\n")
    speak("Jarvis online in text mode.")

    while True:
        try:
            command = input("\n👤 You: ").strip()
            if not command:
                continue

            if is_exit(command):
                speak(random.choice(FAREWELLS))
                break

            response = process_command(command, router, brain)
            if response:
                speak(response)
            else:
                speak("I didn't understand that.")

        except KeyboardInterrupt:
            speak("Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

# ── Voice mode ────────────────────────────────────
def run_voice_mode(stt, recorder, brain, router):
    """
    Press Enter to speak — no wake word needed.
    Good for testing voice pipeline.
    """
    print("🎤  Voice mode. Press Enter to speak.\n")
    speak("Jarvis online. Press Enter to give a command.")

    while True:
        try:
            input("\n⏎  Press Enter to speak...")
            print("🎙️  Listening...")

            recorder.record_until_silence(
                AUDIO_PATH, max_seconds=8
            )
            command = stt.transcribe(AUDIO_PATH)

            if not command or len(command.strip()) < 2:
                speak("I didn't hear anything.")
                continue

            if is_exit(command):
                speak(random.choice(FAREWELLS))
                break

            response = process_command(command, router, brain)
            if response:
                speak(response)
            else:
                speak("I didn't understand that.")

        except KeyboardInterrupt:
            speak("Goodbye!")
            recorder.close()
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)

# ── Entry point ───────────────────────────────────
if __name__ == "__main__":
    # python main.py        → wake word mode (default)
    # python main.py text   → text mode (testing)
    # python main.py voice  → press enter to speak

    mode = sys.argv[1] if len(sys.argv) > 1 else "wake"
    #mode = "text"

    stt, recorder, brain, router = initialize()

    if mode == "text":
        run_text_mode(brain, router)
    elif mode == "voice":
        run_voice_mode(stt, recorder, brain, router)
    else:
        run_with_wakeword(stt, recorder, brain, router)