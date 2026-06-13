# test_audio.py

from core.audio_stream import AudioStream

audio = AudioStream()

print("Listening...")

while True:

    frame = audio.read_frame()

    print(len(frame))