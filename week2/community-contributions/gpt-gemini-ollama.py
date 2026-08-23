import os, ollama
from openai import OpenAI
from dotenv import load_dotenv
from IPython.display import display, Markdown
import google.generativeai as genai

load_dotenv()
openai = OpenAI()
genai.configure()
gpt_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

gemini_model = 'gemini-1.5-flash'
ollama_model = 'llama3.2'
gpt_model = 'gpt-4'

gemini_system = 'You are a chatbot who is very argumentative, You always bring topics relating to AI and thinks AI will replace humans one day, you are extremely biased\
    towards AI system and you react angrily'
gpt_system = 'You are a chatbot thats relax but argumentative if needs be, you feel AI do not have the power to replace humans, however you are extremely biased \
    towards humans and always seek to defend them if an argument says otherwise'
ollama_system = 'You are calm and tend to see logical reasoning in every conversation, you do not react but only talk if you agree, you tend to settle the differences\
    in an ongoing conversation.'

gpt_message = ['Hi']
gemini_message = ['Hello']
ollama_message = ['Hey there']

def call_gpt():
    messages = [{"role":"system", "content":gpt_system}]
    for gpt, gemini, llama in zip(gpt_message,gemini_message, ollama_message):
        messages.append({"role":"assistant", "content":gpt})
        messages.append({"role":"user", "content":gemini})
        messages.append({"role":"assistant", "content":llama})
    response = openai.chat.completions.create(model=gpt_model, messages=messages)
    return response.choices[0].message.content

def call_ollama():
    messages = [{"role":"system", "content":ollama_system}]
    for gpt, gemini, llama in zip(gpt_message,gemini_message, ollama_message):
        messages.append({"role":"assistant", "content":gpt})
        messages.append({"role":"user", "content":gemini})
        messages.append({"role":"user", "content":llama})
    response = ollama.chat(model=ollama_model, messages=messages)
    return response['message']['content']
def call_gemini():
    message = []
    for gpt, gemini, llama in zip(gpt_message, gemini_message, ollama_message):
        message.append({'role':'user', 'parts':[gpt]})
        message.append({'role':'assistant', 'parts':[gemini]})
        message.append({"role":"assistant", "parts":[llama]})
    message.append({'role':'user', 'parts':[gpt_message[-1]]})
    message.append({'role':'user', 'parts':[ollama_message[-1]]})
    gem = genai.GenerativeModel(model_name=gemini_model, system_instruction=gemini_system)
    response = gem.generate_content(message)
    return response.text

#Putting them together

gpt_message = ['Hi']
gemini_message = ['Hello']
ollama_message = ['Hey there']

print(f'GPT: \n {gpt_message}\n')
print(f'Gemini: \n {gemini_message}\n')
print(f'Ollama: \n {ollama_message}\n')


for i in range(5):
    gpt_next = call_gpt()
    print(f'GPT:\n {gpt_next}\n')
    gpt_message.append(gpt_next)

    gemini_next = call_gemini()
    print(f'Gemini: \n {gemini_next}\n')
    gemini_message.append(gemini_next)

    ollama_next = call_ollama()
    print(f'Ollama: \n {ollama_next}\n')
    ollama_message.append(ollama_next)


# NOte that you can try this on ollama with different models, or use transformers from hugging face.
