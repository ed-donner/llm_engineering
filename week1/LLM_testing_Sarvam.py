from sarvamai import SarvamAI
import os
from dotenv import load_dotenv
import base64
import io
import pygame
load_dotenv(override=True)
api_key = os.getenv("SARVAM_API_KEY")

client = SarvamAI(
    api_subscription_key=api_key
)
response = client.text.translate(
    input="Hi, My Name is Vinayak.",
    source_language_code="auto",
    target_language_code="hi-IN",
    speaker_gender="Male"
)

translated_text = response.translated_text

tts_response = client.text_to_speech.convert(
    text=translated_text,
    target_language_code="hi-IN",
    model="bulbul:v3",
    speaker="shubh"
)

combined_audio = "".join(tts_response.audios)
audio_bytes = base64.b64decode(combined_audio)
# Play in memory
pygame.mixer.init()
pygame.mixer.music.load(io.BytesIO(audio_bytes))
pygame.mixer.music.play()
while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(10)