import gradio as gr
from chat import chat
gr.ChatInterface(fn=chat, type="messages").launch(inbrowser=True)