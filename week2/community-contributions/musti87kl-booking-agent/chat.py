import json
from config import openai,MODEL
from tools import tool_functions, tool_cards
from prompt import system_message

def handle_tool_calls(message):
    responses= []
    for tool_call in message.tool_calls:
        name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"spy: AI ordered {name} with {arguments}", flush=True)
        function = tool_functions.get(name)
        result = function(**arguments) if function else f"Sorry, there is no tool called {name}"
        responses.append({"role": "tool", "content": result, "tool_call_id": tool_call.id})
    return responses

MAX_ROUNDS = 5

def chat(message, history):
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL, reasoning_effort="none", messages=messages, tools=tool_cards)
    rounds = 0
    while response.choices[0].finish_reason == "tool_calls" and rounds < MAX_ROUNDS:
        rounds += 1
        ai_message = response.choices[0].message
        messages.append(ai_message)
        messages.extend(handle_tool_calls(ai_message))
        response = openai.chat.completions.create(model=MODEL, reasoning_effort="none", messages=messages, tools=tool_cards)
    return response.choices[0].message.content