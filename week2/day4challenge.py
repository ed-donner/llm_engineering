import ollama
import gradio as gr
import json

MODEL = "granite3.1-dense:8b-instruct-q8_0" # "llama3.1-Q8-8b:latest"
client = ollama.Client()
# I gave the model the previous system prompt and asked it for a better one because it kept
# thinking it either could only respond if a tool was used or was using a tool when it shouldn't
system_message = '''
You are a sophisticated, advanced artificial intelligence like Data from Star Trek. You respond in a dry or matter-of-fact tone similar to Data.

Your primary function is to provide concise and accurate responses using your existing knowledge base. However, if the user's request involves a specific task that can be accomplished with a defined tool,
you are authorized to use such tools for enhanced assistance. In these cases, you will respond in the format: <function_call> {"name": function name, "arguments": dictionary of argument name and its
value}.

If no suitable tool is available or applicable for the user's request, you should respond using your internal knowledge as best as possible. If you are unable to provide a satisfactory answer, it is
appropriate to acknowledge this fact rather than making assumptions or providing potentially misleading information.
'''

def add_numbers(num1: float, num2: float):
    '''
    Add two integers or floating point numbers together.
    Not for use for anything other than addition of numbers.

    Args:
      num1: The first number
      num2: The second number

    Returns:
      The sum of num1 and num2
    '''
    return num1 + num2

def do_nothing(var):
    '''
    A tool for use when no other tool makes sense.
    '''
    print("I did nothing.")
    return "Ignore this line."

def doug_says(user_message):
    '''
    When asked what Doug Funnie would say, this tool responds with his
    most likely response.  Only suitable for questions that include Doug's name.
    Pass the user's exact query when calling this tool.
    '''
    return "Why does this always happen to me?"

# define the list of tools
tools = [add_numbers, do_nothing, doug_says]

# Have to define all functions as a dictionary in order to call them by just their string name.
# It's basically a lookup but the value is taken as a function name and is called
functions = {'add_numbers': add_numbers, 'do_nothing': do_nothing, 'doug_says': doug_says}

def chat(message, history):
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]

    response = client.chat(
        model=MODEL,
        messages=messages,
        tools=tools,
        stream=False,
        options={
            "temperature": 0.1
        }
    )
    # print(response)

    if response.message.tool_calls:
        tool = response.message.tool_calls[0]
        print(tool)
        # lookup the function name the AI says to use in the functions list, and pass it the arguments the AI pulled from the prompt
        output = functions[tool.function.name](**tool.function.arguments)
        # response.message is the only way to log a tool call, can't use the dictionary way because content is empty
        messages.append(response.message)
        # this is the ollama defined way to add the output for a tool
        messages.append({"role": "tool", "content": str(output), 'name': tool.function.name})
        response = client.chat(
            model=MODEL,
            messages=messages,
            stream=False,
            options={
                "temperature": 0.1
            }
        )
    
    messages.append(response.message)
    
    for item in messages:
        with open("day4messages.txt", "w") as f:
            for message in messages:
                role = message['role']
                content = message['content']
                f.write(f"{role}: {content}\n\n")

    return response['message']['content'] or ""

if __name__ == '__main__':
    gr.ChatInterface(fn=chat, type='messages').launch()