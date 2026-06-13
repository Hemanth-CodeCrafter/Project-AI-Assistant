from core.stt import SpeechToText

stt = SpeechToText()

text = stt.transcribe(
    "data/recordings/test.wav"
)

print("\nRecognized Text:")
print(text)   