import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.openrouter_key = os.getenv('OPENAI_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        
        # Models - all configurable via env
        self.text_model = os.getenv('TEXT_MODEL', "openai/gpt-4o-mini")
        self.stt_model = os.getenv('STT_MODEL', "gemini-2.0-flash-exp")
        self.tts_model = os.getenv('TTS_MODEL', "gemini-2.5-flash-preview-tts")
        self.voice_name = os.getenv('VOICE_NAME', 'Kore')
        
        # App settings
        self.port = int(os.getenv('PORT', '7862'))
        self.system_prompt = os.getenv('SYSTEM_PROMPT', "You are a helpful assistant. Keep it simple and practical.")
        
    def validate(self):
        if not self.openrouter_key:
            raise Exception("Missing OPENAI_API_KEY")
        if not self.gemini_key:
            raise Exception("Missing GEMINI_API_KEY")