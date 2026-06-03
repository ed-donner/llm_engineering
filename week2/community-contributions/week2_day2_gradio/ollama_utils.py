import requests
import json
import ollama


def get_downloaded_models():
    models_raw = requests.get("http://localhost:11434/api/tags").content
    models_dict = json.loads(models_raw)
    models = [model["name"] for model in models_dict["models"]]
    return models

def get_ollama_response(model, prompt, translte_from, translte_to, options):
    def get_system_prompt():
        with open('system_prompt.txt', 'r') as file:
            system_prompt = file.read()
        return system_prompt
    
    system_prompt = get_system_prompt()
    user_prompt = f"Translate from {translte_from} to {translte_to}: {prompt}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response = ollama.chat(model, messages, options=options, stream=True)
    for chunck in response:
        
        yield chunck["message"]["content"] 
