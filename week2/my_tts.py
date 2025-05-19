import gradio as gr
import pyttsx3

# Initialize TTS engine
engine = pyttsx3.init()

# Optional: customize voice properties (rate, volume)
engine.setProperty('rate', 150)      # speed (default ~200)
engine.setProperty('volume', 1.0)    # 0.0 to 1.0

# Get available voices (for Mac, use 'com.apple.speech.synthesis.voice.samantha' or similar)
voices = engine.getProperty('voices')
voice_names = [v.name for v in voices]
voice_id_map = {v.name: v.id for v in voices}

# Function that converts text to speech
def read_text(text, voice_choice):
    engine.setProperty('voice', voice_id_map[voice_choice])
    engine.say(text)
    engine.runAndWait()
    return f"✅ Done reading {len(text)} characters."

# Gradio interface
iface = gr.Interface(
    fn=read_text,
    inputs=[
        gr.Textbox(lines=10, label="Enter text to read aloud"),
        gr.Dropdown(choices=voice_names, label="Choose voice", value=voice_names[0]),
    ],
    outputs="text",
    title="🗣️ Text-to-Speech Agent (Offline & Free)",
    description="Paste any text and click to read it aloud using your Mac's voice engine."
)

if __name__ == "__main__":
    iface.launch()