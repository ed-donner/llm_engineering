
import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
from enum import Enum

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
ollama_key = "ollama"



openai = OpenAI()
llama =  OpenAI(api_key=ollama_key,base_url="http://localhost:11434/v1")



class models(Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    Llama = "llama3.2:1b"
    
    
models_list = [m.name for m in models]  # Convert enum to list of string names

def call_model(prompt:str, model:str = "GPT_4O_MINI", system_prompt:str = ""):
    if system_prompt != "":
        messages=[{"role": "system", "content": system_prompt}
                  ,{"role": "user", "content": prompt}]
    else:
        messages=[{"role": "user", "content": prompt}]

    # Select the appropriate client based on model choice
    if model == "GPT_4O_MINI":
        client = openai
        model_name = models.GPT_4O_MINI.value
    else:  # Llama
        client = llama
        model_name = models.Llama.value
    
    stream = client.chat.completions.create(model=model_name, messages=messages, stream=True) # type: ignore
    result = ""
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""
        yield result



    
message_input = gr.Textbox(lines=5)
message_output = gr.Markdown(label="Response:")
model_selector = gr.Dropdown(choices=models_list, value="GPT_4O_MINI", label="Select Model")

view = gr.Interface(fn=call_model, inputs=[message_input, model_selector], outputs=message_output, flagging_mode="never").launch(inbrowser=True, share=False)


