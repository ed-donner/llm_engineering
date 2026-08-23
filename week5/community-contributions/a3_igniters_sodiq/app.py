import gradio as gr
from dotenv import load_dotenv

from answer import answer_question

load_dotenv(override=True)


def format_context(context):
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"
    for doc in context:
        result += f"<span style='color: #ff7800;'>Source: {doc.metadata['source']}</span>\n\n"
        result += doc.page_content + "\n\n"
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

    with gr.Blocks(title="Nigerian Tax Expert Assistant", theme=theme) as ui:
        gr.Markdown("# 🇳🇬 Nigerian Tax Expert Assistant\nAsk me anything about Nigerian Tax Law!")

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="💬 Conversation", height=600, type="messages", show_copy_button=True
                )
                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about Nigerian tax (e.g., CIT, VAT, WHT)...",
                    show_label=False,
                )
                gr.Examples(
                    examples=[
                        "What is the current Company Income Tax (CIT) rate?",
                        "Who is exempt from paying Personal Income Tax?",
                        "How do I calculate Withholding Tax (WHT) on rent?",
                        "What are the penalties for late VAT filing?",
                        "Explain the Tertiary Education Tax (TET).",
                        "Is there a tax exemption for small businesses?",
                        "What is the deadline for filing annual tax returns?",
                        "How does the Finance Act affect Capital Gains Tax?",
                        "What items are exempt from Value Added Tax (VAT)?",
                        "Can I pay my taxes in installments?",
                    ],
                    inputs=[message],
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

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
