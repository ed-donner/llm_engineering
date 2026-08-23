from faster_whisper import WhisperModel


class SpeechToTextService:
    def __init__(self, model_size: str = "tiny", device: str = "cpu"):
        self.model = WhisperModel(
            model_size, device=device, compute_type="int8")

    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribes the given audio file to text.

        Args:
            audio_file_path (str): The path to the audio file.

        Returns:
            str: The transcribed text.
        """
        print("Transcribing the audio file...")
        segments, _ = self.model.transcribe(
            audio_file_path, beam_size=5, vad_filter=True)
        return " ".join(segment.text for segment in segments)
