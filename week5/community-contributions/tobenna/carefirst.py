import gradio as gr
from dotenv import load_dotenv
from answer import answer_question

load_dotenv(override=True)


def format_context(chunks):
    result = "### Retrieved Context\n\n"
    for chunk in chunks:
        source = chunk.metadata.get("source", "Unknown")
        doc_type = chunk.metadata.get("type", "Unknown")
        result += f"**Source:** `{source}` ({doc_type})\n\n"
        result += chunk.page_content[:300]
        if len(chunk.page_content) > 300:
            result += "..."
        result += "\n\n---\n\n"
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

    theme = gr.themes.Soft(
        primary_hue="teal",
        secondary_hue="cyan",
        font=["Inter", "system-ui", "sans-serif"],
    )

    with gr.Blocks(title="PharmAssist - CareFirst Pharmacy", theme=theme) as ui:
        gr.Markdown(
            "# PharmAssist — CareFirst Pharmacy Assistant\n"
            "Ask me about medications, store policies, services, our team, or general health questions!"
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
                    placeholder="e.g. What are the side effects of ibuprofen?",
                    show_label=False,
                )

            with gr.Column(scale=1):
                context_markdown = gr.Markdown(
                    label="Retrieved Context",
                    value="*Retrieved context will appear here when you ask a question.*",
                    container=True,
                    height=600,
                )

        gr.Examples(
            examples=[
                "What are the side effects of Metformin?",
                "Can I return opened medication?",
                "Do you offer flu shots for children?",
                "Can I take ibuprofen with amoxicillin?",
                "How do I transfer my prescription from another pharmacy?",
                "What are your delivery hours?",
                "Does Dr. Chen speak Spanish?",
                "What OTC medications help with seasonal allergies?",
            ],
            inputs=message,
        )

        message.submit(
            put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]
        ).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
