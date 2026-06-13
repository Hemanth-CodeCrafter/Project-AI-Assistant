import pyaudio

class AudioStream:
    def __init__(self):
        #Create PyAudio object
        self.audio = pyaudio.PyAudio()

        #Open mic stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )

    def read_frame(self):
        # Read mic chunk
        frame = self.stream.read(1024)

        return frame
    
    def close(self):
        self.stream.stop_stream()
        self.stream.close()

        self.audio.terminate()