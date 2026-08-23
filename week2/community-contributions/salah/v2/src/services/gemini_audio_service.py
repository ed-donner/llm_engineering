from google import genai
from google.genai import types
import tempfile
import wave
from interfaces.ai_client import AudioService

class GeminiAudioService(AudioService):
    def __init__(self, api_key, stt_model, tts_model, voice_name):
        self.client = genai.Client(api_key=api_key)
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.voice_name = voice_name
        
    def speech_to_text(self, audio_file):
        print(f"[Gemini STT] Processing audio file: {audio_file}")
        print(f"[Gemini STT] Model: {self.stt_model}")
        
        try:
            # Get file size for logging
            import os
            file_size = os.path.getsize(audio_file)
            print(f"[Gemini STT] Audio file size: {file_size} bytes")
            
            print("[Gemini STT] Uploading to Gemini...")
            uploaded_file = self.client.files.upload(file=audio_file)
            print(f"[Gemini STT] File uploaded: {uploaded_file.name}")
            
            print("[Gemini STT] Transcribing...")
            response = self.client.models.generate_content(
                model=self.stt_model,
                contents=["Transcribe the speech in this audio file. Return only the spoken words, nothing else.", uploaded_file]
            )
            
            text = response.text.strip()
            print(f"[Gemini STT] Transcription length: {len(text)} chars")
            print(f"[Gemini STT] Transcription: {text[:100]}...")
            
            # Print usage information if available
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                total_tokens = usage.total_token_count
                
                # Audio input cost: $3.00/1M tokens, text output: $2.50/1M tokens
                cost = (input_tokens * 3.00 + output_tokens * 2.50) / 1_000_000
                
                print(f"[Gemini STT] Token usage:")
                print(f"  - Input tokens (audio): {input_tokens}")
                print(f"  - Output tokens (text): {output_tokens}")
                print(f"  - Total tokens: {total_tokens}")
                print(f"  - Estimated cost: ${cost:.6f}")
            
            print("[Gemini STT] Success")
            return text
            
        except Exception as e:
            print(f"[Gemini STT] Error: {e}")
            return None
    
    def text_to_speech(self, text):
        print(f"[Gemini TTS] Converting text to speech")
        print(f"[Gemini TTS] Model: {self.tts_model}, Voice: {self.voice_name}")
        print(f"[Gemini TTS] Input text length: {len(text)} chars")
        
        try:
            # Keep it short for TTS
            text_to_speak = text[:500] if len(text) > 500 else text
            if len(text) > 500:
                print(f"[Gemini TTS] Text truncated to 500 chars")
            
            print(f"[Gemini TTS] Text preview: {text_to_speak[:100]}...")
            print("[Gemini TTS] Generating audio...")
            
            response = self.client.models.generate_content(
                model=self.tts_model,
                contents=f"Say: {text_to_speak}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name,
                            )
                        )
                    ),
                )
            )
            
            pcm_data = response.candidates[0].content.parts[0].inline_data.data
            print(f"[Gemini TTS] Raw PCM data size: {len(pcm_data)} bytes")
            
            # Print usage information if available
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                total_tokens = usage.total_token_count
                
                # Text input: $0.30/1M tokens, audio output: $10.00/1M tokens
                cost = (input_tokens * 0.30 + output_tokens * 10.00) / 1_000_000
                
                print(f"[Gemini TTS] Token usage:")
                print(f"  - Input tokens (text): {input_tokens}")
                print(f"  - Output tokens (audio): {output_tokens}")
                print(f"  - Total tokens: {total_tokens}")
                print(f"  - Estimated cost: ${cost:.6f}")
            
            # Create WAV file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  
                wav_file.setframerate(24000)
                wav_file.writeframes(pcm_data)
            
            temp_file.close()
            print(f"[Gemini TTS] WAV file created: {temp_file.name}")
            print("[Gemini TTS] Success")
            return temp_file.name
            
        except Exception as e:
            print(f"[Gemini TTS] Error: {e}")
            return None