import gradio as gr

from answer import answer_question
from ingest import sync_notion_notes


def chat_reply(message, history):
    """Append one grounded answer to the chat history.

    Args:
        message: Latest user question.
        history: Existing Gradio chat history.

    Returns:
        Updated chat history, cleared input value, and rendered sources markdown.
    """
    history = history or []  # ensures 'history' is a usable list instead of None
    answer_md, sources_md = answer_question(
        message, history=list(history)
    )  # here we are only passing in the old copy/SNAPSHOT of the history, list(history), without the latest user message

    # updated_history is purely to update Gradio's UI (separating this for ease of reference, not compulsory)
    updated_history = list(
        history
    )  # then we are saving another copy of the history, and then adding the latest user question/message with LLM answer. this avoids changing the same list object that was passed into answer_question()
    updated_history.append({"role": "user", "content": message})
    updated_history.append({"role": "assistant", "content": answer_md})
    return updated_history, "", sources_md


def build_ui():
    """Build the Gradio app for syncing notes and chatting over them.

    Returns:
        Configured `gr.Blocks` app instance.
    """
    with gr.Blocks(title="Notion Notes Assistant") as app:
        gr.Markdown(
            """
            # Notion Notes Assistant
            Sync your Notion notes into Chroma, then chat with answers grounded in your notes.
            """
        )

        with gr.Row():
            sync_button = gr.Button("Sync Notion", variant="primary")
            sync_status = gr.Textbox(label="Sync Status", interactive=False, lines=4)

        with gr.Row():
            chatbot = gr.Chatbot(label="Chat", type="messages", height=520)
            sources_output = gr.Markdown(label="Sources")

        with gr.Row():
            question = gr.Textbox(
                label="Message",
                placeholder="Ask something about your notes...",
                lines=2,
                scale=5,
            )
            ask_button = gr.Button("Send", variant="primary", scale=1)
            clear_button = gr.Button("Clear", scale=1)

        sync_button.click(fn=sync_notion_notes, outputs=sync_status)
        ask_button.click(
            fn=chat_reply,
            inputs=[question, chatbot],
            outputs=[chatbot, question, sources_output],
        )
        question.submit(
            fn=chat_reply,
            inputs=[question, chatbot],
            outputs=[chatbot, question, sources_output],
        )
        clear_button.click(
            lambda: ([], "", ""), outputs=[chatbot, question, sources_output]
        )

    return app


if __name__ == "__main__":
    build_ui().launch(inbrowser=True)
