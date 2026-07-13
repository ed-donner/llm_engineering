import os
import logging
from openai import OpenAI

logger = logging.getLogger("Questher.audio")

def transcribe_audio(audio_path: str, api_key: str = None) -> str:
    """
    Transcribe a local audio file to text using OpenAI's Whisper API.
    """
    if not audio_path:
        return ""
        
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found at path: {audio_path}")
        return "[Error: Audio file not found]"

    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        logger.error("OpenAI API key not set for audio transcription")
        return "[Error: OpenAI API key is missing]"

    try:
        client = OpenAI(api_key=key)
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text or ""
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return f"[Transcription error: {str(e)}]"
