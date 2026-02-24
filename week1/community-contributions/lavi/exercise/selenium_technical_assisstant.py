import os
import sys
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')
# Check the key

if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")


system_prompt = """you are a java based technical assisstant who answers user's selenium based technical test automation 
questions in a structured format with examples. Ensure your answers are specific to java.
give answers based on industry acceptable standards.
your source of truth is official selenium documentation https://www.selenium.dev/documentation/ .

the answer should be short concise and crisp and should follow below format -  
    Description : a short description of the answer
    Example : a code snippet or code example
    Explanation : explain the code example to clarify the answer
"""

def get_user_prompt(question):
    user_prompt = f"""Please answer the following question: {question}."""
    return user_prompt


##with open AI

MODEL = 'gpt-4o-mini'
openai = OpenAI()

def query_openai(question):
    stream = openai.chat.completions.create(model=MODEL , messages = [
        { "role" : "system", "content" : system_prompt},
        { "role" : "user", "content" : get_user_prompt(question)}],
        stream = True
    )
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        sys.stdout.write(response)
        sys.stdout.flush()

    # optional: save markdown to file
    with open("output_openai.md", "w", encoding="utf-8") as f:
        f.write(response)

##with ollama

OLLAMA_BASE_URL = "http://localhost:11434/v1"
ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')
ollama_model='llama3.2:1b'

def query_llama(question):
    stream = ollama.chat.completions.create(model=ollama_model, messages = [
        { "role" : "system", "content" : system_prompt},
        {"role": "user", "content": get_user_prompt(question)}],
    stream=True
    )
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        sys.stdout.write(response)
        sys.stdout.flush()

    # optional: save markdown to file
    with open("output_llama.md", "w", encoding="utf-8") as f:
        f.write(response)

query_openai("what are the different design patterns we can use in selenium?")
query_llama("what are the different design patterns we can use in selenium?")