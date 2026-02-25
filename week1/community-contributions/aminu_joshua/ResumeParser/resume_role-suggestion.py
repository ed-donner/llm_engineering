import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
import pymupdf

load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
ollama_api_key = os.getenv('OLLAMA_API_KEY')

MODEL_OPENAI = 'gpt-4o-mini'
LOCAL_MODEL_OPENAI = 'gpt-oss:20b'

open_ai_model = ''

OLLAMA_API_URL = 'https://api.llama.com/v1'

MODEL_LLAMA = 'llama3.2'
LOCAL_MODEL_LLAMA = 'llama3.2'

ollama_model = ''

if openai_api_key and openai_api_key.startswith('sk-proj-') and len(openai_api_key)>10:
    open_ai_model = MODEL_OPENAI
    print("API key looks good so far")
    openai = OpenAI()
else:
    print(f"Couldn't find your API keys. Would proceed to use local model {LOCAL_MODEL_OPENAI} provided by Ollama")
    open_ai_model = LOCAL_MODEL_OPENAI
    openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')

if ollama_api_key:
    print("API key looks good so far")
    ollama_model = MODEL_LLAMA
    ollama = OpenAI(base_url=OLLAMA_API_URL, api_key=ollama_api_key)
else:
    print("Couldn't find your API keys. Would proceed to use local model {LOCAL_MODEL_LLAMA} provided by Ollama")
    ollama_model = LOCAL_MODEL_LLAMA
    ollama = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')

def read_pdf_file(file_path):
    text = ""
    if file_path.endswith('.pdf'):
        doc = pymupdf.open(file_path)
        for page in doc:
            text += page.get_text()
        return text
    else:
        return None

def get_links_user_prompt(resume_path):
    if not read_pdf_file(resume_path):
        print("Valid path to resume file")
        sys.exit(1)
    else:
        resume = read_pdf_file(resume_path)
    
    user_prompt = f"""
I extracted these information from this resume \n
{resume}\n
create a list of possible job titles that fit this resume.
"""
    return user_prompt

link_system_prompt = """
You are provided with a possible job titles that fit this resume.
You are able to decide which of the job titles are most relevant to the resume,
You should respond in JSON as in this example:

{
    "titles": [
        {"role": "software engineer", "skills": "python, javascript, sql, git, docker, kubernetes"},
        {"role": "data engineer", "skills": "python, javascript, sql, git, docker, kubernetes"}
    ]
}
"""

def suitable_job_titles(resume_path, model):
    stream = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(resume_path)}
        ],
        response_format={"type": "json_object"},
        stream=True
    )

    response = ""
    for chunk in stream:
        content = chunk.choices[0].delta.content or ''
        response += content
        print(content, end="", flush=True)

    return response
        
resume_path = input("Enter the path to the resume file: ")

if not open_ai_model:
    result = suitable_job_titles(resume_path, ollama_model)
else:
    result = suitable_job_titles(resume_path, open_ai_model)



