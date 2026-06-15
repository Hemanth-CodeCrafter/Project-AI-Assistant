# core/recorder.py
import pyaudio
import wave
import os

class Recorder:
    def __init__(self):
        self.chunk    = 1024
        self.format   = pyaudio.paInt16
        self.channels = 1
        self.rate     = 16000  # 16kHz is enough for speech

        # Create PyAudio ONCE — reuse it every recording
        self.audio = pyaudio.PyAudio()
        print("Recorder ready.")

    def record(self, filename, seconds=8):
        """Record audio and save to WAV file"""

        # Make sure output folder exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        print(f"Recording for {seconds} seconds...")

        # Open stream fresh each time but reuse self.audio
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        frames = []
        total_chunks = int(self.rate / self.chunk * seconds)

        for _ in range(total_chunks):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        print("Recording complete.")

        # Save as WAV
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        return filename

    def record_until_silence(self, filename, max_seconds=8):
        """
        Smarter recording — stops automatically when you stop talking.
        No more waiting 5 full seconds every time.
        """
        import numpy as np

        SILENCE_THRESHOLD = 500   # adjust if too sensitive
        SILENCE_CHUNKS    = 30    # stop after ~1.3s of silence

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        print("Listening... (speak now)")
        frames         = []
        silent_count   = 0
        speaking       = False
        max_chunks     = int(self.rate / self.chunk * max_seconds)

        for _ in range(max_chunks):
            data  = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)

            # Check volume level
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume     = np.abs(audio_data).mean()

            if volume > SILENCE_THRESHOLD:
                speaking     = True
                silent_count = 0
            elif speaking:
                silent_count += 1
                if silent_count > SILENCE_CHUNKS:
                    print("Silence detected — done.")
                    break

        stream.stop_stream()
        stream.close()

        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        return filename

    def close(self):
        """Call this when shutting down the assistant"""
        self.audio.terminate()
        print("Recorder closed.")