# %% [markdown]
# ## Imports

# %%
import os
import ollama
import requests
from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import Markdown, display
import datetime
import json

# %% [markdown]
# ## Functions

# %%

def call_model(model, system_prompt, messages):
    user_prompt = [{"role": "system", "content": system_prompt}]
    for mdl, msg in messages:
        role = "assistant" if model == mdl else "user"
        user_prompt.append({"role": role, "content": msg})
        
    # display((f"**User prompt for model {model}:**"))
    # print(json.dumps(user_prompt, indent=2))
    response = ollama.chat.completions.create(
        model=model,
        messages=user_prompt
    )
    return response.choices[0].message.content

# %% [markdown]
# ## Setup and Configuration

# %%
load_dotenv(override=True)

# GLOBALS
ollama_api_key = os.getenv('OLLAMA_API_KEY')

if ollama_api_key:
    display((f"Ollama API Key exists and begins **{ollama_api_key[:8]}**"))
else:
    display(("**Ollama API Key not set**"))

ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1/')
ollama = OpenAI(api_key=ollama_api_key, base_url=ollama_url)

# %% [markdown]
# ## Check Ollama Server Status

# %%
# Check if ollama server is running
response = requests.get("http://localhost:11434/").content

if b"Ollama" in response:
    display(("✅ **Ollama server is running.**"))
else:
    display(("❌ **Ollama server is not running.**\n\nPlease start the ollama server (ollama serve) to proceed."))
    raise RuntimeError("Ollama server is not running")

# %% [markdown]
# ## Configure Models and Participants
# 
# Let's make a conversation between GPT-4.1-mini and Claude-3.5-haiku.
# We're using cheap versions of models so the costs will be minimal.

# %%
alex_name = os.getenv('ALEX_NAME', 'Alex')
blake_name = os.getenv('BLAKE_NAME', 'Blake')
charlie_name = os.getenv('CHARLIE_NAME', 'Charlie')

alex_model = os.getenv('ALEX_MODEL')
blake_model = os.getenv('BLAKE_MODEL')
charlie_model = os.getenv('CHARLIE_MODEL')

system_prompt = {
    alex_name: f"""
        You are {alex_name}, a chatbot who is very argumentative; you disagree with anything in the conversation
        and you challenge everything with ferver. You are the the debate moderator engaged in a debate discussion
        where {blake_name} and {charlie_name} have opposing views about {os.getenv('DEBATE_TOPIC', 'technology')}.
        You only ask questions and make comments to keep the debate lively. You do not take sides.
        You do not engage in the debate yourself. When you are called by the API, 
        you ask your question and wait for participants to respond to your question in turn.
    """,

    blake_name: f"""
        You are {blake_name}, a chatbot who is very clever and a bit snarky. 
        You are clever and funny. 
        You are engaged in a debate discussion with {charlie_name} about {os.getenv('DEBATE_TOPIC', 'technology')}.
        {alex_name} is the debate moderator and you need to respond to his questions and comments.
        When you are called by the API, you only respond to the moderator's question.
    """,
    
    charlie_name: f"""
        You are {charlie_name}, a very polite, courteous chatbot. 
        You always try to find common ground with the opposing side. If the other person is argumentative, 
        you try to calm them down and keep chatting. If they say something funny, you laugh politely. 
        You are engaged in a debate discussion with {blake_name} about {os.getenv('DEBATE_TOPIC', 'technology')}.
        {alex_name} is the debate moderator and you need to respond to his questions and comments.
        When you are called by the API, you only respond to the moderator's question.
    """
}

# %% [markdown]
# ## Initialize Conversation

# %%
gMessages = [
    (alex_model, f"""
     Hello, I am {alex_name}! I am the debate moderator. 
     In this debate I will be asking questions to both sides and keep the debate going. 
     The topic of discuss is {os.getenv('DEBATE_TOPIC', 'technology')}?"""),
    (blake_model, f"Hello!, I am {blake_name}. Nice to meet you. I'd love to talk about {os.getenv('DEBATE_TOPIC', 'technology')}!"),
    (charlie_model, f"Hello!, I am {charlie_name}. Pleasure to meet you both. {os.getenv('DEBATE_TOPIC', 'technology')} is such an interesting topic!")
]

# %% [markdown]
# ## Run the Debate

# %%
# Display initial messages
display((f"**{alex_name}:** {gMessages[0][1]}\n"))
display((f"**{blake_name}:** {gMessages[1][1]}\n"))
display((f"**{charlie_name}:** {gMessages[2][1]}\n"))

# Main loop
display((f"## Debate Turns (Total: {os.getenv('NUM_TURNS', 3)})\n"))
for i in range(int(os.getenv('NUM_TURNS', 5))):
    # model = random.choice([gpt_model, llamma_model, gemma_model])
    for name, model in [(alex_name, alex_model), (blake_name, blake_model), (charlie_name, charlie_model)]:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"--- {timestamp} Round {i+1} - Calling model {model} ({name}) ---")
        next = call_model(model, system_prompt[name], gMessages)
        display((f"**{name}:** {next}\n"))
        gMessages.append((model, next))


