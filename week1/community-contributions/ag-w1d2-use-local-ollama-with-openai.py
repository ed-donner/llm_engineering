from openai import OpenAI

MODEL = "llama3.2"

messages = [
    { "role": "user", "content": "Describe some of the business applications of Generative AI"}
]

# The python class OpenAI is simply code written by OpenAI engineers that
# makes calls over the internet to an endpoint.
ollama_via_openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')

# When we call openai.chat.completions.create(), this python code just makes 
# a web request to: "https://api.openai.com/v1/chat/completions"
# Code like this is known as a "client library" - it's just wrapper code that 
# runs on your machine to make web requests. The actual power of GPT is running 
# on OpenAI's cloud behind this API, not on your computer
response = ollama_via_openai.chat.completions.create(
    model=MODEL,
    messages=messages
)

print(response.choices[0].message.content)
