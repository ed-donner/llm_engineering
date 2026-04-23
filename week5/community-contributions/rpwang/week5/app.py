import gradio as gr
from dotenv import load_dotenv

from rag import answer_question


load_dotenv(override=True)


def format_context(context):
    if not context:
        return "*No context retrieved.*"

    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"
    for doc in context:
        source = doc.metadata.get("source", "unknown")
        doc_type = doc.metadata.get("doc_type", "unknown")
        result += f"<span style='color: #ff7800;'>Source: {source} ({doc_type})</span>\n\n"
        result += doc.page_content + "\n\n"
    return result


def chat(history, rolling_summary):
    last_message = history[-1]["content"]
    prior = history[:-1]
    answer, context, new_summary = answer_question(last_message, prior, rolling_summary)
    history.append({"role": "assistant", "content": answer})
    return history, format_context(context), new_summary


def main():
    def put_message_in_chatbot(message, history):
        return "", history + [{"role": "user", "content": message}]

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Insurellm RAG Assistant (rpwang)", theme=theme) as ui:
        gr.Markdown("# 🧠 Insurellm RAG Assistant (rpwang)\nUses week5/knowledge-base")

        rolling_summary_state = gr.State("")

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="💬 Conversation", height=600, type="messages", show_copy_button=True
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
            inputs=[chatbot, rolling_summary_state],
            outputs=[chatbot, context_markdown, rolling_summary_state],
        )

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
