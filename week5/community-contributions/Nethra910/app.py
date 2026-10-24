import gradio as gr
from dotenv import load_dotenv

from implementation.answer import answer_question

load_dotenv(override=True)


def format_context(context):
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"

    for doc in context:
        result += (
            f"<span style='color: #ff7800;'>"
            f"Source: {doc.metadata['source']}"
            f"</span>\n\n"
        )
        result += doc.page_content + "\n\n"

    return result


def chat(history):
    last_message = history[-1]["content"]

    # Gradio 6 can represent message content in different forms.
    # Make sure the current question is a string.
    if isinstance(last_message, list):
        last_message = "".join(
            item if isinstance(item, str) else str(item)
            for item in last_message
        )

    prior = history[:-1]

    answer, context = answer_question(last_message, prior)

    history.append({
        "role": "assistant",
        "content": answer
    })

    return history, format_context(context)


def main():

    def put_message_in_chatbot(message, history):
        history = history or []

        history.append({
            "role": "user",
            "content": message
        })

        return "", history

    theme = gr.themes.Soft(
        font=["Inter", "system-ui", "sans-serif"]
    )

    with gr.Blocks(
        title="CloudWay Expert Assistant"
    ) as ui:

        gr.Markdown(
            "#  CloudWay Expert Assistant\n"
            "Ask me anything about CloudWay!"
        )

        with gr.Row():

            with gr.Column(scale=1):

                chatbot = gr.Chatbot(
                    label="💬 Conversation",
                    height=600,
                    buttons=["copy_all"]
                )

                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about CloudWay...",
                    show_label=False,
                )

            with gr.Column(scale=1):

                context_markdown = gr.Markdown(
                    label=" Retrieved Context",
                    value="*Retrieved context will appear here*",
                    container=True,
                    height=600,
                )

        message.submit(
            put_message_in_chatbot,
            inputs=[message, chatbot],
            outputs=[message, chatbot]
        ).then(
            chat,
            inputs=chatbot,
            outputs=[chatbot, context_markdown]
        )

    ui.launch(
        inbrowser=True,
        theme=theme
    )


if __name__ == "__main__":
    main()

