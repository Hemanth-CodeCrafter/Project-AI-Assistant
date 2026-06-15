# core/audio_stream.py
# This is ONLY used by wake_word.py for continuous listening
# Recorder.py handles actual command recording separately

import pyaudio
import numpy as np

class AudioStream:
    def __init__(self, chunk_size=1280, sample_rate=16000):
        self.chunk_size  = chunk_size
        self.sample_rate = sample_rate

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        print("Audio stream open.")

    def read_frame(self):
        """Read one chunk — used by wake word detector"""
        raw = self.stream.read(
            self.chunk_size,
            exception_on_overflow=False  # prevents crash on overflow
        )
        # Return as numpy array (openwakeword needs this)
        return np.frombuffer(raw, dtype=np.int16)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        print("Audio stream closed.")