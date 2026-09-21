import gradio as gr
from dotenv import load_dotenv

from implementation.answer import answer_question

load_dotenv(override=True)


def format_context(context):
    result = "<h2 style='color: #1a7f37;'>Relevant Context</h2>\n\n"
    for doc in context:
        result += f"<span style='color: #1a7f37;'>Source: {doc.metadata['source']}</span>\n\n"
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

    def put_example_in_chatbot(message, history):
        return history + [{"role": "user", "content": message}]

    theme = gr.themes.Soft(
        primary_hue="green",
        secondary_hue="blue",
        font=["Inter", "system-ui", "sans-serif"],
    )

    example_questions = [
        "Who won Group A?",
        "What was the score of the France vs Morocco quarterfinal?",
        "Which teams advanced as the best third-placed teams?",
        "When is the final being played and where?",
        "Which team eliminated the United States?",
    ]

    with gr.Blocks(title="World Cup 2026 Expert Assistant", theme=theme) as ui:
        gr.Markdown(
            "# ⚽ World Cup 2026 Expert Assistant\n"
            "Ask me anything about the FIFA World Cup 2026™ — groups, qualifying, "
            "results, and the knockout bracket, from qualifiers through the "
            "quarterfinals."
        )

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="💬 Conversation", height=600, type="messages", show_copy_button=True
                )
                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about the 2026 World Cup...",
                    show_label=False,
                )
                gr.Examples(
                    examples=example_questions,
                    inputs=message,
                    label="Try asking:",
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

    ui.launch(inbrowser=True, share=True)


if __name__ == "__main__":
    main()