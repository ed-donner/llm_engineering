import textwrap
import ollama
from PIL import Image, ImageDraw, ImageFont
import os
import sys
from datetime import datetime
import json

# -------------------------------
# CONFIG
# -------------------------------

MODEL_NAME = "llama3:latest"
SAVE_FOLDER = os.path.expanduser("~/AI_Screensaver")
STATE_FILE = "course_state.json"
HISTORY_FILE = "history.txt"

os.makedirs(SAVE_FOLDER, exist_ok=True)

# -------------------------------
# CURRICULUM STRUCTURE
# -------------------------------

COURSE = {
    "Week 1: Exploring Top Models": [
        "OpenAI API Call and System vs User Prompts",
        "LLM Engineering Building Blocks: Models, Tools & Techniques",
        "Frontier Models: OpenAI GPT, Claude, Gemini & Grok Compared",
        "Open-Source LLMs: LLaMA, Mistral, DeepSeek, and Ollama",
        "Chat Completions API: HTTP Endpoints vs OpenAI Python Client",
        "Using the OpenAI Python Client with Multiple LLM Providers",
        "Base, Chat, and Reasoning Models: Understanding LLM Types",
        "Understanding Transformers: The Architecture Behind GPT and LLMs",
        "Parameters: From Millions to Trillions in GPT, LLaMA & DeepSeek",
        "What Are Tokens? From Characters to GPT's Tokenizer",
        "Understanding Tokenization",
        "Context Windows, API Costs, and Token Limits in LLMs",
        "Chaining GPT Calls"
    ],
    "Week 2: LLMs, Gradio UI and Agents": [
        "Connecting to Multiple Frontier Models with APIs",
        "Local Models with Ollama and Native APIs",
        "LangChain vs LiteLLM",
        "Multi-Model Conversations",
        "Markdown Responses and Streaming with Gradio",
        "System Prompts and Multi-Shot Prompting",
        "Introduction to RAG",
        "How LLM Tool Calling Works",
        "Agentic AI Workflows",
        "Building Multi-Tool Workflows",
        "How Gradio Works"
    ],
    "Week 3: Open Source GenAI with Hugging Face": [
        "Hugging Face Platform Overview",
        "Transformers Library",
        "Hugging Face Pipelines",
        "Tokenizers: Text to Numbers",
        "Chat Templates and Special Tokens",
        "Comparing Tokenizers",
        "Deep Dive into Transformers and Quantization",
        "Inside LLaMA Architecture",
        "Running Open Source LLMs with Hugging Face",
        "Visualizing Token-by-Token Inference"
    ]
}

# Flatten curriculum into ordered list
CURRICULUM = []
for week, topics in COURSE.items():
    for topic in topics:
        CURRICULUM.append(f"{week} - {topic}")

# -------------------------------
# STATE MANAGEMENT
# -------------------------------

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"index": 0}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def get_next_topic():
    state = load_state()
    index = state["index"]

    topic = CURRICULUM[index % len(CURRICULUM)]

    state["index"] = index + 1
    save_state(state)

    return topic

# -------------------------------
# HISTORY MANAGEMENT
# -------------------------------

def get_recent_history(n=10):
    if not os.path.exists(HISTORY_FILE):
        return ""
    with open(HISTORY_FILE, "r") as f:
        lines = f.readlines()
    return "".join(lines[-n:])

def fact_exists(fact):
    if not os.path.exists(HISTORY_FILE):
        return False
    with open(HISTORY_FILE, "r") as f:
        history = f.read()
    return fact.strip() in history

def save_fact(fact):
    with open(HISTORY_FILE, "a") as f:
        f.write(fact.strip() + "\n")

# -------------------------------
# FACT GENERATION
# -------------------------------

def generate_unique_fact(topic, retries=5):
    recent_history = get_recent_history()

    prompt = f"""
You are an expert AI/ML instructor.

Topic: {topic}

Generate ONE concise technical fact under 18 words.
Rules:
- Must be strictly about AI, ML, LLMs, transformers, agents, APIs, or tokenization.
- No numbering.
- No commentary.
- No repetition of previous facts.
- Avoid vague statements.
- Be precise and technical.
- Avoid repeating ideas from below history.

Recent facts:
{recent_history}
"""

    for _ in range(retries):
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt
        )
        fact = response.get("response", "").strip()

        if fact and not fact_exists(fact):
            save_fact(fact)
            return fact

    return "Transformers use self-attention to model long-range token dependencies efficiently."

# -------------------------------
# IMAGE CREATION
# -------------------------------

def create_image(text):
    width, height = 1920, 1080

    # Change background color here if desired
    background_color = "#0F172A"  # dark slate blue
    text_color = "#FFFFFF"

    img = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 80)
    except:
        font = ImageFont.load_default()

    wrapped_text = textwrap.fill(text, width=38)

    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=20)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2
    y = (height - text_height) / 2

    draw.multiline_text(
        (x, y),
        wrapped_text,
        font=font,
        fill=text_color,
        align="center",
        spacing=20
    )

    filename = f"fact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(os.path.join(SAVE_FOLDER, filename))

# -------------------------------
# MAIN EXECUTION
# -------------------------------

if __name__ == "__main__":
    topic = get_next_topic()
    fact = generate_unique_fact(topic)

    final_text = f"{topic}\n\n{fact}"

    create_image(final_text)

    print("Topic:", topic)
    print("Fact:", fact)
    print("Image created successfully!")