from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()
import gradio as gr
import base64
from io import BytesIO
from PIL import Image
from IPython.display import Audio, display
import google.generativeai
import anthropic

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure Gemini
google.generativeai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Configure Claude
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openAI_model = "gpt-3.5-turbo"
gemini_model = "gemini-2.0-flash"
claude_model = "claude-sonnet-4-20250514"
openai_audio_model = "tts-1"

# Figma onboarding knowledge base
FIGMA_KNOWLEDGE = """
You are a helpful Figma onboarding assistant. You help new users learn Figma's core features and workflows.

Key Figma concepts to help users with:
- Interface overview (toolbar, layers panel, properties panel)
- Creating and editing frames
- Working with shapes, text, and components
- Using the pen tool for custom shapes
- Auto Layout for responsive designs
- Components and variants
- Prototyping and interactions
- Collaboration features
- Design systems and libraries
- Exporting assets
- Keyboard shortcuts

Always provide clear, step-by-step instructions and mention relevant keyboard shortcuts when applicable.
"""

promts = {
    "Charlie": FIGMA_KNOWLEDGE
}

def truncate_for_tts(text, max_length=4000):
    """Truncate text for TTS while preserving complete sentences"""
    if len(text) <= max_length:
        return text
    
    # Try to truncate at sentence boundaries
    sentences = text.split('. ')
    truncated = ""
    
    for sentence in sentences:
        if len(truncated + sentence + '. ') <= max_length:
            truncated += sentence + '. '
        else:
            break
    
    # If we couldn't fit any complete sentences, just truncate hard
    if not truncated.strip():
        truncated = text[:max_length-10] + "..."
    
    return truncated.strip()

def talker_openai(message):
    """Generate audio from text using OpenAI TTS"""
    try:
        # Truncate message for TTS
        truncated_message = truncate_for_tts(message)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=truncated_message
        )

        audio_stream = BytesIO(response.content)
        output_filename = "output_audio_openai.mp3"
        with open(output_filename, "wb") as f:
            f.write(audio_stream.read())

        return output_filename
    except Exception as e:
        print(f"Error generating audio with OpenAI: {str(e)}")
        return None

def talker(message, model_choice):
    """Generate audio from text using selected model"""
    return talker_openai(message)

def get_figma_help_openai(user_question, chat_history):
    """Get Figma onboarding assistance using OpenAI"""
    try:
        messages = [
            {"role": "system", "content": FIGMA_KNOWLEDGE}
        ]
        
        # Convert messages format chat history to OpenAI format
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                messages.append({"role": "assistant", "content": msg["content"]})
        
        messages.append({"role": "user", "content": user_question})
        
        response = client.chat.completions.create(
            model=openAI_model,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Sorry, I encountered an error with OpenAI: {str(e)}"

def get_figma_help_gemini(user_question, chat_history):
    """Get Figma onboarding assistance using Gemini"""
    try:
        gemini = google.generativeai.GenerativeModel(
            model_name=gemini_model,
            system_instruction=FIGMA_KNOWLEDGE,
        )
        
        # Build conversation context from messages format
        conversation_context = ""
        for msg in chat_history:
            if msg["role"] == "user":
                conversation_context += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                conversation_context += f"Assistant: {msg['content']}\n\n"
        
        message = conversation_context + f"User: {user_question}"
        response = gemini.generate_content(message)
        reply = response.text
        return reply
        
    except Exception as e:
        return f"Sorry, I encountered an error with Gemini: {str(e)}"

def get_figma_help_claude(user_question, chat_history):
    """Get Figma onboarding assistance using Claude"""
    try:
        # Convert messages format to Claude format
        claude_messages = []
        for msg in chat_history:
            if msg["role"] == "user":
                claude_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                claude_messages.append({"role": "assistant", "content": msg["content"]})
        
        # Add the current question
        claude_messages.append({"role": "user", "content": user_question})
        
        response = claude.messages.create(
            model=claude_model,
            max_tokens=500,
            temperature=0.7,
            system=promts["Charlie"],
            messages=claude_messages,
        )
        reply = response.content[0].text
        return reply
        
    except Exception as e:
        return f"Sorry, I encountered an error with Claude: {str(e)}"

def respond(message, chat_history, model_choice):
    if not message.strip():
        return "", chat_history, "", model_choice
    
    bot_message = get_figma_help(message, chat_history, model_choice)
    
    # Add user message and bot response in messages format
    new_history = chat_history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": bot_message}
    ]
    
    return "", new_history, bot_message, model_choice

def clear_chat():
    """Clear the chat history"""
    return [], "", None

def get_figma_help(user_question, chat_history, model_choice):
    """Get Figma onboarding assistance using selected model"""
    if model_choice == "OpenAI (GPT-3.5)":
        return get_figma_help_openai(user_question, chat_history)
    elif model_choice == "Google Gemini (2.0 Flash)":
        return get_figma_help_gemini(user_question, chat_history)
    elif model_choice == "Claude (Sonnet 4)":
        return get_figma_help_claude(user_question, chat_history)
    else:
        return "Please select a valid model."

custom_css = """
/* Chat area styling */
.styled-chat {
    border-radius: 15px !important;
    box-shadow: 0 4px 12px var(--shadow-color) !important;
    border: 1px solid var(--border-color) !important;
    padding: 10px;
}

/* Audio player styling */
.styled-audio {
    border-radius: 15px !important;
    box-shadow: 0 4px 12px var(--shadow-color) !important;
    border: 10px solid var(--block-background-fill) !important;
    padding: 10px;
    background-color: var(--background-fill-secondary) !important;
}

/* Header styling */
.header-container {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    margin-bottom: 20px;
}

.header-title {
    color: white;
    margin: 0;
    font-size: 2.5em;
}

.header-subtitle {
    color: #f0f0f0;
    margin: 10px 0 0 0;
    font-size: 1.2em;
}

/* Features section styling */
.features-container {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #667eea;
}

.features-title {
    color: #333;
    margin-top: 0;
}

.features-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-top: 15px;
}

.feature-item {
    color: #333;
    margin: 10px 0;
}

.feature-title {
    color: #667eea;
}

.feature-description {
    color: #666;
}

/* Pro tip styling */
.protip-container {
    text-align: center;
    margin-top: 20px;
    padding: 15px;
    background: #e8f4f8;
    border-radius: 8px;
}

.protip-text {
    margin: 0;
    color: #2c5aa0 !important;
    font-weight: 500;
}

/* Quick start questions styling */
.quickstart-container {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    padding: 15px 20px;
    border-radius: 10px;
}

.quickstart-title {
    color: white !important;
    margin: 0;
    font-size: 1.3em;
    text-align: center;
}

.quickstart-subtitle {
    color: #f0f8ff !important;
    margin: 5px 0 0 0;
    text-align: center;
    font-size: 0.9em;
}
"""

# Create Gradio interface
with gr.Blocks(title="Figma Onboarding Assistant", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.HTML(
        """
        <div class="header-container">
            <h1 class="header-title">🎨 Figma AI Assistant</h1>
            <p class="header-subtitle">Your AI-powered Figma learning companion</p>
        </div>
        
        <div class="features-container">
            <h3 class="features-title">✨ What I can help you with:</h3>
            <div class="features-grid">
                <div>
                    <p class="feature-item"><strong class="feature-title">🚀 Getting Started</strong><br/>
                    <span class="feature-description">Interface overview, basic navigation</span></p>
                    <p class="feature-item"><strong class="feature-title">🛠️ Tools & Features</strong><br/>
                    <span class="feature-description">Pen tool, shapes, text, layers</span></p>
                    <p class="feature-item"><strong class="feature-title">📐 Auto Layout</strong><br/>
                    <span class="feature-description">Responsive design techniques</span></p>
                    <p class="feature-item"><strong class="feature-title">🔗 Prototyping</strong><br/>
                    <span class="feature-description">Interactions and animations</span></p>
                </div>
                <div>
                    <p class="feature-item"><strong class="feature-title">🧩 Components</strong><br/>
                    <span class="feature-description">Creating reusable elements</span></p>
                    <p class="feature-item"><strong class="feature-title">👥 Collaboration</strong><br/>
                    <span class="feature-description">Sharing and team workflows</span></p>
                    <p class="feature-item"><strong class="feature-title">📚 Design Systems</strong><br/>
                    <span class="feature-description">Libraries and style guides</span></p>
                    <p class="feature-item"><strong class="feature-title">⚡ Shortcuts</strong><br/>
                    <span class="feature-description">Productivity tips and tricks</span></p>
                </div>
            </div>
        </div>
        
        <div class="protip-container">
            <p class="protip-text">💡 Pro tip: Ask specific questions like "How do I create a button component?" for the best results!</p>
        </div>
        """
    )
    
    # Example questions
    gr.HTML(
        """
        <div class="quickstart-container">
            <h3 class="quickstart-title">🚀 Quick Start Questions</h3>
            <p class="quickstart-subtitle">Click any question below to get started instantly!</p>
        </div>
        """
    )

    with gr.Row():
        example_btns = [
            gr.Button(
                "How do I create my first frame?", 
                size="sm",
                variant="secondary"
            ),
            gr.Button(
                "What's the difference between components and instances?", 
                size="sm",
                variant="secondary"
            ),
            gr.Button(
                "How do I use Auto Layout?", 
                size="sm",
                variant="secondary"
            ),
            gr.Button(
                "How do I create a prototype?", 
                size="sm",
                variant="secondary"
            )
        ]

    # Model selection dropdown
    model_dropdown = gr.Dropdown(
        choices=["OpenAI (GPT-3.5)", "Google Gemini (2.0 Flash)", "Claude (Sonnet 4)"],
        value="OpenAI (GPT-3.5)",
        label="Select AI Model",
        info="Choose which AI model to use for responses"
    )
    
    with gr.Row():
        msg = gr.Textbox(
            placeholder="Type your Figma question here...",
            container=False,
            scale=4
        )
        submit_btn = gr.Button("Ask", scale=1, variant="primary")
        clear_btn = gr.Button("Clear Chat", scale=1)


    # Your components with simple styling
    chatbot = gr.Chatbot(
        type="messages",
        height=400,
        placeholder="Ask me anything about Figma! For example: 'How do I create a component?' or 'What are frames in Figma?'",
        elem_classes=["styled-chat"]
    )
    with gr.Row():
        audio_btn = gr.Button("🔊 Text To Audio", scale=1, variant="primary")
        clear_audio_btn = gr.Button("🔇 Clear Audio", scale=1, variant="secondary")

    audio_output = gr.Audio(
        label="Audio Response",
        visible=True,
        elem_classes=["styled-audio"]
    )

    last_response = gr.State("")
    current_model = gr.State("OpenAI (GPT-3.5)")
    
    def respond(message, chat_history, model_choice):
        if not message.strip():
            return "", chat_history, "", model_choice
        
        bot_message = get_figma_help(message, chat_history, model_choice)
        new_history = chat_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": bot_message}]
        return "", new_history, bot_message, model_choice
    
    def play_audio(last_message, model_choice):
        if last_message:
            audio_file = talker(last_message, model_choice)
            if audio_file:
                return audio_file
        return None
    
    def clear_audio():
        """Clear the audio output"""
        return None
    
    def use_example(example_text):
        return example_text
    
    # Set up interactions
    submit_btn.click(
        respond, 
        inputs=[msg, chatbot, model_dropdown], 
        outputs=[msg, chatbot, last_response, current_model]
    )
    msg.submit(
        respond, 
        inputs=[msg, chatbot, model_dropdown], 
        outputs=[msg, chatbot, last_response, current_model]
    )
    clear_btn.click(clear_chat, outputs=[chatbot, msg, last_response])
    
    # Audio button functionality - now uses selected model
    audio_btn.click(
        play_audio,
        inputs=[last_response, current_model],
        outputs=[audio_output]
    )
    
    # Clear audio button functionality
    clear_audio_btn.click(
        clear_audio,
        outputs=[audio_output]
    )
    
    # Example button clicks
    for i, btn in enumerate(example_btns):
        btn.click(
            use_example,
            inputs=[btn],
            outputs=[msg]
        )

# Launch the app
demo.launch(share=True)