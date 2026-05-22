"""
chat_app.py — Gradio chatbot for Research RAG with PDF upload.

Usage:
    uv run chat_app.py
"""

import os
import gradio as gr
from pathlib import Path
from dotenv import load_dotenv

from implementation.answer import (
    answer_question,
    get_vector_store,
    build_bm25_index,
    RetrievedChunk,
)
from DataIngestionPipeline.smartpdfprocessor import SmartPDFProcessor
from implementation.ingest import prepare_chunks_for_embedding

load_dotenv(override=True)

# ------------------------------------------------------------------ #
# INIT
# ------------------------------------------------------------------ #

vector_store = get_vector_store(use_cloud=True)
bm25_index = build_bm25_index(vector_store)

processor = SmartPDFProcessor(
    gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
    groq_api_key=os.getenv("GROQ_API_KEY", ""),
)


# ------------------------------------------------------------------ #
# UPLOAD
# ------------------------------------------------------------------ #

def upload_pdf(file, progress=gr.Progress()):
    global bm25_index

    if file is None:
        return "⚠️ No file selected.", gr.update()

    pdf_path = file.name if hasattr(file, "name") else str(file)
    filename = Path(pdf_path).name

    try:
        progress(0.1, desc="📄 Reading PDF...")
      

        progress(0.2, desc="🔍 Extracting text, tables, figures...")
        chunks = processor.process_pdf_rich(pdf_path)

        if not chunks:
            progress(0.35, desc="⚡ Rich mode failed. Falling back to fast mode...")
            chunks = processor.process_pdf_fast(pdf_path)

        if not chunks:
            return f"❌ No chunks produced from **{filename}**.", gr.update()

        progress(0.6, desc="🧠 Preparing embedding text...")
        chunks = prepare_chunks_for_embedding(chunks)

        progress(0.7, desc="🗑️ Removing old version...")
        source = chunks[0].metadata.get("source", "")

        if source:
            try:
                existing = vector_store.get(where={"source": source})
                if existing and existing.get("ids"):
                    vector_store.delete(ids=existing["ids"])
            except Exception:
                pass

        progress(0.82, desc="📦 Embedding and storing in Chroma Cloud...")
        vector_store.add_documents(chunks)

        progress(0.92, desc="🔄 Rebuilding BM25 index...")
        bm25_index = build_bm25_index(vector_store)

        progress(1.0, desc="✅ Done!")

        return (
            f"✅ **{filename}** ingested successfully. **{len(chunks)} chunks** embedded and searchable.",
            gr.update(interactive=False, value="✓ Ingested"),
        )

    except Exception as e:
        return f"❌ Upload failed: `{e}`", gr.update()


# ------------------------------------------------------------------ #
# CHAT
# ------------------------------------------------------------------ #

def format_sources_markdown(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "*No sources retrieved.*"

    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"

    for i, chunk in enumerate(chunks, 1):
        meta = chunk.metadata

        source = Path(meta.get("source", "")).name or "unknown"
        section = meta.get("section_title", "—")
        topic = meta.get("topic", "—")
        summary = meta.get("summary", "—")
        pages = f"{meta.get('page_start', '?')}–{meta.get('page_end', '?')}"
        score = f"{chunk.score:.3f}" if chunk.score else "—"
        eq_desc = meta.get("equation_description", "")

        result += f"<h3 style='color: #ff7800;'>Source {i}: {source}</h3>\n\n"
        result += f"**Section:** {section}  \n"
        result += f"**Topic:** {topic}  \n"
        result += f"**Summary:** {summary}  \n"
        result += f"**Pages:** {pages}  \n"
        result += f"**Score:** `{score}`  \n"

        if eq_desc and eq_desc != "none":
            result += f"**Equation:** {eq_desc}  \n"

        preview = chunk.page_content[:700]
        if len(chunk.page_content) > 700:
            preview += "..."

        result += f"\n```text\n{preview}\n```\n\n---\n\n"

    return result
def normalize_message_content(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return " ".join(parts).strip()

    return str(content)

from gradio import ChatMessage


def put_message_in_chatbot(message, history):
    if not message or not message.strip():
        return "", history

    history = history or []
    history.append({"role": "user", "content": message})
    return "", history


def get_msg_role(msg):
    if isinstance(msg, dict):
        return msg.get("role")
    return msg.role


def get_msg_content(msg):
    if isinstance(msg, dict):
        return msg.get("content")
    return msg.content


def chat(history, mode_val):
    if not history:
        return history, "*Ask a question to see retrieved sources here.*"

    last_message = normalize_message_content(get_msg_content(history[-1]))

    prior = []
    for msg in history[:-1]:
        prior.append({
            "role": get_msg_role(msg),
            "content": get_msg_content(msg),
        })

    answer, chunks = answer_question(
        question=last_message,
        history=prior,
        vector_store=vector_store,
        mode=mode_val,
        k=5,
        bm25_index=bm25_index,
    )

    history.append({"role": "assistant", "content": answer})

    return history, format_sources_markdown(chunks)


# ------------------------------------------------------------------ #
# APP
# ------------------------------------------------------------------ #

def create_app():
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Research RAG Assistant", theme=theme) as app:
        gr.Markdown("# 📚 Research RAG Assistant")
        gr.Markdown("Upload academic PDFs and ask grounded questions across your research documents.")

        with gr.Group():
            gr.Markdown("### 📤 Upload Paper")

            with gr.Row():
                pdf_input = gr.File(
                    label="Upload PDF",
                    file_types=[".pdf"],
                    scale=3,
                )
                ingest_btn = gr.Button(
                    "Ingest Paper",
                    variant="primary",
                    scale=1,
                )

            upload_status = gr.Markdown("*Upload status will appear here.*")

        with gr.Group():
            gr.Markdown("### ⚙️ Retrieval Mode")

            mode = gr.Radio(
                choices=["fast", "accurate"],
                value="fast",
                label="fast = hybrid retrieval, accurate = rewrite + rerank",
            )

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="💬 Conversation",
                    height=600,
                  
                  
                )

                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about your uploaded papers...",
                    show_label=False,
                )

                clear_btn = gr.Button("Clear chat", size="sm")

            with gr.Column(scale=1):
                context_markdown = gr.Markdown(
                    label="📚 Retrieved Context",
                    value="*Retrieved context will appear here.*",
                    container=True,
                    height=600,
                )

        ingest_btn.click(
            upload_pdf,
            inputs=[pdf_input],
            outputs=[upload_status, ingest_btn],
        )

        message.submit(
            put_message_in_chatbot,
            inputs=[message, chatbot],
            outputs=[message, chatbot],
        ).then(
            chat,
            inputs=[chatbot, mode],
            outputs=[chatbot, context_markdown],
        )

        clear_btn.click(
            lambda: ([], "*Retrieved context will appear here.*"),
            outputs=[chatbot, context_markdown],
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(inbrowser=True)