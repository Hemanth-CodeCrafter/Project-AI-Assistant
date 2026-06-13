import whisper


class SpeechToText:

    def __init__(self):

        print("Loading Whisper model...")

        # Load Whisper model
        self.model = whisper.load_model("base")

        print("Whisper model loaded.")


    def transcribe(self, audio_path):

        print("Transcribing audio...")

        result = self.model.transcribe(
            audio_path, fp16 = False, language="en"
        )

        text = result["text"]

        return text.strip()