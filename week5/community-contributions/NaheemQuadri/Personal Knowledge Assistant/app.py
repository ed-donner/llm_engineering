import gradio as gr
from dotenv import load_dotenv
from implementation.answer import answer_question

load_dotenv(override=True)


def format_context(context_docs: list, tool_used: str = ""):
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"

    if tool_used:
        result += f"<p><i>Retrieved via: <b>{tool_used}</b></i></p>\n\n"

    if not context_docs:
        result += "<p><i>Context retrieved from SQL (structured date query)</i></p>"
        return result

    for doc in context_docs:
        doc_type = doc.metadata.get('doc_type', '').upper()
        contact = doc.metadata.get('contact', '')
        date = doc.metadata.get('date', '')
        label = f"{doc_type} | {contact} | {date}"
        result += f"<span style='color: #ff7800;'>Source: {label}</span>\n\n"
        result += doc.page_content + "\n\n"

    return result


def chat(history):
    last_message = history[-1]["content"]
    prior = history[:-1]
    answer, docs = answer_question(last_message, prior)
    history.append({"role": "assistant", "content": answer})
    context_html = format_context(docs)
    return history, context_html


def main():
    def put_message_in_chatbot(message, history):
        return "", history + [{"role": "user", "content": message}]

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])
    with gr.Blocks(title="Naheem's Personal Knowledge Assistant", theme=theme) as ui:
        gr.Markdown("# 🧠 Naheem's Personal Knowledge Assistant\nAsk me anything about your calls, messages, and communications!")
        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="💬 Conversation", height=600, type="messages", show_copy_button=True
                )
                message = gr.Textbox(
                    label="Your Question",
                    placeholder="e.g. Who messaged me in January 2025?",
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
            put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]
        ).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])
    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()