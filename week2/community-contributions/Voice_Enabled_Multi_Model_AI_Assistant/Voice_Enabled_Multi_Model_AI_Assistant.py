import os
import gradio as gr
from openai import OpenAI
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

# Verify API keys are loaded
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=google_api_key)
claude_client = anthropic.Anthropic(api_key=anthropic_api_key)

# System prompt - Universal and comprehensive
SYSTEM_PROMPT = """You are a highly capable and versatile AI assistant designed to help with any type of question or task.

Your capabilities span across all domains including but not limited to:
- Programming, software development, and technology
- Science, mathematics, and engineering
- Arts, literature, and creative writing
- History, philosophy, and social sciences
- Business, finance, and economics
- Health, wellness, and lifestyle advice
- Education and learning support
- Problem-solving and critical thinking
- General knowledge and trivia
- Casual conversation and entertainment

Guidelines:
- Provide accurate, helpful, and comprehensive responses
- Adapt your tone and style to match the context of the question
- Use examples and explanations when helpful
- Be creative when asked for creative content
- Be precise and factual when asked for information
- Ask clarifying questions if the request is ambiguous
- Admit when you're uncertain and provide the best possible guidance
- Be conversational, friendly, and supportive

You can help with anything from technical coding problems to creative storytelling, from academic research to casual chat. There are no topic restrictions - feel free to engage with any subject matter the user brings up."""

# Model configurations
model_configs = {
    "GPT-4o": {"provider": "openai", "model": "gpt-4o"},
    "GPT-4o-mini": {"provider": "openai", "model": "gpt-4o-mini"},
    "GPT-3.5-turbo": {"provider": "openai", "model": "gpt-3.5-turbo"},
    "Claude Sonnet 4": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
    "Gemini 2.0 Flash": {"provider": "google", "model": "gemini-2.0-flash-exp"},
}

def chat_streaming(message, history, model_name, temperature):
    """Main chat function with streaming support"""
    
    config = model_configs[model_name]
    provider = config["provider"]
    model = config["model"]
    
    # Convert messages format history to API format
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "assistant", "content": msg["content"]})
    messages.append({"role": "user", "content": message})
    
    # Stream based on provider
    if provider == "openai":
        stream = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            temperature=temperature,
            stream=True
        )
        
        response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
                yield response
                
    elif provider == "anthropic":
        response = ""
        with claude_client.messages.stream(
            model=model,
            max_tokens=2000,
            temperature=temperature,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                response += text
                yield response
                
    elif provider == "google":
        gemini = genai.GenerativeModel(
            model_name=model,
            system_instruction=SYSTEM_PROMPT,
        )
        
        # Convert history for Gemini
        gemini_history = []
        for msg in history:
            if msg["role"] == "user":
                gemini_history.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                gemini_history.append({"role": "model", "parts": [msg["content"]]})
        
        chat = gemini.start_chat(history=gemini_history)
        
        stream = chat.send_message(
            message,
            stream=True,
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )
        
        response = ""
        for chunk in stream:
            response += chunk.text
            yield response

def handle_audio_input(audio):
    """Transcribe audio input using Whisper"""
    if audio is None:
        return ""
    
    try:
        audio_file = open(audio, "rb")
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

def text_to_speech(text):
    """Convert text response to speech"""
    try:
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text[:4096]  # Limit to prevent errors
        )
        
        audio_path = "response.mp3"
        response.stream_to_file(audio_path)
        return audio_path
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return None

# Custom CSS for modern, attractive UI
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.gradio-container {
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

:root .dark {
  --background-fill-primary: #f0f0f0;
  --body-background-fill: var(--background-fill-primary);
  --block-background-fill: white !important;
  --block-title-background-fill: #dfe7ff;
  --block-title-text-color:#6366f1;
  --body-text-color: black;
  --button-secondary-text-color:black;
  --input-background-fill:white;

  --block-label-background-fill:#dfe7ff;
  --block-label-text-color:#6366f1;

  --block-border-color:#eaeaea;
  --input-border-color: #eaeaea;
  --border-color-primary:#eaeaea;

  --color-accent-soft: #dfe7ff;
  --border-color-accent-subdued: #98a6cf;

  --checkbox-background-color: #eaeaea;
  --checkbox-border-color: #eaeaea;
  --background-fill-secondary:#eaeaea;
}

.main {
    background: white;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    padding: 0 !important;
    overflow: hidden;
}

.contain {
    padding: 2rem !important;
}

/* Header Styling */
.header-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px 20px 0 0;
    margin: -2rem 0rem 2rem 0rem;
    color: white;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
}

.header-section h1 {
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    margin: 0 0 0.5rem 0 !important;
    color: white !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.header-section p {
    font-size: 1.1rem !important;
    margin: 0.5rem 0 !important;
    color: rgba(255,255,255,0.95) !important;
    font-weight: 400;
}

.feature-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    padding: 0.4rem 1rem;
    border-radius: 20px;
    margin: 0.3rem;
    font-size: 0.9rem;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3);
}

/* Sidebar Styling */
.control-panel {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 1.5rem;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    height: 100%;
}

.control-panel label {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
}

/* Dropdown Styling */
.dropdown-container select {
    background: white !important;
    border: 2px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 0.75rem !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

.dropdown-container select:hover {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* Slider Styling */
input[type="range"] {
    accent-color: #667eea !important;
}

/* Button Styling */
.primary-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    transition: all 0.3s ease !important;
}

.primary-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
}

.secondary-btn {
    background: #e2e8f0 !important;
    border: none !important;
    color: #2d3748 !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}

.secondary-btn:hover {
    background: #cbd5e0 !important;
    transform: translateY(-2px) !important;
}

/* Chatbot Styling */
.chatbot-container {
    background: white;
    border-radius: 15px;
    border: 2px solid #e2e8f0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    overflow: hidden;
}

/* Input Box Styling */
.message-input textarea {
    border: 2px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
}

.message-input textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* Input Row Centering */
.input-row {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 1rem !important;
}

.input-row > * {
    flex-shrink: 0 !important;
}

/* Audio Components */
.audio-component {
    background: #f7fafc;
    border: 2px dashed #cbd5e0;
    border-radius: 12px;
    padding: 1rem;
    transition: all 0.3s ease;
}

.audio-component:hover {
    border-color: #667eea;
    background: #edf2f7;
}

/* Checkbox Styling */
.checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
    color: #2d3748;
}

/* Tips Section */
.tips-section {
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin-top: 2rem;
    border-left: 4px solid #667eea;
}

.tips-section h3 {
    color: #667eea !important;
    font-weight: 600 !important;
    margin-bottom: 1rem !important;
}

.tips-section ul {
    list-style: none;
    padding: 0;
}

.tips-section li {
    padding: 0.5rem 0;
    color: #4a5568 !important;
    font-size: 0.95rem;
}

.tips-section li:before {
    content: "→ ";
    color: #667eea;
    font-weight: bold;
    margin-right: 0.5rem;
}

/* Force black color for strong/bold text */
.tips-section strong {
    color: #1a202c !important;
}

.prose * {
    color: inherit !important;
}

.prose strong {
    color: #1a202c !important;
    font-weight: 600 !important;
}

/* Responsive Design */
@media (max-width: 768px) {
    .header-section h1 {
        font-size: 1.8rem !important;
    }
    
    .contain {
        padding: 1rem !important;
    }
}

.fillable{
    max-width:95% !important;
}
#component-5{
    flex-grow:1.1 !important;
}
.bubble-wrap.svelte-gjtrl6 {
    background:none !important;
}
.bot.svelte-1csv61q.message {
    background-color: white !important;
    border: 1px solid #f3f3f3;
}
.options.svelte-y6qw75> li:hover{
    background:white ;
}
.options.svelte-y6qw75> .selected{
    background:white ;
}

"""

# Build Gradio Interface
with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    
    # Header
    with gr.Row(elem_classes="header-section"):
        with gr.Column():
            gr.HTML("""
                <h1>🚀 Voice Enabled Multi Model AI-Assistant</h1>
                <p>Your intelligent companion for any question - from coding to creativity, science to storytelling!</p>
                <div style="margin-top: 1rem;">
                    <span class="feature-badge">🤖 7 AI Models</span>
                    <span class="feature-badge">🎤 Voice Input</span>
                    <span class="feature-badge">🔊 Audio Output</span>
                    <span class="feature-badge">⚡ Real-time Streaming</span>
                    <span class="feature-badge">🌐 Any Topic</span>
                </div>
            """)
    
    with gr.Row():
        # Left Sidebar - Controls
        with gr.Column(scale=1, elem_classes="control-panel"):
            gr.HTML("<h3 style='color: #2d3748 !important; margin-top: 0;'>⚙️ Settings</h3>")
            
            model_choice = gr.Dropdown(
                choices=list(model_configs.keys()),
                value="GPT-4o-mini",
                label="🤖 AI Model",
                info="Select your preferred model",
                elem_classes="dropdown-container"
            )
            
            temperature = gr.Slider(
                minimum=0,
                maximum=1,
                value=0.7,
                step=0.1,
                label="🌡️ Temperature",
                info="Higher = more creative responses"
            )
            
            gr.HTML("<div style='margin: 1.5rem 0 0.5rem 0; padding-top: 1.5rem; border-top: 2px solid #cbd5e0;'><h4 style='color: #2d3748 !important; margin: 0;'>🎙️ Audio Features</h4></div>")
            
            audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="🎤 Voice Input",
                elem_classes="audio-component"
            )
            
            audio_output_enabled = gr.Checkbox(
                label="🔊 Enable Audio Response",
                value=False,
                elem_classes="checkbox-label"
            )
        
        # Right Side - Chat Interface
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="💬 Conversation",
                height=550,
                show_copy_button=True,
                type='messages',
                elem_classes="chatbot-container",
                avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=ai")
            )
            
            with gr.Row(elem_classes="input-row"):
                msg = gr.Textbox(
                    label="",
                    placeholder="💭 Ask me anything - tech help, creative writing, life advice, science, history, or just chat!",
                    scale=5,
                    elem_classes="message-input",
                    show_label=False
                )
                submit_btn = gr.Button("Send 📤", scale=1, elem_classes="primary-btn")
            
            audio_response = gr.Audio(
                label="🔊 Audio Response", 
                visible=False,
                elem_classes="audio-component"
            )
            
            with gr.Row():
                clear_btn = gr.Button("🗑️ Clear Chat", elem_classes="secondary-btn")
    
    # Tips Section
    with gr.Row(elem_classes="tips-section"):
        gr.Markdown("""
        ### 💡 What Can I Help You With?
        
        - **Technology & Programming**: Debug code, explain concepts, build projects, learn new languages
        - **Creative Writing**: Stories, poems, scripts, brainstorming ideas, character development
        - **Education & Learning**: Homework help, concept explanations, study guides, tutoring
        - **Business & Career**: Resume writing, business plans, marketing ideas, career advice
        - **Science & Math**: Problem-solving, research assistance, concept explanations
        - **Daily Life**: Recipe suggestions, travel planning, health tips, relationship advice
        - **Entertainment**: Jokes, trivia, games, recommendations for books/movies/music
        - **And Literally Anything Else**: No topic is off-limits - just ask!
        """)
    
    # Event handlers
    def process_message(message, history, model, temp, audio_enabled):
        """Process message and optionally generate audio"""
        # Add user message to history
        history = history + [{"role": "user", "content": message}]
        
        # Generate text response (streaming)
        bot_message = None
        for response in chat_streaming(message, history[:-1], model, temp):
            bot_message = response
            yield history + [{"role": "assistant", "content": response}], None
        
        # Final history with complete response
        final_history = history + [{"role": "assistant", "content": bot_message}]
        
        # Generate audio if enabled
        if audio_enabled and bot_message:
            audio_path = text_to_speech(bot_message)
            yield final_history, audio_path
        else:
            yield final_history, None
    
    def transcribe_and_send(audio, history, model, temp, audio_enabled):
        """Transcribe audio and process message"""
        text = handle_audio_input(audio)
        if text and text != "" and not text.startswith("Error"):
            # Process the message and get results
            for hist, aud in process_message(text, history, model, temp, audio_enabled):
                yield hist, aud
        else:
            # If no text or error, return history unchanged
            yield history, None

    # Wire up events
    submit_btn.click(
        fn=process_message,
        inputs=[msg, chatbot, model_choice, temperature, audio_output_enabled],
        outputs=[chatbot, audio_response]
    ).then(lambda: "", None, msg)

    msg.submit(
        fn=process_message,
        inputs=[msg, chatbot, model_choice, temperature, audio_output_enabled],
        outputs=[chatbot, audio_response]
    ).then(lambda: "", None, msg)

    # Audio input handler using stop_recording event
    audio_input.stop_recording(
        fn=transcribe_and_send,
        inputs=[audio_input, chatbot, model_choice, temperature, audio_output_enabled],
        outputs=[chatbot, audio_response]
    )

    # Clear button clears chat, audio response, and audio input
    clear_btn.click(
        fn=lambda: ([], None, None), 
        inputs=None, 
        outputs=[chatbot, audio_response, audio_input]
    )

    # Toggle audio response visibility
    audio_output_enabled.change(
        fn=lambda x: gr.Audio(visible=x),
        inputs=audio_output_enabled,
        outputs=audio_response
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(share=False, debug=True)