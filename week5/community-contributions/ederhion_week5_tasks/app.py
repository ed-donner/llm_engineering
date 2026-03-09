import os
import gradio as gr
from dotenv import load_dotenv

from config import DB_NAME

# 1. Check for the database BEFORE importing answer.py
if not os.path.exists(DB_NAME) or not os.listdir(DB_NAME):
    print(f"Vector database not found or empty at {DB_NAME}. Running ingestion first...")
    from ingest import run_ingestion
    run_ingestion()

# 2. Import the RAG (Retrieval-Augmented Generation) pipeline
from answer import answer_question

load_dotenv(override=True)

def format_context(context):
    """Formats the retrieved document chunks into readable HTML."""
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"
    for doc in context:
        result += f"<span style='color: #ff7800;'>Source: {doc.metadata['source']}</span>\n\n"
        result += doc.page_content + "\n\n"
    return result

def put_message_in_chatbot(message, history):
    """Instantly displays the user's message in the chat UI before processing."""
    return "", history + [{"role": "user", "content": message}]

def chat(history):
    """Processes the conversation history and generates the assistant's response."""
    last_message = history[-1]["content"]
    prior = history[:-1]
    answer, context = answer_question(last_message, prior)
    history.append({"role": "assistant", "content": answer})
    return history, format_context(context)

def create_ui():
    """Defines and returns the Gradio application layout."""
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Oracle Database Engineering Assistant", theme=theme) as ui:
        gr.Markdown("# Oracle Database Engineering Assistant\nAsk me anything about Oracle Database!")

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="💬 Conversation", height=600, type="messages", show_copy_button=True
                )
                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about Oracle Database...",
                    show_label=False,
                )

            with gr.Column(scale=1):
                context_markdown = gr.Markdown(
                    label="📚 Retrieved Context",
                    value="*Retrieved context will appear here*",
                    container=True,
                    height=600,
                )

        # Connect the UI events to the backend functions
        message.submit(
            put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]
        ).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])
        
    return ui

def main():
    """Initializes and launches the application."""
    ui = create_ui()
    ui.launch(inbrowser=True)

if __name__ == "__main__":
    main()