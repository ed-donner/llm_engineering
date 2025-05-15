import ollama
from IPython.display import Markdown, display

MODEL = "llama3.2"

# Create a messages list (Note that "system" role is not required)
messages = [
    { "role": "user", "content": "Describe some of the business applications of Generative AI"}
]

""" 
#under the covers calls this API with specified payload

OLLAMA_API = "http://local_host:11434/api/chat" 
payload = {
    "model": MODEL,
    "messages": messages,
    "stream": False
}
response = requests.post(OLLAMA_API, json=payload, headers=HEADERS)

"""
response = ollama.chat(model=MODEL, messages=messages)
#print(response['message']['content'])
answer = response['message']['content']

#Note that markdown will not display in VSCode but only in Jupyter
#to view in markdown in VSCode, save output to .md file and then oipen in VSCode
display(Markdown(answer))
print(answer)


