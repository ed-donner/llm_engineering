import gradio as gr
from dotenv import load_dotenv

from implementation.answer import answer_question

load_dotenv(override=True)


def format_context(context):
    result = "<h2 style='color: #1f77b4;'>Retrieved Clinical Context</h2>\n\n"
    for doc in context:
        source = doc.metadata.get("source", "Unknown")
        result += f"<b>Source:</b> {source}<br><br>"
        result += doc.page_content + "<br><br>"
    return result


def chat(history):
    last_message = history[-1]["content"]
    prior = history[:-1]

    answer, context = answer_question(last_message, prior)

    history.append({"role": "assistant", "content": answer})

    return history, format_context(context)


def main():

    def put_message_in_chatbot(message, history):
        return "", history + [{"role": "user", "content": message}]

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Drug Interaction System", theme=theme) as ui:

        gr.Markdown(
            "# Drug Interaction System\nAsk clinical questions about drug interactions, mechanisms, and safety considerations."
        )

        with gr.Row():

            with gr.Column(scale=1):

                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=600,
                    type="messages",
                    show_copy_button=True,
                )

                message = gr.Textbox(
                    placeholder="Example: Can metformin interact with propranolol?",
                    show_label=False,
                )

            with gr.Column(scale=1):

                context_markdown = gr.Markdown(
                    value="Retrieved pharmacology context will appear here.",
                    container=True,
                    height=600,
                )

        message.submit(
            put_message_in_chatbot,
            inputs=[message, chatbot],
            outputs=[message, chatbot],
        ).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()