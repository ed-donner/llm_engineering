import json
import os

notebook_path = r'f:\CODE\Andela-AI-Engineering-Bootcamp\llm_engineering\week5\community-contributions\Mikeaig4real\week5 EXERCISE.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_cell_source = """import gradio as gr
from dotenv import load_dotenv

from implementation.answer import answer_question

load_dotenv(override=True)

def format_context(context):
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\\n\\n"
    for doc in context:
        result += f"<span style='color: #ff7800;'>Source: {doc.metadata.get('source', 'unknown')}</span>\\n\\n"
        result += doc.page_content + "\\n\\n"
    return result

def chat(history):
    last_message = history[-1]["content"]
    prior = history[:-1]
    answer, context = answer_question(last_message, prior)
    history.append({"role": "assistant", "content": answer})
    return history, format_context(context)

def put_message_in_chatbot(message, history):
    return "", history + [{"role": "user", "content": message}]

theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

# Added standard inputs and outputs logic for gradio chatbots
with gr.Blocks(title="Bugs Knowledge Base Assistant", theme=theme) as ui:
    gr.Markdown("# 🐛 Bugs Knowledge Base Assistant\\nAsk me anything about the codebase bugs!")

    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(
                label="💬 Conversation", height=600, type="messages", show_copy_button=True
            )
            message = gr.Textbox(
                label="Your Question",
                placeholder="Ask anything about the bugs...",
                show_label=False,
            )

        with gr.Column(scale=1):
            context_markdown = gr.Markdown(
                label="📚 Retrieved Context",
                value="*Retrieved context will appear here*",
                container=True,
                height=600,
            )

    message.submit(
        put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]
    ).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])

ui.launch(inbrowser=True)"""

lines = new_cell_source.split('\n')
source = [line + '\n' for line in lines[:-1]] + [lines[-1]]

new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {
        "id": "gradio_app_cell"
    },
    "outputs": [],
    "source": source
}

nb['cells'].append(new_cell)

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Gradio cell appended successfully using json!")
