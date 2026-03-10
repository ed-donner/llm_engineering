import gradio as gr
from answer import answer_question


def format_sources(chunks) -> str:
    """Format retrieved chunks as a markdown reference list."""
    if not chunks:
        return "*No sources retrieved.*"

    lines = []
    seen_titles = set()
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.metadata
        title = meta.get("title", "Unknown")
        authors = meta.get("authors", "")
        url = meta.get("arxiv_url", "")
        category = meta.get("primary_category", "")
        published = meta.get("published", "")[:10]
        snippet = chunk.page_content[:200].replace("\n", " ")

        if title not in seen_titles:
            seen_titles.add(title)
            lines.append(
                f"**{len(seen_titles)}. [{title}]({url})**\n\n"
                f"*{authors}* · `{category}` · {published}\n\n"
                f"> {snippet}...\n\n---\n"
            )

    return "\n".join(lines) if lines else "*No sources retrieved.*"


def chat(user_message: str, history: list[dict]):
    """Handle a chat turn and return the answer + formatted sources."""
    llm_history = []
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            llm_history.append({"role": msg["role"], "content": msg["content"]})

    response, chunks = answer_question(user_message, llm_history)
    sources_md = format_sources(chunks)
    return response, sources_md


with gr.Blocks(title="arXiv Research Assistant", theme=gr.themes.Soft()) as app:
    gr.Markdown("# arXiv Research Assistant")
    gr.Markdown("Ask questions about the ingested arXiv papers. Follow-up questions are supported.")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(type="messages")
            msg = gr.Textbox(placeholder="Ask a question...", show_label=False)
            clear = gr.ClearButton([msg, chatbot])
        with gr.Column(scale=2):
            gr.Markdown("### Retrieved Sources")
            sources_display = gr.Markdown("*Sources will appear here after you ask a question.*")

    def respond(user_message, history):
        history = history + [{"role": "user", "content": user_message}]
        answer, sources_md = chat(user_message, history)
        history = history + [{"role": "assistant", "content": answer}]
        return "", history, sources_md

    msg.submit(respond, [msg, chatbot], [msg, chatbot, sources_display])

if __name__ == "__main__":
    app.launch(inbrowser=True)