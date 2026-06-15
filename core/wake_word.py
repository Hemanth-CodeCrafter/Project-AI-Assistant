# core/wake_word.py
import pyaudio
import numpy as np
from openwakeword.model import Model

class WakeWordDetector:
    def __init__(self):
        print("Loading wake word model...")
        
        self.model = Model(
            wakeword_models=["hey jarvis"],
            inference_framework="onnx"
        )
        
        self.chunk_size  = 1280
        self.sample_rate = 16000
        self.audio       = pyaudio.PyAudio()
        self.stream      = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        print("Wake word model loaded.")

    def listen(self):
        """Listen until wake word detected — returns True"""
        self.model.reset()
        
        while True:
            raw  = self.stream.read(
                self.chunk_size,
                exception_on_overflow=False
            )
            audio_data = np.frombuffer(raw, dtype=np.int16)
            
            prediction = self.model.predict(audio_data)
            
            for word, score in prediction.items():
                if score > 0.7:
                    print(f"🔔 Wake word: {word} ({score:.2f})")
                    self.model.reset()
                    return True

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()