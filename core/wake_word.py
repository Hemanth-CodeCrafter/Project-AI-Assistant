import pyaudio
import numpy as np

from openwakeword.model import Model


class WakeWordDetector:

    def __init__(self):

        print("Loading wake word model...")

        self.model = Model()

        print("Wake word model loaded.")

        self.chunk_size = 1280
        self.sample_rate = 16000

        self.audio = pyaudio.PyAudio()

        # Open ONE persistent stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

    def listen(self):

        # Read one audio frame
        audio_data = self.stream.read(
            self.chunk_size,
            exception_on_overflow=False
        )

        # Convert to numpy
        audio_array = np.frombuffer(
            audio_data,
            dtype=np.int16
        )

        # Predict wake word
        prediction = self.model.predict(
            audio_array
        )

        # Check predictions
        for wake_word, score in prediction.items():

            if score > 0.5:

                print(f"\nWake word detected: {wake_word}")

                return True

        return False

    def close(self):

        self.stream.stop_stream()
        self.stream.close()

        self.audio.terminate()