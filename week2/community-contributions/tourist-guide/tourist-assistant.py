import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr


# Initialization

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
MODEL = "gpt-4o-mini"
openai = OpenAI()


# Audio generation
    
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
def talker(message):
        response=openai.audio.speech.create(
            
            model="tts-1",
            voice="onyx",
            input=message
        )
        audio_stream=BytesIO(response.content)
        audio=AudioSegment.from_file(audio_stream, format="mp3")
        play(audio)

system_message = "You are a helpful assistant for tourists visiting a city."
system_message += "Help the user and give him or her good explanation about the cities or places."
system_message += "Talk about history, geography and current conditions."
system_message += "Start with a short explanation about three lines and when the user wants explain more."

#gradio handles the history of user messages and the assistant responses

def chat(history):
    messages = [{"role": "system", "content": system_message}] + history
    response = openai.chat.completions.create(model=MODEL, messages=messages)
   
    reply = response.choices[0].message.content
    history += [{"role":"assistant", "content":reply}]

    talker(reply)
    
    return history

def transcribe_audio(audio_path):
   
    try:
        # Check if audio_path is valid
        if audio_path is None:
            return "No audio detected. Please record again."
        
        # Open the audio file
        with open(audio_path, "rb") as audio_file:
             transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        return transcript.text
    
    except Exception as e:
        return f"Error during transcription: {str(e)}"




##################Interface with Gradio##############################

theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="indigo",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Poppins"), "ui-sans-serif", "system-ui", "sans-serif"]
)

# Load CSS from external file
with open('style.css', 'r') as f:
    css = f.read()

with gr.Blocks(theme=theme, css=css) as ui:
    with gr.Column(elem_classes="container"):
        gr.Markdown("# 🌍 Tourist Assistant", elem_classes="title")
        gr.Markdown("Ask about any city, landmark, or destination around the world", elem_classes="subtitle")
        
        with gr.Blocks() as demo:
            gr.Image("travel.jpg", show_label=False, height=150, container=False, interactive=False)
 
        with gr.Column(elem_classes="chatbot-container"):
            chatbot = gr.Chatbot(
                height=400, 
                type="messages",
                bubble_full_width=False,
                show_copy_button=True,
                elem_id="chatbox"
            )
        
        with gr.Row():
            entry = gr.Textbox(
                label="",
                placeholder="Type your question here or use the microphone below...",
                container=False,
                lines=2,
                scale=10
            )
            
            with gr.Column(scale=1, elem_classes="clear-button"):
                clear = gr.Button("Clear", variant="secondary", size="sm")
        
        with gr.Row(elem_classes="mic-container"):
            audio_input = gr.Audio(
                type="filepath",
                label="🎤 Record",
                sources=["microphone"],
                streaming=False,
                interactive=True,
                autoplay=False,
                show_download_button=False,
                show_share_button=False,
                elem_id="mic-button"
            )
        
            
    def transcribe_and_submit(audio_path):
        transcription = transcribe_audio(audio_path)
        history = chatbot.value if chatbot.value else []
        history += [{"role":"user", "content":transcription}]
        return transcription, history, history, None
        
    audio_input.stop_recording(
        fn=transcribe_and_submit,
        inputs=[audio_input],
        outputs=[entry, chatbot, chatbot, audio_input]
    ).then(
        chat, inputs=chatbot, outputs=[chatbot]
    )

    def do_entry(message, history):
        history += [{"role":"user", "content":message}]
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot]
    )
    clear.click(lambda: None, inputs=None, outputs=chatbot, queue=False)

ui.launch(inbrowser=True)
