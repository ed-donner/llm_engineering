
# ---------------------------------
# Audio Manipulation Utilities
# ---------------------------------

from pathlib import Path
import numpy as np

import sounddevice as sd
import soundfile as sf

from openai import OpenAI
from helpers import get_system_settings


settings = get_system_settings()


def input_audio(sample_rate: int = 16000) -> Path:
    """Record until Enter is pressed, save a WAV file, and return its path."""

    if not isinstance(sample_rate, int) or sample_rate <= 0:
        raise ValueError("sample_rate must be a positive integer")


    settings.AUDIO_PATH.parent.mkdir(parents=True, exist_ok=True)
    chunks = []

    def callback(indata, frames, time, status):
        if status:
            print(status)
        chunks.append(indata.copy())

    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        callback=callback,
    ):
        input("Recording... Press Enter to stop.\n")

    if not chunks:
        raise ValueError("No audio was recorded.")

    audio = np.concatenate(chunks, axis=0)

    sf.write(settings.AUDIO_PATH, audio, sample_rate, format="WAV", subtype="PCM_16")
    print(f"Recording saved to {settings.AUDIO_PATH}")
    return settings.AUDIO_PATH



def read_audio(audio_path: str | Path):
    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")
    return sf.read(path, dtype="float32")


def play_audio(audio_path: str | Path) -> None:
    """Play a local audio file through the default speakers and wait until done."""
    audio, sample_rate = read_audio(audio_path)
    sd.play(audio, samplerate=sample_rate)
    try:
        sd.wait()
    except BaseException:
        sd.stop()
        raise


def transcribe(audio_path: str | Path, language: str = "en") -> str:
    """Transcribe a local audio file; the spoken language defaults to English."""

    print(f"- Transcribing the audio given...")

    with open(audio_path, "rb") as audio_file:
        with OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
        ) as client:
            transcription = client.audio.transcriptions.create(
                model=settings.AUDIO_TO_TEXT_LLM,
                file=audio_file,
                language=language,
            )
            
    return transcription.text


