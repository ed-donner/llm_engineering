import os
from openai import OpenAI


def answer(question):

    # creating the llm
    ollama_url = "http://localhost:11434/v1"
    ollama_model = "llama3.2"

    ollama = OpenAI(base_url=ollama_url,api_key="ollama")

    # creating prompt
    system_prompt = """
    You are an agent that can answer any kind of technical question. so the read the question answer as follow

    1. The question
    2. Solution to the quesition
    3. Example (if any)
    4. A real world example that connectss the question
    """
    user_prompt = """
    Answer the following question: 
    """
    user_prompt += question
    prompt = [{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}]


    # making call to the llm
    stream = ollama.chat.completions.create(model=ollama_model,messages=prompt,stream=True)
   
    # streaming  
    for chunk in stream:
        content = chunk.choices[0].delta.content or ""
        # Print each chunk instantly to the terminal without adding a newline
        print(content, end="", flush=True)


question = input("Enter the question: ")
answer(question)