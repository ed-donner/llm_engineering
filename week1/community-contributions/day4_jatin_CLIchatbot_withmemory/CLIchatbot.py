from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
conversation = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant."
    }
]
while True:
    prompt = input("You: ")

    if prompt.lower() == "exit":
        break
    conversation.append(
        {
            "role": "user",
            "content": prompt
        }
    )
    print(conversation)
    response = client.chat.completions.create(
        model="llama3.2",
        messages=conversation
    )
    assistant_reply=response.choices[0].message.content
    conversation.append({
        "role":"assistant",
        "content":assistant_reply
    })

    print("\nAssistant:")
    print(assistant_reply)
    print()