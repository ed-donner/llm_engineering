import os
import json
import time
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

load_dotenv()

HF_API_KEY = (os.getenv("HF_API_KEY") or "").strip()
OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HF_INFERENCE_BASE = "https://router.huggingface.co/hf-inference/models"
HF_TRANSCRIPTION_URL = f"{HF_INFERENCE_BASE}/openai/whisper-large-v3-turbo"
HF_TRANSCRIPTION_FALLBACK_URL = f"{HF_INFERENCE_BASE}/openai/whisper-large-v3"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

EXT_TO_CONTENT_TYPE = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
}


def resolve_audio_content_type(
    content_type: Optional[str], filename: Optional[str]
) -> str:
    if content_type and content_type not in ("application/octet-stream", ""):
        return content_type
    if filename:
        ext = os.path.splitext(filename.lower())[1]
        if ext in EXT_TO_CONTENT_TYPE:
            return EXT_TO_CONTENT_TYPE[ext]
    return "audio/wav"


def _ndjson_line(payload: dict) -> str:
    return json.dumps(payload) + "\n"

# This function transcribes audio data using Hugging Face's Whisper API.
# 
# Arguments:
# - audio_bytes: The raw audio data to be transcribed.
# - content_type: (Optional) The MIME type of the audio.
# - filename: (Optional) The name of the audio file, used to deduce content type if not provided.
# - retries: How many times to retry if the model is still loading.
#
# Returns:
# - The transcribed text as a string.
#
# Raises:
# - ValueError if the HF_API_KEY is missing, the API consistently fails, or if it times out.
def transcribe_audio_api(
    audio_bytes: bytes,
    content_type: Optional[str] = None,
    filename: Optional[str] = None,
    retries: int = 3,
) -> str:
    # Ensure the Hugging Face API key is available.
    if not HF_API_KEY:
        raise ValueError("HF_API_KEY not configured in .env")

    # Determine the media (MIME) type, using the provided content_type or inferring from filename.
    media_type = resolve_audio_content_type(content_type, filename)
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": media_type,
    }

    # Try to transcribe, retrying if the model is loading.
    for i in range(retries):
        response = requests.post(
            HF_TRANSCRIPTION_URL, headers=headers, data=audio_bytes, timeout=120
        )

        if response.status_code == 200:
            # Success: return the transcribed text.
            return response.json().get("text", "")

        if response.status_code == 503:
            # Model is loading: wait for the suggested time and retry.
            wait_time = response.json().get("estimated_time", 20)
            print(f"Model loading... waiting {wait_time}s ({i + 1}/{retries})")
            time.sleep(wait_time)
            continue

        if response.status_code in (404, 405):
            # Endpoint may not be available; fall back to a backup URL.
            response = requests.post(
                HF_TRANSCRIPTION_FALLBACK_URL,
                headers=headers,
                data=audio_bytes,
                timeout=120,
            )
            if response.status_code == 200:
                return response.json().get("text", "")

        # Any other status codes are treated as errors.
        raise ValueError(f"HF transcription failed ({response.status_code}): {response.text}")

    # If all retries fail due to model still loading, raise a timeout error.
    raise ValueError("Transcription timed out while the model was loading.")


async def generate_stream(
    audio_bytes: bytes,
    content_type: Optional[str],
    filename: Optional[str],
):
    try:
        transcript = transcribe_audio_api(audio_bytes, content_type, filename)
    except ValueError as exc:
        yield _ndjson_line({"error": str(exc)})
        return

    if not transcript.strip():
        yield _ndjson_line({"error": "Transcription returned empty text."})
        return

    yield _ndjson_line({"type": "transcript", "content": transcript})

    if not OPENROUTER_API_KEY:
        yield _ndjson_line({"error": "OPENROUTER_API_KEY not configured in .env"})
        return

    system_prompt = """You produce minutes of meetings from transcripts. Output structured markdown with:
- ## Summary (attendees, location, date if known)
- ## Key discussion points
- ## Takeaways
- ## Action items (with owners if identifiable)
Be concise, professional. Use markdown without code blocks."""

    user_prompt = (
        f"Below is a meeting transcript. Write structured meeting minutes in markdown:\n\n{transcript}"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Meeting Minutes AI",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": True,
    }

    with requests.post(
        OPENROUTER_URL, headers=headers, json=payload, stream=True, timeout=120
    ) as response:
        if response.status_code != 200:
            try:
                err = response.json().get("error", {})
                message = err.get("message", response.text)
            except ValueError:
                message = response.text
            if response.status_code == 401 and "user not found" in message.lower():
                message = (
                    "Invalid OpenRouter API key. Create one at https://openrouter.ai/keys "
                    "and set OPENROUTER_API_KEY in .env, then restart the server."
                )
            yield _ndjson_line({"error": f"OpenRouter error: {message}"})
            return

        for line in response.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8")
            if not line_str.startswith("data: "):
                continue
            data_str = line_str[6:]
            if data_str == "[DONE]":
                break
            try:
                data_json = json.loads(data_str)
                chunk = data_json["choices"][0]["delta"].get("content", "")
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
            if chunk:
                yield _ndjson_line({"type": "chunk", "content": chunk})

    yield _ndjson_line({"type": "done"})


@app.post("/api/process-audio")
async def process_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    return StreamingResponse(
        generate_stream(audio_bytes, file.content_type, file.filename),
        media_type="application/x-ndjson",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
