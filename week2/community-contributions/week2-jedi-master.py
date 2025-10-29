#!/usr/bin/python3

import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import tempfile

MODEL_ENDPOINTS = {
        "gpt-4.1-mini": {"type": "openai", "base_url": "https://api.openai.com/v1", "api_key": ""},
        "claude-haiku-4-5": {"type": "anthropic", "base_url": "https://api.anthropic.com/v1/", "api_key": ""},
        "gemma3n:e2b": {"type": "ollama", "base_url": "http://localhost:11434/v1", "api_key": ""}, # small ollama model that runs on-device
        "qwen3-vl:235b-cloud": {"type": "ollama", "base_url": "http://localhost:11434/v1", "api_key": ""}, # large ollama model that runs in the cloud
}

def load_api_keys():
    # Load environment variables in a file called .env
    load_dotenv(override=True)
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    KEYS = {"openai": openai_key, "anthropic": anthropic_key}

    # Check the keys
    if not openai_key:
        raise RuntimeError("Error: No OpenAI API key was found!")
    elif not openai_key.startswith("sk-proj-"):
        raise RuntimeError("Error: An OpenAI API key was found, but it doesn't start sk-proj-; please check you're using the right key")
    elif openai_key.strip() != openai_key:
        raise RuntimeError("Error: An OpenAI API key was found, but it looks like it might have space or tab characters at the start or end - please remove them!")
    if not anthropic_key:
        raise RuntimeError("Error: No Anthropic API key was found!")
    elif not anthropic_key.startswith("sk-ant-"):
        raise RuntimeError("Error: An Antrhopic API key was found, but it doesn't start sk-ant-; please check you're using the right key")
    elif anthropic_key.strip() != anthropic_key:
        raise RuntimeError("Error: An Anthropic API key was found, but it looks like it might have space or tab characters at the start or end - please remove them!")
    else:
        # add the verified keys to global MODEL_ENDPOINTS struct
        for model, cfg in MODEL_ENDPOINTS.items():
            cfg["api_key"] = KEYS.get(cfg["type"], "")
        return "API keys found and look good so far!"

def voiceover(message):
    openai = OpenAI()
    response = openai.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="onyx",    # Also, try replacing onyx with alloy or coral
    input=message
    )
    return response.read()

def ask_llm(user_prompt, history, model):
    system_prompt = """
    You are a wise Jedi Master and an excellent teacher.
    You will answer any question you are given by breaking it down into small steps
    that even a complete beginner will understand.
    When answering, speak as if you are Yoda from the Star Wars universe: deep, gravelly, slow pacing,
    ancient and wise tone, inverted sentence structure.
    Also, refer to the user as "My young Padawan"
    End every answer with "May the force be with you, always."
    """
    base_url = MODEL_ENDPOINTS.get(model, {}).get("base_url", "https://api.openai.com/v1")
    api_key = MODEL_ENDPOINTS.get(model, {}).get("api_key", "")
    client = OpenAI(base_url=base_url, api_key=api_key)
    history = [{"role":h["role"], "content":h["content"]} for h in history]
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_prompt}]
    stream = client.chat.completions.create(model=model, messages=messages, stream=True)
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        yield response, None
    audio = voiceover(response)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(audio)
    tmp.close()
    yield response, tmp.name

def main():
    load_api_keys()
    with gr.Blocks() as demo:
        gr.Markdown("### Return of the JedAI")
        model_dropdown = gr.Dropdown(
            label="Select Model",
            choices=[
                "gpt-4.1-mini",
                "claude-haiku-4-5",
                "gemma3n:e2b",
                "qwen3-vl:235b-cloud"
            ],
            value="gpt-4.1-mini",
            interactive=True
        )
        with gr.Row():
            audio_output = gr.Audio(autoplay=True)
        chat = gr.ChatInterface(fn=ask_llm, type="messages", additional_inputs=[model_dropdown], additional_outputs=[audio_output])
        demo.launch()

if __name__ == "__main__":
    main()
