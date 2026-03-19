import queue
import sounddevice as sd
import whisper


class StreamingSTT:
    """
    Real-time speech recognition pipeline.
    """

    def __init__(self):

        self.model = whisper.load_model("base")

        self.audio_queue = queue.Queue()

    def callback(self, indata, _frames=None, _time=None, _status=None):

        self.audio_queue.put(indata.copy())

    def listen(self):

        with sd.InputStream(callback=self.callback):

            while True:

                audio = self.audio_queue.get()

                result = self.model.transcribe(audio)

                yield result["text"]