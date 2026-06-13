from core.recorder import Recorder

recorder = Recorder()

recorder.record(
    output_file="data/recordings/test.wav",
    seconds=5
)