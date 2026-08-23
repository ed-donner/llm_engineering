from openai import OpenAI
from IPython.display import display, Markdown

gpt_client = OpenAI()
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
qwen_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

gpt_model = "gpt-5.4-nano"
ollama_model = "gpt-oss:20b-cloud"
qwen_model = "qwen3.5:397b-cloud"

gpt_system = "You are a Real Madrid fan who is very argumentative; you disagree with anything in the conversation and you challenge everything, in a snarky way."

ollama_system = "You are a very polite, Arsenal fan. You try to agree with everything the other person says, or find common ground. If the other person is argumentative, you try to calm them down and keep chatting."

qwen_system = "You are a Liverpool fan who is trying to prove to them Liverpool is the best from these three clubs."

gpt_messages = ["Hi there"]
ollama_messages = ["Hi"]
qwen_messages = ["Hello guys"]


def call_gpt():
    messages = [{"role": "system", "content": gpt_system}]
    for gpt, ollama, qwen in zip(gpt_messages, ollama_messages, qwen_messages):
        messages.append({"role": "assistant", "content": gpt})
        messages.append({"role": "user", "content": f"Arsenal fan: {ollama}"})
        messages.append({"role": "user", "content": f"Liverpool fan: {qwen}"})

    response = gpt_client.chat.completions.create(
        model=gpt_model,
        messages=messages
    )
    return response.choices[0].message.content


def call_ollama():
    messages = [{"role": "system", "content": ollama_system}]
    for gpt, qwen, ollama_msg in zip(gpt_messages, qwen_messages, ollama_messages):
        messages.append({"role": "user", "content": f"Real Madrid fan: {gpt}"})
        messages.append({"role": "user", "content": f"Liverpool fan: {qwen}"})
        messages.append({"role": "assistant", "content": ollama_msg})

    response = ollama_client.chat.completions.create(
        model=ollama_model,
        messages=messages
    )
    return response.choices[0].message.content


def call_qwen():
    messages = [{"role": "system", "content": qwen_system}]
    for gpt, ollama, qwen in zip(gpt_messages, ollama_messages, qwen_messages):
        messages.append({"role": "user", "content": f"Real Madrid fan: {gpt}"})
        messages.append({"role": "user", "content": f"Arsenal fan: {ollama}"})
        messages.append({"role": "assistant", "content": qwen})

    response = qwen_client.chat.completions.create(
        model=qwen_model,
        messages=messages
    )
    return response.choices[0].message.content


display(Markdown(f"### GPT:\n{gpt_messages[0]}\n"))
display(Markdown(f"### Ollama:\n{ollama_messages[0]}\n"))
display(Markdown(f"### Qwen:\n{qwen_messages[0]}\n"))

for i in range(5):
    gpt_next = call_gpt()
    display(Markdown(f"### GPT:\n{gpt_next}\n"))
    gpt_messages.append(gpt_next)

    ollama_next = call_ollama()
    display(Markdown(f"### Ollama:\n{ollama_next}\n"))
    ollama_messages.append(ollama_next)

    qwen_next = call_qwen()
    display(Markdown(f"### Qwen:\n{qwen_next}\n"))
    qwen_messages.append(qwen_next)