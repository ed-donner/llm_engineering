import textwrap
import ollama
from PIL import Image, ImageDraw, ImageFont
import os
import sys
from datetime import datetime


with open("/tmp/ai_screensaver.log", "a") as f:
    f.write(f"{datetime.now()} Python path: {sys.executable}\n")
    f.write(f"{datetime.now()} Working dir: {os.getcwd()}\n")


SAVE_FOLDER = os.path.expanduser("~/AI_Screensaver")
os.makedirs(SAVE_FOLDER, exist_ok=True)
HISTORY_FILE = "history.txt"

def get_recent_history(n=5):
    if not os.path.exists(HISTORY_FILE):
        return ""
    with open(HISTORY_FILE, "r") as f:
        lines = f.readlines()
    return "".join(lines[-n:])

def save_fact(fact):
    with open(HISTORY_FILE, "a") as f:
        f.write(fact + "\n")
TOPICS = ["LLM-Large Language Model", "RAG-Retrieval-Augmented Generation", "QLoRA-Quantized Low-Rank Adaptation", "Agents-AI Agents"]
CURRICULUM = {
    "LLM-Large Language Model": [
        "What is a token?",
        "What is next-token prediction?",
        "What is a transformer?",
        "What is attention?",
        "What are parameters?"
    ],
    "RAG-Retrieval-Augmented Generation": [
        "What is retrieval?",
        "Why embeddings?",
        "Vector databases?",
        "Similarity search?",
        "Context injection?"
    ],
    "QLoRA-Quantized Low-Rank Adaptation": [
        "Fine-tuning vs prompting",
        "What is LoRA?",
        "Why quantization?",
        "4-bit models?",
        "Memory efficiency?"
    ],
    "Agents-AI Agents": [
        "What is tool use?",
        "Planning loops?",
        "Reflection?",
        "Multi-step reasoning?",
        "State persistence?"
    ]
}

def get_next_topic():
    if not os.path.exists("topic_index.txt"):
        index = 0
    else:
        with open("topic_index.txt", "r") as f:
            index = int(f.read())

    topic = TOPICS[index % len(TOPICS)]

    with open("topic_index.txt", "w") as f:
        f.write(str(index + 1))

    return topic

import json
STATE_FILE = "topic_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {t:0 for t in TOPICS}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_next_subtopic(topic):
    state = load_state()
    idx = state.get(topic, 0)
    subtopic = CURRICULUM[topic][idx % len(CURRICULUM[topic])]
    state[topic] = idx + 1
    save_state(state)
    return subtopic


def get_ai_fact(topic):
    recent = get_recent_history()
    
    # Get next subtopic automatically
    subtopic = get_next_subtopic(topic)
    
    prompt = f"""Explain the following concept in the context of Large Language Models and Artifical Intelligence systems. The concept is 
    related to machine learning, not networking or IoT.Explain in ONE beginner-friendly technical sentence under 18 words:
'{subtopic}'
Do NOT include numbering, phases, commentary, or extra formatting.
Make it clear, concise, technical.
"""
    
    response = ollama.generate(
        model="llama3:latest",
        prompt=prompt
    )
    
    fact = response.get("response", "").strip()
    save_fact(fact)
    return fact




def create_image(text):
    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), "#0A192F") # Deep AI navy
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 90)
    except:
        font = ImageFont.load_default()

    # Better wrapping width
    wrapped_text = textwrap.fill(text, width=40)

    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=20)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center vertically with padding
    x = (width - text_width) / 2
    y = (height - text_height) / 2

    draw.multiline_text(
        (x, y),
        wrapped_text,
        font=font,
        fill="#FFFFFF",
        align="center",
        spacing=20
    )

    filename = f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(os.path.join(SAVE_FOLDER, filename))


    filename = f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(os.path.join(SAVE_FOLDER, filename))

if __name__ == "__main__":
    topic = get_next_topic()  # automatically rotates topics
    fact = get_ai_fact(topic)  # now works ✅
    heading = f"{topic} : "
    fact_text = heading + fact
    create_image(fact_text)
    print("Fact received:", fact_text)
    print("Image created successfully!")
