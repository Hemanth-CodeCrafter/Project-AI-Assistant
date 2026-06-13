# core/recorder.py

import pyaudio
import wave

class Recorder:

    def __init__(self):

        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000

        self.audio = pyaudio.PyAudio()

    def record(self,
               filename,
               seconds=5):
        print("Recording command...")

        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )


        frames = []

        # Number of chunks to read
        total_chunks = int(
            self.rate / self.chunk * seconds
        )

        for _ in range(total_chunks):

            data = stream.read(self.chunk)

            frames.append(data)

        print("Recording complete.")

        stream.stop_stream()
        stream.close()

        # Save WAV file
        wf = wave.open(filename, 'wb')

        wf.setnchannels(self.channels)

        wf.setsampwidth(
            self.audio.get_sample_size(
                self.format
            )
        )

        wf.setframerate(self.rate)

        wf.writeframes(
            b''.join(frames)
        )

        wf.close()