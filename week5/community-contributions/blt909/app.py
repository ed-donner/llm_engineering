import gradio as gr
from pathlib import Path
from chromadb import PersistentClient
from dotenv import load_dotenv

from answer import answer_question

load_dotenv(override=True)

# Display all collections available if multiple documentation loaded in chroma
DB_NAME = str(Path(__file__).parent / "rst_doc_db")
chroma = PersistentClient(path=DB_NAME)
collections = [c.name for c in chroma.list_collections()]

def format_context(context):
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"
    for doc in context:
        result += f"<span style='color: #ff7800;'>Source: {doc.metadata['source']}</span>\n\n"
        result += doc.page_content + "\n\n"
    return result


def chat(history, repo):
    last_message = history[-1]["content"]
    prior = history[:-1]
    answer, context = answer_question(last_message, repo, prior)
    history.append({"role": "assistant", "content": answer})
    return history, format_context(context)


def main():
    def put_message_in_chatbot(message, history):
        return "", history + [{"role": "user", "content": message}]

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Technical documentation mentor", theme=theme) as ui:
        gr.Markdown("# 🏢 Awesome mentor on the line\nAsk me anything about your documentation !")

        with gr.Row():
            with gr.Column(scale=1):
                repo = gr.Dropdown(
                    label="Select the repository you need answer from",
                    choices=collections,
                )
                chatbot = gr.Chatbot(
                    label="💬 Conversation", height=600, type="messages", show_copy_button=True
                )
                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything",
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
        ).then(chat, inputs=[chatbot, repo], outputs=[chatbot, context_markdown])

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
