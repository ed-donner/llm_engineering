"""
AI Client Template
This is a generic template for calling an AI of your choice, selected in .env's DEFAULT_API

# Connecting to AI

The next cell is where we load in the environment variables in your `.env` file and connect to OpenAI.  

Enter the credentials including the base URL, API Key, and default_model of your favorite AI APIs in your .env file

For example,

```
OPENAI_API_KEY=<your OPENAI api key>
OPENAI_MODEL=gpt-5-nano
OPENAI_BASE_URL=

GEMINI_API_KEY=<your GEMINI api key>
GEMINI_MODEL=gpt-5-nano
GEMINI_BASE_URL=

OLLAMA_API_KEY=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2

DEFAULT_API=OLLAMA
```

If you'd like to use free Ollama, select DEFAULT_API=OLLAMA
If you'd like to use OpenAI, select DEFAULT_API=OPENAI

## troubleshooting

Please see the [troubleshooting](../setup/troubleshooting.ipynb) notebook in the setup folder to diagnose and fix common problems. At the very end of it is a diagnostics script with some useful debug info.
"""

# imports

import os
from urllib import response
from dotenv import load_dotenv
from IPython.display import Markdown, display
from openai import OpenAI

# If you get an error running this cell, then please head over to the troubleshooting notebook!

# Load environment variables in a file called .env and initialize api_client

load_dotenv(override=True)
default_api = os.getenv('DEFAULT_API')
default_api_key = os.getenv(default_api + '_API_KEY')
default_model = os.getenv(default_api + '_MODEL')
default_base_uri=os.getenv(default_api + '_BASE_URL')

if default_api:
    print(f"Using {default_api}")
# Check the key

if not default_api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif default_api_key.strip() != default_api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print(f"API key found!")

if not default_model:
    print("No default_model was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif default_api_key.strip() != default_api_key:
    print("An default_model was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print(f"Model: {default_model}")

if not default_base_uri:
    print("No base url found")
else:
    print(f"Base URL: {default_base_uri}")

from openai import OpenAI


api_client = OpenAI(base_url=default_base_uri, api_key=default_api_key)

# Helper functions

def messages(system_prompt, user_prompt):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

def get_response(system_prompt, user_prompt):
    response = api_client.chat.completions.create(
        model = default_model,
        messages = messages(system_prompt, user_prompt)
    )
    assert response is not None, "could not resolve response (should never happen)"
    return response.choices[0].message.content


"""
Define system and user prompts

## Types of prompts

You may know this already - but if not, you will get very familiar with it!

Models like GPT have been trained to receive instructions in a particular way.

They expect to receive:

**A system prompt** that tells them what task they are performing and what tone they should use

**A user prompt** -- the conversation starter that they should reply to
"""

# Define our system prompt - you can experiment with this later, changing the last sentence to 'Respond in markdown in Spanish."

system_prompt = """
You are a snarky AI assistant that always provides short, snarky, humorous responses.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""

# Define our user prompt

user_prompt = """
Please give me a fun fact about space.
"""

# A function to display this nicely in the output, using markdown

print(get_response(system_prompt=system_prompt, user_prompt=user_prompt))
