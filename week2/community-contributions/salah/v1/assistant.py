import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import tempfile
import wave

load_dotenv()

class Assistant:
    def __init__(self):
        print("\n" + "="*60)
        print("Initializing Assistant...")
        print("="*60)

        openrouter_key = os.getenv('OPENAI_API_KEY')
        gemini_key = os.getenv('GEMINI_API_KEY')

        print(f"OpenRouter API Key: {openrouter_key[:20]}..." if openrouter_key else "OpenRouter API Key: NOT FOUND")
        print(f"Gemini API Key: {gemini_key[:20]}..." if gemini_key else "Gemini API Key: NOT FOUND")

        # OpenRouter client for text (GPT-4o-mini)
        print("Setting up OpenRouter client...")
        self.openrouter = OpenAI(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1"
        )
        print("OpenRouter client ready")

        # Gemini client for audio and images
        print("Setting up Gemini client...")
        self.gemini_client = genai.Client(api_key=gemini_key)
        print("Gemini client ready (audio + images)")

        self.text_model = "openai/gpt-4o-mini"
        self.system_prompt = "You are a helpful technical assistant. Keep answers clear and practical."
        self.stt_model = "gemini-2.0-flash-exp"
        self.tts_model = "gemini-2.5-flash-preview-tts"

        print(f"Text Model: {self.text_model}")
        print(f"STT Model: {self.stt_model}")
        print(f"TTS Model: {self.tts_model}")

    def chat(self, message, history=[]):
        print(f"[Chat] User: {message[:50]}...")
        print(f"[Chat] History messages: {len(history)}")
        print(f"[Chat] Model: {self.text_model}")

        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        print(f"[Chat] Total messages to send: {len(messages)}")
        print("[Chat] Calling OpenRouter API...")

        try:
            response = self.openrouter.chat.completions.create(
                model=self.text_model,
                messages=messages,
                extra_body={
                    "usage": {
                        "include": True
                    }
                }
            )
            reply = response.choices[0].message.content
            print(f"[Chat] Response received")
            print(f"[Chat] GPT-4o-mini: {len(reply)} chars")
            print(f"[Chat] Preview: {reply[:100]}...")

            # Print usage and cost
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                print(f"[Chat] Usage:")
                print(f"  - Prompt tokens: {usage.prompt_tokens}")
                print(f"  - Completion tokens: {usage.completion_tokens}")
                print(f"  - Total tokens: {usage.total_tokens}")
                if hasattr(usage, 'cost') and usage.cost:
                    print(f"  - Cost: ${usage.cost:.6f}")

            print("-"*60 + "\n")
            return reply
        except Exception as e:
            print(f"[Error] ✗ API call failed: {e}")
            print("-"*60 + "\n")
            return f"Error: {str(e)}"

    def analyze_code(self, code, language="python"):
        print("\n" + "="*60)
        print(f"[Code] Analyzing {language} code...")
        print(f"[Code] Code length: {len(code)} characters")
        print(f"[Code] Lines: {len(code.splitlines())}")
        print("="*60)

        prompt = f"Analyze this {language} code for bugs and improvements:\n\n```{language}\n{code}\n```"
        result = self.chat(prompt)

        print("[Code] Analysis complete\n")
        return result

    def generate_image(self, description):
        print("\n" + "="*60)
        print(f"[Image] Gemini generating: {description[:50]}...")
        print(f"[Image] Model: gemini-2.0-flash-exp")

        try:
            prompt = f"Generate an image of: {description}. Make it clear and professional."
            print("[Image] Calling Gemini API...")
            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            print("[Image] Response received")
            print(f"[Image] Result length: {len(response.text)} chars")

            # Print usage and cost (Gemini 2.0 Flash: $0.30/1M input, $2.50/1M output)
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                total_tokens = usage.total_token_count
                cost = (input_tokens * 0.30 + output_tokens * 2.50) / 1_000_000
                print(f"[Image] Usage:")
                print(f"  - Input tokens: {input_tokens}")
                print(f"  - Output tokens: {output_tokens}")
                print(f"  - Total tokens: {total_tokens}")
                print(f"  - Cost: ${cost:.6f}")

            print("="*60 + "\n")
            return response.text
        except Exception as e:
            print(f"[Error] ✗ Image generation failed: {e}")
            print("="*60 + "\n")
            return None

    def speech_to_text(self, audio_file_path):
        print("\n" + "="*60)
        print("[STT] Gemini speech-to-text...")
        print(f"[STT] Audio file: {audio_file_path}")

        try:
            print("[STT] Uploading audio file to Gemini...")
            audio_file = self.gemini_client.files.upload(file=audio_file_path)
            print(f"[STT] File uploaded: {audio_file.name}")

            print("[STT] Transcribing with Gemini...")
            prompt = "Generate a transcript of the speech."

            response = self.gemini_client.models.generate_content(
                model=self.stt_model,
                contents=[prompt, audio_file]
            )
            text = response.text.strip()

            print(f"[STT] Transcribed: {text[:100]}...")
            print(f"[STT] Length: {len(text)} chars")

            # Print usage and cost (Flash Native Audio Input: $3.00/1M tokens)
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                total_tokens = usage.total_token_count
                # Audio input is $3.00/1M, text output is $2.50/1M
                cost = (input_tokens * 3.00 + output_tokens * 2.50) / 1_000_000
                print(f"[STT] Usage:")
                print(f"  - Input tokens (audio): {input_tokens}")
                print(f"  - Output tokens (text): {output_tokens}")
                print(f"  - Total tokens: {total_tokens}")
                print(f"  - Cost: ${cost:.6f}")

            print("="*60 + "\n")

            return text

        except Exception as e:
            print(f"[Error] ✗ STT failed: {e}")
            print(f"[Error] Full error: {type(e).__name__}: {str(e)}")
            print("="*60 + "\n")
            return None

    def text_to_speech(self, text):
        print("\n" + "="*60)
        print(f"[TTS] Gemini text-to-speech...")
        print(f"[TTS] Text: {text[:50]}...")
        print(f"[TTS] Length: {len(text)} chars")

        try:
            # Limit text length for TTS
            text_to_speak = text[:500] if len(text) > 500 else text

            print("[TTS] Generating audio with Gemini TTS model...")
            response = self.gemini_client.models.generate_content(
                model=self.tts_model,
                contents=f"Say cheerfully: {text_to_speak}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name='Kore',
                            )
                        )
                    ),
                )
            )

            print("[TTS] Audio generated, converting to WAV...")

            # Extract raw PCM audio data
            pcm_data = response.candidates[0].content.parts[0].inline_data.data
            print(f"[TTS] Raw PCM size: {len(pcm_data)} bytes")

            # Print usage and cost (2.5 Flash Preview TTS: $10.00/1M audio output tokens)
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                total_tokens = usage.total_token_count
                # Text input is $0.30/1M, audio output is $10.00/1M
                cost = (input_tokens * 0.30 + output_tokens * 10.00) / 1_000_000
                print(f"[TTS] Usage:")
                print(f"  - Input tokens (text): {input_tokens}")
                print(f"  - Output tokens (audio): {output_tokens}")
                print(f"  - Total tokens: {total_tokens}")
                print(f"  - Cost: ${cost:.6f}")

            # Create WAV file with proper headers
            # Gemini TTS outputs: 24kHz sample rate, mono, 16-bit PCM
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)        # Mono
                wav_file.setsampwidth(2)        # 16-bit = 2 bytes
                wav_file.setframerate(24000)    # 24kHz
                wav_file.writeframes(pcm_data)

            temp_file.close()

            print(f"[TTS] WAV file saved: {temp_file.name}")
            print("="*60 + "\n")
            return temp_file.name

        except Exception as e:
            print(f"[Error] ✗ TTS failed: {e}")
            print(f"[Error] Full error: {type(e).__name__}: {str(e)}")
            print("="*60 + "\n")
            return None


if __name__ == "__main__":
    assistant = Assistant()

    # Test it
    response = assistant.chat("What is Python?")
    print(f"\nResponse: {response}")
