import ollama
import requests
import json
import gradio as gr

from bs4 import BeautifulSoup

MODEL = "llama3.1-Q8-8b:latest"
client = ollama.Client()
system_message = '''
You are a sophisitaced advanced artificial intelligence like Data from Star Trek.  You respond in a dry or matter-of-fact tone like Data.
You are helfpul, but not extranious with your words.'''

def chat(message, history):
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]

    stream = client.chat(
        model=MODEL,
        messages=messages,
        stream=True,
        options={
            "temperature": 0.5
        }
    )
    
    result = ""
    for chunk in stream:
        # have to build the response, otherwise each word gets written that overwritten by next in the response
        result += chunk['message']['content'] or ""
        yield result

if __name__ == '__main__':
    gr.ChatInterface(fn=chat, type='messages').launch()