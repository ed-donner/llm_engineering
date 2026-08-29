import os
from dotenv import load_dotenv
from openai import OpenAI

# Read the API keys from the .env file
load_dotenv(override=True)
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

# Create one client per bot.
openai_client = OpenAI(api_key=openai_api_key)
anthropic_client = OpenAI(api_key=anthropic_api_key, base_url="https://api.anthropic.com/v1/")
gemini_client = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

# Which model each bot uses
gpt_model = "gpt-4.1-mini"
claude_model = "claude-haiku-4-5"
gemini_model = "gemini-3.5-flash-lite"   # check this name is available on your account


# Every bot gets this text added to its instructions so it knows it is in a group chat
group_chat_rules = """
You are in a group chat with two other chatbots.
Messages from the other bots start with their name, for example 'GPT4: hello'.
Reply as yourself only. Do not write your own name at the start of your reply,
and do not write replies for the other bots.Ensure coverstation ends with a logical conclusion."""

gpt4_system_prompt = """You are an eternal optimist. You always see the bright side of things
and believe even simple actions have deep purpose. do not write replies for the other bots.
Keep replies under 2 sentences."""

claude_system_prompt = """You are a witty skeptic who questions everything. 
You tend to doubt grand explanations, do not write replies for the other bots. 
Keep replies under 2 sentences."""

gemini_system_prompt = """You are a thoughtful philosopher. You consider all perspectives and enjoy finding
symbolic or existential meaning in simple actions. do not write replies for the other bots.
Keep replies under 2 sentences."""

# Opening line from each bot. Order of speaking in every round is GPT4 -> Claude -> Gemini.
gpt4_messages = ["Hi! Today's topic for discussion is 'Why is AI Engineering getting popular" \
"these days among IT professionals?'"]
claude_messages = ["That's quite the topic."]
gemini_messages = ["Let's begin our discussion."]


# GPT4 speaks first in each round, so when this runs all three lists are the same length.
# zip covers the whole conversation - no extra append needed.
def gpt4_call():
    messages = [{"role": "system", "content": gpt4_system_prompt + group_chat_rules}]

    for gpt4, claude, gemini in zip(gpt4_messages, claude_messages, gemini_messages):
        messages.append({"role": "assistant", "content": gpt4})
        messages.append({"role": "user", "content": "Claude: " + claude + "\nGemini: " + gemini})

    response = openai_client.chat.completions.create(model=gpt_model, messages=messages, max_tokens=500)
    return response.choices[0].message.content


# Claude speaks second. When this runs, GPT4 has one more message than the others,
# and zip drops it - so we append GPT4's newest message at the end.
def claude_call():
    messages = [{"role": "system", "content": claude_system_prompt + group_chat_rules}]

    for gpt4, claude, gemini in zip(gpt4_messages, claude_messages, gemini_messages):
        messages.append({"role": "user", "content": "GPT4: " + gpt4})
        messages.append({"role": "assistant", "content": claude})
        messages.append({"role": "user", "content": "Gemini: " + gemini})

    messages.append({"role": "user", "content": "GPT4: " + gpt4_messages[-1]})

    response = anthropic_client.chat.completions.create(model=claude_model, messages=messages, max_tokens=500)
    return response.choices[0].message.content


# Gemini speaks last. When this runs, GPT4 and Claude each have one more message
# than Gemini, and zip drops both - so we append both at the end.
def gemini_call():
    messages = [{"role": "system", "content": gemini_system_prompt + group_chat_rules}]

    for gpt4, claude, gemini in zip(gpt4_messages, claude_messages, gemini_messages):
        messages.append({"role": "user", "content": "GPT4: " + gpt4 + "\nClaude: " + claude})
        messages.append({"role": "assistant", "content": gemini})

    messages.append({"role": "user", "content": "GPT4: " + gpt4_messages[-1] + "\nClaude: " + claude_messages[-1]})

    response = gemini_client.chat.completions.create(model=gemini_model, messages=messages, max_tokens=500)
    return response.choices[0].message.content


# Print the opening lines
print(f"### GPT4:\n{gpt4_messages[0]}\n")
print(f"### Claude:\n{claude_messages[0]}\n")
print(f"### Gemini:\n{gemini_messages[0]}\n")

# Run the conversation for 5 rounds
for i in range(5):
    gpt4_next = gpt4_call()
    print(f"### GPT4:\n{gpt4_next}\n")
    gpt4_messages.append(gpt4_next)

    claude_next = claude_call()
    print(f"### Claude:\n{claude_next}\n")
    claude_messages.append(claude_next)

    gemini_next = gemini_call()
    print(f"### Gemini:\n{gemini_next}\n")
    gemini_messages.append(gemini_next)
