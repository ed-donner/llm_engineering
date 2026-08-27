from openai import OpenAI


system_prompt = "You are a helpful assistant in summarizing youtube videos."
user_prompt = "Please summarize the following youtube video: https://www.youtube.com/watch?v=dQw4w9WgXcQ"

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages
)

print(response.choices[0].message.content)
print(response)