import whisper


class SpeechToText:
    """
    Converts spoken audio into text.
    """

    def __init__(self):

        self.model = whisper.load_model("base")

    def transcribe(self, audio_file):

        result = self.model.transcribe(audio_file)

        return result["text"]