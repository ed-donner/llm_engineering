#!/usr/bin/env python3

import os
import torch
import requests
import json
import librosa
import numpy as np
from pathlib import Path
from datetime import datetime
from transformers import pipeline
import gradio as gr

# Basic config
TRANSCRIPTION_MODEL = "openai/whisper-tiny.en"
OLLAMA_MODEL = "llama3.2:latest"
OLLAMA_URL = "http://localhost:11434"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
OUTPUT_DIR = Path("./output")

# ============================
# MODEL LOADING
# ============================

def check_ollama():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            return OLLAMA_MODEL in model_names
        return False
    except:
        return False

def call_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 1000
        }
    }
    
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
        if response.status_code == 200:
            return response.json().get('response', '').strip()
        return "Error: Ollama request failed"
    except:
        return "Error: Could not connect to Ollama"

def load_models():
    print("Loading models...")
    
    if not check_ollama():
        print("Ollama not available")
        return None, False
    
    try:
        transcription_pipe = pipeline(
            "automatic-speech-recognition",
            model=TRANSCRIPTION_MODEL,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            device=0 if DEVICE == "cuda" else -1,
            return_timestamps=True
        )
        print("Models loaded successfully")
        return transcription_pipe, True
    except Exception as e:
        print(f"Failed to load models: {e}")
        return None, False

# ============================
# PROCESSING FUNCTIONS
# ============================

def transcribe_audio(audio_file_path, transcription_pipe):
    if not os.path.exists(audio_file_path):
        return "Error: Audio file not found"
    
    try:
        # Load audio with librosa
        audio, sr = librosa.load(audio_file_path, sr=16000)
        if not isinstance(audio, np.ndarray):
            audio = np.array(audio)
        
        result = transcription_pipe(audio)
        
        # Extract text from result
        if isinstance(result, dict):
            if "text" in result:
                transcription = result["text"].strip()
            elif "chunks" in result:
                transcription = " ".join([chunk["text"] for chunk in result["chunks"]]).strip()
            else:
                transcription = str(result).strip()
        else:
            transcription = str(result).strip()
        
        return transcription
        
    except Exception as e:
        return f"Error: {str(e)}"

def generate_minutes(transcription):
    prompt = f"""Create meeting minutes from this transcript:

{transcription[:2000]}

Include:
- Summary with attendees and topics
- Key discussion points
- Important decisions
- Action items

Meeting Minutes:"""
    
    result = call_ollama(prompt)
    return result

def save_results(transcription, minutes, meeting_type="meeting"):
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{meeting_type}_minutes_{timestamp}.md"
        filepath = OUTPUT_DIR / filename
        
        content = f"""# Meeting Minutes

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Meeting Minutes

{minutes}

## Full Transcription

{transcription}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
        
    except Exception as e:
        return f"Error saving: {str(e)}"

# ============================
# GRADIO INTERFACE
# ============================

def process_audio_file(audio_file, meeting_type, progress=gr.Progress()):
    progress(0.0, desc="Starting...")
    
    if not hasattr(process_audio_file, 'models') or not process_audio_file.models[0]:
        return "", "", "Models not loaded"
    
    transcription_pipe, ollama_ready = process_audio_file.models
    
    if not ollama_ready:
        return "", "", "Ollama not available"
    
    try:
        audio_path = audio_file.name if hasattr(audio_file, 'name') else str(audio_file)
        if not audio_path:
            return "", "", "No audio file provided"
        
        progress(0.2, desc="Transcribing...")
        transcription = transcribe_audio(audio_path, transcription_pipe)
        
        if transcription.startswith("Error:"):
            return transcription, "", "Transcription failed"
        
        progress(0.6, desc="Generating minutes...")
        minutes = generate_minutes(transcription)
        
        if minutes.startswith("Error:"):
            return transcription, minutes, "Minutes generation failed"
        
        progress(0.9, desc="Saving...")
        save_path = save_results(transcription, minutes, meeting_type)
        
        progress(1.0, desc="Complete!")
        
        status = f"""Processing completed!

Transcription: {len(transcription)} characters  
Minutes: {len(minutes)} characters  
Saved to: {save_path}

Models used:
- Transcription: {TRANSCRIPTION_MODEL}
- LLM: {OLLAMA_MODEL}
- Device: {DEVICE}
"""
        
        return transcription, minutes, status
        
    except Exception as e:
        progress(1.0, desc="Failed")
        return "", "", f"Processing failed: {str(e)}"

def create_interface():
    with gr.Blocks(title="Meeting Minutes Creator") as interface:
        
        gr.HTML("<h1>Meeting Minutes Creator</h1><p>HuggingFace Whisper + Ollama</p>")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Audio Input")
                
                audio_input = gr.Audio(
                    label="Upload or Record Audio",
                    type="filepath",
                    sources=["upload", "microphone"]
                )
                
                meeting_type = gr.Dropdown(
                    choices=["meeting", "standup", "interview", "call"],
                    value="meeting",
                    label="Meeting Type"
                )
                
                process_btn = gr.Button("Generate Minutes", variant="primary")
                
                gr.HTML(f"""
                <div>
                    <h4>Configuration</h4>
                    <ul>
                        <li>Transcription: {TRANSCRIPTION_MODEL}</li>
                        <li>LLM: {OLLAMA_MODEL}</li>
                        <li>Device: {DEVICE}</li>
                    </ul>
                </div>
                """)
            
            with gr.Column():
                gr.Markdown("### Results")
                
                status_output = gr.Markdown("Ready to process audio")
                
                with gr.Tabs():
                    with gr.Tab("Meeting Minutes"):
                        minutes_output = gr.Markdown("Minutes will appear here")
                    
                    with gr.Tab("Transcription"):
                        transcription_output = gr.Textbox(
                            "Transcription will appear here",
                            lines=15,
                            show_copy_button=True
                        )
        
        process_btn.click(
            fn=process_audio_file,
            inputs=[audio_input, meeting_type],
            outputs=[transcription_output, minutes_output, status_output],
            show_progress=True
        )
    
    return interface

# ============================
# MAIN APPLICATION
# ============================

def main():
    print("Meeting Minutes Creator - HuggingFace + Ollama")
    print("Loading models...")
    
    transcription_pipe, ollama_ready = load_models()
    
    if not transcription_pipe or not ollama_ready:
        print("Failed to load models or connect to Ollama")
        print("Make sure Ollama is running and has the model available")
        return
    
    process_audio_file.models = (transcription_pipe, ollama_ready)
    
    print("Models loaded successfully!")
    print("Starting web interface...")
    print("Access at: http://localhost:7860")
    
    interface = create_interface()
    
    try:
        interface.launch(
            server_name="localhost",
            server_port=7860,
            debug=False
        )
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"Failed to launch: {e}")

if __name__ == "__main__":
    main()