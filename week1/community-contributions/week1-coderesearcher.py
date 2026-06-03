import ollama, os
from openai import OpenAI
from dotenv import load_dotenv
from IPython.display import Markdown, display

load_dotenv()

open_key = os.getenv("OPENAI_API_KEY") 

OPEN_MODEL = "gpt-4-turbo"
ollama_model = "llama3.2"
openai = OpenAI()

system_prompt = "You are an assistant that focuses on the reason for each code, analysing and interpreting what the code does and how it could be improved, \
    Give your answer in markdown down with two different topics namely: Explanation and Code Improvement. However if you think there is no possible improvement \
        to said code, simply state 'no possible improvement '"

def user_prompt():
    custom_message = input("Write your prompt message: ")
    return custom_message

def explain():
    response = openai.chat.completions.create(model=OPEN_MODEL, 
                                              messages = [
                                                  {"role":"system", "content":system_prompt},
                                                  {"role": "user", "content":user_prompt()}
                                              ])
    result = response.choices[0].message.content
    display(Markdown(result))

# explain()   run this to get the openai output with peronalized input

#With ollama

ollama_api = "https://localhost:11434/api/chat"

def explainer_with_ollama():
    response = ollama.chat(model=ollama_model, messages=[
        {"role":"system", "content":system_prompt},
        {"role":"user", "content":user_prompt()}
    ])
    result = response["message"]["content"]
    display(Markdown(result))

#explainer_with_ollama() run for ollama output with same personalized input
