import time

from core.wake_word import WakeWordDetector
from core.recorder import Recorder
from core.stt import SpeechToText


wake_word = WakeWordDetector()

recorder = Recorder()

stt = SpeechToText()


print("\nAssistant started...\n")

while True:
    # CHECK ONLY ONE FRAME
    detected = wake_word.listen()

    # If wake word detected
    if detected:

        print("\nAssistant Activated\n")

        wake_word.model.reset()

        # IMPORTANT COOLDOWN
        time.sleep(2)

        # Record command
        audio_file = "data/recordings/command.wav"

        recorder.record(
            filename=audio_file,
            seconds=5
        )

        wake_word.model.reset() 
        
        # Speech to text
        text = stt.transcribe(audio_file)

        print("\nYou said:")

        print(text)

        # LONG COOLDOWN
        time.sleep(5)