# the menu: the short word on the dropdown -> the real model name LiteLLM needs
MODELS = {"GPT": "openai/gpt-6-luna", "Claude": "anthropic/claude-haiku-4-5", "Llama": "ollama_chat/llama3.2"}


# fill the 3 blanks for one debater and hand back its finished system prompt
def debater_prompt(name, purpose, rule):
    return f"Your name is {name}. Your aim: {purpose}. Your rule: {rule}. Reply in 1-3 sentences, like a group chat on whatsapp!"


# the judge's prompt: its own 3 blanks + both debaters' names and rules; the only place LOSER: is mentioned
def judge_prompt(name, purpose, rule, d1_name, d1_rule, d2_name, d2_rule):
    return f"Your name is {name}. You judge a debate between {d1_name} and {d2_name}. Your style: {purpose}. How you judge: {rule}. {d1_name}'s rule: {d1_rule}. {d2_name}'s rule: {d2_rule}. When one of them is beaten or breaks their rule, end your message with LOSER: <their name>. Reply in 1-3 sentences."
