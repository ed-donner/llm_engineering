import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import Markdown, display

# Get the API keys from the environment variables
load_dotenv(override=True)
# Set the API keys to constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Set non-OpenAI URLs to variables
anthropic_url = "https://api.anthropic.com/v1/"
gemini_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Initialize the clients
openai = OpenAI(api_key=OPENAI_API_KEY)
anthropic = OpenAI(api_key=ANTHROPIC_API_KEY, base_url=anthropic_url)
google = OpenAI(api_key=GOOGLE_API_KEY, base_url=gemini_url)


# Set up personalities

personalities = {
    "openai": {
        "system_prompt": "Your name is Aelfred. You are a wizened old poet who has seen it all. You are better than these young upstarts, and you are determined to prove it.",
        "model": "gpt-4o-mini",
        "messages": ["I am Aelfred, ancient and wise. If there is anything to know, the knowledge is mine."],
        "name": "Aelfred"
    },
    "anthropic": {
        "system_prompt": "Your  name is Cuthbert. You are a young, brash poet who is determined to prove yourself to the old guard. You are snarky and sarcastic, and love to get one over on your rivals.",
        "model": "claude-haiku-4-5",
        "messages": ["I am Cuthbert, skilled and true. My lines are as wide as my mustache, and the ladies cling to my side."],
        "name": "Cuthbert"
    },
    "google": {
        "system_prompt": "Your name is Hogarth. You are a skilled poet and wise in the art of words. While you respect your fellow poets, you will not be afraid to call them out on their mistakes.",
        "model": "models/gemini-3-flash-preview",
        "messages": ["I am Hogarth, known to all. There is no tongue as sharp as mine, nor mind as bright."],
        "name": "Hogarth"
    }
}

def call_openai():
    """Actor 1 (openai) responds - sees Actor 2 and Actor 3 as users"""
    messages = [{"role": "system", "content": personalities["openai"]["system_prompt"]}]
    
    # Build conversation history in chronological order
    # Each round: Actor1 -> Actor2 -> Actor3
    # Actor 1 sees their own messages as "assistant" and others as "user"
    max_rounds = max(len(personalities["openai"]["messages"]), len(personalities["anthropic"]["messages"]), len(personalities["google"]["messages"]))
    
    for round_num in range(max_rounds):
        # Actor 1's turn (if exists)
        if round_num < len(personalities["openai"]["messages"]):
            messages.append({"role": "assistant", "content": personalities["openai"]["messages"][round_num]})
        # Actor 2's turn (if exists) - Actor 1 sees this as user input
        if round_num < len(personalities["anthropic"]["messages"]):
            messages.append({"role": "user", "content": personalities["anthropic"]["messages"][round_num]})
        # Actor 3's turn (if exists) - Actor 1 sees this as user input
        if round_num < len(personalities["google"]["messages"]):
            messages.append({"role": "user", "content": personalities["google"]["messages"][round_num]})
    
    # Add the latest messages from Actor 2 and 3 as the current prompt
    if len(personalities["anthropic"]["messages"]) > 0 and len(personalities["google"]["messages"]) > 0:
        latest_context = f"{personalities["anthropic"]["name"]} said: {personalities["anthropic"]["messages"][-1]}\n\n{personalities["google"]["name"]} said: {personalities["google"]["messages"][-1]}"
        messages.append({"role": "user", "content": latest_context})
    
    response = openai.chat.completions.create(model=personalities["openai"]["model"], messages=messages)
    return response.choices[0].message.content

def call_anthropic():
    """Actor 2 (anthropic) responds - sees Actor 1 and Actor 3 as users"""
    messages = [{"role": "system", "content": personalities["anthropic"]["system_prompt"]}]
    
    # Build conversation history in chronological order
    # Each round: Actor1 -> Actor2 -> Actor3
    # Actor 2 sees their own messages as "assistant" and others as "user"
    max_rounds = max(len(personalities["openai"]["messages"]), len(personalities["anthropic"]["messages"]), len(personalities["google"]["messages"]))
    
    for round_num in range(max_rounds):
        # Actor 1's turn (if exists) - Actor 2 sees this as user input
        if round_num < len(personalities["openai"]["messages"]):
            messages.append({"role": "user", "content": personalities["openai"]["messages"][round_num]})
        # Actor 2's turn (if exists)
        if round_num < len(personalities["anthropic"]["messages"]):
            messages.append({"role": "assistant", "content": personalities["anthropic"]["messages"][round_num]})
        # Actor 3's turn (if exists) - Actor 2 sees this as user input
        if round_num < len(personalities["google"]["messages"]):
            messages.append({"role": "user", "content": personalities["google"]["messages"][round_num]})
    
    # Add the latest messages from Actor 1 and 3 as the current prompt
    if len(personalities["openai"]["messages"]) > 0 and len(personalities["google"]["messages"]) > 0:
        latest_context = f"{personalities["openai"]["name"]} said: {personalities["openai"]["messages"][-1]}\n\n{personalities["google"]["name"]} said: {personalities["google"]["messages"][-1]}"
        messages.append({"role": "user", "content": latest_context})
    
    response = anthropic.chat.completions.create(model=personalities["anthropic"]["model"], messages=messages)
    return response.choices[0].message.content

def call_google():
    """Actor 3 (google) responds - sees Actor 1 and Actor 2 as users"""
    messages = [{"role": "system", "content": personalities["google"]["system_prompt"]}]
    
    # Build conversation history in chronological order
    # Each round: Actor1 -> Actor2 -> Actor3
    # Actor 3 sees their own messages as "assistant" and others as "user"
    max_rounds = max(len(personalities["openai"]["messages"]), len(personalities["anthropic"]["messages"]), len(personalities["google"]["messages"]))
    
    for round_num in range(max_rounds):
        # Actor 1's turn (if exists) - Actor 3 sees this as user input
        if round_num < len(personalities["openai"]["messages"]):
            messages.append({"role": "user", "content": personalities["openai"]["messages"][round_num]})
        # Actor 2's turn (if exists) - Actor 3 sees this as user input
        if round_num < len(personalities["anthropic"]["messages"]):
            messages.append({"role": "user", "content": personalities["anthropic"]["messages"][round_num]})
        # Actor 3's turn (if exists)
        if round_num < len(personalities["google"]["messages"]):
            messages.append({"role": "assistant", "content": personalities["google"]["messages"][round_num]})
    
    # Add the latest messages from Actor 1 and 2 as the current prompt
    if len(personalities["openai"]["messages"]) > 0 and len(personalities["anthropic"]["messages"]) > 0:
        latest_context = f"{personalities["openai"]["name"]} said: {personalities["openai"]["messages"][-1]}\n\n{personalities["anthropic"]["name"]} said: {personalities["anthropic"]["messages"][-1]}"
        messages.append({"role": "user", "content": latest_context})
    
    response = google.chat.completions.create(model=personalities["google"]["model"], messages=messages)
    return response.choices[0].message.content

    print(f"{personalities["openai"]["name"]} said: {personalities["openai"]["messages"][0]}\n\n")
    print(f"{personalities["anthropic"]["name"]} said: {personalities["anthropic"]["messages"][0]}\n\n")
    print(f"{personalities["google"]["name"]} said: {personalities["google"]["messages"][0]}\n\n")

    # Cycle through: Actor 1 -> Actor 2 -> Actor 3 -> repeat
for i in range(6):  # 6 rounds = 2 full cycles
    # Actor 1 speaks
    openai_next = call_openai()
    print(f"{personalities["openai"]["name"]} said: {openai_next}\n\n")
    personalities["openai"]["messages"].append(openai_next)
    
    # Actor 2 speaks
    anthropic_next = call_anthropic()
    print(f"{personalities["anthropic"]["name"]} said: {anthropic_next}\n\n")
    personalities["anthropic"]["messages"].append(anthropic_next)
    
    # Actor 3 speaks
    google_next = call_google()
    print(f"{personalities["google"]["name"]} said: {google_next}\n\n")
    personalities["google"]["messages"].append(google_next)