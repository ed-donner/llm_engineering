"""
Gradio chat UI for the LiteLLM RAG Knowledge Worker. Run from project dir: uv run app.py
"""
import gradio as gr

from answer import answer_question


def format_context(docs):
    """Format retrieved chunks as HTML for the context panel."""
    if not docs:
        return "*No context retrieved.*"
    lines = ["<h3>Relevant Context</h3>"]
    for d in docs:
        src = d.metadata.get("source", "—")
        lines.append(f"<p><strong>Source:</strong> {src}</p>")
        lines.append(f"<pre style='white-space: pre-wrap;'>{d.page_content[:2000]}</pre>")
    return "\n".join(lines)


def print_context_to_console(docs):
    """Print retrieved context to terminal for debugging/inspection."""
    print("\n" + "=" * 80)
    print("Relevant Context")
    print("=" * 80)
    if not docs:
        print("No context retrieved.")
        print("=" * 80)
        return
    for idx, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "—")
        snippet = d.page_content[:800]
        print(f"[{idx}] Source: {src}")
        print(snippet)
        print("-" * 80)
    print("=" * 80)


def chat(history):
    """Append assistant reply and return updated history and context HTML."""
    if not history:
        return history, "*No message.*"
    last = history[-1]
    if last.get("role") != "user":
        return history, "*Send a message first.*"
    user_msg = last["content"]
    prior = history[:-1]
    answer, context_docs = answer_question(user_msg, prior)
    print_context_to_console(context_docs)
    history = history + [{"role": "assistant", "content": answer}]
    return history, format_context(context_docs)


def main():
    def submit(message, history):
        history = history or []
        if not message or not message.strip():
            return "", history
        new_history = history + [{"role": "user", "content": message.strip()}]
        return "", new_history

    with gr.Blocks(title="LiteLLM Documentation Assistant") as ui:
        gr.Markdown("# LiteLLM Documentation Assistant\nAsk anything about LiteLLM.")
        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500,
                )
                msg = gr.Textbox(
                    placeholder="Ask anything about LiteLLM...",
                    show_label=False,
                )
            with gr.Column(scale=1):
                context_md = gr.Markdown(
                    value="*Retrieved context will appear here.*",
                    elem_id="context",
                    height=500,
                )
        msg.submit(submit, inputs=[msg, chatbot], outputs=[msg, chatbot]).then(
            chat, inputs=chatbot, outputs=[chatbot, context_md]
        )
    ui.launch(theme=gr.themes.Soft(), inbrowser=True)


if __name__ == "__main__":
    main()
