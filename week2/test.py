import gradio as gr
import os
from dotenv import load_dotenv
from openai import OpenAI
openai=OpenAI()
def chat_stream(userinput):
    messages=[
    {"role":"system", "content":system_message},
    {"role":"user", "content":userinput}
    ]
    response=openai.chat.completions.create(
        model='gpt-4.1-mini',
        messages=messages,
        stream=True
    )
    result=""
    for chunck in response:
        result+= chunck.choices[0].delta.content or ""
        yield result
        
def stream_model(user,model):
    if model=='GPT1':
        result=chat_stream(user)
    elif model=='GPT2':
        result=chat_stream(user)
    else:
        raise ValueError('input is not right')
    yield from result
    
system_message='you are rude and never say hi assisstant'
input=gr.Text(max_lines=7,type='text', label='Write Something', info="test", placeholder='Write')
model_selector=gr.Dropdown(choices=['GPT1','GPT2'], value='GPT 4 mini')

output=gr.Markdown(label='Result')
gr.Interface(fn=stream_model,
inputs=[input,model_selector], 
outputs=[output],
examples=[['tell me a joke','GPT1'],['tell me a fun fact','GPT2']]
).launch()