
import re
import tempfile
import base64
from pathlib import Path


def transcribe_audio(audio_path, client, model):
    """Convert recorded audio into text."""

    if not audio_path:
        return ""

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=model,
            file=audio_file
        )

    return transcription.text.strip()


def generate_speech(recipe, client, model):
    """Generate spoken instructions for a recipe."""

    if not recipe:
        return None

    # Remove common Markdown formatting
    text = re.sub(r"[#*`]", "", recipe)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.strip()

    # Speech API input limit: 4096 characters
    text = text[:4000]

    if not text:
        return None

    # Unique temporary file for each response
    with tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    ) as temp_file:
        output_path = Path(temp_file.name)

    try:
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice="coral",
            input=text,
            response_format="mp3",
            instructions=(
                "Speak clearly and naturally, like a helpful "
                "cooking instructor. Use a calm, friendly tone."
            )
        ) as response:
            response.stream_to_file(output_path)

    except Exception:
        output_path.unlink(missing_ok=True)
        raise

    return str(output_path)

def transcribe_recording(audio_data, client, model):
    if not audio_data:
        return ""

    header, encoded = audio_data.split(",", 1)

    suffix = ".mp4" if "mp4" in header else ".webm"

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False
    ) as file:
        file.write(base64.b64decode(encoded))
        path = Path(file.name)

    try:
        return transcribe_audio(str(path), client, model)
    finally:
        path.unlink(missing_ok=True)
