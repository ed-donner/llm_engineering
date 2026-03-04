"""
ULTRA DUMMIE DESCRIPTION
------------------------
What this file does:
- It is the project's web screen (Gradio).
- It receives what the user types.
- It calls answer2.py to get an answer.
- It shows answer and retrieved context.

Internal steps:
1) Loads environment and imports answer_question from answer2.py.
2) Defines format_context() to render sources and retrieved text.
3) Defines chat():
   - takes last user message,
   - sends question + history to RAG backend,
   - appends assistant response to history,
   - returns updated chat + context for UI.
4) In main() it builds layout:
   - left: conversation
   - right: retrieved context
5) Starts Gradio server and opens browser.

Key logic:
- app2.py does not do retrieval or embeddings.
- It only orchestrates UI + calls to the engine (answer2.py).
"""

import gradio as gr  # Imports Gradio to build the web chat interface.
from dotenv import load_dotenv  # Imports function to load environment variables from .env.

from implementation.answer2 import answer_question  # Imports RAG backend function adapted to Ollama.

load_dotenv(override=True)  # Loads environment variables allowing overwrite of existing values.
DEBUG = True  # Enables or disables debug logs to trace UI events.


def dbg(message):  # Defines helper to print traces only when DEBUG is active.
    if DEBUG:  # Checks debug flag.
        print(f"[APP] {message}")  # Prints log with module prefix.


def format_context(context):  # Defines function to format retrieved context for UI display.
    dbg(f"Formatting context: {len(context)} docs")  # Traces how many docs will be rendered on right panel.
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"  # Starts HTML block with context title.
    for doc in context:  # Iterates through each retrieved document.
        result += f"<span style='color: #ff7800;'>Source: {doc.metadata['source']}</span>\n\n"  # Adds line with document source.
        result += doc.page_content + "\n\n"  # Adds document text content.
    return result  # Returns final formatted text to render in Markdown.


def chat(history):  # Defines callback that processes one conversation turn.
    dbg(f"chat() received with {len(history)} messages")  # Traces history size received from UI.
    last_message = history[-1]["content"]  # Takes content of last user message.
    prior = history[:-1]  # Separates previous history excluding last question.
    dbg(f"Last user message: {last_message}")  # Traces incoming question text.
    answer, context = answer_question(last_message, prior)  # Calls RAG backend to get answer and context.
    dbg(f"Answer generated. Context docs={len(context)}")  # Traces context volume returned by backend.
    history.append({"role": "assistant", "content": answer})  # Appends assistant response to history.
    dbg(f"History after response: {len(history)} messages")  # Traces final history size after append.
    return history, format_context(context)  # Returns updated history and formatted context.


def main():  # Defines main function that builds and launches the app.
    def put_message_in_chatbot(message, history):  # Defines helper to insert user message into chat.
        dbg(f"Captured user message: {message}")  # Traces text written by user.
        dbg(f"History before user append: {len(history)}")  # Traces history size before adding turn.
        return "", history + [{"role": "user", "content": message}]  # Clears input and adds user message to history.

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])  # Configures visual theme of the app.
    dbg("Building Gradio interface")  # Traces start of UI construction.

    with gr.Blocks(title="Insurellm Expert Assistant", theme=theme) as ui:  # Creates main interface container with title and theme.
        gr.Markdown("# Insurellm Expert Assistant\nAsk me anything about Insurellm!")  # Shows app header.

        with gr.Row():  # Creates a row to distribute columns.
            with gr.Column(scale=1):  # Creates left column for chat and text box.
                chatbot = gr.Chatbot(  # Creates chatbot conversation component.
                    label="Conversation", height=600, type="messages", show_copy_button=True  # Configures label, size, message type, and copy button.
                )  # Closes Chatbot component definition.
                message = gr.Textbox(  # Creates textbox to write questions.
                    label="Your Question",  # Defines logical input label.
                    placeholder="Ask anything about Insurellm...",  # Defines helper placeholder text.
                    show_label=False,  # Hides visual label for cleaner UI.
                )  # Closes Textbox definition.

            with gr.Column(scale=1):  # Creates right column to display retrieved context.
                context_markdown = gr.Markdown(  # Creates Markdown component to render context.
                    label="Retrieved Context",  # Defines context panel label.
                    value="*Retrieved context will appear here*",  # Defines initial text before first query.
                    container=True,  # Enables visual container around component.
                    height=600,  # Sets height to align with chat panel.
                )  # Closes Markdown component definition.

        message.submit(  # Configures event when sending text with Enter.
            put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]  # Step 1: inserts user message and clears input.
        ).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])  # Step 2: generates answer and updates displayed context.

    ui.launch(inbrowser=True)  # Starts Gradio server and opens browser automatically.
    dbg("Gradio server started")  # Traces server startup confirmation.


if __name__ == "__main__":  # Executes main only when this file runs as main script.
    main()  # Calls main function to start application.
