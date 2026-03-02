import base64
import json
import os
import sqlite3
import sys
from io import BytesIO

import gradio as gr
import pymupdf
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

load_dotenv(override=True)
openai_api_key = os.getenv("OPENAI_API_KEY")
open_router_api_key = os.getenv("OPENROUTER_API_KEY")

MODEL_OPENAI = "gpt-4o-mini"
LOCAL_MODEL_OPENAI = "gpt-oss:20b"

open_ai_model = ""

if (
    openai_api_key
    and openai_api_key.startswith("sk-proj-")
    and len(openai_api_key) > 10
):
    open_ai_model = MODEL_OPENAI
    print("API key looks good so far")
    openai = OpenAI()
else:
    print(
        f"Couldn't find your API keys. Would proceed to use local model {LOCAL_MODEL_OPENAI} provided by Ollama"
    )
    open_ai_model = LOCAL_MODEL_OPENAI
    openai = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

if open_router_api_key:
    print(f"Open Router API Key exists and begins {open_router_api_key[:8]}")
else:
    print("Open Router API Key not set")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

IMAGE_MODEL = "x/z-image-turbo"
AUDIO_MODEL = "legraphista/Orpheus"

openrouter = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=open_router_api_key)

DB = "roles.db"


def read_pdf_file(file_path):
    text = ""
    if file_path.endswith(".pdf"):
        doc = pymupdf.open(file_path)
        for page in doc:
            text += page.get_text()
        return text
    else:
        return None


system_message = """
You are a helpful career coach.
Give short, courteous answers, no more than 100 words.
Inform the user about the skills required for the job title they are interested in.
Always be accurate. If you don't know the answer, say so.
"""

link_system_prompt = """
You are provided with a possible job titles that fit this resume.
You are able to decide which of the job titles are most relevant to the resume,
You should respond in JSON as in this example:

{
    "titles": [
        {"role": "software engineer", "skills": ["python", "javascript", "sql", "git", "docker", "kubernetes"]},
        {"role": "data engineer", "skills": ["python", "javascript", "sql", "git", "docker", "kubernetes"]}
    ]
}
"""

skills_function = {
    "name": "get_title_skills",
    "description": "Get the skills required for a job title.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The job title that the customer wants to get the skills for",
            },
        },
        "required": ["title"],
        "additionalProperties": False,
    },
}
tools = [{"type": "function", "function": skills_function}]


def get_links_user_prompt(resume_path):
    if not read_pdf_file(resume_path):
        print("Valid path to resume file")
        sys.exit(1)
    else:
        resume = read_pdf_file(resume_path)

    user_prompt = f"""
I extracted these information from this resume \n
{resume}\n
create a list of possible job titles that fit this resume.
"""
    return user_prompt


link_system_prompt = """
You are provided with a possible job titles that fit this resume.
You are able to decide which of the job titles are most relevant to the resume,
You should respond in JSON as in this example:

{
    "titles": [
        {"role": "software engineer", "skills": "python, javascript, sql, git, docker, kubernetes"},
        {"role": "data engineer", "skills": "python, javascript, sql, git, docker, kubernetes"}
    ]
}
"""


def suitable_job_titles(resume_path, model):
    stream = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(resume_path)},
        ],
        response_format={"type": "json_object"},
        stream=True,
    )

    response = ""
    for chunk in stream:
        content = chunk.choices[0].delta.content or ""
        response += content
        print(content, end="", flush=True)

    # Convert the string into a Python object
    try:
        response_json = json.loads(response)
    except json.JSONDecodeError:
        print("Warning: failed to parse JSON. Returning raw string.")
        response_json = response

    return response_json


def populate_db(job_titles):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role TEXT PRIMARY KEY,
                skills TEXT
            )
        """)

        for title in job_titles["titles"]:
            skills_list = title["skills"]
            skills_json = json.dumps(skills_list)

            cursor.execute(
                "INSERT OR REPLACE INTO roles (role, skills) VALUES (?, ?)",
                (title["role"], skills_json),
            )

        conn.commit()


resume_path = input("Enter the path to the resume file: ")

job_titles = suitable_job_titles(resume_path, open_ai_model)
populate_db(job_titles)


def get_title_skills(title):
    print(f"DATABASE TOOL CALLED: Getting skills for {title}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT skills FROM roles WHERE LOWER(role) = LOWER(?)", (title,)
        )
        row = cursor.fetchone()
        skills = json.loads(row[0])
        return (
            f"Skills for {title} are {skills}"
            if skills
            else "No skills data available for this title"
        )


def talker(message):
    response = openrouter.chat.completions.create(
        model="openai/gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "onyx", "format": "pcm16"},
        messages=[{"role": "user", "content": message}],
        stream=True,
    )

    with open("output.raw", "wb") as f:
        for chunk in response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            audio_delta = getattr(delta, "audio", None)

            # Use getattr to safely check for the 'audio' attribute
            if audio_delta:
                # The data is base64 encoded; decode it to bytes before writing
                b64_data = (
                    audio_delta.get("data")
                    if isinstance(audio_delta, dict)
                    else getattr(audio_delta, "data", None)
                )
                if b64_data:
                    f.write(base64.b64decode(b64_data))


def handle_tool_calls_and_return_cities(message):
    responses = []
    cities = []
    for tool_call in message.tool_calls:
        if tool_call.function.name == "get_title_skills":
            arguments = json.loads(tool_call.function.arguments)
            title = arguments.get("title")
            cities.append(title)
            skills_details = get_title_skills(title)
            responses.append(
                {
                    "role": "tool",
                    "content": skills_details,
                    "tool_call_id": tool_call.id,
                }
            )
    return responses, cities


def artist(skills):
    image_response = openai.images.generate(
        model=IMAGE_MODEL,
        prompt=f"Present the skills required for {skills} in a visual way",
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )

    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))


def chat(history):
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = [{"role": "system", "content": system_message}] + history
    response = openai.chat.completions.create(
        model=open_ai_model, messages=messages, tools=tools
    )
    skills = []
    image = None

    while response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        responses, cities = handle_tool_calls_and_return_cities(message)
        messages.append(message)
        messages.extend(responses)
        response = openai.chat.completions.create(
            model=open_ai_model, messages=messages, tools=tools
        )

    reply = response.choices[0].message.content
    history += [{"role": "assistant", "content": reply}]

    voice = talker(reply)

    if skills:
        image = artist(skills[0])

    return history, voice, image


def handle_tool_calls_and_return_skills(message):
    responses = []
    skills = []
    for tool_call in message.tool_calls:
        if tool_call.function.name == "get_title_skills":
            arguments = json.loads(tool_call.function.arguments)
            title = arguments.get("title")
            skills.append(title)
            skills_details = get_title_skills(title)
            responses.append(
                {
                    "role": "tool",
                    "content": skills_details,
                    "tool_call_id": tool_call.id,
                }
            )
    return responses, skills


def put_message_in_chatbot(message, history):
    return "", history + [{"role": "user", "content": message}]


with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=300, type="messages")
        image_output = gr.Image(height=300, interactive=False)
    with gr.Row():
        audio_output = gr.Audio(type="filepath")
    with gr.Row():
        message = gr.Textbox(label="Chat with our AI Assistant:")

    # Hooking up events to callbacks

    message.submit(
        put_message_in_chatbot,
        inputs=[message, chatbot],
        outputs=[message, chatbot],
    ).then(chat, inputs=chatbot, outputs=[chatbot, audio_output, image_output])

ui.launch()
