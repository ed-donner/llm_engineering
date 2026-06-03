import gradio as gr
from simple_assistant import Assistant

class SimpleUI:
    def __init__(self):
        print("\n" + "="*60)
        print("Starting up...")
        print("="*60)
        self.assistant = Assistant()
        self.history = []  # Text history for API
        self.display_history = []  # Display history with audio for chat UI
        self.audio_enabled = True
        print("UI initialized")
        print("Audio features: Gemini STT + TTS")
        print("="*60 + "\n")

    def add_message(self, msg):
        print("\n" + ">"*60)
        print(f"[UI] New message: {msg[:50]}...")

        if not msg.strip():
            print("[UI] Empty message, ignoring")
            print(">"*60 + "\n")
            return self.display_history, ""

        print(f"[UI] Adding to history (current: {len(self.history)} messages)")
        # Add to API history (text only)
        self.history.append({"role": "user", "content": msg})
        # Add to display history
        self.display_history.append({"role": "user", "content": msg})

        print("[UI] Getting AI response...")
        response = self.assistant.chat(msg, self.history)

        print(f"[UI] Adding response to history")
        # Add to API history (text only)
        self.history.append({"role": "assistant", "content": response})
        # Add to display history
        self.display_history.append({"role": "assistant", "content": response})
        print(f"[UI] Total history: {len(self.history)} messages")

        print(f"[UI] Returning {len(self.display_history)} messages to display")
        print(">"*60 + "\n")
        return self.display_history, ""

    def handle_voice_input(self, audio_file):
        print("\n" + ">"*60)
        print("[UI] Voice input received")
        print(f"[UI] Audio file: {audio_file}")

        if not audio_file:
            print("[UI] No audio file")
            print(">"*60 + "\n")
            return self.display_history, None

        # Transcribe
        print("[UI] Transcribing with Gemini...")
        text = self.assistant.speech_to_text(audio_file)

        if not text:
            print("[UI] Transcription failed")
            print(">"*60 + "\n")
            error_msg = "Sorry, couldn't transcribe audio"
            self.history.append({"role": "assistant", "content": error_msg})
            self.display_history.append({"role": "assistant", "content": error_msg})
            return self.display_history, None

        print(f"[UI] Transcribed: {text}")

        # Add to API history (text only)
        self.history.append({"role": "user", "content": text})

        # Add voice message to display history with audio file
        self.display_history.append({
            "role": "user",
            "content": {
                "path": audio_file,
                "alt_text": f"🎤 {text}"
            }
        })

        # Get response
        print("[UI] Getting AI response...")
        response = self.assistant.chat(text, self.history)

        # Add text response to API history
        self.history.append({"role": "assistant", "content": response})

        # Generate audio response
        print("[UI] Generating audio with Gemini TTS...")
        audio_response = self.assistant.text_to_speech(response)

        if audio_response:
            print(f"[UI] ✓ Audio response generated")
            # Add response with audio to display history
            self.display_history.append({
                "role": "assistant",
                "content": {
                    "path": audio_response,
                    "alt_text": f"🔊 {response[:100]}..."
                }
            })
        else:
            print(f"[UI] ⚠ No audio, text only")
            self.display_history.append({"role": "assistant", "content": response})

        print(f"[UI] Returning {len(self.display_history)} messages")
        print(">"*60 + "\n")

        return self.display_history, None

    def analyze(self, code, lang):
        print("\n" + ">"*60)
        print(f"[UI] Code analysis request")
        print(f"[UI] Language: {lang}")
        print(f"[UI] Code length: {len(code)} chars")

        if not code.strip():
            print("[UI] Empty code, ignoring")
            print(">"*60 + "\n")
            return self.display_history

        print("[UI] Calling analyze_code...")
        result = self.assistant.analyze_code(code, lang)

        print("[UI] Adding to history")
        # Add to API history
        self.history.append({"role": "user", "content": f"Analyze {lang} code"})
        self.history.append({"role": "assistant", "content": result})

        # Add to display history
        self.display_history.append({"role": "user", "content": f"Analyze {lang} code"})
        self.display_history.append({"role": "assistant", "content": result})

        print(f"[UI] Returning {len(self.display_history)} messages")
        print(">"*60 + "\n")
        return self.display_history

    def create_ui(self):
        print("\n" + "="*60)
        print("Creating Gradio UI...")
        print("="*60)

        with gr.Blocks() as app:

            gr.Markdown("# Tech Assistant")
            gr.Markdown("**Voice-enabled**: Type or record audio messages")

            # Chat panel - shows all messages including audio
            chat = gr.Chatbot(type="messages", height=500)
            print("✓ Chatbot created")

            # Input area at bottom (like ChatGPT)
            with gr.Row():
                msg = gr.Textbox(
                    label="Message",
                    placeholder="Type a message or record audio...",
                    scale=9,
                    container=False
                )
                mic = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎤 Record",
                    scale=1,
                    waveform_options={"show_controls": False}
                )
            print("✓ Message and record inputs created")

            # Wire events
            msg.submit(self.add_message, msg, [chat, msg])
            print("✓ Message submit event wired")

            mic.stop_recording(self.handle_voice_input, mic, [chat, mic])
            print("✓ Voice input event wired")

            # Tools section
            with gr.Accordion("Tools", open=False):

                gr.Markdown("### Code Analysis")
                code = gr.Textbox(label="Code", lines=8)
                lang = gr.Dropdown(
                    choices=["python", "javascript", "java"],
                    value="python",
                    label="Language"
                )
                analyze_btn = gr.Button("Analyze")
                print("✓ Code analysis tools created")

                analyze_btn.click(self.analyze, [code, lang], chat)
                print("✓ Analyze button event wired")

        print("✓ UI creation complete")
        print("="*60 + "\n")
        return app

    def launch(self):
        print("\n" + "="*60)
        print("Launching Gradio app...")
        print("="*60)
        app = self.create_ui()
        print("Starting server on port 7862...")
        print("="*60 + "\n")
        app.launch(server_port=7862)


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# TECH ASSISTANT - SIMPLE UI")
    print("#"*60 + "\n")

    ui = SimpleUI()
    ui.launch()
