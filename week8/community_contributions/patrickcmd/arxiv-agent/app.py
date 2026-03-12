import gradio as gr
from agent import run_agent

TOOL_ICONS = {
    "search_knowledge_base": "🔍",
    "search_arxiv": "📄",
    "ingest_papers": "📥",
    "get_paper_details": "ℹ️",
}


def format_sources(chunks) -> str:
    """Format retrieved chunks as a markdown reference list."""
    if not chunks:
        return "*No sources retrieved.*"

    lines: list[str] = []
    seen_titles: set[str] = set()
    for chunk in chunks:
        meta = chunk.metadata
        title = meta.get("title", "Unknown")
        if title in seen_titles:
            continue
        seen_titles.add(title)

        authors = meta.get("authors", "")
        url = meta.get("arxiv_url", "")
        category = meta.get("primary_category", "")
        published = meta.get("published", "")[:10]
        snippet = chunk.page_content[:200].replace("\n", " ")

        lines.append(
            f"**{len(lines) + 1}. [{title}]({url})**\n\n"
            f"*{authors}* · `{category}` · {published}\n\n"
            f"> {snippet}...\n\n---\n"
        )

    return "\n".join(lines) if lines else "*No sources retrieved.*"


def format_tool_log(tool_log: list[dict]) -> str:
    """Format the tool-usage log for the sidebar."""
    if not tool_log:
        return "*No tools used.*"

    lines: list[str] = []
    for i, entry in enumerate(tool_log, 1):
        tool = entry["tool"]
        args = entry["args"]
        icon = TOOL_ICONS.get(tool, "🔧")

        if tool == "search_knowledge_base":
            desc = f'Searched KB: "{args.get("query", "")}"'
        elif tool == "search_arxiv":
            desc = f'Searched arXiv: "{args.get("query", "")}"'
        elif tool == "ingest_papers":
            count = len(args.get("arxiv_urls", []))
            desc = f"Ingested {count} paper(s)"
        elif tool == "get_paper_details":
            desc = f'Paper details: {args.get("arxiv_url", "")}'
        else:
            desc = f"{tool}({args})"

        lines.append(f"{i}. {icon} {desc}")

    return "\n".join(lines)


def chat(user_message: str, history: list[dict]):
    """Handle a single chat turn via the agent."""
    llm_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
        if msg["role"] in ("user", "assistant")
    ]

    response, chunks, tool_log = run_agent(user_message, llm_history)
    return response, format_sources(chunks), format_tool_log(tool_log)


with gr.Blocks(title="arXiv Research Agent", theme=gr.themes.Soft()) as app:
    gr.Markdown("# arXiv Research Agent")
    gr.Markdown(
        "An **agentic** research assistant that can search papers, "
        "ingest new ones on the fly, and answer complex questions "
        "with multi-step reasoning."
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(type="messages")
            msg = gr.Textbox(
                placeholder="Ask a question about research papers...",
                show_label=False,
            )
            clear = gr.ClearButton([msg, chatbot])
        with gr.Column(scale=2):
            gr.Markdown("### Agent Activity")
            tools_display = gr.Markdown(
                "*Tool usage will appear here after you ask a question.*"
            )
            gr.Markdown("### Retrieved Sources")
            sources_display = gr.Markdown(
                "*Sources will appear here after you ask a question.*"
            )

    def respond(user_message, history):
        history = history + [{"role": "user", "content": user_message}]
        answer, sources_md, tools_md = chat(user_message, history)
        history = history + [{"role": "assistant", "content": answer}]
        return "", history, sources_md, tools_md

    msg.submit(
        respond,
        [msg, chatbot],
        [msg, chatbot, sources_display, tools_display],
    )

if __name__ == "__main__":
    app.launch(inbrowser=True)
