import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr




load_dotenv(override=True)

openai_api_key =os.getenv("OPENAI_API_KEY")


openai = OpenAI()
MODEL = 'gpt-4.1-mini'

system_message = "you are helpful assistant"

def chat(message:str,history):
    history = [{"role":h["role"],"content":h["content"]} for h in history]
    history.append ({"role":"assistant","content":system_message})
    history.append({"role":"user","content":message})
    stream = openai.chat.completions.create(model=MODEL, messages=history, stream=True) # type: ignore

    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
        yield response

gr.ChatInterface(fn=chat).launch(inbrowser=True)