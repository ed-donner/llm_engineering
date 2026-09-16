import gradio as gr
from dotenv import load_dotenv

from implementation.answer import answer_question

load_dotenv(override=True)


def format_context(context):
    if not context:
        return "### Retrieved Context\n\nNo relevant context found."

    result = "### 📚 Retrieved Context\n\n"

    for doc in context:
        source = doc.metadata.get("source", "Unknown")
        result += f"**Source:** `{source}`\n\n"
        result += f"{doc.page_content}\n\n---\n\n"

    return result


def chat(history):
    if not history:
        return history, "### 📚 Retrieved Context\n\nNo context yet."

    last_message = history[-1]["content"]
    prior = history[:-1]

    answer, context = answer_question(last_message, prior)

    history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    return history, format_context(context)


def main():
    def put_message_in_chatbot(message, history):
        if not message.strip():
            return "", history

        return "", history + [
            {
                "role": "user",
                "content": message,
            }
        ]

    theme = gr.themes.Soft(
        font=["Inter", "system-ui", "sans-serif"]
    )

    with gr.Blocks(
        title="Insurellm Expert Assistant",
        theme=theme,
    ) as ui:
        gr.Markdown(
            "# 🏢 Insurellm Expert Assistant\n"
            "Ask me anything about Insurellm!"
        )

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="💬 Conversation",
                    height=600,
                    type="messages",
                    show_copy_button=True,
                )

                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about Insurellm...",
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
            put_message_in_chatbot,
            inputs=[message, chatbot],
            outputs=[message, chatbot],
        ).then(
            chat,
            inputs=chatbot,
            outputs=[chatbot, context_markdown],
        )

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
