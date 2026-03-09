"""
Gradio chat UI for the Galdunx RAG chatbot.
Run from week5/IbrahimSheriff: python app.py
Or from repo root: python -m week5.IbrahimSheriff.app (if week5 is on path).
"""
import gradio as gr

from answer import answer_question
from ingest import fetch_documents, create_chunks, create_embeddings

_INGEST_MSG = (
    "The knowledge base is not loaded yet. Please click **Re-ingest knowledge base** below, "
    "or run from the terminal: `python week5/IbrahimSheriff/ingest.py`"
)


def _history_to_dicts(history):
    """Convert Gradio chat history to list[dict] with role and content."""
    out = []
    for msg in history or []:
        if isinstance(msg, (list, tuple)) and len(msg) >= 2:
            user_msg, assistant_msg = msg[0], msg[1]
            out.append({"role": "user", "content": user_msg})
            out.append({"role": "assistant", "content": assistant_msg})
        elif isinstance(msg, dict):
            out.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        else:
            role = getattr(msg, "role", "user")
            content = getattr(msg, "content", str(msg))
            out.append({"role": role, "content": content})
    return out


def chat(message, history):
    """Chat handler for Gradio: answer using RAG and return the reply text."""
    if not message or not message.strip():
        return ""
    history_dicts = _history_to_dicts(history)
    try:
        answer, _ = answer_question(message, history_dicts)
        return answer
    except Exception as e:
        if "does not exist" in str(e) or "NotFoundError" in type(e).__name__:
            return _INGEST_MSG
        raise


def run_ingest():
    """Run ingestion and return a status message."""
    try:
        documents = fetch_documents()
        chunks = create_chunks(documents)
        create_embeddings(chunks)
        return "Re-ingestion complete. Vector store updated."
    except Exception as e:
        return f"Re-ingestion failed: {e}"


def main():
    with gr.Blocks(title="Galdunx RAG Chat") as demo:
        gr.Markdown("# Galdunx Knowledge Assistant\nChat with the assistant about Galdunx and its services.")
        gr.ChatInterface(
            fn=chat,
            type="messages",
            textbox=gr.Textbox(placeholder="Ask about Galdunx...", container=False),
        )
        with gr.Row():
            ingest_btn = gr.Button("Re-ingest knowledge base")
            status = gr.Textbox(label="Status", interactive=False)
        ingest_btn.click(fn=run_ingest, outputs=status)
    demo.launch(inbrowser=True)


if __name__ == "__main__":
    main()
