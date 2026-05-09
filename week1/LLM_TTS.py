import asyncio
import base64
import os
import pyaudio
from sarvamai import AsyncSarvamAI, AudioOutput, EventResponse
import sarvamai.text_to_speech_streaming.client as _sar_tts_ws
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("SARVAM_API_KEY")

# Sarvam SDK passes explicit ping_interval/ping_timeout into connect(); setdefault
# does not override them. Default 20s/20s often hits ConnectionClosedError (1011
# "keepalive ping timeout") on slower or busy links. Disable client keepalive pings;
# TTS streaming already sends frames so the socket is not idle for long.
orig_ws_connect = _sar_tts_ws.websockets_client_connect


def _ws_connect_relaxed(*args, **kwargs):
    # Must return the same Connect instance as the real client.connect — not a
    # coroutine — so Sarvam's `async with websockets_client_connect(...)` works.
    kwargs["ping_interval"] = None
    kwargs["ping_timeout"] = None
    return orig_ws_connect(*args, **kwargs)


_sar_tts_ws.websockets_client_connect = _ws_connect_relaxed

# ─── Audio Playback Setup ─────────────────────────────────────────────────────

SAMPLE_RATE = 16000       # Hz — best for real-time voice streaming
CHANNELS = 1              # Mono
FORMAT = pyaudio.paInt16  # linear16 PCM format

p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    output=True
)

# ─── Sarvam Client ───────────────────────────────────────────────────────────

client = AsyncSarvamAI(api_subscription_key=api_key)

# ─── System & User Prompts ───────────────────────────────────────────────────

system_prompt = """
You are a helpful and concise voice assistant.
Keep answers short (2-4 sentences) since the response will be spoken aloud.
Avoid bullet points, markdown, or special characters.
Use simple, conversational language.
"""

user_prompt = "What is climate change and why does it matter?"

# ─── Main Pipeline ───────────────────────────────────────────────────────────

async def live_audio_playback():

    # Step 1: Get answer from Chat model
    print("Getting answer from chat model...")
    chat_response = await client.chat.completions(
        model="sarvam-m",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ]
    )

    answer_text = chat_response.choices[0].message.content
    print(f"Answer: {answer_text}\n")
    print("Streaming audio in real time...\n")

    # Step 2: Connect to WebSocket TTS and stream audio
    async with client.text_to_speech_streaming.connect(
        model="bulbul:v3",
        send_completion_event=True
    ) as ws:

        # Configure voice — use linear16 for direct PCM playback (no decoding overhead)
        await ws.configure(
            target_language_code="en-IN",   # change to "hi-IN", "ta-IN", etc.
            speaker="shubh",
            pace=1.0,
            output_audio_codec="linear16",  # raw PCM — best for live playback
            speech_sample_rate=SAMPLE_RATE
        )

        # Send chat answer to TTS
        await ws.convert(answer_text)
        await ws.flush()  # force immediate processing

        # Step 3: Play each audio chunk immediately as it arrives
        async for message in ws:
            if isinstance(message, AudioOutput):
                audio_chunk = base64.b64decode(message.data.audio)
                # PyAudio blocks; run off the event loop so WebSocket ping/pong still runs.
                await asyncio.to_thread(stream.write, audio_chunk)

            elif isinstance(message, EventResponse):
                if message.data.event_type == "final":
                    print("\nPlayback complete.")
                    break

    # Cleanup
    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == "__main__":
    asyncio.run(live_audio_playback())
