from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv(override=True)


api_key = os.getenv('GROQ_API_KEY')


GROQ_BASE_URL = "https://api.groq.com/openai/v1"

groq = OpenAI(
    api_key=api_key,
    base_url=GROQ_BASE_URL
)

def chat(messages: list):
    stream = groq.chat.completions.create(
        model = "openai/gpt-oss-120b",
        messages=messages,
        stream=True
    )
    result = ""
    for chunk in stream:
        content = chunk.choices[0].delta.content or ""
        if content:
            result += content
            yield content
    # return result
        


try:
    user_message = input("USER: ")
    messages = [
        {"role":"system", "content" : "you are an assisstant with a great sense of humour. Your replies often contains jokes. you can talk in hindi and english. You always reply in roman script. You reply in Hinglish when user replies in hindi"},
        {"role" : "user", "content": user_message}
    ]

    while user_message:
        print(f"AI: ", end = "")
        text = ""
        for message in chat(messages=messages):
            print(message, end = "", flush=True)
            text += message
        print()
        
        user_message = input("USER: ")
        messages.extend(
            [
                {"role" : "assistant", "content" : text},
                {"role" : "user", "content" : user_message}
            ]
        )
        
        
        
except Exception as e:
    print(f"error: {e}")
    