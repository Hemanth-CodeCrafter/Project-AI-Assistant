from faster_whisper import WhisperModel

class SpeechToText:
    def __init__(self):
        # "tiny" = fastest, works well for commands
        # "base" = slightly slower but more accurate
        self.model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"  # uses less RAM
        )
        print("Whisper model loaded.")

    def transcribe(self, audio_path):
        print("Transcribing audio...")
        segments, info = self.model.transcribe(
            audio_path,
            language="en",
            beam_size=1,        # faster, less accurate but fine for commands
            vad_filter=True,    # skips silence automatically
        )
        text = " ".join([s.text for s in segments])
        return text.strip()