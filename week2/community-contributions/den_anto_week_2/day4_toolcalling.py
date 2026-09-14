import os
import json
from typing import cast
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
import gradio as gr



#Initialize

load_dotenv(override=True)


openai_api_key = os.getenv("OPENAI_API_KEY")
MODEL ="gpt-4o-mini"

openai = OpenAI()

system_message = """
you are a librerian, that assists customers find books available, when
a customer asks about a book check the books we have an reply if it is instock
"""


#tool function
books_list =[
  {"book": "Muqaddimah", "author": "Ibn Khaldun"},
  {"book": "Al-Tahafut al-Tahafut", "author": "Al-Ghazali"},
  {"book": "Kitab al-Shifa", "author": "Avicenna (Ibn Sina)"},
  {"book": "Al-Muwatta", "author": "Imam Malik"},
  {"book": "Sahih al-Bukhari", "author": "Al-Bukhari"},
  {"book": "Al-Risala", "author": "Al-Shafi'i"},
  {"book": "Hayy ibn Yaqzan", "author": "Ibn Tufail"},
  {"book": "Fuṣūḥ al-Hikma", "author": "Rumi"},
  {"book": "Diwan al-Mutanabbi", "author": "Al-Mutanabbi"},
  {"book": "Al-Kamil fi al-Tarikh", "author": "Ibn Kathir"}
]

def get_check_list(book_name):
    return book_name in [book["book"] for book in books_list]




tools = cast(list[ChatCompletionToolParam], [{
    "type": "function",
    "function": {
        "name": "get_check_list",
        "description": "Check whether a book is available in the library.",
        "parameters": {
            "type": "object",
            "properties": {
                "book_name": {
                    "type": "string",
                    "description": "The title of the book to look up.",
                }
            },
            "required": ["book_name"],
            "additionalProperties": False,
        },
    },
}])

def handle_call(function_name,arg):
    if function_name == "get_check_list":
        return get_check_list(arg["book_name"])


    


#chat function and gradio

def chat(message,history):
    history =[{"role":h["role"],"content":h["content"]} for h in history]
    messages = cast(list[ChatCompletionMessageParam], [{"role":"system","content":system_message}]+history+[{"role":"user","content":message}])
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)

    tool_calls = response.choices[0].message.tool_calls or []
    if not tool_calls:
        yield response.choices[0].message.content or ""
        

    messages.append(cast(ChatCompletionMessageParam, response.choices[0].message))
    for tool_call in tool_calls:
        if tool_call.type != "function":
            continue

        arg = json.loads(tool_call.function.arguments)
        result = handle_call(tool_call.function.name,arg)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result),
        })

    stream = openai.chat.completions.create(model=MODEL,messages=messages, stream=True) #type:ignore
    result =""
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""
        yield result



gr.ChatInterface(fn=chat).launch(inbrowser=True)