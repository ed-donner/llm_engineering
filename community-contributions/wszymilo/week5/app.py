"""
Gradio app: Tab 1 Ingest (upload .docx/.pdf/.txt, ingest into FAISS),
Tab 2 Answer (chat + sources panel). Temp dir via mkdtemp; cleared on new upload;
removed on app closure.
"""

import atexit
import shutil
import tempfile
from pathlib import Path

import gradio as gr

from ingest import run_ingestion, load_vectorstore
from rag import answer_question

# Temporary directory created at startup; removed on process exit
_temp_dir = tempfile.mkdtemp(prefix="rag_exercise_")


def _cleanup_temp():
    try:
        shutil.rmtree(_temp_dir, ignore_errors=True)
    except Exception:
        pass


atexit.register(_cleanup_temp)

ALLOWED_EXTENSIONS = {".docx", ".pdf", ".txt"}


def _clear_and_save_uploads(uploaded_files, state):
    """On new upload: wipe temp dir, copy uploaded files into it. Return new state."""
    if not state:
        state = {"temp_dir": _temp_dir, "faiss_index_path": None, "vectorstore": None}
    temp_dir = state.get("temp_dir") or _temp_dir
    # Wipe temp dir contents (including faiss_index)
    path = Path(temp_dir)
    for child in path.iterdir():
        try:
            if child.is_file():
                child.unlink()
            else:
                shutil.rmtree(child, ignore_errors=True)
        except Exception:
            pass
    # Save uploaded files into temp dir (Gradio returns list of paths)
    if uploaded_files:
        for f in uploaded_files:
            src = f if isinstance(f, str) else getattr(f, "name", None)
            if src and Path(src).exists():
                dest = path / Path(src).name
                shutil.copy2(src, dest)
    # New upload wipes vectorstore until user clicks Ingest again
    state["faiss_index_path"] = None
    state["vectorstore"] = None
    return state


def format_context(chunks):
    """Format reranked chunks for the sources panel (like week5/app.py)."""
    if not chunks:
        return "*No sources retrieved.*"
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"
    for doc in chunks:
        src = doc.metadata.get("source", "—")
        result += f"<span style='color: #ff7800;'>Source: {src}</span>\n\n"
        result += doc.page_content + "\n\n"
    return result


def do_ingest(state, progress=gr.Progress()):
    """Run ingestion from temp dir; update state with faiss path and vectorstore."""
    if not state or not state.get("temp_dir"):
        state = {"temp_dir": _temp_dir, "faiss_index_path": None, "vectorstore": None}
    temp_dir = state["temp_dir"]

    def report(p, msg):
        progress(p, desc=msg)

    try:
        faiss_index_path = run_ingestion(temp_dir, progress_callback=report)
        vectorstore = load_vectorstore(faiss_index_path)
        state["faiss_index_path"] = faiss_index_path
        state["vectorstore"] = vectorstore
        return state, "Ingestion complete. You can switch to the Answer tab and ask questions."
    except Exception as e:
        return state, f"Ingestion failed: {e}"


def chat_turn(message, history, state):
    """One chat turn: run RAG, append assistant reply, return history and formatted sources."""
    if not state or not state.get("vectorstore"):
        return history, "*Please ingest documents first (Data tab).*"
    history = history + [{"role": "user", "content": message}]
    try:
        answer, chunks = answer_question(message, history[:-1], state["vectorstore"])
        history = history + [{"role": "assistant", "content": answer}]
        return history, format_context(chunks)
    except Exception as e:
        history = history + [{"role": "assistant", "content": f"Error: {e}"}]
        return history, format_context([])


def main():
    theme = gr.themes.Soft(primary_hue=gr.themes.colors.orange, font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="RAG Exercise", theme=theme) as ui:
        gr.Markdown("# RAG with your documents\nUpload .docx, .pdf, or .txt and ask questions.")

        state = gr.State(
            {"temp_dir": _temp_dir, "faiss_index_path": None, "vectorstore": None}
        )

        with gr.Tabs():
            with gr.TabItem("Data / Ingest", id=1):
                gr.Markdown("Upload documents. Each new upload clears the previous set. Then click **Ingest**.")
                file_input = gr.File(
                    label="Upload files",
                    file_count="multiple",
                    file_types=[".docx", ".pdf", ".txt"],
                )
                ingest_btn = gr.Button("Ingest")
                ingest_status = gr.Textbox(
                    label="Status",
                    value="Upload files and click Ingest.",
                    interactive=False,
                )
                file_input.change(
                    fn=lambda files, s: (_clear_and_save_uploads(files or [], s), "Files saved. Click Ingest to build the index."),
                    inputs=[file_input, state],
                    outputs=[state, ingest_status],
                )
                ingest_btn.click(
                    fn=do_ingest,
                    inputs=[state],
                    outputs=[state, ingest_status],
                )

            with gr.TabItem("Answer", id=2):
                gr.Markdown("Ask questions about your documents. Ingest first if you haven't.")
                with gr.Row():
                    with gr.Column(scale=1):
                        chatbot = gr.Chatbot(
                            label="Conversation",
                            height=500,
                            type="messages",
                            show_copy_button=True,
                        )
                        msg_in = gr.Textbox(
                            label="Your question",
                            placeholder="Ask anything about your documents…",
                            show_label=False,
                        )
                    with gr.Column(scale=1):
                        context_md = gr.Markdown(
                            label="Retrieved context (after rerank)",
                            value="*Retrieved context will appear here after you ask a question.*",
                            container=True,
                            height=500,
                        )
                msg_in.submit(
                    fn=lambda m, h, s: chat_turn(m, h, s),
                    inputs=[msg_in, chatbot, state],
                    outputs=[chatbot, context_md],
                ).then(
                    fn=lambda: "",
                    inputs=[],
                    outputs=[msg_in],
                )

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
